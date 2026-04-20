#!/bin/bash
set -e
if [[ $EUID -ne 0 ]]; then echo "Run as root"; exit 1; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Installing orchestrator dependencies..."
pip3 install -r "$REPO_ROOT/brain/orchestrator/requirements.txt"
pip3 install -e "$REPO_ROOT/shared/"

cat > /etc/systemd/system/vh-orchestrator.service <<EOF
[Unit]
Description=VirtualHelmet Orchestrator
After=network.target mosquitto.service
Wants=vh-audio.service vh-voice.service vh-hud.service

[Service]
Type=simple
User=pi
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/python3 $REPO_ROOT/brain/orchestrator/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vh-orchestrator
echo "=== Orchestrator setup complete ==="
echo "Start with: systemctl start vh-orchestrator"
