# Handycam

A real-time webcam visual effect for **TouchDesigner 2023** (Python 3.11).

MediaPipe tracks both hands. Their fingertips frame **three overlapping
quadrilaterals**, and each quad renders the webcam through a different print
effect. Outside every quad the **clean webcam** shows through with a hard
(un-feathered) edge. The quads track your hands live, and **disappear entirely**
the moment a quad's hands aren't detected.

| Quad | Framed by (both hands) | Effect |
|---|---|---|
| **A** | thumb + index tips | **Risograph** — vibrant misregistered ink passes |
| **B** | index + middle tips | **Negative** — inverted webcam colors |
| **C** | middle + ring tips | **Stippling** — bold red halftone dots on paper |

Each quad needs **both hands** (two fingertips each = four corners). Raise both
hands and spread your fingers to open the quads; lower a hand and the quads it
fed vanish, leaving the clean webcam.

## What's in this repo

| File | Purpose |
|---|---|
| `build_network.py` | Auto-builder — paste into TD's Textport to construct the whole network. |
| `config.py` | All tunables: plugin paths, fingertip landmarks, per-effect params, smoothing, coord flags. |
| `scripts/hands_to_chop.py` | Script CHOP callbacks — parse the hands JSON DAT into 3 quads (24 corner channels + `presentA/B/C`). |
| `scripts/plugin_hands_only.py` | Turns off every MediaPipe detector except Hands (declutters the feed, frees GPU). |
| `shaders/riso_cmyk.frag` | Risograph: 3 misregistered subtractive ink passes (cyan / green / yellow). |
| `shaders/negative.frag` | Photographic negative (`1 - rgb`), `NEGATIVE_AMOUNT` mixes original↔inverted. |
| `shaders/stipple_red.frag` | Brick-grid red halftone, luminance-driven dot radius. |
| `shaders/quad_composite.frag` | Point-in-quad cross-product mask + paper grain; `uActive` hides the quad when hands are gone. |
| `docs/channel_mapping.md` | One-time discovery of the plugin's hands JSON DAT path and webcam TOP. |

> **Note:** TouchDesigner `.toe` files are binary, so the project itself isn't
> checked in as a file you can edit. Instead, `build_network.py` *generates* the
> network programmatically. Run it once (or after any `config.py`/shader change).

## Prerequisites

- **TouchDesigner 2023** (Python 3.11).
- **MediaPipe plugin:** [`torinmb/mediapipe-touchdesigner`](https://github.com/torinmb/mediapipe-touchdesigner)
  — download the latest release `.zip` and grab `MediaPipe.tox`.

## Setup

1. Open TouchDesigner. Drag **`MediaPipe.tox`** into your project; when prompted,
   check **"Enable External .tox"**.
2. In the component, **select your webcam** and **enable the Hands model**.
3. Follow **`docs/channel_mapping.md`** to confirm the hands JSON DAT path and the
   webcam TOP. Paste them into `config.py` (`HANDS_DAT_PATH`, `WEBCAM_SELECT_TOP`).
4. *(Optional)* Run `scripts/plugin_hands_only.py` to disable the other detectors.
5. Open the **Textport** (`Alt+T`) and run:
   ```python
   exec(open(r'C:/Users/biyon/handycam/build_network.py').read())
   ```
6. The network builds under **`/handycam`**. View `/handycam/out1`.

## Verifying it works

- With **no hands up**, the output is the **clean webcam** — no shapes at all.
- Raise **both hands**, fingers spread → **three quads** appear: risograph inks
  (thumb+index), color **negative** (index+middle), red **stipple** (middle+ring).
- Move your hands → the quads track **smoothly** (no jitter).
- Lower a hand → the quads it fed **disappear instantly**, back to clean webcam.

## Tuning (`config.py`, then re-run the builder)

| Symptom / goal | Change |
|---|---|
| Quads mirrored left/right | `MIRROR_X = True` |
| Quads vertically inverted | toggle `FLIP_Y` |
| Mirrored / selfie webcam | `WEBCAM_FLIP_X = True` |
| Too jittery / too laggy | `LAG` (0.05–0.10) |
| Risograph misalignment strength | `RISO_OFFSET_PX` (2–6) |
| Negative intensity | `NEGATIVE_AMOUNT` (0 = off, 1 = full) |
| Stipple dots too big / small | `STIPPLE_CELL_PX` (8–18) |
| More/less analog feel | `GRAIN_OPACITY`, `DESATURATE` |
| Different finger pairs | `THUMB_INDEX` / `INDEX_INDEX` / `MIDDLE_INDEX` / `RING_INDEX` |

## Notes / known gotchas

- **Webcam contention:** the plugin captures the camera internally. By default
  (`WEBCAM_SOURCE = 'select'`) we reuse the plugin's `/project1/MediaPipe/video`
  feed so two operators don't fight over the camera. Set it to `'videodevice'`
  for an own Video Device In TOP only if the plugin doesn't expose a usable feed.
- **A quad needs both hands.** `hands_to_chop.py` only marks a quad present when
  it gets all four corners (two fingertips from each hand); otherwise that quad's
  `uActive` flag goes to 0 and `quad_composite.frag` hides it.
- **`MIRROR_X`** flips landmark x per-channel but does not reverse quad winding —
  if a quad's fill looks wrong after mirroring, that's the place to look.
- **Shader errors:** if a GLSL TOP turns red, right-click → view errors. The
  shaders target the TD GLSL-TOP convention (`out vec4 fragColor;`,
  `sTD2DInputs[]`, `vUV.st`, `uTD2DInfos[]`).
