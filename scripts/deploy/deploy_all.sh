#!/bin/bash
# Deploy to all devices and restart all services
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
FAIL=0

run_deploy() {
    local name="$1"
    local script="$2"
    echo ""
    if bash "$SCRIPT_DIR/$script" --restart; then
        echo "  [PASS] $name"
        ((PASS++))
    else
        echo "  [FAIL] $name"
        ((FAIL++))
    fi
}

echo "=== VirtualHelmet: Deploy All ==="
echo "Deploying to all 4 devices with service restart..."

run_deploy "Brain (Pi 4)"          "deploy_brain.sh"
run_deploy "LED node (10.11)"       "deploy_led_node.sh"
run_deploy "Sensor node (10.12)"    "deploy_sensor_node.sh"
run_deploy "Power node (10.13)"     "deploy_power_node.sh"

echo ""
echo "=== Deploy Summary: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
