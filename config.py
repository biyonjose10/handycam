"""
Handycam configuration.

Edit the values here, then re-run build_network.py inside TouchDesigner's Textport.
The two things you MUST set after installing the plugin are HANDS_CHOP_PATH and the
SRC_* channel names — see docs/channel_mapping.md for the one-time discovery steps.
"""

# --- Plugin hookup (EDIT after dropping in MediaPipe.tox) -------------------------
# Path to the torinmb mediapipe-touchdesigner hands CHOP (left/right landmark stream).
HANDS_CHOP_PATH  = '/project1/MediaPipe/hands'
# Path to the plugin's webcam passthrough TOP (used as the clean source frame).
PLUGIN_VIDEO_TOP = '/project1/MediaPipe/webcam'
# True  -> use the plugin's passthrough TOP as the webcam source (avoids camera contention)
# False -> create our own Video Device In TOP
USE_PLUGIN_PASSTHROUGH = True

# Source channel names AS THEY APPEAR in the hands CHOP. These are the plugin's
# internal names and are NOT publicly documented — discover them once (see docs/)
# and paste them here. We extract wrist (landmark 0); switch to 9 for palm center.
SRC_LEFT_X  = 'left:wrist:tx'
SRC_LEFT_Y  = 'left:wrist:ty'
SRC_RIGHT_X = 'right:wrist:tx'
SRC_RIGHT_Y = 'right:wrist:ty'

# --- Coordinate handling ----------------------------------------------------------
FLIP_Y     = True    # MediaPipe y is top-down; TD UV is bottom-up -> use (1 - y)
MIRROR_X   = False   # set True if the webcam is shown mirrored (selfie view)
SWAP_HANDS = False   # set True if the left/right triangle corners feel swapped

# --- Triangle apex ----------------------------------------------------------------
APEX_MODE = 'fixed'      # 'fixed' or 'midpoint' (upward-projected midpoint of hands)
APEX      = (0.5, 0.95)  # UV; TD UV y=1 is the TOP of the frame, so 0.95 ~ top-center

# --- Smoothing --------------------------------------------------------------------
LAG = 0.07               # Lag CHOP time constant in seconds (0.05-0.10)

# --- Risograph --------------------------------------------------------------------
# Palette is baked into riso.frag; listed here for reference only.
PALETTE   = ['#1a3a6e', '#2d5a27', '#d4a017', '#ffffff']
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
