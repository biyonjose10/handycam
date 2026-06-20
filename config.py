"""
Handycam configuration.

Edit these values, then re-run build_network.py inside TouchDesigner's Textport.
The hand data comes from the torinmb MediaPipe plugin as a JSON DAT, which a small
Script CHOP parses into channels (see scripts/hands_to_chop.py).
"""

# --- Plugin hookup ----------------------------------------------------------------
# The plugin's hands output DAT (JSON). Confirmed path from the loaded MediaPipe.tox:
HANDS_DAT_PATH = '/project1/MediaPipe/hands'
# Which hand landmark drives the triangle corner: 0 = wrist, 9 ~ palm center.
LANDMARK_INDEX = 0

# --- Webcam source ----------------------------------------------------------------
# 'device' -> our own Video Device In TOP (default camera)
# 'select' -> reuse an existing TOP elsewhere by path (set WEBCAM_SELECT_TOP)
WEBCAM_SOURCE      = 'select'                       # reuse the plugin's feed (avoids camera contention)
WEBCAM_SELECT_TOP  = '/project1/MediaPipe/video'    # the plugin's webcam TOP (same space as landmarks)
WEBCAM_FLIP_X      = False    # plugin feed is already in landmark space; no extra mirror needed

# --- Coordinate handling ----------------------------------------------------------
FLIP_Y     = True    # MediaPipe y is top-down; TD UV is bottom-up -> use (1 - y)
MIRROR_X   = False   # flip landmark x if the triangle is left/right reversed
SWAP_HANDS = False   # swap which hand drives which bottom corner

# --- Triangle apex ----------------------------------------------------------------
APEX_MODE = 'fixed'      # 'fixed' or 'midpoint' (upward-projected midpoint of hands)
APEX      = (0.5, 0.95)  # UV; TD UV y=1 is the TOP of the frame, so 0.95 ~ top-center

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
