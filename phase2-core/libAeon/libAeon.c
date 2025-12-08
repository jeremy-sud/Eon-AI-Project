/**
 * @file libAeon.c
 * @brief Proyecto Eón - Implementación del Núcleo ESN Ultraligero
 *
 * "La inteligencia no se crea, se descubre."
 */

#include "libAeon.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================
 * FUNCIONES INTERNAS
 * ============================================================ */

/**
 * @brief Generador LCG (Linear Congruential Generator)
 */
uint32_t aeon_random(uint32_t *state) {
  *state = (*state * 1103515245 + 12345) & 0x7fffffff;
  return *state;
}

/**
 * @brief Aproximación rápida de tanh usando polinomio
 *
 * Para punto fijo: tanh(x) ≈ x para |x| < 1, ±1 para |x| > 1
 */
aeon_state_t aeon_tanh_approx(aeon_state_t x) {
#if AEON_USE_FIXED_POINT
  /* Saturación simple para punto fijo */
  if (x > AEON_SCALE)
    return AEON_SCALE;
  if (x < -AEON_SCALE)
    return -AEON_SCALE;
  /* Aproximación: tanh(x) ≈ x - x^3/3 para |x| < 1 */
  aeon_state_t x2 = (x * x) >> AEON_SCALE_BITS;
  aeon_state_t x3 = (x2 * x) >> AEON_SCALE_BITS;
  return x - (x3 / 3);
#else
  /* Aproximación polinomial de tanh */
  if (x > 2.0f)
    return 1.0f;
  if (x < -2.0f)
    return -1.0f;
  float x2 = x * x;
  return x * (1.0f - x2 / 3.0f + x2 * x2 / 15.0f);
#endif
}

/**
 * @brief Genera hash simple basado en datos
 */
static void generate_hash(aeon_hash_t *hash, uint32_t seed, time_t timestamp) {
  uint32_t state = seed ^ (uint32_t)timestamp;

  for (int i = 0; i < 16; i++) {
    state = aeon_random(&state);
    hash->bytes[i] = (uint8_t)(state & 0xFF);
  }
}

/* ============================================================
 * MOMENTO CERO - NACIMIENTO
 * ============================================================ */

int aeon_birth(aeon_core_t *core, uint32_t seed) {
  if (core == NULL)
    return -1;

  /* Limpiar toda la estructura */
  memset(core, 0, sizeof(aeon_core_t));

  /* === MOMENTO CERO === */
  core->certificate.birth_time = time(NULL);

  /* Generar semilla si no se proporcionó */
  if (seed == 0) {
    seed = (uint32_t)core->certificate.birth_time;
  }
  core->certificate.reservoir_seed = seed;

  /* Generar hash de nacimiento */
  generate_hash(&core->certificate.birth_hash, seed,
                core->certificate.birth_time);

  /* Metadatos */
  core->certificate.reservoir_size = AEON_RESERVOIR_SIZE;
  core->certificate.version = AEON_VERSION;

  /* === INICIALIZAR RESERVOIR ("LA NADA") === */
  uint32_t rng_state = seed;

  /* W_in: Pesos de entrada aleatorios */
  for (int i = 0; i < AEON_RESERVOIR_SIZE * AEON_INPUT_SIZE; i++) {
    uint32_t r = aeon_random(&rng_state);
#if AEON_USE_FIXED_POINT
    /* Rango [-128, 127] mapeado a [-1, 1) en punto fijo */
    core->W_in[i] = (aeon_weight_t)((r % 256) - 128);
#else
    core->W_in[i] = ((float)(r % 1000) / 500.0f) - 1.0f;
#endif
  }

  /* W_reservoir: Conexiones escasas */
  core->sparse_count = 0;
  int total_connections = AEON_RESERVOIR_SIZE * AEON_RESERVOIR_SIZE;
  int target_connections = total_connections / AEON_SPARSITY_FACTOR;

  for (int i = 0;
       i < target_connections &&
       core->sparse_count <
           (AEON_RESERVOIR_SIZE * AEON_RESERVOIR_SIZE / AEON_SPARSITY_FACTOR);
       i++) {

    uint32_t r = aeon_random(&rng_state);
    uint16_t idx = r % total_connections;

    /* Evitar duplicados (simple) */
    bool exists = false;
    for (int j = 0; j < core->sparse_count; j++) {
      if (core->sparse_indices[j] == idx) {
        exists = true;
        break;
      }
    }

    if (!exists) {
      core->sparse_indices[core->sparse_count] = idx;
      r = aeon_random(&rng_state);
#if AEON_USE_FIXED_POINT
      core->W_reservoir[core->sparse_count] = (aeon_weight_t)((r % 256) - 128);
#else
      core->W_reservoir[core->sparse_count] =
          ((float)(r % 1000) / 500.0f) - 1.0f;
#endif
      core->sparse_count++;
    }
  }

  /* W_out: Inicializar a cero (se entrena después) */
  memset(core->W_out, 0, sizeof(core->W_out));

  /* Estado inicial */
  memset(core->state, 0, sizeof(core->state));
  core->samples_processed = 0;
  core->learning_sessions = 0;
  core->is_trained = false;

  return 0;
}

/* ============================================================
 * PERSISTENCIA
 * ============================================================ */

int aeon_save(const aeon_core_t *core, const char *filename) {
  if (core == NULL || filename == NULL)
    return -1;

  FILE *f = fopen(filename, "wb");
  if (f == NULL)
    return -2;

  /* Escribir estructura completa */
  size_t written = fwrite(core, sizeof(aeon_core_t), 1, f);
  fclose(f);

  return (written == 1) ? 0 : -3;
}

int aeon_load(aeon_core_t *core, const char *filename) {
  if (core == NULL || filename == NULL)
    return -1;

  FILE *f = fopen(filename, "rb");
  if (f == NULL)
    return -2;

  /* Leer estructura completa */
  size_t read = fread(core, sizeof(aeon_core_t), 1, f);
  fclose(f);

  return (read == 1) ? 0 : -3;
}

/* ============================================================
 * PROCESAMIENTO
 * ============================================================ */

void aeon_update(aeon_core_t *core, const aeon_state_t *input) {
  if (core == NULL || input == NULL)
    return;

  aeon_state_t new_state[AEON_RESERVOIR_SIZE];

  /* Contribución de entrada: W_in * input */
  for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
    aeon_state_t sum = 0;
    for (int j = 0; j < AEON_INPUT_SIZE; j++) {
      int idx = i * AEON_INPUT_SIZE + j;
#if AEON_USE_FIXED_POINT
      sum += ((aeon_state_t)core->W_in[idx] * input[j]) >> AEON_SCALE_BITS;
#else
      sum += core->W_in[idx] * input[j];
#endif
    }
    new_state[i] = sum;
  }

  /* Contribución del reservoir (escaso): W_reservoir * state */
  for (int k = 0; k < core->sparse_count; k++) {
    uint16_t idx = core->sparse_indices[k];
    int i = idx / AEON_RESERVOIR_SIZE; /* Fila */
    int j = idx % AEON_RESERVOIR_SIZE; /* Columna */

#if AEON_USE_FIXED_POINT
    new_state[i] += ((aeon_state_t)core->W_reservoir[k] * core->state[j]) >>
                    AEON_SCALE_BITS;
#else
    new_state[i] += core->W_reservoir[k] * core->state[j];
#endif
  }

  /* Aplicar no-linealidad y actualizar estado */
  for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
    core->state[i] = aeon_tanh_approx(new_state[i]);
  }

  core->samples_processed++;
}

void aeon_predict(const aeon_core_t *core, aeon_state_t *output) {
  if (core == NULL || output == NULL)
    return;

  /* output = W_out * state */
  for (int i = 0; i < AEON_OUTPUT_SIZE; i++) {
    aeon_state_t sum = 0;
    for (int j = 0; j < AEON_RESERVOIR_SIZE; j++) {
      int idx = i * AEON_RESERVOIR_SIZE + j;
#if AEON_USE_FIXED_POINT
      sum +=
          ((aeon_state_t)core->W_out[idx] * core->state[j]) >> AEON_SCALE_BITS;
#else
      sum += core->W_out[idx] * core->state[j];
#endif
    }
    output[i] = sum;
  }
}

void aeon_reset(aeon_core_t *core) {
  if (core == NULL)
    return;
  memset(core->state, 0, sizeof(core->state));
}

/* ============================================================
 * ENTRENAMIENTO
 * ============================================================ */

float aeon_train(aeon_core_t *core, const aeon_state_t *inputs,
                 const aeon_state_t *targets, uint16_t n_samples,
                 uint16_t washout) {
  if (core == NULL || inputs == NULL || targets == NULL)
    return -1.0f;
  if (n_samples <= washout)
    return -2.0f;

  uint16_t train_samples = n_samples - washout;

  /*
   * ENTRENAMIENTO OPTIMIZADO PARA PUNTO FIJO
   *
   * Usamos regresión de mínimos cuadrados con acumuladores de mayor precisión.
   * Para evitar overflow en punto fijo, trabajamos en float durante el
   * entrenamiento y convertimos al final.
   */

  /* Reset y recolectar estados en formato float para precisión */
  aeon_reset(core);

  /* Acumuladores para regresión (S^T * S) y (S^T * Y) */
  float StS[AEON_RESERVOIR_SIZE][AEON_RESERVOIR_SIZE];
  float StY[AEON_RESERVOIR_SIZE][AEON_OUTPUT_SIZE];

  /* Inicializar acumuladores */
  for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
    for (int j = 0; j < AEON_RESERVOIR_SIZE; j++) {
      StS[i][j] = (i == j) ? 1e-4f : 0.0f; /* Regularización en diagonal */
    }
    for (int o = 0; o < AEON_OUTPUT_SIZE; o++) {
      StY[i][o] = 0.0f;
    }
  }

  /* Pasar datos y acumular */
  for (uint16_t t = 0; t < n_samples; t++) {
    aeon_update(core, &inputs[t * AEON_INPUT_SIZE]);

    if (t >= washout) {
      /* Extraer estado actual como float */
      float state_f[AEON_RESERVOIR_SIZE];
      for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
#if AEON_USE_FIXED_POINT
        state_f[i] = (float)core->state[i] / AEON_SCALE;
#else
        state_f[i] = core->state[i];
#endif
      }

      /* Target actual */
      float target_f[AEON_OUTPUT_SIZE];
      for (int o = 0; o < AEON_OUTPUT_SIZE; o++) {
#if AEON_USE_FIXED_POINT
        target_f[o] = (float)targets[t * AEON_OUTPUT_SIZE + o] / AEON_SCALE;
#else
        target_f[o] = targets[t * AEON_OUTPUT_SIZE + o];
#endif
      }

      /* Acumular S^T * S (matriz de covarianza) */
      for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
        for (int j = i; j < AEON_RESERVOIR_SIZE; j++) {
          float prod = state_f[i] * state_f[j];
          StS[i][j] += prod;
          if (i != j)
            StS[j][i] += prod; /* Simetría */
        }

        /* Acumular S^T * Y */
        for (int o = 0; o < AEON_OUTPUT_SIZE; o++) {
          StY[i][o] += state_f[i] * target_f[o];
        }
      }
    }
  }

  /*
   * Resolver W_out = (S^T*S)^(-1) * S^T*Y usando eliminación Gaussiana
   * simplificada (Gauss-Jordan para sistemas pequeños)
   */

  /* Invertir StS usando Gauss-Jordan (in-place con matriz identidad) */
  float inv[AEON_RESERVOIR_SIZE][AEON_RESERVOIR_SIZE];

  /* Inicializar inversa como identidad */
  for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
    for (int j = 0; j < AEON_RESERVOIR_SIZE; j++) {
      inv[i][j] = (i == j) ? 1.0f : 0.0f;
    }
  }

  /* Gauss-Jordan */
  for (int col = 0; col < AEON_RESERVOIR_SIZE; col++) {
    /* Buscar pivote máximo */
    int max_row = col;
    float max_val = StS[col][col] > 0 ? StS[col][col] : -StS[col][col];

    for (int row = col + 1; row < AEON_RESERVOIR_SIZE; row++) {
      float val = StS[row][col] > 0 ? StS[row][col] : -StS[row][col];
      if (val > max_val) {
        max_val = val;
        max_row = row;
      }
    }

    /* Intercambiar filas si es necesario */
    if (max_row != col) {
      for (int k = 0; k < AEON_RESERVOIR_SIZE; k++) {
        float tmp = StS[col][k];
        StS[col][k] = StS[max_row][k];
        StS[max_row][k] = tmp;
        tmp = inv[col][k];
        inv[col][k] = inv[max_row][k];
        inv[max_row][k] = tmp;
      }
    }

    /* Normalizar fila pivote */
    float pivot = StS[col][col];
    if (pivot == 0.0f)
      pivot = 1e-10f; /* Evitar división por cero */

    for (int k = 0; k < AEON_RESERVOIR_SIZE; k++) {
      StS[col][k] /= pivot;
      inv[col][k] /= pivot;
    }

    /* Eliminar en otras filas */
    for (int row = 0; row < AEON_RESERVOIR_SIZE; row++) {
      if (row != col) {
        float factor = StS[row][col];
        for (int k = 0; k < AEON_RESERVOIR_SIZE; k++) {
          StS[row][k] -= factor * StS[col][k];
          inv[row][k] -= factor * inv[col][k];
        }
      }
    }
  }

  /* Calcular W_out = inv(StS) * StY */
  for (int o = 0; o < AEON_OUTPUT_SIZE; o++) {
    for (int i = 0; i < AEON_RESERVOIR_SIZE; i++) {
      float sum = 0.0f;
      for (int k = 0; k < AEON_RESERVOIR_SIZE; k++) {
        sum += inv[i][k] * StY[k][o];
      }

      /* Limitar magnitud del peso para estabilidad */
      if (sum > 2.0f)
        sum = 2.0f;
      if (sum < -2.0f)
        sum = -2.0f;

#if AEON_USE_FIXED_POINT
      core->W_out[o * AEON_RESERVOIR_SIZE + i] =
          (aeon_weight_t)(sum * AEON_SCALE);
#else
      core->W_out[o * AEON_RESERVOIR_SIZE + i] = sum;
#endif
    }
  }

  core->is_trained = true;
  core->learning_sessions++;

  /* Calcular MSE */
  float mse = 0.0f;
  aeon_reset(core);

  for (uint16_t t = washout; t < n_samples; t++) {
    aeon_update(core, &inputs[t * AEON_INPUT_SIZE]);

    aeon_state_t pred[AEON_OUTPUT_SIZE];
    aeon_predict(core, pred);

    for (int o = 0; o < AEON_OUTPUT_SIZE; o++) {
#if AEON_USE_FIXED_POINT
      float p = (float)pred[o] / AEON_SCALE;
      float y = (float)targets[t * AEON_OUTPUT_SIZE + o] / AEON_SCALE;
#else
      float p = pred[o];
      float y = targets[t * AEON_OUTPUT_SIZE + o];
#endif
      float diff = p - y;
      mse += diff * diff;
    }
  }

  return mse / (float)(train_samples * AEON_OUTPUT_SIZE);
}

int aeon_prune(aeon_core_t *core, float threshold) {
  if (core == NULL)
    return -1;

  int pruned_count = 0;
  int total_weights = AEON_OUTPUT_SIZE * AEON_RESERVOIR_SIZE;

#if AEON_USE_FIXED_POINT
  aeon_weight_t fixed_threshold = (aeon_weight_t)(threshold * AEON_SCALE);
#endif

  for (int i = 0; i < total_weights; i++) {
    aeon_weight_t w = core->W_out[i];

#if AEON_USE_FIXED_POINT
    if (abs(w) < fixed_threshold) {
      core->W_out[i] = 0;
      pruned_count++;
    }
#else
    if (fabs(w) < threshold) {
      core->W_out[i] = 0.0f;
      pruned_count++;
    }
#endif
  }

  return pruned_count;
}

/* ============================================================
 * UTILIDADES
 * ============================================================ */

uint32_t aeon_memory_usage(const aeon_core_t *core) {
  if (core == NULL)
    return 0;
  return sizeof(aeon_core_t);
}

uint32_t aeon_age_seconds(const aeon_core_t *core) {
  if (core == NULL)
    return 0;
  return (uint32_t)(time(NULL) - core->certificate.birth_time);
}

void aeon_hash_to_string(const aeon_hash_t *hash, char *buffer) {
  if (hash == NULL || buffer == NULL)
    return;

  for (int i = 0; i < 16; i++) {
    sprintf(buffer + i * 2, "%02x", hash->bytes[i]);
  }
  buffer[32] = '\0';
}
