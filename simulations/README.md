# VirtualHelmet Simulation Layer

Run Phase 1 software (orchestrator, HUD) against mock sensor and node data on a Windows development machine — no Raspberry Pi hardware required. All mock nodes publish/subscribe to a local Mosquitto MQTT broker at `localhost:1883`.

---

## Prerequisites

- Python 3.9 or later
- [Mosquitto for Windows](https://mosquitto.org/download/) installed and available on PATH
- Install Python dependencies:

```
pip install -r simulations/requirements.txt
```

---

## How to Run

### 1. Start the Mosquitto broker

Open a terminal and run:

```
mosquitto -v
```

This starts Mosquitto on `localhost:1883` with verbose logging. Leave this terminal open.

### 2. Start the simulation

In a second terminal, from the project root:

```
py -3 simulations/run_simulation.py
```

This launches all four mock nodes as subprocesses and prints a status banner. Each mock node's stdout is forwarded with a label prefix so you can see what each one is publishing.

### 3. Start the orchestrator

In a third terminal:

```
py -3 brain/orchestrator/main.py
```

### 4. Start the HUD

In a fourth terminal:

```
py -3 brain/hud/main.py
```

### 5. Send test commands

Use `simulations/test_commands.sh` in Git Bash or WSL to fire all 17 voice commands in sequence:

```bash
bash simulations/test_commands.sh
```

Or send individual commands manually — see the section below.

---

## Config Override

`simulations/sim_config.yaml` is the config file loaded by all simulation scripts. It points the broker at `127.0.0.1:1883` and sets simulation parameters. It does **not** modify `config/brain.yaml` — the brain services read their own config. If you need the brain services to connect to the same local broker, update `config/brain.yaml` broker settings to match, or pass the config path as an argument if supported.

Key simulation parameters:

| Key | Default | Description |
|-----|---------|-------------|
| `sensor_poll_hz` | 10 | IMU and LiDAR publish rate |
| `power_poll_interval_s` | 5 | Battery publish interval |
| `gps_poll_interval_s` | 1 | GPS publish interval |
| `battery_drain_rate_pct_per_min` | 0.5 | SOC drain rate for testing |
| `gps_start_lat/lon` | Nashville, TN | Starting GPS coordinates |

---

## What Each Mock Does

### `mock_sensor_node.py`
Simulates the Pi Zero sensor node. Publishes on:
- `helmet/sensors/imu` — pitch/roll oscillate ±5° on slow sine waves; heading increments 0→360° over 60 s; yaw drifts slightly. Published at `sensor_poll_hz`.
- `helmet/sensors/environment` — temperature 22 °C ±0.2 with noise, humidity 55% ±1, pressure 1013.25 hPa. Published every 5 s.
- `helmet/sensors/airquality` — `warming_up=true` for the first 20 seconds (accelerated from real 20 min for testing); then CO₂ 800 ±50 ppm, TVOC 100 ±20 ppb. Published every 10 s.
- `helmet/system/heartbeat` — every 30 s.

### `mock_power_node.py`
Simulates the Pi Zero power node. Publishes on:
- `helmet/power/battery` — starts at 85% SOC and drains at the configured rate. Voltage is derived from a SOC→voltage lookup table (8.4 V at 100%, 6.0 V at 0%). Constant 1200 mA load. `charging=false`. Includes ETA and remaining Wh. Published every `power_poll_interval_s`.
- `helmet/system/heartbeat` — every 30 s.

### `mock_gps_lidar.py`
Simulates GPS and LiDAR. Publishes on:
- `helmet/gps/position` — starts at the configured coordinates. `fix_quality=0` for first 5 seconds (cold-start simulation), then `fix_quality=1` with 8 satellites. Position drifts ~0.000001°/s in a slowly-rotating direction. Published at 1 Hz.
- `helmet/lidar/distance` — distance oscillates between 0.5 m and 5.0 m on a 10 s sine wave, `strength=500`, `valid=true`. Published at `lidar_poll_hz`.
- `helmet/system/heartbeat` — every 30 s (node id `brain/gps`).

### `mock_led_node.py`
Monitors LED command topics and prints what the LED node would do — no hardware needed. Subscribes to:
- `helmet/leds/eyes`
- `helmet/leds/accent`
- `helmet/leds/alert`

Example output:
```
[LED EYES]   pattern=active  color=[0,180,255]  brightness=60
[LED ACCENT] pattern=idle    color=[0,100,200]  brightness=40
[LED ALERT]  type=low_battery  active=True
```

---

## Example mosquitto_pub Test Commands

All 17 voice commands:

```bash
# Lights
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"lights_on"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"lights_off"}'

# Status and sensors
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"status"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"battery"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"distance"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"heading"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"temperature"}'

# Navigation
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"mark_waypoint"}'

# Modes
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"night_mode"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"resume"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"power_save"}'

# Music
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"music_play"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"music_pause"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"music_next"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"volume_up"}'
mosquitto_pub -h 127.0.0.1 -t "helmet/voice/commands" -m '{"command":"volume_down"}'

# HUD overlay (direct topic, not a voice command)
mosquitto_pub -h 127.0.0.1 -t "helmet/hud/overlay" -m '{"theme":"night_mode"}'
```
