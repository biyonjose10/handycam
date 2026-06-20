# hands_to_chop.py — Script CHOP callbacks: parse the MediaPipe hands JSON DAT
# into 4 channels (hand_left_x/y, hand_right_x/y).
#
# Loaded by build_network.py into the script_hands CHOP's "Callbacks DAT".
# The placeholders __HANDS_DAT_PATH__ and __LANDMARK_INDEX__ are substituted at
# build time from config.py — do not edit those by hand here.
#
# The plugin's /project1/MediaPipe/hands DAT contains JSON shaped like:
#   {"gestureResults":{"landmarks":[[{x,y,z}*21], ...],
#                      "handednesses":[[{"categoryName":"Left"/"Right",...}], ...]},
#    "resolution":{"width":1280,"height":720}}
# Coordinates are normalized 0..1, origin TOP-LEFT, y DOWN.

import json

HANDS_DAT = '__HANDS_DAT_PATH__'
LM = __LANDMARK_INDEX__          # 0 = wrist, 9 ~ palm center

DEFAULTS = {
    'hand_left_x': 0.25, 'hand_left_y': 0.80,
    'hand_right_x': 0.75, 'hand_right_y': 0.80,
}
NAMES = ('hand_left_x', 'hand_left_y', 'hand_right_x', 'hand_right_y')


def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 1

    # Start from the last good values so a hand dropping out for a frame holds steady.
    vals = dict(scriptOp.fetch('prev', dict(DEFAULTS)))

    dat = op(HANDS_DAT)
    try:
        txt = dat.text if dat else ''
        data = json.loads(txt) if txt.strip() else {}
        gr = data.get('gestureResults', data)
        lms = gr.get('landmarks', []) or []
        handed = gr.get('handednesses') or gr.get('handedness') or []
        for i, hand in enumerate(lms):
            if not hand or LM >= len(hand):
                continue
            pt = hand[LM]
            label = 'Left'
            if i < len(handed) and handed[i]:
                label = handed[i][0].get('categoryName', label)
            key = 'left' if str(label).lower().startswith('l') else 'right'
            vals['hand_%s_x' % key] = float(pt['x'])
            vals['hand_%s_y' % key] = float(pt['y'])
    except Exception as e:
        debug('hands_to_chop parse error:', e)

    scriptOp.store('prev', vals)
    for name in NAMES:
        scriptOp.appendChan(name).vals = [vals[name]]
    return


def onSetupParameters(scriptOp):
    return
