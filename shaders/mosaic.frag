// mosaic.frag — Pixel mosaic: quantize the webcam into NxN blocks, each block
// painted with the single color sampled at its center. Input 0: webcam.

uniform vec2 uBlock;   // x = block size in pixels (bigger = chunkier)

out vec4 fragColor;

void main() {
    vec2 res  = uTD2DInfos[0].res.zw;   // .zw = width,height in pixels
    vec2 frag = vUV.st * res;
    float b   = max(1.0, uBlock.x);

    // Snap to the center of the block this fragment falls in.
    vec2 cellCenter = (floor(frag / b) + 0.5) * b;
    vec3 col = texture(sTD2DInputs[0], cellCenter / res).rgb;

    fragColor = vec4(col, 1.0);
}
