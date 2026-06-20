# plugin_hands_only.py
# Run in TouchDesigner's Textport:
#   exec(open(r'C:/Users/biyon/handycam/scripts/plugin_hands_only.py').read())
#
# Turns OFF every MediaPipe detector except Hands. This declutters the webcam
# feed (removes the face mesh, person/object boxes, pose skeleton) and frees up
# GPU. Fully reversible — flip any toggle back On in the MediaPipe parameters.

mp = op('/project1/MediaPipe')
if mp is None:
    print("[plugin_hands_only] /project1/MediaPipe not found — check the path.")
else:
    turned_off, kept_on = [], []
    for p in mp.pars():
        label = (p.label or '').strip().lower()
        if not label:
            continue
        # Only touch the detector toggles (their labels start with Detect/Classify).
        if not (label.startswith('detect') or label.startswith('classify')):
            continue
        try:
            if 'hand' in label:
                p.val = 1
                kept_on.append(p.label)
            else:
                p.val = 0
                turned_off.append(p.label)
        except Exception as e:
            print("  [warn] could not set", p.name, ":", e)

    print("[plugin_hands_only] turned OFF:", turned_off)
    print("[plugin_hands_only] kept ON :", kept_on)
    print("[plugin_hands_only] done — go view /handycam/out1")
