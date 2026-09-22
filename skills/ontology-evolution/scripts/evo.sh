#!/bin/bash
# evo.sh - ontology-evolution mechanism lane entry point.
#
# Usage: evo.sh <new|status|advance|archive> [args]
# Run from the skill root: bash scripts/evo.sh <command> [args]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/evo.py" "$@"
