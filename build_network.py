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

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
import config as _cfg
importlib.reload(_cfg)
C = _cfg


# --- small helpers ----------------------------------------------------------------
def read_shader(name):
    with open(os.path.join(SHADERS_DIR, name), 'r', encoding='utf-8') as f:
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


# --- CHOP chain: plugin hands -> select/rename -> lag -> null ---------------------
sel = make(td.selectCHOP, 'sel_hands', -600, 0)
src_names = f"{C.SRC_LEFT_X} {C.SRC_LEFT_Y} {C.SRC_RIGHT_X} {C.SRC_RIGHT_Y}"
setp(sel, channames=src_names, renamefrom=src_names,
     renameto='hand_left_x hand_left_y hand_right_x hand_right_y')
hands_src = op(C.HANDS_CHOP_PATH)
if hands_src:
    connect(sel, 0, hands_src)
else:
    print(f"  [warn] HANDS_CHOP_PATH '{C.HANDS_CHOP_PATH}' not found — "
          f"wire it manually after adding MediaPipe.tox")

lag = make(td.lagCHOP, 'lag_hands', -420, 0)
setp(lag, lag1=C.LAG, lag2=C.LAG)
connect(lag, 0, sel)

null_hands = make(td.nullCHOP, 'null_hands', -240, 0)
connect(null_hands, 0, lag)


# --- coordinate expressions for the GLSL uniforms --------------------------------
def chan(name):
    return f"op('null_hands')['{name}']"


def x_expr(name):
    return f"(1-{chan(name)})" if C.MIRROR_X else chan(name)


def y_expr(name):
    return f"(1-{chan(name)})" if C.FLIP_Y else chan(name)


# Optionally swap which hand drives which bottom corner.
L = ('hand_right_x', 'hand_right_y') if C.SWAP_HANDS else ('hand_left_x', 'hand_left_y')
R = ('hand_left_x', 'hand_left_y') if C.SWAP_HANDS else ('hand_right_x', 'hand_right_y')
left_x, left_y = x_expr(L[0]), y_expr(L[1])
right_x, right_y = x_expr(R[0]), y_expr(R[1])


# --- webcam source ----------------------------------------------------------------
if C.USE_PLUGIN_PASSTHROUGH:
    webcam = make(td.selectTOP, 'webcam_src', -600, -300)
    setp(webcam, top=C.PLUGIN_VIDEO_TOP)
    if not op(C.PLUGIN_VIDEO_TOP):
        print(f"  [warn] PLUGIN_VIDEO_TOP '{C.PLUGIN_VIDEO_TOP}' not found yet")
else:
    webcam = make(td.videodeviceinTOP, 'webcam_src', -600, -300)
    setp(webcam, resolutionw=C.RESOLUTION[0], resolutionh=C.RESOLUTION[1])


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


# --- triangle compositor ----------------------------------------------------------
comp_glsl = make_glsl('triangle_composite', 'triangle_composite.frag', 160, -300)

if C.APEX_MODE == 'midpoint':
    set_vec(comp_glsl, 0, 'uApex',
            ex=f"(({left_x})+({right_x}))/2", vy=C.APEX[1])
else:
    set_vec(comp_glsl, 0, 'uApex', vx=C.APEX[0], vy=C.APEX[1])
set_vec(comp_glsl, 1, 'uLeft', ex=left_x, ey=left_y)
set_vec(comp_glsl, 2, 'uRight', ex=right_x, ey=right_y)
set_vec(comp_glsl, 3, 'uGrain', vx=C.GRAIN_OPACITY, vy=C.DESATURATE)

connect(comp_glsl, 0, webcam)     # raw  -> sTD2DInputs[0]
connect(comp_glsl, 1, halftone)   # fx   -> sTD2DInputs[1]
connect(comp_glsl, 2, noise)      # grain-> sTD2DInputs[2]


# --- output -----------------------------------------------------------------------
out = make(td.outTOP, 'out1', 380, -300)
connect(out, 0, comp_glsl)
out.viewer = True

print(f"Done. Output: {out.path}")
print("Reminders:")
print("  * Select your webcam + enable Hands in the MediaPipe.tox.")
print("  * If channels look wrong, verify SRC_* names (docs/channel_mapping.md).")
print("  * Toggle MIRROR_X / SWAP_HANDS / FLIP_Y in config.py if the triangle")
print("    tracks the wrong hand or is inverted, then re-run this script.")
print("  * Check each GLSL TOP's node for compile errors (red); read its info via")
print("    right-click > 'View Errors' if a shader fails to compile.")
