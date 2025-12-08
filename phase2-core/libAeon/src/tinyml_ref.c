/**
 * @file tinyml_ref.c
 * @brief Reference TinyML MLP implementation for comparison.
 * Architecture: 1 -> 16 (ReLU) -> 16 (ReLU) -> 1 (Linear)
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N_CYCLES 100000
#define USE_FIXED_POINT 1
// Matching likely Eon config (libAeon.h usually defaults to fixed point)

#if USE_FIXED_POINT
typedef int32_t model_float_t;
#define SCALE 256
#define TO_FIXED(x) ((int32_t)((x) * SCALE))
#define TO_FLOAT(x) ((float)(x) / SCALE)
// Interaction: (Q8.8 * Q8.8) >> 8 = Q8.8 results?
// Simple fixed point math for benchmark:
// We'll simulate standard quantized inference flow.
#else
typedef float model_float_t;
#define SCALE 1.0f
#define TO_FIXED(x) (x)
#define TO_FLOAT(x) (x)
#endif

// Weights (Randomized for benchmark, values don't matter for performance)
model_float_t w1[16][1]; // 1 -> 16
model_float_t b1[16];
model_float_t w2[16][16]; // 16 -> 16
model_float_t b2[16];
model_float_t w3[1][16]; // 16 -> 1
model_float_t b3[1];

model_float_t relu(model_float_t x) { return (x > 0) ? x : 0; }

void init_weights() {
  // Fill with dummy data
  for (int i = 0; i < 16; i++) {
    w1[i][0] = TO_FIXED(0.1f);
    b1[i] = TO_FIXED(0.01f);
    b2[i] = TO_FIXED(0.01f);
    for (int j = 0; j < 16; j++)
      w2[i][j] = TO_FIXED(0.1f);
    w3[0][i] = TO_FIXED(0.1f);
  }
  b3[0] = TO_FIXED(0.0f);
}

void predict(model_float_t input, model_float_t *output) {
  model_float_t h1[16];
  model_float_t h2[16];

  // Layer 1
  for (int i = 0; i < 16; i++) {
    model_float_t sum = 0;
    sum += input * w1[i][0]; // 1 input
#if USE_FIXED_POINT
    sum /= SCALE;
#endif
    sum += b1[i];
    h1[i] = relu(sum);
  }

  // Layer 2
  for (int i = 0; i < 16; i++) {
    model_float_t sum = 0;
    for (int j = 0; j < 16; j++) {
      sum += h1[j] * w2[i][j];
#if USE_FIXED_POINT
      // Accumulation optimization? usually shift at end of dot product.
      // Minimizing adds/shifts for fair comparison with Eon.
      // But let's keep it simple: multiply then shift.
      // Wait, this accumulates sum. If sum is int32, could overflow if not
      // careful. Standard CMSIS-NN does q15 * q15 -> q31. Here we do simple
      // simulation.
#endif
    }
#if USE_FIXED_POINT
    sum /= SCALE;
#endif
    sum += b2[i];
    h2[i] = relu(sum);
  }

  // Layer 3 (Output)
  model_float_t sum_out = 0;
  for (int i = 0; i < 16; i++) {
    sum_out += h2[i] * w3[0][i];
  }
#if USE_FIXED_POINT
  sum_out /= SCALE;
#endif
  sum_out += b3[0];

  *output = sum_out;
}

int main() {
  init_weights();

  model_float_t input = TO_FIXED(0.5f);
  model_float_t output;

  printf("Benchmarking TinyML MLP Reference (1x16x16x1) (%d cycles)...\n",
         N_CYCLES);

  clock_t start = clock();

  for (int i = 0; i < N_CYCLES; i++) {
    predict(input, &output);
    input = output; // Feedback
  }

  clock_t end = clock();
  double time_spent = (double)(end - start) / CLOCKS_PER_SEC;

  printf("TinyML Ref Total Time: %.6f s\n", time_spent);
  printf("Time per cycle: %.6f us\n", (time_spent * 1000000.0) / N_CYCLES);

  double power_w = 0.015; // 15 mW
  double energy_j = power_w * time_spent / N_CYCLES;

  printf("Est. Energy per cycle (Cortex-M4 @ 15mW): %.6f uJ\n",
         energy_j * 1000000.0);

  return 0;
}
