"""
Handycam configuration.

Edit these values, then re-run build_network.py inside TouchDesigner's Textport.
Hand data comes from the torinmb MediaPipe plugin as a JSON DAT, which a Script CHOP
parses into three finger-framed quads (see scripts/hands_to_chop.py).
"""

# --- Plugin hookup ----------------------------------------------------------------
HANDS_DAT_PATH = '/project1/MediaPipe/hands'

# Fingertip landmarks framing the three quads:
#   Quad A (Risograph) = thumb + index
#   Quad B (Cyanotype) = index + middle
#   Quad C (Stippling) = middle + ring
THUMB_INDEX  = 4
INDEX_INDEX  = 8
MIDDLE_INDEX = 12
RING_INDEX   = 16

# --- Webcam source ----------------------------------------------------------------
WEBCAM_SOURCE      = 'select'                     # reuse the plugin's feed (no camera contention)
WEBCAM_SELECT_TOP  = '/project1/MediaPipe/video'  # plugin webcam TOP (same space as landmarks)
WEBCAM_FLIP_X      = False

# --- Coordinate handling ----------------------------------------------------------
FLIP_Y   = True     # MediaPipe y is top-down; TD UV is bottom-up -> use (1 - y)
MIRROR_X = False    # flip landmark x if the quads are left/right reversed

# --- Smoothing --------------------------------------------------------------------
LAG = 0.07          # Lag CHOP time constant in seconds (0.05-0.10)

# --- Effect: Risograph (quad A) ---------------------------------------------------
RISO_OFFSET_PX = 4.0     # misregistration offset between ink passes (2-6)

# --- Effect: Cyanotype (quad B) ---------------------------------------------------
CYANO_CONTRAST = 1.6     # tonal contrast (1.0 = none, higher = starker)
CYANO_BLEED_PX = 2.0     # soft photochemical bleed radius, pixels

# --- Effect: Stippling (quad C) ---------------------------------------------------
STIPPLE_CELL_PX = 14.0   # halftone dot cell size @1280x720 (coarser = bigger dots)

# --- Paper / finish (applied inside every quad) -----------------------------------
GRAIN_OPACITY = 0.08     # paper-grain overlay opacity
DESATURATE    = 0.0      # keep 0 to preserve the vivid ink colors

# --- Output -----------------------------------------------------------------------
RESOLUTION = (1280, 720)
