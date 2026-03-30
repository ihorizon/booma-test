#!/usr/bin/env bash
# Start the Booma API locally. Safe to run from anywhere (always cds into services/).
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f app/main.py ]]; then
  echo "Error: expected app/main.py in $(pwd). Keep run-dev.sh inside services/."
  exit 1
fi
if [[ ! -d .venv ]]; then
  echo "Create the venv first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
# shellcheck source=/dev/null
source .venv/bin/activate
export BOOMA_LOG_LEVEL="${BOOMA_LOG_LEVEL:-INFO}"
echo "Starting API from: $(pwd)"
echo "URL: http://127.0.0.1:8000/health"
echo "Set BOOMA_LOG_LEVEL=DEBUG for more application log detail."
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level debug
