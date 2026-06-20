// cyanotype.frag — Cyanotype look: monochrome Prussian-blue, white highlights,
// indigo shadows, high contrast, soft photochemical bleed. Input 0: webcam.

uniform vec2 uParams;   // x = contrast, y = bleed radius in pixels

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main() {
    vec2 uv    = vUV.st;
    vec2 texel = uTD2DInfos[0].res.xy;
    float contrast = uParams.x;
    float b = uParams.y;

    // Soft bleed: 5-tap average of luminance for a hazy, wet-print quality.
    float L = luma(texture(sTD2DInputs[0], uv).rgb) * 2.0;
    L += luma(texture(sTD2DInputs[0], uv + vec2( b, 0.0) * texel).rgb);
    L += luma(texture(sTD2DInputs[0], uv + vec2(-b, 0.0) * texel).rgb);
    L += luma(texture(sTD2DInputs[0], uv + vec2(0.0,  b) * texel).rgb);
    L += luma(texture(sTD2DInputs[0], uv + vec2(0.0, -b) * texel).rgb);
    L /= 6.0;

    // High contrast tonal curve.
    L = clamp((L - 0.5) * contrast + 0.5, 0.0, 1.0);

    // Cyanotype ramp: deep indigo -> Prussian blue -> white.
    const vec3 DEEP  = vec3(0.02, 0.05, 0.20);
    const vec3 MID   = vec3(0.06, 0.26, 0.56);
    const vec3 WHITE = vec3(1.0);
    vec3 col = (L < 0.5) ? mix(DEEP, MID, L * 2.0)
                         : mix(MID, WHITE, (L - 0.5) * 2.0);

    fragColor = vec4(col, 1.0);
}
