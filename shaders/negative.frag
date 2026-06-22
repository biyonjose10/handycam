// negative.frag — Photographic negative: invert the webcam's colors (1 - rgb).
// Input 0: webcam. uAmount.x mixes between the original (0) and full negative (1).

uniform vec2 uAmount;   // x = negative amount (0 = off, 1 = full invert)

out vec4 fragColor;

void main() {
    vec3 src = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 inv = vec3(1.0) - src;
    vec3 col = mix(src, inv, clamp(uAmount.x, 0.0, 1.0));
    fragColor = vec4(col, 1.0);
}
