#!/usr/bin/env bash
# Validate the package; optionally also validate a separate initialized project.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/harness/bin/verify.py" "$@"
