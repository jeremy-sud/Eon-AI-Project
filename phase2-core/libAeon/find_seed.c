#include "libAeon.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

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
  const int N_SAMPLES = 300;
  aeon_state_t inputs[N_SAMPLES];
  aeon_state_t targets[N_SAMPLES];
  generate_data(inputs, N_SAMPLES);

  for (int i = 0; i < N_SAMPLES - 1; i++)
    targets[i] = inputs[i + 1];
  targets[N_SAMPLES - 1] = inputs[0];

  aeon_core_t core;

  printf("Searching for seed with MSE < 0.02...\n");

  for (int seed = 1; seed < 1000; seed++) {
    aeon_birth(&core, seed);
    float mse = aeon_train(&core, inputs, targets, N_SAMPLES, 50);

    if (mse < 0.02f) {
      printf("\nFOUND! Seed: %d, MSE: %f\n", seed, mse);
      return 0;
    }
    if (seed % 100 == 0)
      printf(".");
  }

  printf("\nCould not find seed in first 1000.\n");
  return 1;
}
