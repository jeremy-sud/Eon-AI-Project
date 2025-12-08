/**
 * Eón Voice - Keyword Spotting
 * Target: Cortex-M4 (e.g., STM32F4, nRF52)
 * Memory: < 4KB
 *
 * Logic available:
 * 1. Read 4 floats (Spectral Bands).
 * 2. Update Reservoir.
 * 3. Train on first N samples (Supervised Learning Simulation).
 * 4. Predict probability of Keyword.
 */

#include "../../phase2-core/libAeon/libAeon.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Adjust Core for Multi-Input
// Note: libAeon default typically single input. We need config.
// But libAeon.h defines macros via AEON_INPUT_SIZE
// We must redefine AEON_INPUT_SIZE BEFORE including libAeon...
// BUT libAeon.c is compiled separately or linked.
// Ideally we recompile libAeon with -DAEON_INPUT_SIZE=4.
// For this prototype, we'll manually handle the input array size
// or assume we rebuild for this app. We'll use a local include hack if needed
// or just modify the make command to define it.

// Let's assume we compile with -DAEON_INPUT_SIZE=4

#define TRAIN_SAMPLES 1000
#define THRESHOLD 0.7f

// Helper for Q8.8 fixed point
#ifndef AEON_SCALE
#define AEON_SCALE 256.0f
#endif
int16_t aeon_float_to_fixed(float f) { return (int16_t)(f * AEON_SCALE); }
float aeon_fixed_to_float(int16_t i) { return (float)i / AEON_SCALE; }

int main() {
  aeon_core_t core;
  aeon_birth(&core, 123); // Seed

  // Arrays for training
  // We need heap for this amount of training data maybe?
  // 1000 samples * 4 inputs * 2 bytes = 8KB. Might blow stack on small device.
  // For PC sim, malloc is fine.
  aeon_state_t *inputs = malloc(TRAIN_SAMPLES * 4 * sizeof(aeon_state_t));
  aeon_state_t *targets = malloc(TRAIN_SAMPLES * 1 * sizeof(aeon_state_t));

  float b1, b2, b3, b4;
  int target_in;
  char line[256];

  int sample_idx = 0;
  int test_mode = 0;

  // Skip header
  fgets(line, sizeof(line), stdin);

  printf("EON VOICE KWS STARTED\n");
  printf("Status: RECORDING/TRAINING (%d samples)...\n", TRAIN_SAMPLES);

  while (fgets(line, sizeof(line), stdin)) {
    if (sscanf(line, "%f,%f,%f,%f,%d", &b1, &b2, &b3, &b4, &target_in) != 5)
      continue;

    aeon_state_t in_vec[4];
    in_vec[0] = aeon_float_to_fixed(b1);
    in_vec[1] = aeon_float_to_fixed(b2);
    in_vec[2] = aeon_float_to_fixed(b3);
    in_vec[3] = aeon_float_to_fixed(b4);

    aeon_state_t tgt_val = aeon_float_to_fixed((float)target_in);

    if (!test_mode) {
      // Collecting Training Data
      memcpy(&inputs[sample_idx * 4], in_vec, 4 * sizeof(aeon_state_t));
      targets[sample_idx] = tgt_val;
      sample_idx++;

      if (sample_idx >= TRAIN_SAMPLES) {
        // Train
        printf("Status: TRAINING... ");

        // Note: aeon_train expects contiguous arrays.
        // Our inputs are flat (N * 4).

        aeon_train(&core, inputs, targets, TRAIN_SAMPLES, 50);
        printf("DONE.\nStatus: LISTENING...\n");
        test_mode = 1;

        // Cleanup
        free(inputs);
        free(targets);
      }
    } else {
      // Inference
      aeon_update(&core, in_vec);

      aeon_state_t out[1];
      aeon_predict(&core, out);

      float prob = aeon_fixed_to_float(out[0]);

      if (prob > THRESHOLD) {
        printf("DETECTED: EON (Conf: %.2f) at sample %d\n", prob, sample_idx);
      }
      sample_idx++;
    }
  }

  return 0;
}
