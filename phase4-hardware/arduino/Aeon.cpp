/**
 * Aeon.cpp - Implementación de librería Arduino
 *
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#include "Aeon.h"

// Factor de escala para punto fijo Q8.8
#define SCALE 256
#define SCALE_BITS 8

Aeon::Aeon(uint8_t reservoirSize) {
  _size = min(reservoirSize, AEON_MAX_RESERVOIR);
  _trained = false;
  _sparse_count = 0;
  _rng = 0;
}

void Aeon::begin(uint32_t seed) {
  // Inicializar RNG
  _rng = (seed == 0) ? millis() : seed;

  // Limpiar estado
  reset();

  // Inicializar W_in (pesos de entrada aleatorios)
  for (uint8_t i = 0; i < _size; i++) {
    _W_in[i] = (int8_t)((_random() % 256) - 128);
    _W_out[i] = 0; // Se entrena después
  }

  // Inicializar reservoir escaso
  _sparse_count = 0;
  uint16_t target = (_size * _size) / AEON_SPARSITY;
  uint16_t max_sparse = sizeof(_sparse_from);

  for (uint16_t i = 0; i < target && _sparse_count < max_sparse; i++) {
    uint8_t from = _random() % _size;
    uint8_t to = _random() % _size;
    int8_t weight = (int8_t)((_random() % 256) - 128);

    _sparse_from[_sparse_count] = from;
    _sparse_to[_sparse_count] = to;
    _sparse_weight[_sparse_count] = weight;
    _sparse_count++;
  }

  _trained = false;
}

uint32_t Aeon::_random() {
  _rng = (_rng * 1103515245UL + 12345UL) & 0x7FFFFFFFUL;
  return _rng;
}

int16_t Aeon::_tanh_approx(int16_t x) {
  // Saturación y aproximación simple
  if (x > SCALE)
    return SCALE;
  if (x < -SCALE)
    return -SCALE;

  // tanh(x) ≈ x - x³/3 para |x| < 1
  int32_t x2 = ((int32_t)x * x) >> SCALE_BITS;
  int32_t x3 = (x2 * x) >> SCALE_BITS;
  return x - (x3 / 3);
}

float Aeon::_toFloat(int16_t fixed) { return (float)fixed / SCALE; }

int16_t Aeon::_toFixed(float f) { return (int16_t)(f * SCALE); }

void Aeon::update(float input) {
  int16_t input_fixed = _toFixed(input);
  int16_t new_state[AEON_MAX_RESERVOIR];

  // Contribución de entrada
  for (uint8_t i = 0; i < _size; i++) {
    int32_t sum = ((int32_t)_W_in[i] * input_fixed) >> SCALE_BITS;
    new_state[i] = (int16_t)sum;
  }

  // Contribución del reservoir (escaso)
  for (uint16_t k = 0; k < _sparse_count; k++) {
    uint8_t from = _sparse_from[k];
    uint8_t to = _sparse_to[k];
    int32_t contrib = ((int32_t)_sparse_weight[k] * _state[from]) >> SCALE_BITS;
    new_state[to] += (int16_t)contrib;
  }

  // Aplicar tanh y actualizar
  for (uint8_t i = 0; i < _size; i++) {
    _state[i] = _tanh_approx(new_state[i]);
  }
}

float Aeon::predict() {
  int32_t sum = 0;
  for (uint8_t i = 0; i < _size; i++) {
    sum += ((int32_t)_W_out[i] * _state[i]) >> SCALE_BITS;
  }
  return _toFloat((int16_t)sum);
}

float Aeon::train(float *inputs, float *targets, uint16_t n_samples,
                  uint8_t washout) {
  if (n_samples <= washout)
    return -1.0f;

  uint16_t train_samples = n_samples - washout;

  // Acumuladores para regresión simplificada
  float sum_xy[AEON_MAX_RESERVOIR];
  float sum_xx[AEON_MAX_RESERVOIR];

  for (uint8_t i = 0; i < _size; i++) {
    sum_xy[i] = 0;
    sum_xx[i] = 0;
  }

  // Reset y recolectar
  reset();

  for (uint16_t t = 0; t < n_samples; t++) {
    update(inputs[t]);

    if (t >= washout) {
      float y = targets[t];
      for (uint8_t i = 0; i < _size; i++) {
        float x = _toFloat(_state[i]);
        sum_xy[i] += x * y;
        sum_xx[i] += x * x;
      }
    }
  }

  // Calcular pesos de salida
  for (uint8_t i = 0; i < _size; i++) {
    float weight = sum_xy[i] / (sum_xx[i] + 1e-6f);
    weight = constrain(weight, -2.0f, 2.0f);
    _W_out[i] = (int8_t)(weight * 64); // Escala reducida para int8
  }

  _trained = true;

  // Calcular MSE
  reset();
  float mse = 0;

  for (uint16_t t = washout; t < n_samples; t++) {
    update(inputs[t]);
    float pred = predict();
    float diff = pred - targets[t];
    mse += diff * diff;
  }

  return mse / train_samples;
}

void Aeon::reset() {
  for (uint8_t i = 0; i < _size; i++) {
    _state[i] = 0;
  }
}

uint16_t Aeon::memoryUsage() {
  return sizeof(Aeon) + _size * sizeof(int16_t) + // state
         _size * sizeof(int8_t) * 2 +             // W_in, W_out
         _sparse_count * 3;                       // sparse connections
}
