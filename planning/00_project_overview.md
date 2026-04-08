# Project VirtualHelmet — Overview

## Concept
A functional Halo MJOLNIR-style helmet (expanding to full suit) featuring:
- Heads-up display (HUD) with system status overlays
- AI-powered visual recognition (object/person detection)
- Voice command recognition (offline, no cloud dependency)
- Distributed electronics via Raspberry Pi network
- 3D printed shell and structural components

## Guiding Principles
- **Offline-first**: All AI runs locally. No cloud dependency.
- **Distributed**: Pi 4 is the brain; Pi Zero 2Ws handle I/O at the edges.
- **Modular**: Helmet is Phase 1. Suit pieces are added later as nodes.
- **Halo aesthetic**: MJOLNIR design language throughout.

## Hardware Inventory (On Hand)
- 1x Raspberry Pi 4 (main compute)
- Multiple Raspberry Pi Zero 2W (distributed controllers)
- USB Logitech camera(s)
- Pi camera modules
- Assorted sensors (TBD — inventory needed)
- 3D printer

## Hardware To Acquire
- See-through HUD display solution (see `03_display_research.md`)

## Project Phases
| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Helmet — HUD, voice, LEDs, sensors | Planning |
| 2 | Helmet — Visual recognition, advanced HUD | Not started |
| 3 | Suit — Chest, gauntlets, boots as nodes | Not started |

## Directory Structure
```
VirtualHelmet/
├── planning/           ← Architecture docs, research, decisions
├── hardware/           ← Wiring diagrams, BOM, pin maps
├── firmware/           ← Code for each Pi node
│   ├── brain/          ← Pi 4 main orchestrator
│   ├── led-node/       ← Pi Zero LED controller
│   ├── sensor-node/    ← Pi Zero sensor hub
│   └── power-node/     ← Pi Zero power management
├── hud/                ← HUD rendering engine
├── models/             ← AI/ML model files
└── assets/             ← Fonts, icons, sound files for HUD
```
