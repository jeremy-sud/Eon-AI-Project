/**
 * Aeon ESP32 - Versión con WiFi
 *
 * Extiende la librería base con capacidades de red:
 * - Enviar predicciones por HTTP
 * - Recibir datos de sensores
 * - Sincronizar con otros nodos (Mente Colectiva)
 *
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#ifndef AEON_ESP32_H
#define AEON_ESP32_H

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

// Incluir librería base
#include "../arduino/Aeon.h"

class AeonESP32 : public Aeon {
public:
  AeonESP32(uint8_t reservoirSize = 16) : Aeon(reservoirSize) {}

  /**
   * Conectar a WiFi
   */
  bool connectWiFi(const char *ssid, const char *password,
                   uint16_t timeout_ms = 10000) {
    WiFi.begin(ssid, password);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED) {
      if (millis() - start > timeout_ms)
        return false;
      delay(100);
    }
    return true;
  }

  /**
   * Obtener IP local
   */
  String getIP() { return WiFi.localIP().toString(); }

  /**
   * Enviar predicción a servidor
   */
  bool sendPrediction(const char *serverUrl, float input, float prediction) {
    if (WiFi.status() != WL_CONNECTED)
      return false;

    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<128> doc;
    doc["input"] = input;
    doc["prediction"] = prediction;
    doc["memory_bytes"] = memoryUsage();
    doc["chip_id"] = String((uint32_t)ESP.getEfuseMac(), HEX);

    String json;
    serializeJson(doc, json);

    int code = http.POST(json);
    http.end();

    return code == 200;
  }

  /**
   * Obtener pesos de otro nodo (para Mente Colectiva)
   */
  bool syncWeights(const char *peerUrl) {
    if (WiFi.status() != WL_CONNECTED)
      return false;

    HTTPClient http;
    http.begin(String(peerUrl) + "/weights");

    int code = http.GET();
    if (code != 200) {
      http.end();
      return false;
    }

    String payload = http.getString();
    http.end();

    // TODO: Parsear y mezclar pesos
    // Por ahora solo retorna éxito de conexión
    return true;
  }

  /**
   * Obtener ID único del chip
   */
  String getChipId() { return String((uint32_t)ESP.getEfuseMac(), HEX); }
};

#endif // AEON_ESP32_H
