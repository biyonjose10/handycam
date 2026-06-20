// stipple_red.frag — Stippling / halftone: bold red dots on white. Dot radius is
// driven by the darkness of the underlying pixel (darker = bigger, denser dots).
// Coarse grid so individual dots stay legible. Input 0: webcam.

uniform vec2 uCell;   // x = halftone cell size in pixels

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main() {
    vec2 uv   = vUV.st;
    vec2 res  = uTD2DInfos[0].res.zw;
    vec2 frag = uv * res;
    float c   = max(3.0, uCell.x);

    // Brick-offset grid: shift alternate rows by half a cell.
    float row  = floor(frag.y / c);
    float xoff = mod(row, 2.0) * 0.5 * c;
    vec2 cellId     = vec2(floor((frag.x - xoff) / c), row);
    vec2 cellCenter = (cellId + 0.5) * c + vec2(xoff, 0.0);

    // Sample tone at the cell center; darker -> bigger dot.
    float L = luma(texture(sTD2DInputs[0], cellCenter / res).rgb);
    float radius = (1.0 - L) * 0.62 * c;
    float d = distance(frag, cellCenter);
    float inside = step(d, radius);

    const vec3 RED   = vec3(0.85, 0.10, 0.12);
    const vec3 PAPER = vec3(0.98, 0.97, 0.95);
    vec3 col = mix(PAPER, RED, inside);

    fragColor = vec4(col, 1.0);
}
