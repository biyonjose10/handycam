// triangle_composite.frag — Hand-tracked triangular mask compositor.
// Input 0: raw webcam (clean passthrough, shown OUTSIDE the triangle)
// Input 1: halftone/risograph result (shown INSIDE the triangle)
// Input 2: paper-grain noise (monochrome)
//
// The three triangle vertices arrive as vec2 uniforms in UV space (0..1, y up).
// A cross-product sign test decides whether each pixel is inside the triangle.
// Edge is hard (no feathering). Inside the triangle we add paper grain and a
// slight desaturation for the lo-fi analog feel; outside stays a clean webcam.

uniform vec2 uApex;     // top-center vertex
uniform vec2 uLeft;     // bottom-left vertex  (left hand)
uniform vec2 uRight;    // bottom-right vertex (right hand)
uniform vec2 uGrain;    // x = grain opacity (0..1), y = desaturation amount (0..1)

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float edgeSign(vec2 p, vec2 a, vec2 b) {
    return (p.x - b.x) * (a.y - b.y) - (a.x - b.x) * (p.y - b.y);
}

bool pointInTriangle(vec2 p, vec2 a, vec2 b, vec2 c) {
    float d1 = edgeSign(p, a, b);
    float d2 = edgeSign(p, b, c);
    float d3 = edgeSign(p, c, a);
    bool hasNeg = (d1 < 0.0) || (d2 < 0.0) || (d3 < 0.0);
    bool hasPos = (d1 > 0.0) || (d2 > 0.0) || (d3 > 0.0);
    return !(hasNeg && hasPos);   // all same sign => inside
}

void main() {
    vec2 uv    = vUV.st;
    vec3 raw   = texture(sTD2DInputs[0], uv).rgb;
    vec3 fx    = texture(sTD2DInputs[1], uv).rgb;
    vec3 grain = texture(sTD2DInputs[2], uv).rgb;

    bool inside = pointInTriangle(uv, uApex, uLeft, uRight);

    vec3 col;
    if (inside) {
        col = fx;
        // paper grain overlay (multiply), gentle opacity
        col = mix(col, col * grain, clamp(uGrain.x, 0.0, 1.0));
        // slight desaturation toward luminance
        col = mix(col, vec3(luma(col)), clamp(uGrain.y, 0.0, 1.0));
    } else {
        col = raw;
    }

    fragColor = vec4(col, 1.0);
}
