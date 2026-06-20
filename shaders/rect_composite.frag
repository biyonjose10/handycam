// rect_composite.frag — Hand-framed rectangular mask compositor.
// Input 0: raw webcam (clean passthrough, shown OUTSIDE the box)
// Input 1: glitched risograph result (shown INSIDE the box)
// Input 2: paper-grain noise (monochrome)
//
// The two box corners arrive as vec2 uniforms in UV space (0..1, y up): one per
// hand (midpoint of that hand's thumb + index). The axis-aligned rectangle is the
// bounding box of the two corners. Hard edges (no feathering). Inside the box we
// add paper grain + slight desaturation; outside stays a clean webcam.

uniform vec2 uCornerL;   // one hand's frame corner
uniform vec2 uCornerR;   // the other hand's frame corner
uniform vec2 uGrain;     // x = grain opacity (0..1), y = desaturation (0..1)

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main() {
    vec2 uv    = vUV.st;
    vec3 raw   = texture(sTD2DInputs[0], uv).rgb;
    vec3 fx    = texture(sTD2DInputs[1], uv).rgb;
    vec3 grain = texture(sTD2DInputs[2], uv).rgb;

    vec2 lo = min(uCornerL, uCornerR);
    vec2 hi = max(uCornerL, uCornerR);
    bool inside = all(greaterThanEqual(uv, lo)) && all(lessThanEqual(uv, hi));

    vec3 col;
    if (inside) {
        col = fx;
        col = mix(col, col * grain, clamp(uGrain.x, 0.0, 1.0));
        col = mix(col, vec3(luma(col)), clamp(uGrain.y, 0.0, 1.0));
    } else {
        col = raw;
    }

    fragColor = vec4(col, 1.0);
}
