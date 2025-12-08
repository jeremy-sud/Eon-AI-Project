/**
 * Aeon.h - Librería Arduino para Proyecto Eón
 *
 * Echo State Network ultraligero para microcontroladores.
 * Diseñado para Arduino Nano (2KB RAM) y superiores.
 *
 * Uso:
 *   #include <Aeon.h>
 *   Aeon esn(16);  // 16 neuronas
 *   esn.train(inputs, targets, 100);
 *   float pred = esn.predict(input);
 *
 * Memoria: ~500 bytes para 16 neuronas
 *
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 * https://github.com/SistemasUrsol
 */

#ifndef AEON_H
#define AEON_H

#include <Arduino.h>

// Configuración por defecto
#ifndef AEON_MAX_RESERVOIR
#define AEON_MAX_RESERVOIR 32 // Máximo de neuronas
#endif

#ifndef AEON_SPARSITY
#define AEON_SPARSITY 4 // 1 de cada N conexiones
#endif

class Aeon {
public:
  /**
   * Constructor
   * @param reservoirSize Número de neuronas (default: 16)
   */
  Aeon(uint8_t reservoirSize = 16);

  /**
   * Inicializa el reservoir con una semilla
   * @param seed Semilla para RNG (0 = usar millis())
   */
  void begin(uint32_t seed = 0);

  /**
   * Actualiza el estado con una entrada
   * @param input Valor de entrada [-1, 1]
   */
  void update(float input);

  /**
   * Obtiene predicción basada en estado actual
   * @return Valor predicho
   */
  float predict();

  /**
   * Entrena con datos
   * @param inputs Array de entradas
   * @param targets Array de objetivos
   * @param n_samples Número de muestras
   * @param washout Muestras a descartar (default: 20)
   * @return MSE del entrenamiento
   */
  float train(float *inputs, float *targets, uint16_t n_samples,
              uint8_t washout = 20);

  /**
   * Resetea el estado del reservoir
   */
  void reset();

  /**
   * Obtiene uso de memoria en bytes
   */
  uint16_t memoryUsage();

  /**
   * Obtiene el estado de entrenamiento
   */
  bool isTrained() { return _trained; }

protected:
  uint8_t _size; // Tamaño del reservoir
  bool _trained; // Estado de entrenamiento

  // Estado (punto fijo Q8.8)
  int16_t _state[AEON_MAX_RESERVOIR];

  // Pesos (punto fijo Q?.?) -> int8_t
  int8_t _W_in[AEON_MAX_RESERVOIR];
  int8_t _W_out[AEON_MAX_RESERVOIR];

  // Conexiones escasas del reservoir
  uint8_t _sparse_from[AEON_MAX_RESERVOIR * AEON_MAX_RESERVOIR / AEON_SPARSITY];
  uint8_t _sparse_to[AEON_MAX_RESERVOIR * AEON_MAX_RESERVOIR / AEON_SPARSITY];
  int8_t
      _sparse_weight[AEON_MAX_RESERVOIR * AEON_MAX_RESERVOIR / AEON_SPARSITY];
  uint16_t _sparse_count;

  // RNG estado
  uint32_t _rng;

  // Funciones internas
  uint32_t _random();
  int16_t _tanh_approx(int16_t x);
  float _toFloat(int16_t fixed);
  int16_t _toFixed(float f);
};

#endif // AEON_H
