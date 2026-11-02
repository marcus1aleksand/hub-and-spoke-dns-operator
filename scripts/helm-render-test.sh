#!/usr/bin/env bash
# Regression tests for Helm value handling in the dns-operator chart.
#
# The "default" template function treats false and 0 as empty values, so
# "{{ default .Values.x true }}" silently ignores an explicit false and
# "{{ default .Values.x 1 }}" always renders 1. These tests pin the rendered
# output for the values that used to be ignored.
#
# Run with: bash scripts/helm-render-test.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${REPO_ROOT}/charts"

FAILURES=0

pass() { printf '  ok   - %s
' "$1"; }

fail_case() {
  printf '  FAIL - %s
' "$1"
  FAILURES=$((FAILURES + 1))
}

assert_contains() {
  local description="$1" haystack="$2" needle="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    pass "$description"
  else
    fail_case "$description (expected to find '$needle')"
  fi
}

render() {
  helm template dns-operator "$CHART_DIR" "$@" 2>&1
}

echo "dns-operator helm render tests"

# replicaCount has to be honoured instead of always rendering 1.
assert_contains "default replicaCount renders 1" "$(render)" "replicas: 1"
assert_contains "replicaCount 3 is honoured" "$(render --set replicaCount=3)" "replicas: 3"
assert_contains "replicaCount 0 is honoured" "$(render --set replicaCount=0)" "replicas: 0"

# automountServiceAccountToken has to keep an explicit false.
assert_contains "automountServiceAccountToken defaults to false" "$(render)" "automountServiceAccountToken: false"
assert_contains "automountServiceAccountToken false is honoured" "$(render --set deployment.automountServiceAccountToken=false)" "automountServiceAccountToken: false"
assert_contains "automountServiceAccountToken true is honoured" "$(render --set deployment.automountServiceAccountToken=true)" "automountServiceAccountToken: true"

if [[ $FAILURES -gt 0 ]]; then
  printf '
%d check(s) failed
' "$FAILURES"
  exit 1
fi

printf '
All checks passed
'
