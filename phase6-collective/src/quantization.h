#ifndef QUANTIZATION_H
#define QUANTIZATION_H

#include <stddef.h>
#include <stdint.h>

/**
 * @brief Compress float array to 1-bit per element (packed).
 *
 * @param weights Input array of floats.
 * @param count Number of weights.
 * @param output Output buffer (must be at least ceil(count/8) bytes).
 * @return Number of bytes written.
 */
int quantize_1bit(const float *weights, int count, uint8_t *output);

/**
 * @brief Decompress 1-bit packed array to floats.
 *
 * @param input Input buffer (1-bit packed).
 * @param count Number of weights to unpack.
 * @param weights Output array of floats.
 * @param scale Magnitude to assign (e.g., 0.1 -> +0.1 / -0.1).
 */
void dequantize_1bit(const uint8_t *input, int count, float *weights,
                     float scale);

#endif
