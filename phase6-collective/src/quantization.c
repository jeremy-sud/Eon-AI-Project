#include "quantization.h"
#include <string.h>

int quantize_1bit(const float *weights, int count, uint8_t *output) {
  if (!weights || !output || count <= 0)
    return 0;

  int bytes = (count + 7) / 8;
  memset(output, 0, bytes);

  for (int i = 0; i < count; i++) {
    if (weights[i] >= 0) {
      // Set the bit corresponding to index i
      // Byte index: i / 8
      // Bit index: i % 8
      output[i / 8] |= (1 << (i % 8));
    }
    // Else leave as 0 (representing negative)
  }
  return bytes;
}

void dequantize_1bit(const uint8_t *input, int count, float *weights,
                     float scale) {
  if (!input || !weights || count <= 0)
    return;

  for (int i = 0; i < count; i++) {
    int byte_idx = i / 8;
    int bit_idx = i % 8;

    if (input[byte_idx] & (1 << bit_idx)) {
      weights[i] = scale;
    } else {
      weights[i] = -scale;
    }
  }
}
