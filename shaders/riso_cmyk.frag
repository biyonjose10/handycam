// riso_cmyk.frag — Risograph look: 3 vibrant ink passes (green / yellow / cyan-blue),
// each sampled at a slightly different offset (misregistration), composited
// subtractively on white paper. Input 0: webcam.
//
// Highlights burn out to white (low ink coverage); mids/shadows pick up saturated,
// slightly-misaligned ink — the signature offset-print look.

uniform vec2 uOffsetPx;   // x = misregistration offset in pixels

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main() {
    vec2 uv    = vUV.st;
    vec2 texel = uTD2DInfos[0].res.xy;
    float o = uOffsetPx.x;

    // Three vibrant inks.
    const vec3 INK_CYAN  = vec3(0.16, 0.74, 0.86);  // icy cyan-blue
    const vec3 INK_GREEN = vec3(0.18, 0.80, 0.28);  // electric green
    const vec3 INK_YELL  = vec3(1.00, 0.82, 0.05);  // warm yellow

    // Each pass reads luminance at its own diagonal offset -> misregistration.
    float Lc = luma(texture(sTD2DInputs[0], uv + vec2(-o, -o) * texel).rgb);
    float Lg = luma(texture(sTD2DInputs[0], uv + vec2( o, -o) * texel).rgb);
    float Ly = luma(texture(sTD2DInputs[0], uv + vec2( 0.0, o) * texel).rgb);

    // Ink coverage: darker -> more ink. Different ranges per ink for color variety.
    float cc = smoothstep(0.75, 0.05, Lc);          // cyan strong in shadows
    float cg = smoothstep(0.85, 0.20, Lg) * 0.85;   // green through the mids
    float cy = smoothstep(0.95, 0.35, Ly) * 0.80;   // yellow broad / warm areas

    // Subtractive print: start white, multiply each ink pass.
    vec3 col = vec3(1.0);
    col *= mix(vec3(1.0), INK_CYAN,  cc);
    col *= mix(vec3(1.0), INK_GREEN, cg);
    col *= mix(vec3(1.0), INK_YELL,  cy);

    fragColor = vec4(col, 1.0);
}
