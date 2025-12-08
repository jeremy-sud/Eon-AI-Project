/**
 * @file demo.c
 * @brief Proyecto Eón - Demo del Núcleo C
 *
 * Demuestra el Momento Cero y aprendizaje con libAeon.
 */

#include "libAeon.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

/* Generar onda sinusoidal para entrenamiento */
void generate_sine_wave(aeon_state_t *data, int n_samples) {
  for (int i = 0; i < n_samples; i++) {
    float t = (float)i * 0.1f;
    float value = sinf(t);
#if AEON_USE_FIXED_POINT
    data[i] = (aeon_state_t)(value * AEON_SCALE);
#else
    data[i] = value;
#endif
  }
}

void print_header(const char *title) {
  printf("\n");
  printf("╔═══════════════════════════════════════════════════════════════╗\n");
  printf("║  %-60s ║\n", title);
  printf("╚═══════════════════════════════════════════════════════════════╝\n");
}

int main(void) {
  print_header("PROYECTO EÓN - Demo libAeon (C)");

  /* Estructura del núcleo */
  aeon_core_t core;

  /* === MOMENTO CERO === */
  printf("\n[1/5] Momento Cero (Nacimiento)...\n");

  int result = aeon_birth(&core, 0);
  if (result != 0) {
    printf("Error en nacimiento: %d\n", result);
    return 1;
  }

  char hash_str[33];
  aeon_hash_to_string(&core.certificate.birth_hash, hash_str);

  printf("    ✓ Nacimiento: %ld (Unix timestamp)\n",
         (long)core.certificate.birth_time);
  printf("    ✓ Hash: %s\n", hash_str);
  printf("    ✓ Reservoir: %d neuronas\n", core.certificate.reservoir_size);
  printf("    ✓ Conexiones escasas: %d\n", core.sparse_count);
  printf("    ✓ Memoria: %u bytes\n", aeon_memory_usage(&core));

  /* === GENERAR DATOS === */
  printf("\n[2/5] Generando datos de entrenamiento...\n");

  const int N_SAMPLES = 300;
  aeon_state_t inputs[N_SAMPLES];
  aeon_state_t targets[N_SAMPLES];

  generate_sine_wave(inputs, N_SAMPLES);

  /* Target = siguiente valor */
  for (int i = 0; i < N_SAMPLES - 1; i++) {
    targets[i] = inputs[i + 1];
  }
  targets[N_SAMPLES - 1] = inputs[0];

  printf("    ✓ Generadas %d muestras (onda sinusoidal)\n", N_SAMPLES);

  /* === ENTRENAR === */
  printf("\n[3/5] Entrenando...\n");

  float mse = aeon_train(&core, inputs, targets, N_SAMPLES, 50);

  printf("    ✓ MSE: %.6f\n", mse);
  printf("    ✓ Entrenado: %s\n", core.is_trained ? "Sí" : "No");
  printf("    ✓ Sesiones: %u\n", core.learning_sessions);

  /* === PREDECIR === */
  printf("\n[4/5] Prediciendo...\n");

  aeon_reset(&core);

  float total_error = 0.0f;
  int test_samples = 50;

  printf("    Input → Predicción (Real)\n");

  for (int i = 200; i < 200 + test_samples; i++) {
    aeon_update(&core, &inputs[i]);

    aeon_state_t pred;
    aeon_predict(&core, &pred);

#if AEON_USE_FIXED_POINT
    float p = (float)pred / AEON_SCALE;
    float y = (float)targets[i] / AEON_SCALE;
    float x = (float)inputs[i] / AEON_SCALE;
#else
    float p = pred;
    float y = targets[i];
    float x = inputs[i];
#endif

    float err = (p - y) * (p - y);
    total_error += err;

    /* Mostrar algunas predicciones */
    if (i % 10 == 0) {
      printf("    %.3f → %.3f (%.3f)\n", x, p, y);
    }
  }

  printf("\n    ✓ MSE test: %.6f\n", total_error / test_samples);

  /* === GUARDAR === */
  printf("\n[5/5] Guardando estado...\n");

  const char *filename = "aeon_demo.bin";
  result = aeon_save(&core, filename);

  if (result == 0) {
    printf("    ✓ Guardado en: %s\n", filename);
  } else {
    printf("    ✗ Error guardando: %d\n", result);
  }

  /* === PODA === */
  printf("\n[6/6] Poda Estructural (Pruning)...\n");

  float threshold = 0.1f;
  int pruned = aeon_prune(&core, threshold);

  printf("    ✓ Umbral: %.2f\n", threshold);
  printf("    ✓ Conexiones podadas: %d / %d\n", pruned,
         AEON_OUTPUT_SIZE * AEON_RESERVOIR_SIZE);

  /* Verificar impacto en precisión */
  aeon_reset(&core);
  float total_error_pruned = 0.0f;

  for (int i = 200; i < 200 + test_samples; i++) {
    aeon_update(&core, &inputs[i]);
    aeon_state_t pred;
    aeon_predict(&core, &pred);

#if AEON_USE_FIXED_POINT
    float p = (float)pred / AEON_SCALE;
    float y = (float)targets[i] / AEON_SCALE;
#else
    float p = pred;
    float y = targets[i];
#endif
    float err = (p - y) * (p - y);
    total_error_pruned += err;
  }

  printf("    ✓ MSE post-poda: %.6f\n", total_error_pruned / test_samples);

  /* === RESUMEN === */
  print_header("RESUMEN");

  printf("\n");
  printf("  • Tamaño del núcleo: %u bytes (%.2f KB)\n",
         aeon_memory_usage(&core), (float)aeon_memory_usage(&core) / 1024.0f);
  printf("  • Reservoir: %d neuronas\n", AEON_RESERVOIR_SIZE);
  printf("  • Conexiones: %d (escasas)\n", core.sparse_count);
  printf("  • Punto fijo: %s\n",
         AEON_USE_FIXED_POINT ? "Sí (Q8.8)" : "No (float)");
  printf("  • Edad: %u segundos\n", aeon_age_seconds(&core));
  printf("\n");

  print_header("MOMENTO CERO VERIFICADO");
  printf("\n  La inteligencia emerge de ~%u bytes.\n\n",
         aeon_memory_usage(&core));

  return 0;
}
