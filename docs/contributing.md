# Contributing

We welcome contributions! Here's how to get started.

## Development Setup

1. **Fork and clone** the repository:
    ```bash
    git clone https://github.com/YOUR-USERNAME/hub-and-spoke-dns-operator.git
    cd hub-and-spoke-dns-operator
    ```

2. **Install pre-commit hooks:**
    ```bash
    brew install pre-commit
    pre-commit install
    ```

3. **Install Python dependencies:**
    ```bash
    cd operator
    pip install -r requirements.txt
    ```

4. **Run tests:**
    ```bash
    python -m pytest test_main.py -v
    ```

## Project Structure

```
hub-and-spoke-dns-operator/
├── operator/                    # Python operator source
│   ├── main.py                  # Main operator logic
│   ├── providers/               # Cloud DNS provider implementations
│   │   ├── base.py              # Abstract base provider
│   │   ├── azure.py             # Azure DNS provider
│   │   ├── gcp.py               # Google Cloud DNS provider
│   │   └── aws.py               # AWS Route53 provider
│   ├── test_main.py             # Unit tests
│   ├── Dockerfile               # Container image
│   └── requirements.txt         # Python dependencies
├── charts/                      # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── docs/                        # Documentation (MkDocs)
└── secrets-injector/            # External secrets integration
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes and ensure tests pass
3. Pre-commit hooks will run automatically on `git commit`
4. Push and open a Pull Request against `main`

## CI Pipeline

All PRs trigger:

- **Lint & Security Scan** — Flake8 linting + Checkov security scanning
- **Build & Test** — Docker build verification
- **Unit Tests** — Python test suite

## Code of Conduct

Be kind, be respectful, and help make this project welcoming for everyone.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/blob/main/LICENSE).
