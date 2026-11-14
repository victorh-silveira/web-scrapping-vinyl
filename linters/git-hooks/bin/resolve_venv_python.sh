#!/usr/bin/env bash
set -euo pipefail

if [ -x ".venv/bin/python" ]; then
  echo ".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  echo ".venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  command -v python3
else
  command -v python
fi
