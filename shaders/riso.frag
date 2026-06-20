// riso.frag — Risograph 4-ink posterize with per-layer misregistration.
// Input 0: source webcam (RGBA).
// TouchDesigner GLSL TOP convention: out vec4 fragColor; sTD2DInputs[]; vUV.st; uTD2DInfos[].
//
// The source luminance is posterized into 4 bands; each band is assigned one ink
// from a fixed risograph palette. Each ink layer is sampled with a small diagonal
// pixel offset to fake the imperfect physical registration of a real Riso print.

uniform vec2 uOffsetPx;   // x = misregistration offset in pixels (y unused)

out vec4 fragColor;

// Palette (linear-ish sRGB values of the requested hex codes)
const vec3 INK0 = vec3(0.102, 0.227, 0.431); // #1a3a6e prussian blue   -> shadows
const vec3 INK1 = vec3(0.176, 0.353, 0.153); // #2d5a27 forest green    -> mid-low
const vec3 INK2 = vec3(0.831, 0.627, 0.090); // #d4a017 golden yellow   -> mid-high
const vec3 INK3 = vec3(1.000, 1.000, 1.000); // white                   -> highlights

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

// 1.0 if the luminance sampled at (uv + offset px) lands in band b (0..3), else 0.0
float bandMask(vec2 uv, vec2 offPx, int b) {
    vec2 texel = uTD2DInfos[0].res.xy;          // (1/w, 1/h)
    float L = luma(texture(sTD2DInputs[0], uv + offPx * texel).rgb);
    int band = int(clamp(floor(L * 4.0), 0.0, 3.0));
    return band == b ? 1.0 : 0.0;
}

void main() {
    vec2 uv = vUV.st;
    float o = uOffsetPx.x;

    // Per-ink diagonal offsets — overlap at edges produces the misregistration fringe.
    vec2 off0 = vec2(-o, -o);
    vec2 off1 = vec2( o, -o);
    vec2 off2 = vec2(-o,  o);
    vec2 off3 = vec2( 0.0, 0.0);

    // Over-composite in band order (shadows -> highlights). Base is the shadow ink.
    vec3 col = INK0;
    col = mix(col, INK1, bandMask(uv, off1, 1));
    col = mix(col, INK2, bandMask(uv, off2, 2));
    col = mix(col, INK3, bandMask(uv, off3, 3));
    // band0 reinforced last so true-shadow pixels stay prussian even after offset bleed
    col = mix(col, INK0, bandMask(uv, off0, 0));

    fragColor = vec4(col, 1.0);
}
