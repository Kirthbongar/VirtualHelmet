#!/bin/bash
set -e
if [[ $EUID -ne 0 ]]; then echo "Run as root"; exit 1; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[1/3] Installing Pygame dependencies..."
apt-get update -qq
apt-get install -y python3-pygame libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

echo "[2/3] Installing Python packages..."
pip3 install -r "$REPO_ROOT/brain/hud/requirements.txt"
pip3 install -e "$REPO_ROOT/shared/"

echo "[3/3] Creating systemd service..."
cat > /etc/systemd/system/vh-hud.service <<EOF
[Unit]
Description=VirtualHelmet HUD Display
After=network.target graphical.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=SDL_VIDEODRIVER=x11
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/python3 $REPO_ROOT/brain/hud/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF

systemctl daemon-reload
systemctl enable vh-hud
echo ""
echo "=== HUD setup complete ==="
echo "Add to /boot/config.txt for 800x480 HDMI:"
echo "  hdmi_group=2"
echo "  hdmi_mode=87"
echo "  hdmi_cvt=800 480 60 6 0 0 0"
echo "  hdmi_drive=2"
