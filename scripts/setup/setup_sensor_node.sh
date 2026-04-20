#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SENSOR_NODE_DIR="$(realpath "$SCRIPT_DIR/../../sensor-node")"
SHARED_DIR="$(realpath "$SCRIPT_DIR/../../shared")"

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo)." >&2
    exit 1
fi

echo "Installing system packages..."
apt-get install -y python3-pip i2c-tools

echo "Enabling I2C interface..."
raspi-config nonint do_i2c 0

echo "Installing sensor node Python dependencies..."
pip3 install -r "$SENSOR_NODE_DIR/requirements.txt"

echo "Installing shared module in editable mode..."
pip3 install -e "$SHARED_DIR/"

SERVICE_FILE=/etc/systemd/system/vh-sensor.service

echo "Writing systemd service to $SERVICE_FILE..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=VirtualHelmet Sensor Node
After=network.target

[Service]
ExecStart=/usr/bin/python3 $SENSOR_NODE_DIR/main.py
WorkingDirectory=$SENSOR_NODE_DIR
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vh-sensor

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling vh-sensor service..."
systemctl daemon-reload
systemctl enable vh-sensor

echo "Scanning I2C bus 1 for connected devices..."
i2cdetect -y 1

echo ""
echo "Sensor node setup complete."
echo "Start the service with: systemctl start vh-sensor"
echo "View logs with: journalctl -u vh-sensor -f"
