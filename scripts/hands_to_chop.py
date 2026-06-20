# hands_to_chop.py — Script CHOP callbacks: parse the MediaPipe hands JSON DAT
# into 4 channels (hand_left_x/y, hand_right_x/y), where each "hand_*" point is
# the BOX CORNER for that hand: the midpoint of the thumb tip and index tip
# (the "finger-frame" gesture). The two corners become opposite corners of the
# rectangular mask.
#
# Loaded by build_network.py into the script_hands CHOP's "Callbacks DAT".
# Placeholders are substituted at build time from config.py.
#
# /project1/MediaPipe/hands JSON shape:
#   {"gestureResults":{"landmarks":[[{x,y,z}*21], ...],
#                      "handednesses":[[{"categoryName":"Left"/"Right"}], ...]}}
# Coordinates are normalized 0..1, origin TOP-LEFT, y DOWN.
# Landmark indices: 4 = thumb tip, 8 = index tip, 0 = wrist (fallback).

import json

HANDS_DAT = '__HANDS_DAT_PATH__'
THUMB = __THUMB_INDEX__
INDEX = __INDEX_INDEX__

DEFAULTS = {
    'hand_left_x': 0.30, 'hand_left_y': 0.35,
    'hand_right_x': 0.70, 'hand_right_y': 0.65,
}
NAMES = ('hand_left_x', 'hand_left_y', 'hand_right_x', 'hand_right_y')


def _corner(hand):
    """Midpoint of thumb tip and index tip; falls back to wrist (0)."""
    n = len(hand)
    if THUMB < n and INDEX < n:
        t, i = hand[THUMB], hand[INDEX]
        return (float(t['x']) + float(i['x'])) * 0.5, (float(t['y']) + float(i['y'])) * 0.5
    p = hand[0]
    return float(p['x']), float(p['y'])


def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 1

    # Hold last good values so a hand dropping out for a frame stays steady.
    vals = dict(scriptOp.fetch('prev', dict(DEFAULTS)))

    dat = op(HANDS_DAT)
    try:
        txt = dat.text if dat else ''
        data = json.loads(txt) if txt.strip() else {}
        gr = data.get('gestureResults', data)
        lms = gr.get('landmarks', []) or []
        handed = gr.get('handednesses') or gr.get('handedness') or []
        for i, hand in enumerate(lms):
            if not hand:
                continue
            label = 'Left'
            if i < len(handed) and handed[i]:
                label = handed[i][0].get('categoryName', label)
            key = 'left' if str(label).lower().startswith('l') else 'right'
            cx, cy = _corner(hand)
            vals['hand_%s_x' % key] = cx
            vals['hand_%s_y' % key] = cy
    except Exception as e:
        debug('hands_to_chop parse error:', e)

    scriptOp.store('prev', vals)
    for name in NAMES:
        scriptOp.appendChan(name).vals = [vals[name]]
    return


def onSetupParameters(scriptOp):
    return
