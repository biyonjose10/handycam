# hands_to_chop.py — Script CHOP callbacks: parse the MediaPipe hands JSON DAT
# into FOUR finger-framed quads (32 channels):
#   Quad A (cA0..cA3): both hands' THUMB  + INDEX  tips -> Risograph
#   Quad B (cB0..cB3): both hands' INDEX  + MIDDLE tips -> Negative
#   Quad C (cC0..cC3): both hands' MIDDLE + RING   tips -> Stippling
#   Quad D (cD0..cD3): both hands' RING   + PINKY  tips -> Mosaic
#
# Each quad: 2 fingertips per hand = 4 points, ordered counter-clockwise around
# their centroid so the point-in-quad test always sees a clean convex polygon.
#
# Loaded by build_network.py into the script_hands CHOP's "Callbacks DAT".
# Placeholders are substituted at build time from config.py.
# Coords normalized 0..1, origin TOP-LEFT, y DOWN.
# LM 4=thumb, 8=index, 12=middle, 16=ring, 20=pinky (fingertips).

import json
import math

HANDS_DAT = '__HANDS_DAT_PATH__'
THUMB = __THUMB_INDEX__
INDEX = __INDEX_INDEX__
MIDDLE = __MIDDLE_INDEX__
RING = __RING_INDEX__
PINKY = __PINKY_INDEX__

# (lo finger, hi finger) per quad, and a default centered quad for each.
QUADS = ('A', 'B', 'C', 'D')
PAIRS = {'A': (THUMB, INDEX), 'B': (INDEX, MIDDLE), 'C': (MIDDLE, RING), 'D': (RING, PINKY)}
DEFAULTS = {
    'A': [(0.24, 0.42), (0.50, 0.42), (0.50, 0.62), (0.24, 0.62)],
    'B': [(0.38, 0.30), (0.64, 0.30), (0.64, 0.50), (0.38, 0.50)],
    'C': [(0.52, 0.42), (0.78, 0.42), (0.78, 0.62), (0.52, 0.62)],
    'D': [(0.66, 0.50), (0.92, 0.50), (0.92, 0.70), (0.66, 0.70)],
}
NAMES = tuple('c%s%d%s' % (q, i, ax) for q in QUADS for i in range(4) for ax in ('x', 'y'))


def _pt(hand, idx):
    n = len(hand)
    p = hand[idx] if idx < n else hand[0]
    return (float(p['x']), float(p['y']))


def _ordered(pts):
    cx = sum(p[0] for p in pts) / 4.0
    cy = sum(p[1] for p in pts) / 4.0
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def _finalize(pts, prev):
    if len(pts) >= 4:
        return _ordered(pts[:4])
    if len(pts) == 2:
        (ax, ay), (bx, by) = pts
        return _ordered([(ax, ay), (bx, by), (bx + 0.04, by + 0.04), (ax + 0.04, ay + 0.04)])
    return list(prev)


def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 1

    prev = scriptOp.fetch('prev', {q: list(DEFAULTS[q]) for q in QUADS})
    acc = {q: [] for q in QUADS}
    dat = op(HANDS_DAT)
    try:
        txt = dat.text if dat else ''
        data = json.loads(txt) if txt.strip() else {}
        gr = data.get('gestureResults', data)
        lms = gr.get('landmarks', []) or []
        for hand in lms[:2]:
            if not hand:
                continue
            for q in QUADS:
                lo, hi = PAIRS[q]
                acc[q].append(_pt(hand, lo))
                acc[q].append(_pt(hand, hi))
    except Exception as e:
        debug('hands_to_chop parse error:', e)

    out = {q: _finalize(acc[q], prev[q]) for q in QUADS}
    # A quad is "present" only when both hands contributed its two fingertips
    # (4 points). Fewer points (one hand / no hands) -> hide the quad entirely.
    present = {q: (1.0 if len(acc[q]) >= 4 else 0.0) for q in QUADS}
    scriptOp.store('prev', out)

    flat = [v for q in QUADS for p in out[q] for v in p]
    for name, val in zip(NAMES, flat):
        scriptOp.appendChan(name).vals = [val]
    for q in QUADS:
        scriptOp.appendChan('present' + q).vals = [present[q]]
    return


def onSetupParameters(scriptOp):
    return
