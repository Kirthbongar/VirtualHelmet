#!/bin/bash
# Deploy Pi 4 brain services
# Usage: ./deploy_brain.sh [--restart]
set -e

BRAIN_HOST="pi@192.168.10.1"
REMOTE_DIR="/home/pi/virtualhelmet"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESTART=false
[[ "$1" == "--restart" ]] && RESTART=true

echo "=== Deploying brain to $BRAIN_HOST ==="

# Ensure remote directory exists
ssh "$BRAIN_HOST" "mkdir -p $REMOTE_DIR"

# Rsync source directories
for dir in brain shared config assets; do
    if [[ -d "$REPO_ROOT/$dir" ]]; then
        echo "  Syncing $dir/..."
        rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '*.egg-info' \
            "$REPO_ROOT/$dir/" "$BRAIN_HOST:$REMOTE_DIR/$dir/"
    fi
done

echo "  Deploy complete."

if $RESTART; then
    echo "  Restarting brain services..."
    ssh "$BRAIN_HOST" "sudo systemctl restart vh-orchestrator vh-voice vh-hud vh-audio vh-lidar vh-gps 2>&1 || true"
    sleep 3
    echo ""
    echo "  Service status:"
    ssh "$BRAIN_HOST" "systemctl is-active vh-orchestrator vh-voice vh-hud vh-audio vh-lidar vh-gps 2>&1" | while read -r line; do
        echo "    $line"
    done
fi

echo "=== Brain deploy done ==="
