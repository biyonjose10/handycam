# hands_to_chop.py — Script CHOP callbacks: parse the MediaPipe hands JSON DAT
# into TWO finger-framed quads (16 channels):
#   Quad A (cA0..cA3): both hands' THUMB tip + INDEX tip   -> normal effect
#   Quad B (cB0..cB3): both hands' INDEX tip + MIDDLE tip   -> inverse effect
#
# Each quad: 2 fingertips per hand = 4 points, ordered counter-clockwise around
# their centroid so the point-in-quad test always sees a clean convex polygon.
#
# Loaded by build_network.py into the script_hands CHOP's "Callbacks DAT".
# Placeholders are substituted at build time from config.py.
# Coords normalized 0..1, origin TOP-LEFT, y DOWN. LM 4=thumb, 8=index, 12=middle.

import json
import math

HANDS_DAT = '__HANDS_DAT_PATH__'
THUMB = __THUMB_INDEX__
INDEX = __INDEX_INDEX__
MIDDLE = __MIDDLE_INDEX__

DEF_A = [(0.30, 0.40), (0.60, 0.40), (0.60, 0.60), (0.30, 0.60)]
DEF_B = [(0.40, 0.28), (0.70, 0.28), (0.70, 0.48), (0.40, 0.48)]
NAMES = (
    'cA0x', 'cA0y', 'cA1x', 'cA1y', 'cA2x', 'cA2y', 'cA3x', 'cA3y',
    'cB0x', 'cB0y', 'cB1x', 'cB1y', 'cB2x', 'cB2y', 'cB3x', 'cB3y',
)


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

    prevA, prevB = scriptOp.fetch('prev', (list(DEF_A), list(DEF_B)))
    A, B = [], []
    dat = op(HANDS_DAT)
    try:
        txt = dat.text if dat else ''
        data = json.loads(txt) if txt.strip() else {}
        gr = data.get('gestureResults', data)
        lms = gr.get('landmarks', []) or []
        for hand in lms[:2]:
            if not hand:
                continue
            A.append(_pt(hand, THUMB))
            A.append(_pt(hand, INDEX))
            B.append(_pt(hand, INDEX))
            B.append(_pt(hand, MIDDLE))
    except Exception as e:
        debug('hands_to_chop parse error:', e)

    A = _finalize(A, prevA)
    B = _finalize(B, prevB)
    scriptOp.store('prev', (A, B))

    flat = [v for p in A for v in p] + [v for p in B for v in p]
    for name, val in zip(NAMES, flat):
        scriptOp.appendChan(name).vals = [val]
    return


def onSetupParameters(scriptOp):
    return
