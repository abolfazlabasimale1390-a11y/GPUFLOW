#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "GPUFlow Local Lab - launcher"
if [[ ! -f "gpuflow.runtime" ]]; then
  echo "ERROR: gpuflow.runtime is missing. Copy it from the Execution Build."
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")
PY
python3 -m pip install -r requirements.txt
python3 run_server.py
