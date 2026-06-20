"""
Handycam network builder.

Run this INSIDE TouchDesigner's Textport (Alt+T):

    exec(open(r'C:/Users/biyon/handycam/build_network.py').read())

It (re)creates /handycam containing the full hand-tracked risograph triangle
network: CHOP chain -> webcam source -> riso GLSL -> halftone GLSL ->
triangle compositor -> Out. Idempotent: deletes and rebuilds /handycam each run.

Prereqs:
  1. The torinmb MediaPipe.tox is in the project, webcam selected, Hands enabled.
  2. config.py has the correct HANDS_CHOP_PATH and SRC_* channel names.
"""

import os
import sys
import importlib
import td

# ---------------------------------------------------------------------------------
PROJECT_DIR = r'C:\Users\biyon\handycam'
SHADERS_DIR = os.path.join(PROJECT_DIR, 'shaders')
SCRIPTS_DIR = os.path.join(PROJECT_DIR, 'scripts')

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
import config as _cfg
importlib.reload(_cfg)
C = _cfg


# --- small helpers ----------------------------------------------------------------
def read_shader(name):
    with open(os.path.join(SHADERS_DIR, name), 'r', encoding='utf-8') as f:
        return f.read()


def read_script(name):
    with open(os.path.join(SCRIPTS_DIR, name), 'r', encoding='utf-8') as f:
        return f.read()


def setp(o, **kw):
    """Set parameters, warning (not crashing) on any name that doesn't exist."""
    for k, v in kw.items():
        p = getattr(o.par, k, None)
        if p is None:
            print(f"  [warn] {o.path}: no parameter '{k}'")
            continue
        try:
            p.val = v
        except Exception as e:
            print(f"  [warn] {o.path}.{k} = {v!r} failed: {e}")


def setexpr(o, name, expr):
    p = getattr(o.par, name, None)
    if p is None:
        print(f"  [warn] {o.path}: no parameter '{name}'")
        return
    p.expr = expr


def connect(dst, idx, src):
    if src is None:
        print(f"  [warn] {dst.path}: input {idx} source missing")
        return
    dst.inputConnectors[idx].connect(src)


# --- (re)create container ---------------------------------------------------------
root = op('/')
old = root.op('handycam')
if old:
    old.destroy()
comp = root.create(td.baseCOMP, 'handycam')
print(f"Building network in {comp.path} ...")


def make(typ, name, x, y):
    o = comp.create(typ, name)
    o.nodeX, o.nodeY = x, y
    return o


def make_glsl(name, shader_file, x, y):
    g = make(td.glslTOP, name, x, y)
    dat = make(td.textDAT, name + '_src', x, y - 130)
    dat.text = read_shader(shader_file)
    g.par.pixeldat = dat.name
    g.par.outputresolution = 'useinput'   # inherit 1280x720 from connected input
    return g


def set_vec(g, idx, uname, vx=None, vy=None, ex=None, ey=None):
    """Define custom uniform vec on a GLSL TOP (Vectors page, 0-indexed slot)."""
    setp(g, **{f'vec{idx}name': uname})
    if ex is not None:
        setexpr(g, f'vec{idx}valuex', ex)
    elif vx is not None:
        setp(g, **{f'vec{idx}valuex': vx})
    if ey is not None:
        setexpr(g, f'vec{idx}valuey', ey)
    elif vy is not None:
        setp(g, **{f'vec{idx}valuey': vy})


# --- CHOP chain: hands JSON DAT -> Script CHOP parser -> lag -> null --------------
cb = make(td.textDAT, 'script_hands_callbacks', -600, -150)
parser = read_script('hands_to_chop.py')
parser = parser.replace('__HANDS_DAT_PATH__', C.HANDS_DAT_PATH)
parser = parser.replace('__THUMB_INDEX__', str(C.THUMB_INDEX))
parser = parser.replace('__INDEX_INDEX__', str(C.INDEX_INDEX))
cb.text = parser

# Per-frame cook trigger: a Script CHOP with no live input cooks once and stops.
# Feed it a value that changes every frame so it re-parses the hands DAT each frame.
tick = make(td.constantCHOP, 'frame_tick', -780, 0)
setp(tick, name0='tick')
setexpr(tick, 'value0', 'absTime.frame')

script_hands = make(td.scriptCHOP, 'script_hands', -600, 0)
script_hands.par.callbacks = cb.name
connect(script_hands, 0, tick)          # cook trigger (values ignored by the script)
if not op(C.HANDS_DAT_PATH):
    print(f"  [warn] HANDS_DAT_PATH '{C.HANDS_DAT_PATH}' not found yet")

lag = make(td.lagCHOP, 'lag_hands', -420, 0)
setp(lag, lag1=C.LAG, lag2=C.LAG)
connect(lag, 0, script_hands)

null_hands = make(td.nullCHOP, 'null_hands', -240, 0)
connect(null_hands, 0, lag)

# Hand-speed -> glitch intensity: derivative of the corner positions.
slope = make(td.slopeCHOP, 'hand_slope', -420, 150)
connect(slope, 0, null_hands)
null_slope = make(td.nullCHOP, 'null_slope', -240, 150)
connect(null_slope, 0, slope)


# --- coordinate expressions for the GLSL uniforms --------------------------------
def chan(name):
    return f"op('null_hands')['{name}']"


def x_expr(name):
    return f"(1-{chan(name)})" if C.MIRROR_X else chan(name)


def y_expr(name):
    return f"(1-{chan(name)})" if C.FLIP_Y else chan(name)


# Quad corner UV expressions (FLIP_Y / MIRROR_X applied per channel).
CORNERS = ['c0', 'c1', 'c2', 'c3']
corner_xy = {c: (x_expr(c + 'x'), y_expr(c + 'y')) for c in CORNERS}

# Hand-motion magnitude (from the slope CHOP, all 8 corner channels) -> 0..1.
_sl = "op('null_slope')"
_chs = ['c0x', 'c0y', 'c1x', 'c1y', 'c2x', 'c2y', 'c3x', 'c3y']
_terms = '+'.join(f"{_sl}['{c}']**2" for c in _chs)
motion_expr = f"min(1.0, (({_terms})**0.5)*{C.GLITCH_MOTION_GAIN})"


# --- webcam source ----------------------------------------------------------------
if C.WEBCAM_SOURCE == 'select':
    cam = make(td.selectTOP, 'webcam_in', -600, -300)
    setp(cam, top=C.WEBCAM_SELECT_TOP)
    if not op(C.WEBCAM_SELECT_TOP):
        print(f"  [warn] WEBCAM_SELECT_TOP '{C.WEBCAM_SELECT_TOP}' not found yet")
else:
    cam = make(td.videodeviceinTOP, 'webcam_in', -600, -300)

if C.WEBCAM_FLIP_X:
    webcam = make(td.flipTOP, 'webcam_flip', -420, -300)
    setp(webcam, flipx=1)
    connect(webcam, 0, cam)
else:
    webcam = cam


# --- risograph + halftone ---------------------------------------------------------
riso = make_glsl('riso', 'riso.frag', -360, -300)
set_vec(riso, 0, 'uOffsetPx', vx=C.MISREG_PX, vy=C.MISREG_PX)
connect(riso, 0, webcam)

halftone = make_glsl('halftone', 'halftone.frag', -120, -300)
set_vec(halftone, 0, 'uCellPx', vx=C.CELL_PX, vy=C.CELL_PX)
set_vec(halftone, 1, 'uDensity', vx=C.DENSITY_TOP, vy=C.DENSITY_BOTTOM)
connect(halftone, 0, riso)


# --- paper grain ------------------------------------------------------------------
noise = make(td.noiseTOP, 'paper_grain', -360, -480)
setp(noise, resolutionw=C.RESOLUTION[0], resolutionh=C.RESOLUTION[1],
     mono=1, period=20.0)


# --- glitch stage (with feedback trails) ------------------------------------------
glitch = make_glsl('glitch', 'glitch.frag', 120, -300)
set_vec(glitch, 0, 'uShiftPx', vx=C.GLITCH_RGB_SHIFT_PX, vy=0.0)
set_vec(glitch, 1, 'uScan', vx=C.GLITCH_SCAN_FREQ, vy=C.GLITCH_SCAN_AMT)
set_vec(glitch, 2, 'uFeedback', vx=C.GLITCH_FEEDBACK, vy=0.0)
set_vec(glitch, 3, 'uMotion', ex=motion_expr)
set_vec(glitch, 4, 'uTime', ex='absTime.seconds')

glitch_fb = make(td.feedbackTOP, 'glitch_fb', 120, -460)
setp(glitch_fb, top=glitch.name)        # capture glitch's previous frame

connect(glitch, 0, halftone)            # content -> sTD2DInputs[0]
connect(glitch, 1, glitch_fb)           # feedback -> sTD2DInputs[1]


# --- quad compositor --------------------------------------------------------------
comp_glsl = make_glsl('quad_composite', 'quad_composite.frag', 360, -300)
for idx, c in enumerate(CORNERS):           # uC0..uC3 in vec slots 0..3
    ex, ey = corner_xy[c]
    set_vec(comp_glsl, idx, 'u' + c.upper(), ex=ex, ey=ey)
set_vec(comp_glsl, 4, 'uGrain', vx=C.GRAIN_OPACITY, vy=C.DESATURATE)

connect(comp_glsl, 0, webcam)     # raw     -> sTD2DInputs[0]
connect(comp_glsl, 1, glitch)     # glitched-> sTD2DInputs[1]
connect(comp_glsl, 2, noise)      # grain   -> sTD2DInputs[2]


# --- output -----------------------------------------------------------------------
out = make(td.outTOP, 'out1', 560, -300)
connect(out, 0, comp_glsl)
out.viewer = True

print(f"Done. Output: {out.path}")
print("Reminders:")
print("  * Make the finger-frame: thumb + index of BOTH hands = box corners.")
print("  * Toggle MIRROR_X / FLIP_Y in config.py if the box is mirrored/inverted.")
print("  * Tune glitch via GLITCH_* in config.py, then re-run this script.")
print("  * Check each GLSL TOP's node for compile errors (red); right-click >")
print("    'View Errors' if a shader fails to compile.")
