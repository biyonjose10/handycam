# Discovering the plugin's hand-CHOP channel names

The torinmb `mediapipe-touchdesigner` plugin streams hand landmarks as CHOP
channels, but the exact channel names are internal to the `.tox` and are **not
publicly documented**. You discover them once, paste them into `config.py`, and
never touch them again.

## Steps

1. Drag **`MediaPipe.tox`** into your project. When prompted, check
   **"Enable External .tox"** (keeps your `.toe` small).
2. Select your webcam in the component, and **enable the Hands model**.
3. Find the CHOP that carries the hand landmark stream (often named `hands`,
   `hand_tracking`, or similar inside the component). Note its full path —
   this is your `HANDS_CHOP_PATH`.
4. Drop an **Info CHOP** or **Examine DAT** onto that CHOP (drag it out, then
   set its operator parameter to the hands CHOP) to list every channel name.
   Alternatively, middle-click the CHOP to see its channel list in the pop-up.
5. Identify the four channels you need:
   - **left hand, wrist (landmark 0), X** and **Y**
   - **right hand, wrist (landmark 0), X** and **Y**
   Landmark indices: `0` = wrist, `9` = middle-finger MCP (≈ palm center). The
   spec uses the wrist; switch to `9` if you prefer the palm.
6. Paste those four exact names into `config.py`:
   ```python
   SRC_LEFT_X  = '<paste here>'
   SRC_LEFT_Y  = '<paste here>'
   SRC_RIGHT_X = '<paste here>'
   SRC_RIGHT_Y = '<paste here>'
   ```
7. Re-run `build_network.py`. The `sel_hands` Select CHOP renames them to the
   stable names `hand_left_x/y`, `hand_right_x/y` that the rest of the network
   (and the GLSL uniforms) depend on.

## Notes

- If the plugin reports handedness from the camera's point of view, the user's
  physical left hand may be labelled "Right" (and vice-versa). If the triangle
  corners feel swapped, set `SWAP_HANDS = True` in `config.py`.
- The plugin normalises coordinates to `0..1` with origin at the **top-left**
  (y increases downward). `FLIP_Y = True` converts this to TouchDesigner's UV
  space (origin bottom-left). If your webcam is shown mirrored, also try
  `MIRROR_X = True`.
- Coordinate channels are usually named with a `tx`/`ty` (translate) or `x`/`y`
  suffix per landmark — the placeholder names in `config.py` are guesses; the
  discovery step above gives you the real ones.
