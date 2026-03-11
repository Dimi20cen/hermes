#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/srv/stacks/hermes"
VENV_DIR="$REPO_DIR/.venv"
LOCK_DIR="/tmp/hermes-deploy.lock"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Deploy already running. Exiting."
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

cd "$REPO_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Hermes deploy..."
/usr/bin/git pull --ff-only
/usr/bin/python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -e "$REPO_DIR"
/usr/bin/systemctl --user restart hermes.service
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hermes deploy complete."
