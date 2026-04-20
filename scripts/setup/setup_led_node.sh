#!/bin/bash
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Installing Python dependencies..."
pip3 install -r "$REPO_ROOT/led-node/requirements.txt"
pip3 install -e "$REPO_ROOT/shared/"

echo "Adding pi user to spi and audio groups (required for ws281x)..."
usermod -a -G spi,audio pi

echo "Installing systemd service..."
cat > /etc/systemd/system/vh-led.service <<EOF
[Unit]
Description=VirtualHelmet LED Node
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_ROOT/led-node
ExecStart=/usr/bin/python3 $REPO_ROOT/led-node/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vh-led
systemctl start vh-led

echo "vh-led service enabled and started."
