// quad_composite.frag — Hand-framed quadrilateral mask compositor.
// Input 0: raw webcam (clean passthrough, shown OUTSIDE the quad)
// Input 1: glitched risograph result (shown INSIDE the quad)
// Input 2: paper-grain noise (monochrome)
//
// The 4 quad corners arrive as vec2 uniforms in UV space (0..1, y up), ordered
// around the polygon (the 4 fingertips: both hands' thumb + index). A cross-product
// sign test decides inside/outside for a convex quad of EITHER winding. Hard edges.
// Inside we add paper grain + slight desaturation; outside stays a clean webcam.

uniform vec2 uC0, uC1, uC2, uC3;
uniform vec3 uGrain;     // x = grain opacity, y = desaturation, z = invert flag (>0.5)
uniform vec2 uActive;    // x > 0.5 => quad live; otherwise hide it (clean webcam everywhere)

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float edge(vec2 p, vec2 a, vec2 b) {
    return (p.x - a.x) * (b.y - a.y) - (p.y - a.y) * (b.x - a.x);
}

bool inQuad(vec2 p) {
    float d0 = edge(p, uC0, uC1);
    float d1 = edge(p, uC1, uC2);
    float d2 = edge(p, uC2, uC3);
    float d3 = edge(p, uC3, uC0);
    bool neg = (d0 < 0.0) || (d1 < 0.0) || (d2 < 0.0) || (d3 < 0.0);
    bool pos = (d0 > 0.0) || (d1 > 0.0) || (d2 > 0.0) || (d3 > 0.0);
    return !(neg && pos);   // all edges same sign => inside
}

void main() {
    vec2 uv    = vUV.st;
    vec3 raw   = texture(sTD2DInputs[0], uv).rgb;
    vec3 fx    = texture(sTD2DInputs[1], uv).rgb;
    vec3 grain = texture(sTD2DInputs[2], uv).rgb;

    vec3 col;
    if (uActive.x > 0.5 && inQuad(uv)) {
        col = (uGrain.z > 0.5) ? (vec3(1.0) - fx) : fx;   // inverse layer = negative colors
        col = mix(col, col * grain, clamp(uGrain.x, 0.0, 1.0));
        col = mix(col, vec3(luma(col)), clamp(uGrain.y, 0.0, 1.0));
    } else {
        col = raw;
    }

    fragColor = vec4(col, 1.0);
}
