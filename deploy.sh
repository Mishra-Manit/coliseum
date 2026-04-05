#!/bin/bash
set -e

PROJECT_DIR="/home/manitmishra/coliseum-backend/backend"
SERVICE="coliseum"

echo "========================================"
echo "Starting Deployment: Coliseum Backend"
echo "========================================"

echo "Stopping service..."
sudo systemctl stop $SERVICE

echo "Pulling latest code..."
cd $PROJECT_DIR
git pull origin main

echo "Checking for new dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Restarting service..."
sudo systemctl start $SERVICE

echo "Waiting 5 seconds for startup..."
sleep 5

echo "Deployment complete. Checking status:"
sudo systemctl status $SERVICE --no-pager
