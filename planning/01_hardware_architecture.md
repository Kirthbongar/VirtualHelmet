# Hardware Architecture

## Node Overview

```
┌─────────────────────────────────────────────────────────┐
│                    HELMET SYSTEM                        │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           RASPBERRY PI 4  (Brain)                │   │
│  │                                                  │   │
│  │  • Vision AI (OpenCV + TFLite)                   │   │
│  │  • Voice recognition (Vosk, offline)             │   │
│  │  • HUD rendering engine                          │   │
│  │  • MQTT broker (Mosquitto)                       │   │
│  │  • System orchestrator                           │   │
│  │  • WiFi Access Point (hosts all nodes)           │   │
│  │                                                  │   │
│  │  Inputs:  USB camera, Pi cam, USB microphone     │   │
│  │  Output:  HUD display (HDMI → display module)    │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │ WiFi / MQTT                            │
│        ┌────────┴────────┐────────────┐                 │
│        ▼                 ▼            ▼                  │
│  ┌───────────┐   ┌───────────┐  ┌───────────┐           │
│  │ Zero 2W   │   │ Zero 2W   │  │ Zero 2W   │           │
│  │ LED Node  │   │ Sensor    │  │ Power     │           │
│  │           │   │ Hub       │  │ Monitor   │           │
│  │ Eye LEDs  │   │ IMU       │  │ Battery   │           │
│  │ Accent    │   │ Temp/Hum  │  │ Voltage   │           │
│  │ Lighting  │   │ Air qual  │  │ Current   │           │
│  │ Status    │   │ Proximity │  │ Cutoffs   │           │
│  └───────────┘   └───────────┘  └───────────┘           │
└─────────────────────────────────────────────────────────┘
                          │
               Future suit expansion
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  ┌───────────┐     ┌───────────┐     ┌───────────┐
  │ Zero 2W   │     │ Zero 2W   │     │ Zero 2W   │
  │ Chest     │     │ Gauntlet  │     │ Boots     │
  │ Node      │     │ Node      │     │ Node      │
  └───────────┘     └───────────┘     └───────────┘
```

---

## Pi 4 — Main Brain

**Role:** Central compute, AI processing, HUD rendering, network host

| Resource | Purpose |
|----------|---------|
| USB Port 1 | Logitech USB camera (forward-facing, external) |
| USB Port 2 | USB microphone |
| USB Port 3 | Reserved (Pi camera adapter or storage) |
| CSI Camera Port | Pi camera module (secondary angle or internal) |
| HDMI | HUD display output |
| WiFi | Access point for all Zero nodes |
| GPIO | Reserved (status LED, boot button) |

**Software services running on Pi 4:**
- `mosquitto` — MQTT broker
- `vision-service` — camera capture + AI inference
- `voice-service` — wake word detection + command parsing
- `hud-service` — HUD rendering and display output
- `orchestrator` — state machine, routes commands to nodes

---

## Pi Zero 2W — LED Node

**Role:** Controls all helmet lighting

| Resource | Purpose |
|----------|---------|
| GPIO 18 (PWM) | WS2812B data line — visor eye LEDs |
| GPIO 19 | WS2812B data line — accent/trim LEDs |
| GPIO 21 | Status LED (system heartbeat) |
| WiFi | MQTT subscriber/publisher |

**MQTT topics (subscribes):**
- `helmet/leds/eyes` — color, brightness, pattern
- `helmet/leds/accent` — color, brightness, pattern
- `helmet/leds/alert` — override for alerts

---

## Pi Zero 2W — Sensor Hub

**Role:** Reads and publishes all helmet sensor data

| Resource | Purpose |
|----------|---------|
| I2C (GPIO 2/3) | IMU (MPU-6050) — head orientation, acceleration |
| I2C | BME280 — temperature, humidity, pressure inside helmet |
| I2C | CCS811 or MQ-135 — CO2 / air quality (optional) |
| GPIO | Proximity sensor (IR or ultrasonic) |
| WiFi | MQTT publisher |

**MQTT topics (publishes):**
- `helmet/sensors/imu` — orientation data (yaw, pitch, roll)
- `helmet/sensors/environment` — temp, humidity, pressure
- `helmet/sensors/airquality` — CO2 ppm (if equipped)

---

## Pi Zero 2W — Power Monitor

**Role:** Monitors battery and manages power distribution

| Resource | Purpose |
|----------|---------|
| I2C | INA219 — current and voltage sensing |
| GPIO | Relay or MOSFET control (non-critical loads) |
| WiFi | MQTT publisher |

**MQTT topics (publishes):**
- `helmet/power/battery` — voltage, current, estimated %, time remaining

---

## Network Architecture

All nodes connect to a WiFi access point hosted by the Pi 4.
This is a closed, isolated network — no internet required.

```
Pi 4 (Access Point)
  SSID: VirtualHelmet-NET
  IP:   192.168.10.1

  Zero LED Node      192.168.10.11
  Zero Sensor Node   192.168.10.12
  Zero Power Node    192.168.10.13
  [Future suit nodes 192.168.10.20+]
```

**Protocol:** MQTT (Mosquitto) on port 1883
- All inter-node communication goes through the Pi 4 broker
- Nodes publish sensor data, subscribe to command topics
- Pi 4 orchestrator subscribes to all topics, publishes commands

---

## Camera Strategy

| Camera | Position | Purpose |
|--------|----------|---------|
| Logitech USB | Front of helmet, external | Primary vision AI feed |
| Pi Camera Module | Inside visor or secondary angle | Backup / close-range |

**Phase 2 consideration:** Stereo camera setup for depth estimation.

---

## Sensor Wishlist (to verify against on-hand inventory)

| Sensor | Purpose | Priority |
|--------|---------|----------|
| MPU-6050 | Head orientation (IMU) | High |
| BME280 | Internal temp/humidity/pressure | High |
| INA219 | Battery voltage/current | High |
| CCS811 | CO2 / air quality | Medium |
| HC-SR04 | Ultrasonic proximity | Low |
| Compass (HMC5883L) | Heading for HUD | Medium |

---

## Open Hardware Questions
1. What sensors are in the on-hand inventory? (Need to verify against wish list)
2. What battery solution? (LiPo pack, 18650 cells, USB power bank?)
3. LED type on hand? (WS2812B, APA102, plain LED strips?)
4. Any servo/actuator hardware? (Faceplate mechanism — Phase 2 consideration)
