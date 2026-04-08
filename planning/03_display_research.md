# HUD Display Research — See-Through Visor

## Requirement
The visor must allow the wearer to see through it clearly (like a real Halo helmet)
while also displaying HUD information overlaid on that view.

---

## Options Evaluated

### Option 1 — Half-Mirror Beamsplitter (RECOMMENDED)
**How it works:** A small LCD/OLED display is angled behind the visor. A half-silvered
mirror (beamsplitter) mounted at ~45° reflects the display image toward the eye while
also letting real-world light pass through.

```
          [ Real World ]
                │
                ▼
    ┌─── Visor outer surface ───┐
    │                           │
    │       ╱ Beamsplitter ╲    │
    │      ╱   (45° angle)  ╲   │
    │     ╱                  ╲  │
    │    ◄── Reflected HUD    │  │  ← Display (LCD/OLED, side-mounted)
    │                         │  │
    └─────────────────────────┘  │
                │
             [ Eye ]
```

**Pros:**
- Proven by DIY community (405th, hackaday, Raspberry Eye project)
- Real see-through maintained
- Driven directly by Pi 4 HDMI output
- 3D-printable mounting bracket possible
- Scalable — upgrade display later without changing optics concept

**Cons:**
- Requires optical alignment (precision mounting)
- Bright outdoor environments reduce HUD visibility
- Curved Halo visor may introduce edge distortion
- Needs a flatter section or inset panel in visor design

**Estimated Cost:** $150–450
- Beamsplitter cube or plate: ~$30–80 (optocity.com, edmundoptics.com)
- Small LCD/OLED (2.4"–3.5" HDMI): ~$80–150
- Fresnel magnifying lens: ~$20–30
- 3D printed mount: ~$5 filament

**Pi 4 Connection:** HDMI → mini HDMI adapter → display

---

### Option 2 — Transparent OLED (Backup Option)
**How it works:** A small transparent OLED panel mounted in visor — you see through
it and it shows data.

**Pros:**
- Simplest optical setup (no extra mirrors)
- Clean, minimal form factor

**Cons:**
- Very small (1.51" typical max for hobby market)
- Low brightness — washed out in daylight
- Limited HUD area
- Harder to source

**Cost:** $25–100 for small models

**Verdict:** Good for a single data readout (battery %, compass) but not a full HUD.
Could be used as a **supplemental** element alongside Option 1.

---

### Option 3 — Pico Projector (NOT RECOMMENDED)
Curved Halo visor geometry causes severe focus and distortion issues.
Community reports from 405th.com confirm this approach fails on compound-curved visors.

---

### Option 4 — Waveguide AR (NOT RECOMMENDED YET)
Requires precision manufacturing not achievable DIY. $2000+ and not hobbyist-accessible in 2026.
**Watch for 2027–2028** — consumer waveguide kits are emerging.

---

## Recommended Display Approach — Phase 1

**Primary: Half-mirror beamsplitter + 2.4"–3.5" HDMI display**
**Supplemental (optional): 1.51" transparent OLED for secondary data**

### Visor Design Consideration
The 3D printed visor should include a **flat inset panel or pocket** on one side
(likely left or right of center) where the beamsplitter assembly mounts. This avoids
the curvature distortion problem while keeping the outer visor shape true to Halo.

```
  Halo Visor (outer profile):
  ╭──────────────────────────╮
  │   ╔════════════╗         │  ← Flat inset panel (one side)
  │   ║ Beamsplitter║        │
  │   ║ Assembly    ║        │
  │   ╚════════════╝         │
  ╰──────────────────────────╯
```

---

## Shopping List — Display Module

| Item | Source | Approx Cost |
|------|--------|------------|
| Beamsplitter plate/cube | Edmund Optics, Optocity, Amazon | $30–80 |
| 2.4"–3.5" HDMI display (IPS) | Waveshare, Adafruit, Amazon | $80–150 |
| Fresnel lens (pocket magnifier) | Amazon | $10–20 |
| Mini HDMI to HDMI adapter | Amazon | $5–10 |
| HUD combiner film (optional) | Specialized optics suppliers | $50–100 |

---

## Open Questions
1. Single eye or dual eye HUD? (single is simpler and less disorienting)
2. Left eye or right eye dominant? (mount display on dominant side)
3. Should the visor design have a removable/replaceable flat panel for optics iteration?
4. Test optical assembly on bench before integrating into helmet shell?
