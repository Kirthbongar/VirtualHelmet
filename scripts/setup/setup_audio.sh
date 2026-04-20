#!/bin/bash
set -e
if [[ $EUID -ne 0 ]]; then echo "Run as root"; exit 1; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[1/5] Installing audio packages..."
apt-get update -qq
apt-get install -y pulseaudio pulseaudio-module-bluetooth bluez python3-dbus mpris-proxy

echo "[2/5] Enabling Bluetooth service..."
systemctl enable bluetooth
systemctl start bluetooth

echo "[3/5] Configuring PulseAudio for system-wide mode..."
# System-wide pulseaudio for service context
if ! grep -q "system-instance" /etc/pulse/client.conf 2>/dev/null; then
    echo "default-server = unix:/run/pulse/native" >> /etc/pulse/client.conf
fi

echo "[4/5] Installing Piper TTS..."
pip3 install piper-tts
PIPER_MODEL_DIR="$REPO_ROOT/models/tts"
mkdir -p "$PIPER_MODEL_DIR"
echo "Download en_US-lessac-medium voice model from:"
echo "  https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium"
echo "  Place .onnx and .onnx.json files in: $PIPER_MODEL_DIR/"

echo "[5/5] Testing audio output..."
speaker-test -t wav -c 2 -l 1 || echo "  [WARN] speaker-test failed — check audio device"

echo ""
echo "=== Audio Setup Complete ==="
echo "Pairing instructions:"
echo "  1. bluetoothctl"
echo "  2. power on"
echo "  3. agent on"
echo "  4. discoverable on"
echo "  5. scan on"
echo "  6. pair <PHONE_MAC>"
echo "  7. trust <PHONE_MAC>"
echo "  8. connect <PHONE_MAC>"
echo "  9. Update audio.bluetooth_device_mac in config/brain.yaml"
