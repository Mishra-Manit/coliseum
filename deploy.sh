#!/bin/bash
set -e

PROJECT_DIR="/home/manitmishra/coliseum-backend/backend"
SERVICE="coliseum"

echo "========================================"
echo "Starting Deployment: Coliseum Backend"
echo "========================================"

echo "Requesting graceful shutdown..."
sudo systemctl kill --signal=SIGTERM $SERVICE 2>/dev/null || true

MAX_WAIT=300
ELAPSED=0
INTERVAL=5
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if ! systemctl is-active --quiet $SERVICE; then
        echo "Service stopped gracefully after ${ELAPSED}s."
        break
    fi
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    echo "  Waiting for current cycle to finish... (${ELAPSED}s/${MAX_WAIT}s)"
done

if systemctl is-active --quiet $SERVICE; then
    echo "Timed out waiting. Force stopping..."
    sudo systemctl stop $SERVICE
fi

echo "Pulling latest code..."
cd $PROJECT_DIR
git pull origin main

echo "Checking for new dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Syncing systemd service file..."
if ! diff -q /etc/systemd/system/$SERVICE.service $PROJECT_DIR/../infra/$SERVICE.service > /dev/null 2>&1; then
    echo "  Service file changed, updating..."
    sudo cp $PROJECT_DIR/../infra/$SERVICE.service /etc/systemd/system/$SERVICE.service
    sudo systemctl daemon-reload
else
    echo "  Service file unchanged."
fi

echo "Restarting service..."
sudo systemctl start $SERVICE

echo "Waiting 5 seconds for startup..."
sleep 5

echo "Deployment complete. Checking status:"
sudo systemctl status $SERVICE --no-pager
