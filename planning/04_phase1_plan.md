# Phase 1 Plan — Helmet Build

## Goal
A functional Halo MJOLNIR helmet with:
- Working HUD display (system status overlay)
- Voice command recognition (offline)
- Animated LED eyes + accent lighting
- Sensor monitoring (temp, orientation, battery)
- Distributed Pi 4 + Pi Zero 2W architecture

## Phase 1 Milestones

### Milestone 1 — Hardware Setup & Networking
- [ ] Flash Pi OS Lite on Pi 4 and all Zero 2W units
- [ ] Configure Pi 4 as WiFi access point
- [ ] Connect all Zero 2Ws to Pi 4 network
- [ ] Install Mosquitto MQTT broker on Pi 4
- [ ] Verify MQTT communication between Pi 4 and each Zero
- [ ] Assign static IPs to all nodes

### Milestone 2 — Sensor Node
- [ ] Wire IMU (MPU-6050) to Zero sensor hub
- [ ] Wire BME280 (temp/humidity) to Zero sensor hub
- [ ] Wire INA219 (battery monitor) to Zero power node
- [ ] Write sensor polling firmware (Python, asyncio)
- [ ] Publish sensor data to MQTT topics
- [ ] Verify data received on Pi 4

### Milestone 3 — LED Node
- [ ] Wire WS2812B (or equivalent) LEDs for eye lights
- [ ] Wire accent LEDs
- [ ] Write LED controller firmware
- [ ] Subscribe to MQTT LED topics on Zero LED node
- [ ] Test color, brightness, pattern commands from Pi 4

### Milestone 4 — Voice Commands
- [ ] Connect USB microphone to Pi 4
- [ ] Install and configure Vosk (offline STT)
- [ ] Implement wake word detection ("Cortana")
- [ ] Implement command parser
- [ ] Route commands to orchestrator
- [ ] Test: "Cortana, lights on" → LED node responds

### Milestone 5 — HUD Display
- [ ] Source beamsplitter and small HDMI display
- [ ] Test optical assembly on bench (before helmet integration)
- [ ] Set up Pygame HUD renderer on Pi 4
- [ ] Display: heading, battery %, temp, system status
- [ ] Connect live MQTT sensor data to HUD
- [ ] Tune layout and readability

### Milestone 6 — 3D Print Helmet Shell
- [ ] Find/design Halo MJOLNIR helmet base model
- [ ] Plan visor flat inset panel for optics assembly
- [ ] Print test sections (visor, back panel, side pieces)
- [ ] Fit test with electronics mock-ups
- [ ] Final print and assembly

### Milestone 7 — Integration
- [ ] Mount all Pi nodes inside helmet
- [ ] Route cables cleanly
- [ ] Mount LED assemblies in eye positions
- [ ] Install optics assembly in visor
- [ ] First full system boot inside helmet
- [ ] Tune and debug

---

## Open Decisions Before Starting

| Decision | Options | Notes |
|----------|---------|-------|
| Battery solution | LiPo pack, 18650 cells, USB power bank | Needs runtime estimate |
| LED type | WS2812B (addressable), APA102, plain LEDs | WS2812B recommended |
| Single vs dual HUD eye | Single (simpler) vs dual (immersive) | Start with single |
| HUD framework | Pygame vs Qt vs raw framebuffer | Pygame recommended to start |
| TTS for Cortana voice | espeak-ng vs Piper | Piper sounds more natural |

---

## Bill of Materials — To Acquire (Phase 1)

| Item | Purpose | Priority | Est. Cost |
|------|---------|----------|-----------|
| Beamsplitter plate | HUD optics | Critical | $30–80 |
| 2.4"–3.5" HDMI display | HUD screen | Critical | $80–150 |
| Fresnel lens | HUD magnifier | Critical | $10–20 |
| USB microphone | Voice input | Critical | $20–40 |
| LiPo battery pack | Power | Critical | $30–60 |
| INA219 breakout | Battery monitor | High | $5–10 |
| MPU-6050 breakout | IMU/heading | High | $5–10 |
| BME280 breakout | Temp/humidity | High | $5–10 |
| WS2812B LED strip/ring | Eye LEDs | High | $10–20 |
| Mini HDMI adapter | Pi 4 to display | High | $5–10 |
| Halo helmet 3D model | Shell | Critical | Free (community) |

**Estimated Phase 1 hardware cost (excluding on-hand items):** ~$200–420
