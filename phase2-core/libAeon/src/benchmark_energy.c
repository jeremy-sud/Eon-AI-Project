/**
 * @file benchmark_energy.c
 * @brief Benchmark energy consumption (via execution time) for Eon Motor.
 */

#include "../libAeon.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N_CYCLES 100000

int main() {
    aeon_core_t core;
    if (aeon_birth(&core, 42) != 0) {
        fprintf(stderr, "Failed to initialize Eon core.\n");
        return 1;
    }

    // Dummy training to ensure connections are active (though random weights exist at birth)
    // Actually, untrained reservoir works fine for benchmarking inference cost.

    aeon_state_t input = 100; // 1.0 in fixed point (if scale is 100? No, scale is 256 or 1)
    // Check scale in libAeon.h, usually 256 for fixed point.
    // We just pass a value.
    aeon_state_t output;

    printf("Benchmarking Eon Motor (%d cycles)...\n", N_CYCLES);

    clock_t start = clock();

    for (int i = 0; i < N_CYCLES; i++) {
        // Typical cycle: Update with input -> Predict next
        aeon_update(&core, &input);
        aeon_predict(&core, &output);
        
        // Feedback loop for realism (output becomes next input)
        input = output;
    }

    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Eon Total Time: %.6f s\n", time_spent);
    printf("Time per cycle: %.6f us\n", (time_spent * 1000000.0) / N_CYCLES);
    
    // Calculate simulated energy for Cortex-M4 @ 64MHz
    // Assumption: 64 MHz clock.
    // Cycles = Time * 64,000,000
    // Power ~ 10-20 mW active (depends on board). Let's use 15 mW.
    // Energy (J) = Power (W) * Time (s)
    
    double power_w = 0.015; // 15 mW
    double energy_j = power_w * time_spent / N_CYCLES;
    
    printf("Est. Energy per cycle (Cortex-M4 @ 15mW): %.6f uJ\n", energy_j * 1000000.0);

    return 0;
}
