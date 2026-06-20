# Handycam

A real-time webcam visual effect for **TouchDesigner 2023** (Python 3.11).

MediaPipe tracks both hands. Each hand's wrist becomes a bottom corner of a
dynamic triangle whose apex sits near top-center of the frame. **Inside** the
triangle the webcam is rendered with a risograph / cyanotype + halftone-stippling
aesthetic; **outside** the clean webcam shows through with a hard (un-feathered)
edge. The triangle tracks your hands live.

```
        apex (top-center)
            /\
           /  \        inside  = riso + halftone (blue/green/gold/white, paper grain)
          /    \       outside = clean webcam
         /      \
   left hand   right hand   <- wrist positions, smoothed
```

## What's in this repo

| File | Purpose |
|---|---|
| `build_network.py` | Auto-builder — paste into TD's Textport to construct the whole network. |
| `config.py` | All tunables: plugin paths, channel names, palette, halftone, smoothing. |
| `shaders/riso.frag` | 4-band luminance posterize → ink palette → misregistration. |
| `shaders/halftone.frag` | Ink-colored brick-grid halftone, luminance-driven dots, vertical density gradient. |
| `shaders/triangle_composite.frag` | Point-in-triangle mask + paper grain + desaturation. |
| `docs/channel_mapping.md` | One-time discovery of the plugin's hand-CHOP channel names. |

> **Note:** TouchDesigner `.toe` files are binary, so the project itself isn't
> checked in as a file you can edit. Instead, `build_network.py` *generates* the
> network programmatically. Run it once (or after any `config.py` change).

## Prerequisites

- **TouchDesigner 2023** (Python 3.11).
- **MediaPipe plugin:** [`torinmb/mediapipe-touchdesigner`](https://github.com/torinmb/mediapipe-touchdesigner)
  — download the latest release `.zip` and grab `MediaPipe.tox`.

## Setup

1. Open TouchDesigner. Drag **`MediaPipe.tox`** into your project; when prompted,
   check **"Enable External .tox"**.
2. In the component, **select your webcam** and **enable the Hands model**.
3. Follow **`docs/channel_mapping.md`** to find the hands CHOP path and the four
   landmark channel names. Paste them into `config.py` (`HANDS_CHOP_PATH`,
   `PLUGIN_VIDEO_TOP`, `SRC_LEFT_X/Y`, `SRC_RIGHT_X/Y`).
4. Open the **Textport** (`Alt+T`) and run:
   ```python
   exec(open(r'C:/Users/biyon/handycam/build_network.py').read())
   ```
5. The network builds under **`/handycam`**. View `/handycam/out1`.

## Verifying it works

- Background shows the **clean webcam**.
- Raise both hands → a **sharp-edged triangle** appears, apex top-center, bottom
  corners at your wrists.
- Inside: posterized **blue / green / gold / white** ink bands with **ink-colored
  halftone dots** (denser toward the bottom) and subtle **paper grain**.
- Move your hands → the triangle updates **smoothly** (no jitter), with the
  correct hand mapped to each corner and no vertical inversion.

## Tuning (`config.py`, then re-run the builder)

| Symptom / goal | Change |
|---|---|
| Triangle follows the wrong hand | `SWAP_HANDS = True` |
| Triangle is vertically inverted | toggle `FLIP_Y` |
| Mirrored / selfie webcam | `MIRROR_X = True` |
| Too jittery / too laggy | `LAG` (0.05–0.10) |
| Dots too big / small | `CELL_PX` (8–12) |
| Stronger print misalignment | `MISREG_PX` (2–4) |
| More/less analog feel | `GRAIN_OPACITY`, `DESATURATE` |
| Apex follows hands | `APEX_MODE = 'midpoint'` |

## Notes / known gotchas

- **Webcam contention:** the plugin captures the camera internally. By default
  (`USE_PLUGIN_PASSTHROUGH = True`) we reuse the plugin's passthrough frame so two
  operators don't fight over the camera. Only set it `False` (own Video Device In
  TOP) if the plugin doesn't expose a usable passthrough TOP.
- **Misregistration:** done in `riso.frag` for speed. The spec's literal
  "Transform TOP offset per layer" approach is an equivalent node-based
  alternative if you'd rather build it from separate colorized layers.
- **Shader errors:** if a GLSL TOP turns red, right-click → view errors. The
  shaders target the TD GLSL-TOP convention (`out vec4 fragColor;`,
  `sTD2DInputs[]`, `vUV.st`, `uTD2DInfos[]`).
