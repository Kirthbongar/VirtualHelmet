#!/bin/bash
# VirtualHelmet Phase 1 Integration Test
# Run from dev machine after deploy_all.sh

BROKER="192.168.10.1"
TIMEOUT=10
PASS=0
FAIL=0
MANUAL=0

pass() { echo "  [PASS] $1"; ((PASS++)); }
fail() { echo "  [FAIL] $1"; ((FAIL++)); }
manual() { echo "  [MANUAL] $1 — visually verify"; ((MANUAL++)); }

echo "=== VirtualHelmet Phase 1 Integration Test ==="
echo "Broker: $BROKER"
echo ""

# ---- Network ----
echo "[Network]"

for ip in 192.168.10.11 192.168.10.12 192.168.10.13; do
    if ping -c 2 -W 2 "$ip" > /dev/null 2>&1; then
        pass "Ping $ip"
    else
        fail "Ping $ip — node unreachable"
    fi
done

# ---- Sensor node ----
echo ""
echo "[Sensor Node]"

IMU_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/sensors/imu" -C 1 -W "$TIMEOUT" 2>/dev/null)
if echo "$IMU_MSG" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'pitch' in d and 'roll' in d and 'heading_deg' in d" 2>/dev/null; then
    pass "IMU topic — valid JSON with pitch, roll, heading_deg"
else
    fail "IMU topic — missing or invalid"
fi

ENV_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/sensors/environment" -C 1 -W "$TIMEOUT" 2>/dev/null)
if echo "$ENV_MSG" | python3 -c "import sys,json; d=json.load(sys.stdin); t=d['temperature_c']; assert 0<=t<=60" 2>/dev/null; then
    pass "Environment topic — temperature in valid range (0–60°C)"
else
    fail "Environment topic — missing or temperature out of range"
fi

# ---- Power node ----
echo ""
echo "[Power Node]"

BAT_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/power/battery" -C 1 -W "$TIMEOUT" 2>/dev/null)
if echo "$BAT_MSG" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['voltage_v']>4.0 and 0<=d['soc_percent']<=100" 2>/dev/null; then
    pass "Battery topic — voltage > 4V, SOC 0–100%"
else
    fail "Battery topic — missing or values out of range"
fi

# ---- LED node ----
echo ""
echo "[LED Node]"

mosquitto_pub -h "$BROKER" -t "helmet/leds/eyes" -m '{"color":[255,0,0],"brightness":50,"pattern":"active"}' 2>/dev/null
manual "LED eyes — should be solid red now"

mosquitto_pub -h "$BROKER" -t "helmet/leds/alert" -m '{"type":"low_battery","active":true}' 2>/dev/null
manual "LED alert — should be amber pulse now"
sleep 2
mosquitto_pub -h "$BROKER" -t "helmet/leds/alert" -m '{"type":"low_battery","active":false}' 2>/dev/null
manual "LED alert cleared — should return to previous pattern"

# ---- GPS / LiDAR ----
echo ""
echo "[GPS / LiDAR]"

LIDAR_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/lidar/distance" -C 1 -W "$TIMEOUT" 2>/dev/null)
if echo "$LIDAR_MSG" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'distance_m' in d and 'valid' in d" 2>/dev/null; then
    pass "LiDAR topic — valid JSON with distance_m, valid fields"
else
    fail "LiDAR topic — missing or invalid"
fi

GPS_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/gps/position" -C 1 -W "$TIMEOUT" 2>/dev/null)
if echo "$GPS_MSG" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'fix_quality' in d" 2>/dev/null; then
    pass "GPS topic — fix_quality field present"
else
    fail "GPS topic — missing or invalid"
fi

# ---- Voice ----
echo ""
echo "[Voice Service]"

VOICE_STATUS=$(ssh pi@192.168.10.1 "systemctl is-active vh-voice 2>/dev/null" 2>/dev/null)
if [[ "$VOICE_STATUS" == "active" ]]; then
    pass "vh-voice service is active on brain"
else
    fail "vh-voice service is not active (status: $VOICE_STATUS)"
fi

manual "Voice — say 'Cortana, battery' and verify command appears on helmet/voice/commands"

# ---- HUD ----
echo ""
echo "[HUD Service]"

HUD_STATUS=$(ssh pi@192.168.10.1 "systemctl is-active vh-hud 2>/dev/null" 2>/dev/null)
if [[ "$HUD_STATUS" == "active" ]]; then
    pass "vh-hud service is active on brain"
else
    fail "vh-hud service is not active (status: $HUD_STATUS)"
fi

mosquitto_pub -h "$BROKER" -t "helmet/hud/overlay" -m '{"theme":"night_mode"}' 2>/dev/null
manual "HUD — should switch to red night mode theme"
sleep 2
mosquitto_pub -h "$BROKER" -t "helmet/hud/overlay" -m '{"theme":"halo_green"}' 2>/dev/null

# ---- Orchestrator ----
echo ""
echo "[Orchestrator]"

STATUS_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/system/status" -C 1 -W 35 2>/dev/null)
if echo "$STATUS_MSG" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'nodes' in d and 'mode' in d" 2>/dev/null; then
    pass "System status topic publishing (nodes, mode fields present)"
else
    fail "System status topic — not received within 35 seconds"
fi

echo "  Testing low-battery alert trigger..."
mosquitto_pub -h "$BROKER" -t "helmet/power/battery" \
    -m '{"voltage_v":7.0,"current_ma":500,"power_w":3.5,"soc_percent":15,"eta_minutes":30,"charging":false,"timestamp":0}' \
    2>/dev/null
ALERT_MSG=$(mosquitto_sub -h "$BROKER" -t "helmet/leds/alert" -C 1 -W 5 2>/dev/null)
if [[ -n "$ALERT_MSG" ]]; then
    pass "Orchestrator triggered LED alert on low battery mock publish"
else
    fail "Orchestrator did not trigger LED alert — check vh-orchestrator logs"
fi

# ---- Summary ----
echo ""
echo "=== Results: $PASS passed, $FAIL failed, $MANUAL manual checks ==="
echo ""
if [[ $MANUAL -gt 0 ]]; then
    echo "Complete the $MANUAL manual visual checks listed above."
fi

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
