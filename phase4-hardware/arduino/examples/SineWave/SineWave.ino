/**
 * Ejemplo: Predicción de Onda Sinusoidal
 *
 * Demuestra Eón prediciendo el siguiente valor de una onda.
 * Compatible con Arduino Nano, Uno, Mega, ESP8266, ESP32.
 *
 * Hardware: Solo Arduino, sin componentes adicionales.
 *
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#include "Aeon.h"

// Crear instancia con 16 neuronas (~500 bytes)
Aeon esn(16);

// Datos de entrenamiento (onda sinusoidal)
const uint16_t N_SAMPLES = 100;
float inputs[N_SAMPLES];
float targets[N_SAMPLES];

void setup() {
  Serial.begin(115200);
  while (!Serial)
    delay(10);

  Serial.println(F("\n=== Proyecto Eón - Arduino Demo ==="));
  Serial.println(F("\"La inteligencia no se crea, se descubre.\"\n"));

  // Inicializar Eón
  esn.begin();
  Serial.print(F("Memoria usada: "));
  Serial.print(esn.memoryUsage());
  Serial.println(F(" bytes"));

  // Generar datos de entrenamiento
  Serial.println(F("\nGenerando onda sinusoidal..."));
  for (uint16_t i = 0; i < N_SAMPLES; i++) {
    float t = i * 0.1;
    inputs[i] = sin(t);
    targets[i] = sin(t + 0.1); // Siguiente valor
  }

  // Entrenar
  Serial.println(F("Entrenando..."));
  unsigned long start = millis();
  float mse = esn.train(inputs, targets, N_SAMPLES, 20);
  unsigned long elapsed = millis() - start;

  Serial.print(F("MSE: "));
  Serial.println(mse, 6);
  Serial.print(F("Tiempo: "));
  Serial.print(elapsed);
  Serial.println(F(" ms"));

  Serial.println(F("\n=== Predicciones ==="));
  Serial.println(F("Entrada -> Predicción (Real)"));

  // Probar predicciones
  esn.reset();
  for (uint16_t i = 0; i < 10; i++) {
    esn.update(inputs[i + 50]);
    float pred = esn.predict();

    Serial.print(inputs[i + 50], 3);
    Serial.print(F(" -> "));
    Serial.print(pred, 3);
    Serial.print(F(" ("));
    Serial.print(targets[i + 50], 3);
    Serial.println(F(")"));
  }

  Serial.println(F("\n✓ Demo completado"));
  Serial.println(F("Proyecto Eón - Sistemas Ursol"));
}

void loop() {
  // Demostración continua: predecir con datos en tiempo real
  static float phase = 0;

  float input = sin(phase);
  esn.update(input);
  float pred = esn.predict();

  // Enviar por Serial para graficar con Serial Plotter
  Serial.print(input);
  Serial.print(",");
  Serial.println(pred);

  phase += 0.1;
  delay(50);
}
