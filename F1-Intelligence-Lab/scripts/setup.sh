#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PORTAL_DIR=$(dirname "$SCRIPT_DIR")
WORKSPACE_DIR=$(dirname "$PORTAL_DIR")

python3 -m venv "$PORTAL_DIR/.venv"
. "$PORTAL_DIR/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install \
  -e "$WORKSPACE_DIR/F1-StewardLens" \
  -e "$WORKSPACE_DIR/F1-Telemetry-Pit-Crew[f1]" \
  -e "$PORTAL_DIR[dev]"

printf '%s\n' "Setup complete."
printf '%s\n' "Run: cd '$PORTAL_DIR' && . .venv/bin/activate && uvicorn f1_intelligence_lab.app:app --reload"

