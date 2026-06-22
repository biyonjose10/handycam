# Finding the plugin's hands DAT and webcam TOP

Handycam reads hand landmarks from the torinmb `mediapipe-touchdesigner`
plugin's **hands JSON DAT** (not a CHOP), and reuses the plugin's webcam frame.
You confirm both paths once, paste them into `config.py`, and never touch them
again. The defaults below match a stock `MediaPipe.tox` dropped at
`/project1/MediaPipe`.

## What the code expects

```python
# config.py
HANDS_DAT_PATH    = '/project1/MediaPipe/hands'    # JSON DAT of landmarks
WEBCAM_SELECT_TOP = '/project1/MediaPipe/video'    # plugin's webcam frame
```

`scripts/hands_to_chop.py` parses the DAT's JSON each frame. It reads
`gestureResults.landmarks` — a list of up to two hands, each a list of 21
landmark points with normalized `x`/`y` (origin **top-left**, y **down**).
Fingertip landmark indices it uses: `4` = thumb, `8` = index, `12` = middle,
`16` = ring.

## Steps

1. Drag **`MediaPipe.tox`** into your project. When prompted, check
   **"Enable External .tox"** (keeps your `.toe` small).
2. Select your webcam in the component, and **enable the Hands model**.
3. Find the **DAT carrying the hand landmark JSON** inside the component
   (typically named `hands`). Note its full path → this is `HANDS_DAT_PATH`.
   Middle-click it to confirm the text is JSON containing a `landmarks` array.
4. Find the **TOP carrying the webcam frame** the landmarks were computed on
   (typically `video`). Note its full path → this is `WEBCAM_SELECT_TOP`.
5. If your paths differ from the defaults, paste the real ones into `config.py`.
6. Re-run `build_network.py`.

## Sanity-checking the JSON shape

If the quads don't track, middle-click the hands DAT and confirm the structure
matches what `hands_to_chop.py` expects:

```json
{ "gestureResults": { "landmarks": [ [ {"x":0.5,"y":0.5,"z":0.0}, ... ], ... ] } }
```

The parser also accepts the `landmarks` array at the top level (it falls back to
`data` if `gestureResults` is absent). If the plugin nests it differently, adjust
the `gr = data.get('gestureResults', data)` / `gr.get('landmarks', [])` lines.

## Notes

- The plugin normalises coordinates to `0..1` with origin at the **top-left**
  (y increases downward). `FLIP_Y = True` converts this to TouchDesigner's UV
  space (origin bottom-left). If the webcam looks mirrored, also try
  `MIRROR_X = True` — but note it flips x per-channel and does **not** reverse a
  quad's winding.
- A quad needs **both hands** (two fingertips each). With one hand or none, that
  quad's `present` flag is 0 and it's hidden — this is expected behavior.
- Run `scripts/plugin_hands_only.py` to switch off the face/pose/object detectors
  if the plugin is also drawing those on the feed.
