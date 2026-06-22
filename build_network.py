"""
Handycam network builder.

Run this INSIDE TouchDesigner's Textport (Alt+T):

    exec(open(r'C:/Users/biyon/handycam/build_network.py').read())

It (re)creates /handycam: CHOP chain -> webcam source -> four print-effect GLSL
TOPs (Risograph / Negative / Stippling / Mosaic) -> four stacked quad compositors
-> Out. Four finger-framed quads: A = thumb+index (Riso), B = index+middle
(Negative), C = middle+ring (Stipple), D = ring+pinky (Mosaic). Idempotent:
rebuilds /handycam each run.

Prereqs:
  1. The torinmb MediaPipe.tox is in the project, webcam selected, Hands enabled.
  2. config.py has the correct HANDS_DAT_PATH.
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


def set_vec(g, idx, uname, vx=None, vy=None, vz=None, ex=None, ey=None, ez=None):
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
    if ez is not None:
        setexpr(g, f'vec{idx}valuez', ez)
    elif vz is not None:
        setp(g, **{f'vec{idx}valuez': vz})


# --- CHOP chain: hands JSON DAT -> Script CHOP parser -> lag -> null --------------
cb = make(td.textDAT, 'script_hands_callbacks', -600, -150)
parser = read_script('hands_to_chop.py')
parser = parser.replace('__HANDS_DAT_PATH__', C.HANDS_DAT_PATH)
parser = parser.replace('__THUMB_INDEX__', str(C.THUMB_INDEX))
parser = parser.replace('__INDEX_INDEX__', str(C.INDEX_INDEX))
parser = parser.replace('__MIDDLE_INDEX__', str(C.MIDDLE_INDEX))
parser = parser.replace('__RING_INDEX__', str(C.RING_INDEX))
parser = parser.replace('__PINKY_INDEX__', str(C.PINKY_INDEX))
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


# --- coordinate expressions for the GLSL uniforms --------------------------------
def chan(name):
    return f"op('null_hands')['{name}']"


def x_expr(name):
    return f"(1-{chan(name)})" if C.MIRROR_X else chan(name)


def y_expr(name):
    return f"(1-{chan(name)})" if C.FLIP_Y else chan(name)


# Quad corner UV expressions (FLIP_Y / MIRROR_X applied per channel), for all 4 quads.
QUAD_A = ['cA0', 'cA1', 'cA2', 'cA3']   # thumb + index   -> Risograph
QUAD_B = ['cB0', 'cB1', 'cB2', 'cB3']   # index + middle  -> Negative
QUAD_C = ['cC0', 'cC1', 'cC2', 'cC3']   # middle + ring   -> Stippling
QUAD_D = ['cD0', 'cD1', 'cD2', 'cD3']   # ring + pinky    -> Mosaic
corner_xy = {c: (x_expr(c + 'x'), y_expr(c + 'y'))
             for c in QUAD_A + QUAD_B + QUAD_C + QUAD_D}


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


# --- four print effects (each from the clean webcam) ------------------------------
riso = make_glsl('riso_cmyk', 'riso_cmyk.frag', -360, -300)
set_vec(riso, 0, 'uOffsetPx', vx=C.RISO_OFFSET_PX, vy=C.RISO_OFFSET_PX)
connect(riso, 0, webcam)

negative = make_glsl('negative', 'negative.frag', -360, -120)
set_vec(negative, 0, 'uAmount', vx=C.NEGATIVE_AMOUNT)
connect(negative, 0, webcam)

stipple = make_glsl('stipple', 'stipple_red.frag', -360, 60)
set_vec(stipple, 0, 'uCell', vx=C.STIPPLE_CELL_PX, vy=C.STIPPLE_CELL_PX)
connect(stipple, 0, webcam)

mosaic = make_glsl('mosaic', 'mosaic.frag', -360, 240)
set_vec(mosaic, 0, 'uBlock', vx=C.MOSAIC_BLOCK_PX, vy=C.MOSAIC_BLOCK_PX)
connect(mosaic, 0, webcam)


# --- paper grain ------------------------------------------------------------------
noise = make(td.noiseTOP, 'paper_grain', -360, -480)
setp(noise, resolutionw=C.RESOLUTION[0], resolutionh=C.RESOLUTION[1],
     mono=1, period=20.0)


# --- quad compositors: A (riso) -> B (negative) -> C (stipple) -> D (mosaic) -------
def quad_layer(name, quad, x, background, effect, present_chan):
    g = make_glsl(name, 'quad_composite.frag', x, -300)
    for idx, c in enumerate(quad):          # uC0..uC3 in vec slots 0..3
        ex, ey = corner_xy[c]
        set_vec(g, idx, 'uC%d' % idx, ex=ex, ey=ey)
    set_vec(g, 4, 'uGrain', vx=C.GRAIN_OPACITY, vy=C.DESATURATE, vz=0.0)
    # uActive: 1 only while both hands frame this quad -> hide it when hands vanish.
    set_vec(g, 5, 'uActive', ex="op('null_hands')['%s']" % present_chan)
    set_vec(g, 6, 'uOutline', vx=C.OUTLINE_PX, vy=C.OUTLINE_OPACITY)
    connect(g, 0, background)   # shown outside the quad
    connect(g, 1, effect)       # effect shown inside the quad
    connect(g, 2, noise)        # paper grain
    return g

quad_a = quad_layer('quad_a', QUAD_A, 120, webcam, riso, 'presentA')
quad_b = quad_layer('quad_b', QUAD_B, 320, quad_a, negative, 'presentB')
quad_c = quad_layer('quad_c', QUAD_C, 520, quad_b, stipple, 'presentC')
quad_d = quad_layer('quad_d', QUAD_D, 720, quad_c, mosaic, 'presentD')


# --- output -----------------------------------------------------------------------
out = make(td.outTOP, 'out1', 920, -300)
connect(out, 0, quad_d)
out.viewer = True

print(f"Done. Output: {out.path}")
print("Reminders:")
print("  * Quads: thumb+index = Risograph, index+middle = Negative,")
print("    middle+ring = Stippling, ring+pinky = Mosaic. Frame each with both hands.")
print("  * Toggle MIRROR_X / FLIP_Y in config.py if the quads are mirrored/inverted.")
print("  * Tune RISO_/NEGATIVE_/STIPPLE_/MOSAIC_ values in config.py, then re-run.")
print("  * Check each GLSL TOP's node for compile errors (red); right-click >")
print("    'View Errors' if a shader fails to compile.")
