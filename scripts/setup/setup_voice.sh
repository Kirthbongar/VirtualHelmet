#!/bin/bash
set -e
if [[ $EUID -ne 0 ]]; then echo "Run as root"; exit 1; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[1/4] Installing audio input packages..."
apt-get update -qq
apt-get install -y portaudio19-dev python3-pyaudio

echo "[2/4] Installing Python dependencies..."
pip3 install -r "$REPO_ROOT/brain/voice/requirements.txt"
pip3 install -e "$REPO_ROOT/shared/"

echo "[3/4] Available audio input devices:"
python3 - <<'PYEOF'
import pyaudio
pa = pyaudio.PyAudio()
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"  [{i}] {info['name']}")
pa.terminate()
PYEOF
echo "Set voice.mic_device_index in config/brain.yaml to the device index above."

echo "[4/4] Downloading models..."
bash "$SCRIPT_DIR/download_models.sh"

# Create systemd service
cat > /etc/systemd/system/vh-voice.service <<EOF
[Unit]
Description=VirtualHelmet Voice Service
After=network.target vh-audio.service
Wants=vh-audio.service

[Service]
Type=simple
User=pi
WorkingDirectory=$REPO_ROOT
ExecStart=/usr/bin/python3 $REPO_ROOT/brain/voice/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vh-voice
echo ""
echo "=== Voice setup complete ==="
echo "Run 'systemctl start vh-voice' after downloading models."
