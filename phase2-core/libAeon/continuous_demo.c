/**
 * @file continuous_demo.c
 * @brief Proyecto Eón - Demo de Alimentación Continua
 *
 * Ejecuta el core en bucle continuo con series de tiempo
 * que incluyen cambios bruscos (picos climáticos), guardando
 * pesos periódicamente para simular "vida" de un sensor.
 *
 * Plan de Alimentación Inmediata - Fase 1
 *
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#include "libAeon.h"
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

/* Control de bucle */
volatile int keep_running = 1;

void signal_handler(int sig) {
  (void)sig;
  keep_running = 0;
  printf("\n[!] Señal recibida, finalizando...\n");
}

/**
 * @brief Genera serie climática con cambios bruscos
 *
 * Simula temperatura con:
 * - Base sinusoidal (día/noche)
 * - Tendencia gradual
 * - Picos aleatorios (tormentas, olas de calor)
 * - Ruido gaussiano
 */
void generate_climate_series(aeon_state_t *data, int n_samples, uint32_t seed) {
  uint32_t rng = seed;

  for (int i = 0; i < n_samples; i++) {
    float t = (float)i * 0.05f;

    /* Base: ciclo día/noche */
    float base = sinf(t) * 0.4f;

    /* Tendencia: calentamiento gradual */
    float trend = (float)i / (float)n_samples * 0.2f;

    /* Picos aleatorios (10% de probabilidad) */
    float spike = 0.0f;
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    if ((rng % 100) < 10) {
      spike = ((rng % 200) - 100) / 100.0f * 0.6f; /* ±0.6 */
    }

    /* Ruido */
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    float noise = ((rng % 100) - 50) / 500.0f; /* ±0.1 */

    float value = base + trend + spike + noise;

    /* Saturar a [-1, 1] */
    if (value > 1.0f)
      value = 1.0f;
    if (value < -1.0f)
      value = -1.0f;

#if AEON_USE_FIXED_POINT
    data[i] = (aeon_state_t)(value * AEON_SCALE);
#else
    data[i] = value;
#endif
  }
}

void print_header(const char *title) {
  printf("\n");
  printf(
      "╔═══════════════════════════════════════════════════════════════╗\n");
  printf("║  %-60s ║\n", title);
  printf(
      "╚═══════════════════════════════════════════════════════════════╝\n");
}

void print_progress_bar(int current, int total, float mse) {
  int bar_width = 40;
  float progress = (float)current / (float)total;
  int filled = (int)(progress * bar_width);

  printf("\r  [");
  for (int i = 0; i < bar_width; i++) {
    if (i < filled)
      printf("█");
    else
      printf("░");
  }
  printf("] %3.0f%% | Epoch %d/%d | MSE: %.6f", progress * 100, current, total,
         mse);
  fflush(stdout);
}

int main(int argc, char *argv[]) {
  /* Configuración */
  int n_epochs = 10;
  int save_interval = 2;
  int samples_per_epoch = 500;

  if (argc > 1)
    n_epochs = atoi(argv[1]);
  if (argc > 2)
    save_interval = atoi(argv[2]);
  if (argc > 3)
    samples_per_epoch = atoi(argv[3]);

  signal(SIGINT, signal_handler);

  print_header("PROYECTO EÓN - Alimentación Continua");

  printf("\n  Configuración:\n");
  printf("    • Epochs: %d\n", n_epochs);
  printf("    • Muestras/epoch: %d\n", samples_per_epoch);
  printf("    • Guardar cada: %d epochs\n", save_interval);
  printf("    • Ctrl+C para detener\n");

  /* Crear núcleo */
  aeon_core_t core;
  uint32_t seed = (uint32_t)time(NULL);

  printf("\n[1] Momento Cero (Nacimiento)...\n");
  int result = aeon_birth(&core, seed);
  if (result != 0) {
    printf("Error en nacimiento: %d\n", result);
    return 1;
  }

  char hash_str[33];
  aeon_hash_to_string(&core.certificate.birth_hash, hash_str);
  printf("    ✓ Seed: %u\n", seed);
  printf("    ✓ Hash: %.16s...\n", hash_str);
  printf("    ✓ Memoria: %u bytes\n", aeon_memory_usage(&core));

  /* Buffers */
  aeon_state_t *inputs = malloc(samples_per_epoch * sizeof(aeon_state_t));
  aeon_state_t *targets = malloc(samples_per_epoch * sizeof(aeon_state_t));

  if (!inputs || !targets) {
    printf("Error: sin memoria\n");
    return 1;
  }

  /* === BUCLE DE APRENDIZAJE CONTINUO === */
  print_header("APRENDIZAJE CONTINUO (Serie Climática)");

  float best_mse = 999.0f;
  float total_mse = 0.0f;

  for (int epoch = 1; epoch <= n_epochs && keep_running; epoch++) {
    /* Generar nueva serie con seed diferente cada epoch */
    uint32_t epoch_seed = seed + epoch * 12345;
    generate_climate_series(inputs, samples_per_epoch, epoch_seed);

    /* Target = siguiente valor */
    for (int i = 0; i < samples_per_epoch - 1; i++) {
      targets[i] = inputs[i + 1];
    }
    targets[samples_per_epoch - 1] = inputs[0];

    /* Entrenar */
    float mse = aeon_train(&core, inputs, targets, samples_per_epoch, 50);
    total_mse += mse;

    if (mse < best_mse) {
      best_mse = mse;
    }

    print_progress_bar(epoch, n_epochs, mse);

    /* Guardar periódicamente */
    if (epoch % save_interval == 0) {
      char filename[64];
      snprintf(filename, sizeof(filename), "aeon_epoch_%03d.bin", epoch);
      aeon_save(&core, filename);
      printf(" → Guardado: %s", filename);
    }

    printf("\n");

    /* Pequeña pausa para simular tiempo real */
    usleep(100000); /* 100ms */
  }

  /* === RESUMEN === */
  print_header("RESUMEN DE ALIMENTACIÓN");

  float avg_mse = total_mse / n_epochs;

  printf("\n");
  printf("  • Epochs completados: %d\n",
         keep_running ? n_epochs : (int)(n_epochs * (total_mse / avg_mse)));
  printf("  • Muestras totales: %d\n",
         core.samples_processed ? (int)core.samples_processed
                                : n_epochs * samples_per_epoch);
  printf("  • Sesiones de aprendizaje: %u\n", core.learning_sessions);
  printf("  • MSE promedio: %.6f\n", avg_mse);
  printf("  • Mejor MSE: %.6f\n", best_mse);
  printf("  • Edad: %u segundos\n", aeon_age_seconds(&core));
  printf("\n");

  /* Guardar estado final */
  const char *final_file = "aeon_final.bin";
  if (aeon_save(&core, final_file) == 0) {
    printf("  ✓ Estado final guardado: %s\n", final_file);
  }

  /* Limpiar */
  free(inputs);
  free(targets);

  print_header("ALIMENTACIÓN COMPLETADA");
  printf("\n  El conocimiento ha crecido.\n\n");

  return 0;
}
