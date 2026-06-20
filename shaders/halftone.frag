// halftone.frag — Ink-colored halftone / stippling over the risograph layers.
// Input 0: risograph color result (from riso.frag).
//
// Offset brick grid (every other row shifted half a cell). Dot radius is driven by
// the darkness of the underlying pixel (darker = bigger dot). A vertical gradient
// makes dots denser/bigger toward the bottom of the frame. Dots are drawn in the
// underlying ink color over a paper-light background (so the palette is preserved,
// never black/white).

uniform vec2 uCellPx;     // x = base halftone cell size in pixels (y unused)
uniform vec2 uDensity;    // x = cell multiplier at top, y = cell multiplier at bottom

out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main() {
    vec2 uv  = vUV.st;
    vec2 res = uTD2DInfos[0].res.zw;       // (width, height)
    vec2 frag = uv * res;                  // pixel coordinates

    // Vertical density gradient. TD UV: y=0 bottom, y=1 top.
    // Smaller cell -> denser/bigger dots. Interpolate bottom->top.
    float densMix = mix(uDensity.y, uDensity.x, uv.y);
    float c = max(2.0, uCellPx.x * densMix);

    // Brick offset: shift alternate rows by half a cell.
    float row  = floor(frag.y / c);
    float xoff = mod(row, 2.0) * 0.5 * c;
    vec2 cellId     = vec2(floor((frag.x - xoff) / c), row);
    vec2 cellCenter = (cellId + 0.5) * c + vec2(xoff, 0.0);

    // Sample the underlying ink color at the cell center.
    vec3 src = texture(sTD2DInputs[0], cellCenter / res).rgb;
    float L  = luma(src);

    // Darker pixel -> larger dot (up to ~half the cell).
    float radius = (1.0 - L) * 0.5 * c;
    float d      = distance(frag, cellCenter);
    float inside = step(d, radius);        // hard-edged dot

    // Paper between dots, ink color inside dots.
    vec3 paper = vec3(0.96, 0.95, 0.91);   // warm off-white print stock
    vec3 col   = mix(paper, src, inside);

    fragColor = vec4(col, 1.0);
}
