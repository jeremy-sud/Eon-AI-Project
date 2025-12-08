/**
 * @file test_aeon.c
 * @brief Test de Regresión para libAeon
 *
 * Verifica estabilidad numérica y consumo de recursos.
 */

#include "libAeon.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define ANSI_COLOR_RED "\x1b[31m"
#define ANSI_COLOR_GREEN "\x1b[32m"
#define ANSI_COLOR_RESET "\x1b[0m"

void test_passed(const char *test_name) {
  printf(ANSI_COLOR_GREEN "✓ PASS: %s" ANSI_COLOR_RESET "\n", test_name);
}

void test_failed(const char *test_name, const char *reason) {
  printf(ANSI_COLOR_RED "✗ FAIL: %s - %s" ANSI_COLOR_RESET "\n", test_name,
         reason);
  exit(1);
}

void generate_data(aeon_state_t *data, int n_samples) {
  for (int i = 0; i < n_samples; i++) {
    float val = sinf((float)i * 0.1f);
#if AEON_USE_FIXED_POINT
    data[i] = (aeon_state_t)(val * AEON_SCALE);
#else
    data[i] = val;
#endif
  }
}

int main(void) {
  printf("=== Aeon Core Regression Tests ===\n");
  printf("Config: Size=%d, Sparsity=%d, FixedPoint=%d\n", AEON_RESERVOIR_SIZE,
         AEON_SPARSITY_FACTOR, AEON_USE_FIXED_POINT);

  aeon_core_t core;

  // TEST 1: Initialization
  if (aeon_birth(&core, 3) != 0) { // Fixed seed 3
    test_failed("Initialization", "aeon_birth failed");
  }
  if (core.certificate.reservoir_seed != 3) {
    test_failed("Initialization", "Seed mismatch");
  }
  test_passed("Initialization");

  // TEST 2: Memory Usage
  uint32_t size = aeon_memory_usage(&core);
  if (size == 0 ||
      size > 5000) { // Expecting < 2KB usually, but <5KB safe margin
    char msg[64];
    sprintf(msg, "Memory usage suspicious: %u bytes", size);
    test_failed("Memory Usage", msg);
  }
  test_passed("Memory Check");

  // TEST 3: Training Stability (MSE)
  const int N_SAMPLES = 300;
  aeon_state_t inputs[N_SAMPLES];
  aeon_state_t targets[N_SAMPLES];
  generate_data(inputs, N_SAMPLES);

  // Target = Next step
  for (int i = 0; i < N_SAMPLES - 1; i++)
    targets[i] = inputs[i + 1];
  targets[N_SAMPLES - 1] = inputs[0];

  float mse = aeon_train(&core, inputs, targets, N_SAMPLES, 50);

  printf("Training MSE: %f\n", mse);

  // Baseline observed: 0.009 (Fixed Point) - 0.0004 (Float)
  // Threshold set to 0.02 to catch significant regressions
  if (mse > 0.02f) {
    char msg[64];
    sprintf(msg, "MSE > 0.02 (Got %f)", mse);
    test_failed("Training Stability", msg);
  }
  test_passed("Training Stability");

  printf("\nAll tests passed successfully.\n");
  return 0;
}
