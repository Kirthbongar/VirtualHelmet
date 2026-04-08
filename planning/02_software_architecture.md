# Software Architecture

## Stack Overview

| Layer | Technology | Runs On |
|-------|-----------|---------|
| OS | Raspberry Pi OS Lite (64-bit) | All devices |
| Message Bus | MQTT (Mosquitto) | Pi 4 (broker), all nodes |
| Vision AI | OpenCV + TensorFlow Lite / MediaPipe | Pi 4 |
| Voice AI | Vosk (offline STT + wake word) | Pi 4 |
| HUD Engine | Pygame (or Qt) | Pi 4 |
| Node Firmware | Python 3 (asyncio) | Each Zero 2W |
| Configuration | YAML | All devices |

---

## Service Map — Pi 4

```
┌─────────────────────────────────────────────────────────────┐
│                       PI 4 SERVICES                         │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   vision-   │    │   voice-     │    │  sensor-      │  │
│  │   service   │    │   service    │    │  aggregator   │  │
│  │             │    │              │    │               │  │
│  │ USB Camera  │    │ USB Mic      │    │ Subscribes    │  │
│  │ → OpenCV    │    │ → Vosk       │    │ all MQTT      │  │
│  │ → TFLite    │    │ Wake word    │    │ sensor topics │  │
│  │ → Detections│    │ Commands     │    │               │  │
│  └──────┬──────┘    └──────┬───────┘    └───────┬───────┘  │
│         │                  │                    │           │
│         └──────────────────┼────────────────────┘           │
│                            ▼                                │
│                 ┌─────────────────────┐                     │
│                 │    orchestrator     │                     │
│                 │                    │                     │
│                 │  State machine      │                     │
│                 │  Command router     │                     │
│                 │  Mode manager       │                     │
│                 └──────────┬──────────┘                     │
│                            │                                │
│              ┌─────────────┼──────────────┐                 │
│              ▼             ▼              ▼                  │
│      ┌──────────┐  ┌──────────┐  ┌──────────────┐          │
│      │   hud-   │  │  MQTT    │  │  config-     │          │
│      │ renderer │  │  broker  │  │  manager     │          │
│      │          │  │          │  │              │          │
│      │ Pygame   │  │Mosquitto │  │ YAML configs │          │
│      │ Overlays │  │ Port 1883│  │ Hot reload   │          │
│      │ → HDMI   │  │          │  │              │          │
│      └──────────┘  └──────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## HUD Layout — Phase 1

```
┌────────────────────────────────────────────────────────┐
│  [HEADING: 045° NE]              [BATTERY: 87%] ████░  │
│                                                        │
│                                                        │
│              [ VISOR / REAL WORLD VIEW ]               │
│                                                        │
│                                                        │
│  [TEMP: 72°F / 22°C]         [SYSTEM: ONLINE ●]       │
│  [HUM: 45%]                  [VOICE: READY  ●]        │
└────────────────────────────────────────────────────────┘
```

**Phase 2 additions:**
- Target lock box overlay (from vision AI)
- Friend/foe tags
- Range to target
- Motion/threat indicators

---

## Voice Command System

**Wake word:** "Cortana" (configurable)

**Command structure:** `[wake word] [command]`

| Command | Action |
|---------|--------|
| "Cortana, scan" | Run object detection sweep |
| "Cortana, lights on/off" | Toggle eye LEDs |
| "Cortana, status" | Read system status aloud or on HUD |
| "Cortana, night mode" | Switch HUD to low-light color scheme |
| "Cortana, power save" | Dim LEDs, reduce polling |
| "Cortana, shutdown" | Graceful system shutdown |
| "Cortana, mark target" | Tag detected object on HUD |

**Voice engine:** Vosk (fully offline, runs on Pi 4)
- Small model (~50MB) for fast response
- No cloud calls, no latency from internet

---

## Visual Recognition — Phase 2

**Pipeline:**
```
USB Camera → OpenCV capture → TFLite inference → detections
     ↓                                                ↓
Frame buffer                               MQTT: helmet/vision/detections
     ↓                                                ↓
HUD renderer ←─────────────────────────── Overlay boxes + labels
```

**Models (TFLite, optimized for Pi 4):**
- Object detection: SSD MobileNet v2 (COCO classes)
- Person detection: MediaPipe Person Detection
- Custom model: Friend/foe classification (to be trained)

---

## Orchestrator State Machine

```
         ┌─────────┐
    ────► │  BOOT   │
         └────┬────┘
              │ all services ready
              ▼
         ┌─────────┐
         │  IDLE   │ ◄──── voice: "standby"
         └────┬────┘
              │ wake word detected
              ▼
         ┌─────────┐
         │  ACTIVE │ ◄──── default operating mode
         └────┬────┘
         ┌────┴─────────────────────┐
         │                         │
    ┌────▼────┐               ┌────▼────┐
    │  SCAN   │               │  ALERT  │
    │  MODE   │               │  MODE   │
    │(vision) │               │(battery │
    └─────────┘               │ / temp) │
                              └─────────┘
```

---

## MQTT Topic Schema

```
helmet/
├── system/
│   ├── status          ← overall system health
│   ├── mode            ← current orchestrator mode
│   └── heartbeat       ← all nodes publish alive ping
├── sensors/
│   ├── imu             ← orientation (yaw, pitch, roll)
│   ├── environment     ← temp, humidity, pressure
│   └── airquality      ← CO2 ppm
├── power/
│   └── battery         ← voltage, current, %, ETA
├── vision/
│   └── detections      ← object detection results
├── voice/
│   └── commands        ← recognized commands
├── leds/
│   ├── eyes            ← eye LED control
│   └── accent          ← accent LED control
└── hud/
    └── overlay         ← HUD element updates
```

---

## Configuration — YAML Example

```yaml
# helmet-config.yaml
system:
  name: "MJOLNIR-MK1"
  voice_wake_word: "cortana"
  log_level: "info"

network:
  ssid: "VirtualHelmet-NET"
  broker_host: "192.168.10.1"
  broker_port: 1883

hud:
  theme: "halo_green"       # halo_green | iron_man_red | blue
  brightness: 80            # percent
  show_compass: true
  show_battery: true
  show_temp: true

vision:
  enabled: false            # Phase 2
  camera_device: "/dev/video0"
  model: "ssd_mobilenet_v2"
  confidence_threshold: 0.65

leds:
  eyes:
    color: [0, 180, 255]    # RGB - Halo blue-white
    brightness: 100
    idle_pulse: true
  accent:
    color: [0, 100, 200]
    brightness: 60
```

---

## Open Software Questions
1. HUD framework: Pygame vs Qt vs custom framebuffer renderer?
2. Vosk model size vs accuracy tradeoff for Pi 4?
3. Offline TTS (text-to-speech) for Cortana responses — espeak-ng or Piper?
4. Logging/telemetry: local file or SQLite database?
5. OTA update strategy for Zero nodes?
