/**
 * ESP32 Demo: Predicción con envío WiFi
 *
 * Entrena localmente y envía predicciones a un servidor.
 *
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#include "AeonESP32.h"

// Configuración WiFi
const char *WIFI_SSID = "TuRedWiFi";
const char *WIFI_PASS = "TuPassword";
const char *SERVER_URL = "http://192.168.1.100:5000/api/predict";

// Crear instancia
AeonESP32 esn(16);

// Datos
const uint16_t N_SAMPLES = 100;
float inputs[N_SAMPLES];
float targets[N_SAMPLES];

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println(F("\n=== Proyecto Eón - ESP32 Demo ==="));
  Serial.print(F("Chip ID: "));
  Serial.println(esn.getChipId());

  // Conectar WiFi
  Serial.print(F("Conectando a WiFi..."));
  if (esn.connectWiFi(WIFI_SSID, WIFI_PASS)) {
    Serial.println(F(" OK"));
    Serial.print(F("IP: "));
    Serial.println(esn.getIP());
  } else {
    Serial.println(F(" FALLO"));
    Serial.println(F("Continuando sin WiFi..."));
  }

  // Inicializar Eón
  esn.begin();
  Serial.print(F("Memoria: "));
  Serial.print(esn.memoryUsage());
  Serial.println(F(" bytes"));

  // Generar datos
  for (uint16_t i = 0; i < N_SAMPLES; i++) {
    float t = i * 0.1;
    inputs[i] = sin(t);
    targets[i] = sin(t + 0.1);
  }

  // Entrenar
  Serial.println(F("Entrenando..."));
  float mse = esn.train(inputs, targets, N_SAMPLES, 20);
  Serial.print(F("MSE: "));
  Serial.println(mse, 6);

  Serial.println(F("\n✓ Listo para predecir"));
}

void loop() {
  static float phase = 0;

  // Generar entrada
  float input = sin(phase);

  // Predecir
  esn.update(input);
  float pred = esn.predict();

  // Mostrar
  Serial.print(F("In: "));
  Serial.print(input, 3);
  Serial.print(F(" -> Pred: "));
  Serial.println(pred, 3);

  // Enviar a servidor (si hay WiFi)
  if (WiFi.status() == WL_CONNECTED) {
    esn.sendPrediction(SERVER_URL, input, pred);
  }

  phase += 0.1;
  delay(500);
}
