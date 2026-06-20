// glitch.frag — Heavy glitch stage applied to the risograph/halftone content.
// Input 0: halftone/riso result (the stylized image to glitch)
// Input 1: feedback (this TOP's previous frame, via a Feedback TOP) for trails
//
// RGB channel shift (chromatic split), per-scanline horizontal jitter, occasional
// block displacement, scanlines, and decaying feedback trails. Intensity rises
// with hand motion (uMotion) and animates over time (uTime).

uniform vec2 uShiftPx;    // x = base RGB shift in pixels
uniform vec2 uScan;       // x = scanline frequency, y = scanline amount
uniform vec2 uFeedback;   // x = feedback/trail amount (0..~0.97)
uniform vec2 uMotion;     // x = motion 0..1 (from hand speed)
uniform vec2 uTime;       // x = seconds

out vec4 fragColor;

float hash(float n) { return fract(sin(n) * 43758.5453); }

void main() {
    vec2 uv    = vUV.st;
    vec2 res   = uTD2DInfos[0].res.zw;
    vec2 texel = uTD2DInfos[0].res.xy;
    float motion = clamp(uMotion.x, 0.0, 1.0);
    float t = uTime.x;

    // Per-scanline horizontal jitter, stronger with motion.
    float band = floor(uv.y * res.y / 6.0);
    float j    = hash(band + floor(t * 20.0)) - 0.5;
    float amt  = uShiftPx.x * (0.6 + motion * 2.0);
    float dx   = (amt + j * amt * 3.0) * texel.x;

    // Occasional block displacement on a few scanlines.
    float blk  = step(0.985, hash(band * 1.7 + floor(t * 12.0))) * (0.02 + 0.06 * motion);
    vec2 disp  = vec2(blk * sign(j), 0.0);

    // Chromatic split.
    float r = texture(sTD2DInputs[0], uv + vec2(dx, 0.0) + disp).r;
    float g = texture(sTD2DInputs[0], uv + disp).g;
    float b = texture(sTD2DInputs[0], uv - vec2(dx, 0.0) + disp).b;
    vec3 col = vec3(r, g, b);

    // Scanlines.
    col *= 1.0 - uScan.y * 0.5 * (0.5 + 0.5 * sin(uv.y * uScan.x));

    // Feedback trails: sample previous frame drifting slightly upward, decayed.
    vec3 fb = texture(sTD2DInputs[1], uv + vec2(0.0, 1.5) * texel).rgb;
    col = max(col, fb * clamp(uFeedback.x, 0.0, 0.97));

    fragColor = vec4(col, 1.0);
}
