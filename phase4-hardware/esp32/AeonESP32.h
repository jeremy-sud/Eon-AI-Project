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
   * Obtener pesos comprimidos (para enviar a otros nodos)
   * Protocolo: 1-Bit Weight Exchange
   * Retorna tamaño en bytes
   */
  size_t getCompressedWeights(uint8_t *buffer, size_t bufferSize) {
    size_t needed = (this->_size + 7) / 8;
    if (bufferSize < needed)
      return 0;

    _quantizeWOut(buffer);
    return needed;
  }

  /**
   * Obtener pesos de otro nodo (para Mente Colectiva)
   * Protocolo: 1-Bit Weight Exchange
   */
  bool syncWeights(const char *peerUrl) {
    if (WiFi.status() != WL_CONNECTED)
      return false;

    HTTPClient http;
    // Request binary weights directly (assuming endpoint handles this)
    http.begin(String(peerUrl) + "/weights/binary");

    int code = http.GET();
    if (code != 200) {
      http.end();
      return false;
    }

    // Get payload as bytes
    // Note: In real ESP32 usage we should stream this if large, but
    // for small reservoir (e.g. 16 neuronas -> 2 bytes) String is fine or
    // buffering. However, HTTPClient has getStream().
    int len = http.getSize();
    if (len <= 0) {
      http.end();
      return false;
    }

    // Buffer for compressed data
    uint8_t *buffer = (uint8_t *)malloc(len);
    if (!buffer) {
      http.end();
      return false;
    }

    WiFiClient *stream = http.getStreamPtr();
    if (stream->available()) {
      stream->readBytes(buffer, len);
    }

    // Dequantize and update W_out directly
    // Using a fixed magnitude for 1-bit restoration (e.g. 32 approx 0.5 in
    // Q?.?)
    _dequantizeToWOut(buffer, this->_size, 32);

    free(buffer);
    http.end();
    return true;
  }

  /**
   * Obtener ID único del chip
   */
  String getChipId() { return String((uint32_t)ESP.getEfuseMac(), HEX); }

private:
  /**
   * Descomprime 1-bit weights y actualiza W_out localmente
   */
  void _dequantizeToWOut(const uint8_t *input, int count, int8_t magnitude) {
    if (!input || count > AEON_MAX_RESERVOIR)
      return;

    for (int i = 0; i < count; i++) {
      int byte_idx = i / 8;
      int bit_idx = i % 8;

      if (input[byte_idx] & (1 << bit_idx)) {
        this->_W_out[i] = magnitude;
      } else {
        this->_W_out[i] = -magnitude;
      }
    }
  }

  /**
   * Comprime W_out a 1-bit por peso
   */
  void _quantizeWOut(uint8_t *output) {
    memset(output, 0, (this->_size + 7) / 8);

    for (int i = 0; i < this->_size; i++) {
      if (this->_W_out[i] >= 0) {
        // Bit index logic: i/8 idx, i%8 bit
        output[i / 8] |= (1 << (i % 8));
      }
    }
  }
};

#endif // AEON_ESP32_H
