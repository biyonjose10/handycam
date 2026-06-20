# hands_to_chop.py — Script CHOP callbacks: parse the MediaPipe hands JSON DAT
# into the 4 corners of the finger-framed quad (8 channels c0x..c3y).
#
# Each hand contributes two fingertip points (thumb tip + index tip), giving 4
# points total. They're ordered counter-clockwise around their centroid so the
# downstream point-in-quad test always sees a clean convex polygon, regardless of
# how the hands are held or labelled.
#
# Loaded by build_network.py into the script_hands CHOP's "Callbacks DAT".
# Placeholders are substituted at build time from config.py.
#
# /project1/MediaPipe/hands JSON: gestureResults.landmarks = [[{x,y,z}*21], ...]
# Coords normalized 0..1, origin TOP-LEFT, y DOWN. LM 4 = thumb tip, 8 = index tip.

import json
import math

HANDS_DAT = '__HANDS_DAT_PATH__'
THUMB = __THUMB_INDEX__
INDEX = __INDEX_INDEX__

# Default quad (landmark space, y down) when no hands are seen.
DEF_PTS = [(0.35, 0.40), (0.65, 0.40), (0.65, 0.60), (0.35, 0.60)]
NAMES = ('c0x', 'c0y', 'c1x', 'c1y', 'c2x', 'c2y', 'c3x', 'c3y')


def _two_points(hand):
    """Thumb tip and index tip of one hand; falls back to wrist."""
    n = len(hand)
    if THUMB < n and INDEX < n:
        t, i = hand[THUMB], hand[INDEX]
        return (float(t['x']), float(t['y'])), (float(i['x']), float(i['y']))
    p = hand[0]
    return (float(p['x']), float(p['y'])), (float(p['x']) + 0.02, float(p['y']) + 0.02)


def _ordered(pts):
    """Order 4 points CCW around their centroid -> clean convex quad."""
    cx = sum(p[0] for p in pts) / 4.0
    cy = sum(p[1] for p in pts) / 4.0
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 1

    prev = scriptOp.fetch('prev', list(DEF_PTS))
    pts = []
    dat = op(HANDS_DAT)
    try:
        txt = dat.text if dat else ''
        data = json.loads(txt) if txt.strip() else {}
        gr = data.get('gestureResults', data)
        lms = gr.get('landmarks', []) or []
        for hand in lms[:2]:
            if not hand:
                continue
            a, b = _two_points(hand)
            pts.append(a)
            pts.append(b)
    except Exception as e:
        debug('hands_to_chop parse error:', e)

    if len(pts) >= 4:
        pts = _ordered(pts[:4])
    elif len(pts) == 2:
        # one hand only: a small quad hugging its two fingertips
        (ax, ay), (bx, by) = pts
        pts = _ordered([(ax, ay), (bx, by), (bx + 0.04, by + 0.04), (ax + 0.04, ay + 0.04)])
    else:
        pts = list(prev)

    scriptOp.store('prev', pts)
    flat = [v for p in pts for v in p]
    for name, val in zip(NAMES, flat):
        scriptOp.appendChan(name).vals = [val]
    return


def onSetupParameters(scriptOp):
    return
