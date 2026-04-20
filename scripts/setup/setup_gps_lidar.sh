#!/bin/bash
set -e
if [[ $EUID -ne 0 ]]; then echo "Run as root"; exit 1; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[1/5] Enabling UART for LiDAR..."
if ! grep -q "enable_uart=1" /boot/config.txt; then
    echo "enable_uart=1" >> /boot/config.txt
fi
# Remove serial console from cmdline
if grep -q "console=serial0" /boot/cmdline.txt; then
    sed -i 's/console=serial0,[0-9]* //g' /boot/cmdline.txt
    echo "  Serial console removed from cmdline.txt"
fi

echo "[2/5] Installing packages..."
apt-get update -qq
apt-get install -y python3-pip

echo "[3/5] Installing Python dependencies..."
pip3 install -r "$REPO_ROOT/brain/gps/requirements.txt"
pip3 install -e "$REPO_ROOT/shared/"

echo "[4/5] Creating data directory..."
mkdir -p "$REPO_ROOT/brain/gps/data"

echo "[5/5] Testing sensors..."
echo "--- Testing LiDAR (5 frames) ---"
python3 - <<'PYEOF'
import sys
sys.path.insert(0, '/home/pi/VirtualHelmet')
try:
    from brain.lidar.tfmini import TFminiS
    lidar = TFminiS('/dev/ttyAMA0')
    lidar.open()
    for i in range(5):
        f = lidar.read_frame()
        print(f"  Frame {i+1}: {f['distance_m']}m, strength={f['strength']}, valid={f['valid']}")
    lidar.close()
except Exception as e:
    print(f"  LiDAR test failed: {e}")
PYEOF

echo "--- Testing GPS (10 sentences) ---"
python3 - <<'PYEOF'
import serial, time
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
    count = 0
    start = time.time()
    while count < 10 and time.time() - start < 15:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line.startswith('$'):
            print(f"  {line}")
            count += 1
    ser.close()
except Exception as e:
    print(f"  GPS test failed: {e}")
PYEOF

echo ""
echo "=== GPS/LiDAR Setup Complete ==="
echo "Reboot required for UART changes: sudo reboot"
