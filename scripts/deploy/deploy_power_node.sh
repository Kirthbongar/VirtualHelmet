#!/bin/bash
# Deploy power node (Pi Zero 2W at 192.168.10.13)
# Usage: ./deploy_power_node.sh [--restart]
set -e

NODE_HOST="pi@192.168.10.13"
REMOTE_DIR="/home/pi/virtualhelmet"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESTART=false
[[ "$1" == "--restart" ]] && RESTART=true

echo "=== Deploying power node to $NODE_HOST ==="

ssh "$NODE_HOST" "mkdir -p $REMOTE_DIR"

for dir in power-node shared config; do
    if [[ -d "$REPO_ROOT/$dir" ]]; then
        echo "  Syncing $dir/..."
        rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '*.egg-info' \
            "$REPO_ROOT/$dir/" "$NODE_HOST:$REMOTE_DIR/$dir/"
    fi
done

echo "  Deploy complete."

if $RESTART; then
    echo "  Restarting vh-power..."
    ssh "$NODE_HOST" "sudo systemctl restart vh-power 2>&1 || true"
    sleep 2
    status=$(ssh "$NODE_HOST" "systemctl is-active vh-power 2>&1")
    echo "  vh-power: $status"
fi

echo "=== Power node deploy done ==="
