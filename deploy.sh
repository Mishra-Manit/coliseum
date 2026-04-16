#!/bin/bash
set -e

# Derive paths from this scripts location so it works on any host/user
REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PROJECT_DIR="$REPO_DIR/backend"
SERVICE="coliseum"

echo "========================================"
echo "Starting Deployment: Coliseum Backend"
echo "Repo: $REPO_DIR"
echo "========================================"

echo "Requesting graceful shutdown..."
sudo systemctl kill --signal=SIGTERM "$SERVICE" 2>/dev/null || true

MAX_WAIT=300
ELAPSED=0
INTERVAL=5
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if ! systemctl is-active --quiet "$SERVICE"; then
        echo "Service stopped gracefully after ${ELAPSED}s."
        break
    fi
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    echo "  Waiting for current cycle to finish... (${ELAPSED}s/${MAX_WAIT}s)"
done

if systemctl is-active --quiet "$SERVICE"; then
    echo "Timed out waiting. Force stopping..."
    sudo systemctl stop "$SERVICE"
fi

echo "Pulling latest code..."
cd "$REPO_DIR"
git pull origin main

echo "Checking for new dependencies..."
source "$PROJECT_DIR/venv/bin/activate"
pip install -q -r "$PROJECT_DIR/requirements.txt"

echo "Syncing systemd service file..."
UNIT_SRC="$REPO_DIR/infra/$SERVICE.service"
UNIT_DST="/etc/systemd/system/$SERVICE.service"
if [ -f "$UNIT_SRC" ] && ! sudo diff -q "$UNIT_DST" "$UNIT_SRC" >/dev/null 2>&1; then
    echo "  Service file changed, updating..."
    sudo cp "$UNIT_SRC" "$UNIT_DST"
    sudo systemctl daemon-reload
else
    echo "  Service file unchanged."
fi

echo "Restarting service..."
sudo systemctl start "$SERVICE"

echo "Waiting 5 seconds for startup..."
sleep 5

echo "Deployment complete. Checking status:"
sudo systemctl status "$SERVICE" --no-pager
