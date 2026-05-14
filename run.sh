#!/bin/bash
CONAN_ROOT="/Users/nchronaios/Documents/Github/conan"
export PYTHONPATH="$CONAN_ROOT"
exec "$CONAN_ROOT/.venv/bin/python3.14" -m conan.cli "$@"
