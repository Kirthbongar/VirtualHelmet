#!/bin/bash
set -e

if [[ "$EUID" -ne 0 ]]; then
    echo "This script must be run as root." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Enable I2C
raspi-config nonint do_i2c 0

# System packages
apt-get install -y python3-pip i2c-tools

# Python dependencies
pip3 install -r "$REPO_ROOT/power-node/requirements.txt"

# Shared library (editable install)
pip3 install -e "$REPO_ROOT/shared/"

# Systemd service
cat > /etc/systemd/system/vh-power.service <<EOF
[Unit]
Description=VirtualHelmet Power Node
After=network.target

[Service]
ExecStart=/usr/bin/python3 $REPO_ROOT/power-node/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vh-power
systemctl start vh-power

# Verify I2C bus
i2cdetect -y 1
