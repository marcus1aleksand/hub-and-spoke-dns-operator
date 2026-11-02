"""Regression tests for the container image and HTTP server lifecycle.

These cover bugs that unit tests on the source tree cannot catch:
  1. Dockerfile not copying every module that main.py imports, so the image
     crashes at startup with ModuleNotFoundError.
  2. main() shutting the aiohttp server down immediately, so the /healthz and
     /readyz probes the chart relies on never answer.
"""

import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

OPERATOR_DIR = Path(__file__).parent
DOCKERFILE = OPERATOR_DIR / "Dockerfile"
REQUIREMENTS = OPERATOR_DIR / "requirements.txt"

# A free high port so the lifecycle test never collides with a real service.
TEST_PORT = 18099


def _requirement_names():
    """Top-level distribution names from requirements.txt."""
    names = set()
    for line in REQUIREMENTS.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        names.add(re.split(r"[=<>!~;\[\s]", line, maxsplit=1)[0].strip().lower())
    return names


def _copied_sources():
    """Return the paths the Dockerfile copies into the image."""
    copied = []
    for line in DOCKERFILE.read_text().splitlines():
        match = re.match(r"^COPY\s+(\S+)\s+\S+$", line.strip())
        if match:
            copied.append(match.group(1).rstrip("/"))
    return copied


def test_dockerfile_exists():
    assert DOCKERFILE.is_file(), "operator/Dockerfile must exist to build the image"


def test_dockerfile_copies_annotations_module():
    """main.py does 'from annotations import ...', so annotations.py must ship."""
    assert "annotations.py" in _copied_sources(), (
        "Dockerfile must COPY annotations.py; main.py imports it and the "
        "container crashes on startup with ModuleNotFoundError"
    )


def test_dockerfile_copies_every_local_module_main_imports():
    """Every first-party module main.py imports must be present in the image."""
    main_source = (OPERATOR_DIR / "main.py").read_text()
    imported = {
        name
        for pair in re.findall(r"^from\s+(\w+)\s+import|^import\s+(\w+)", main_source, re.M)
        for name in pair
        if name
    }

    # Anything installable via requirements.txt is provided by pip, not COPY.
    installed = _requirement_names() | {
        "os",
        "logging",
        "asyncio",
        "time",
        "pytest",
        "json",
        "re",
        "sys",
    }
    local_modules = sorted(name for name in imported - installed if name not in ("main", "providers"))

    copied = set(_copied_sources())
    missing = [name for name in local_modules if name + ".py" not in copied]
    assert not missing, "Dockerfile does not copy local module(s) imported by main.py: " f"{missing}"


# main.py builds a provider at import time, so the import needs the same env
# the chart injects into the container.
CONTAINER_ENV = {
    "CLOUD_PROVIDER": "azure",
    "MANAGED_IDENTITY_CLIENT_ID": "test",
    "AZURE_SUBSCRIPTION_ID": "test",
    "AZURE_DNS_ZONE": "example.com",
    "AZURE_DNS_RESOURCE_GROUP": "test",
    "CUSTOM_TTL": "300",
}


def test_image_filesystem_can_import_main(tmp_path):
    """Reproduce the image layout from the Dockerfile, then import main."""
    for src in _copied_sources():
        source_path = OPERATOR_DIR / src
        if source_path.is_dir():
            shutil.copytree(source_path, tmp_path / src, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, tmp_path / src)

    script = (
        "import os, sys\n"
        "from unittest.mock import MagicMock, patch\n"
        "sys.path.insert(0, " + repr(str(tmp_path)) + ")\n"
        "os.environ.update(" + repr(CONTAINER_ENV) + ")\n"
        "with patch('kubernetes.config.load_incluster_config', MagicMock()), \\\n"
        "     patch('providers.azure.ManagedIdentityCredential', MagicMock()), \\\n"
        "     patch('providers.azure.DnsManagementClient', MagicMock()):\n"
        "    import main\n"
        "print('IMPORT_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert "IMPORT_OK" in result.stdout, (
        "Importing main.py from the simulated image layout failed:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def _load_main_in_subprocess(port, operator_seconds):
    """Run main.main() in a child process and probe the HTTP port."""
    script = (
        "import asyncio, os, sys\n"
        "from unittest.mock import MagicMock, patch\n"
        "sys.path.insert(0, " + repr(str(OPERATOR_DIR)) + ")\n"
        "os.environ.update(" + repr(CONTAINER_ENV) + ")\n"
        "with patch('kubernetes.config.load_incluster_config', MagicMock()), \\\n"
        "     patch('providers.azure.ManagedIdentityCredential', MagicMock()), \\\n"
        "     patch('providers.azure.DnsManagementClient', MagicMock()):\n"
        "    import main\n"
        "from aiohttp import web\n"
        "_real = web.TCPSite\n"
        "web.TCPSite = lambda runner, host, p: _real(runner, host, " + str(port) + ")\n"
        "main.web.TCPSite = web.TCPSite\n"
        "main.kopf.operator = lambda: asyncio.sleep(" + str(operator_seconds) + ")\n"
        "asyncio.run(main.main())\n"
    )
    return subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=str(OPERATOR_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _port_is_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def test_http_server_stays_up_while_operator_runs():
    """The chart probes /healthz and /readyz, so the server must keep listening."""
    proc = _load_main_in_subprocess(TEST_PORT, 30)
    try:
        deadline = time.time() + 20
        listening = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if _port_is_open(TEST_PORT):
                listening = True
                break
            time.sleep(0.2)
        assert proc.poll() is None, (
            "main() exited instead of running the operator:\n"
            f"{proc.communicate()[1].decode(errors='replace')[-2000:]}"
        )
        assert listening, (
            "HTTP server was not accepting connections while the operator was "
            "running; the chart's /healthz and /readyz probes would fail"
        )
    finally:
        proc.kill()
        proc.wait(timeout=10)


def test_http_server_closed_when_operator_stops():
    """Cleanup must still run once the operator exits."""
    proc = _load_main_in_subprocess(TEST_PORT + 1, 1)
    try:
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
    assert proc.returncode == 0, (
        "main() should exit cleanly when the operator stops:\n"
        f"{proc.communicate()[1].decode(errors='replace')[-2000:]}"
    )
    assert not _port_is_open(TEST_PORT + 1), "HTTP server should be closed after the operator exits"
