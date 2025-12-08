/**
 * Eón Bio Monitor
 * Detects Arrhythmias on Ultra-Low Power Devices (<2KB RAM)
 *
 * Logic:
 * 1. Learns user's baseline HRV (Heart Rate Variability) in first N beats.
 * 2. Predicts next RR interval.
 * 3. Flags deviations as Anomalies.
 */

#include "../../phase2-core/libAeon/libAeon.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define CALIBRATION_BEATS 50
// Anomaly threshold: 20% deviation from prediction
// (Standard medical bounds for Ectopic beats are roughly >20% pre-maturity)
#define ANOMALY_THRESHOLD_PCT 0.20f

// Helper functions (Basic fixed point conversion)
// Redefining scale just in case, but using ifndef
#ifndef AEON_SCALE
#define AEON_SCALE 256.0f
#endif

int16_t aeon_float_to_fixed(float f) { return (int16_t)(f * AEON_SCALE); }
float aeon_fixed_to_float(int16_t i) { return (float)i / AEON_SCALE; }

// Global/Static vars for loop continuity
static aeon_state_t last_input;
static aeon_state_t last_prediction;

int main() {
  aeon_core_t core;
  // Birth with specific seed for reproducibility on device
  aeon_birth(&core, 777);

  float rr_in;
  int beat_count = 0;

  // Buffers for training (small window)
  aeon_state_t inputs[CALIBRATION_BEATS];
  aeon_state_t targets[CALIBRATION_BEATS];

  printf("EON BIO MONITOR STARTED\n");
  printf("Status: CALIBRATING...\n");

  while (scanf("%f", &rr_in) == 1) {

    // Normalize input (roughly to range [-1, 1] relative to 1000ms usually)
    float norm_in = (rr_in - 1000.0f) / 500.0f;
    aeon_state_t input_fixed = aeon_float_to_fixed(norm_in);

    // Calibration Phase
    if (beat_count < CALIBRATION_BEATS) {
      if (beat_count > 0) {
        inputs[beat_count - 1] =
            last_input; // Train to predict CURRENT (input_fixed) from PREV
                        // (last_input)?
        // Standard ESN training: Input(t) -> Target(t+1)
        // Here inputs array is 'state input', targets is 'desired output'
        // We want W_out * state(t) = target(t+1)
        // So inputs[] should be... wait. aeon_train takes inputs/targets.
        // It runs state update on inputs[t]. So state(t) is from inputs[t].
        // Then it trains W_out * state(t) to match targets[t].
        // So if we want to predict FUTURE, we want inputs[t] = RR_t, targets[t]
        // = RR_t+1.

        inputs[beat_count - 1] = last_input;
        targets[beat_count - 1] = input_fixed;
      }
      last_input = input_fixed;

      if (beat_count == CALIBRATION_BEATS - 1) {
        // Train W_out
        // We have inputs[0..48] and targets[0..48] (49 samples)
        aeon_train(&core, inputs, targets, CALIBRATION_BEATS - 1, 5);
        printf("Status: MONITORING ACTIVE\n");

        // Initialize prediction for the very next step
        // Update state with current input (which is the last one seen)
        aeon_update(&core, &input_fixed);
        aeon_state_t pred_out[1];
        aeon_predict(&core, pred_out);
        last_prediction = pred_out[0];
      }
    }
    // Monitor Phase
    else {
      // 1. Compare prediction made at (t-1) with actual (t) [Current rr_in]
      float predicted_rr_norm = aeon_fixed_to_float(last_prediction);
      float predicted_rr = (predicted_rr_norm * 500.0f) + 1000.0f;

      float deviation = fabs(predicted_rr - rr_in) / predicted_rr;

      if (deviation > ANOMALY_THRESHOLD_PCT) {
        printf("ALERT: Arrhythmia Detected! Beat %d | RR: %.0fms | Pred: "
               "%.0fms | Dev: %.1f%%\n",
               beat_count, rr_in, predicted_rr, deviation * 100);
      }

      // 2. Update state with current
      aeon_update(&core, &input_fixed);

      // 3. Predict next
      aeon_state_t pred_out[1];
      aeon_predict(&core, pred_out);
      last_prediction = pred_out[0];
    }

    beat_count++;
  }

  return 0;
}
