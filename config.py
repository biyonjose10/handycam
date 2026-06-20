"""
Handycam configuration.

Edit these values, then re-run build_network.py inside TouchDesigner's Textport.
The hand data comes from the torinmb MediaPipe plugin as a JSON DAT, which a small
Script CHOP parses into channels (see scripts/hands_to_chop.py).
"""

# --- Plugin hookup ----------------------------------------------------------------
# The plugin's hands output DAT (JSON). Confirmed path from the loaded MediaPipe.tox:
HANDS_DAT_PATH = '/project1/MediaPipe/hands'
# Each hand's box corner = midpoint of these two landmarks (finger-frame gesture).
THUMB_INDEX = 4   # thumb tip
INDEX_INDEX = 8   # index fingertip

# --- Webcam source ----------------------------------------------------------------
# 'device' -> our own Video Device In TOP (default camera)
# 'select' -> reuse an existing TOP elsewhere by path (set WEBCAM_SELECT_TOP)
WEBCAM_SOURCE      = 'select'                       # reuse the plugin's feed (avoids camera contention)
WEBCAM_SELECT_TOP  = '/project1/MediaPipe/video'    # the plugin's webcam TOP (same space as landmarks)
WEBCAM_FLIP_X      = False    # plugin feed is already in landmark space; no extra mirror needed

# --- Coordinate handling ----------------------------------------------------------
FLIP_Y     = True    # MediaPipe y is top-down; TD UV is bottom-up -> use (1 - y)
MIRROR_X   = False   # flip landmark x if the box is left/right reversed
SWAP_HANDS = False   # cosmetic now (box is the bounding box of both corners)

# --- Glitch (inside the box) ------------------------------------------------------
GLITCH_RGB_SHIFT_PX = 6.0    # chromatic split base, pixels
GLITCH_SCAN_FREQ    = 400.0  # scanline frequency
GLITCH_SCAN_AMT     = 0.35   # scanline strength 0..1
GLITCH_FEEDBACK     = 0.85   # trail/echo amount 0..~0.97 (higher = longer trails)
GLITCH_MOTION_GAIN  = 40.0   # how strongly hand speed drives glitch intensity

# --- Smoothing --------------------------------------------------------------------
LAG = 0.07               # Lag CHOP time constant in seconds (0.05-0.10)

# --- Risograph --------------------------------------------------------------------
PALETTE   = ['#1a3a6e', '#2d5a27', '#d4a017', '#ffffff']   # baked into riso.frag (reference)
MISREG_PX = 3.0          # misregistration diagonal offset, pixels (2-4)

# --- Halftone ---------------------------------------------------------------------
CELL_PX        = 10.0    # dot cell size @1280x720 (8-12)
DENSITY_TOP    = 1.3     # cell multiplier at top of frame (>1 = sparser/smaller)
DENSITY_BOTTOM = 0.8     # cell multiplier at bottom (<1 = denser/bigger)

# --- Paper / finish ---------------------------------------------------------------
GRAIN_OPACITY = 0.15     # paper-grain overlay opacity
DESATURATE    = 0.20     # desaturation amount inside the triangle

# --- Output -----------------------------------------------------------------------
RESOLUTION = (1280, 720)
