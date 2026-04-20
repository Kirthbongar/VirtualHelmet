#!/bin/bash
# Deploy sensor node (Pi Zero 2W at 192.168.10.12)
# Usage: ./deploy_sensor_node.sh [--restart]
set -e

NODE_HOST="pi@192.168.10.12"
REMOTE_DIR="/home/pi/virtualhelmet"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESTART=false
[[ "$1" == "--restart" ]] && RESTART=true

echo "=== Deploying sensor node to $NODE_HOST ==="

ssh "$NODE_HOST" "mkdir -p $REMOTE_DIR"

for dir in sensor-node shared config; do
    if [[ -d "$REPO_ROOT/$dir" ]]; then
        echo "  Syncing $dir/..."
        rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '*.egg-info' \
            "$REPO_ROOT/$dir/" "$NODE_HOST:$REMOTE_DIR/$dir/"
    fi
done

echo "  Deploy complete."

if $RESTART; then
    echo "  Restarting vh-sensor..."
    ssh "$NODE_HOST" "sudo systemctl restart vh-sensor 2>&1 || true"
    sleep 2
    status=$(ssh "$NODE_HOST" "systemctl is-active vh-sensor 2>&1")
    echo "  vh-sensor: $status"
fi

echo "=== Sensor node deploy done ==="
