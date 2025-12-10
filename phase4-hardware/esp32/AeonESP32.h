/**
 * Aeon ESP32 - Versión con WiFi y Sistema Thelema
 *
 * Extiende la librería base con capacidades de red:
 * - Enviar predicciones por HTTP
 * - Recibir datos de sensores
 * - Sincronizar con otros nodos (Mente Colectiva)
 * - Sistema de Voluntad Verdadera (Thelema)
 *
 * Filosofía Thelema:
 * "Hacer tu Voluntad será el todo de la Ley"
 * Cada nodo tiene una órbita única y no debe desviarse de ella.
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

// =============================================================================
// SISTEMA DE VOLUNTAD VERDADERA (THELEMA)
// =============================================================================

/**
 * Dominios de datos que un nodo puede procesar
 */
enum DataDomain {
  DOMAIN_TEMPERATURE = 0,
  DOMAIN_HUMIDITY = 1,
  DOMAIN_AUDIO = 2,
  DOMAIN_MOTION = 3,
  DOMAIN_LIGHT = 4,
  DOMAIN_PRESSURE = 5,
  DOMAIN_VIBRATION = 6,
  DOMAIN_VOLTAGE = 7,
  DOMAIN_TIMESERIES = 8,
  DOMAIN_GENERIC = 9,
  DOMAIN_COUNT = 10
};

/**
 * Decisiones de tarea basadas en Voluntad Verdadera
 */
enum TaskDecision {
  DECISION_ACCEPT = 0,      // Tarea alineada con Voluntad
  DECISION_HIGH_PRIORITY = 1, // Parcialmente alineada
  DECISION_LOW_PRIORITY = 2,  // Desalineada pero aceptable
  DECISION_REJECT = 3         // Fuera de la Voluntad - rechazar
};

/**
 * Estructura para el Vector de Voluntad Verdadera
 */
struct TrueWillVector {
  DataDomain genesisDomain;           // Dominio nativo del nodo
  uint8_t affinity[DOMAIN_COUNT];     // Afinidad [0-255] por dominio
  uint16_t processingCount[DOMAIN_COUNT]; // Contador de procesamiento
  uint8_t inertia;                    // Resistencia al cambio [0-255]
  uint8_t rejectionThreshold;         // Umbral de rechazo [0-255]
  uint8_t highCostThreshold;          // Umbral de costo alto [0-255]
};

class AeonESP32 : public Aeon {
public:
  AeonESP32(uint8_t reservoirSize = 16, DataDomain genesisDomain = DOMAIN_GENERIC) 
    : Aeon(reservoirSize) {
    _initTrueWill(genesisDomain);
  }

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

  // =========================================================================
  // SISTEMA THELEMA: Voluntad Verdadera
  // =========================================================================

  /**
   * Calcula el vector de Voluntad Verdadera normalizado.
   * 
   * Retorna la "fuerza de voluntad" hacia cada dominio.
   * 
   * @param willVector Array de salida [DOMAIN_COUNT] con valores 0-255
   */
  void calculateTrueWillVector(uint8_t *willVector) {
    uint32_t total = 0;
    uint16_t rawWill[DOMAIN_COUNT];
    
    // Calcular voluntad bruta por dominio
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      // Experiencia normalizada (procesamiento / total)
      uint16_t totalProcessing = 0;
      for (int j = 0; j < DOMAIN_COUNT; j++) {
        totalProcessing += _trueWill.processingCount[j];
      }
      uint8_t experience = (totalProcessing > 0) 
        ? (_trueWill.processingCount[i] * 255 / totalProcessing) 
        : 0;
      
      // Voluntad = afinidad * (1 + experiencia/256)
      rawWill[i] = (uint16_t)_trueWill.affinity[i] * (256 + experience) / 256;
      total += rawWill[i];
    }
    
    // Normalizar a 0-255
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      willVector[i] = (total > 0) ? (rawWill[i] * 255 / total) : 0;
    }
  }

  /**
   * Evalúa el costo de procesar una tarea en un dominio específico.
   * 
   * @param domain Dominio solicitado
   * @return TaskDecision indicando si aceptar/rechazar
   */
  TaskDecision evaluateTaskCost(DataDomain domain) {
    uint8_t affinity = _trueWill.affinity[domain];
    
    if (affinity >= _trueWill.highCostThreshold) {
      return (affinity >= 200) ? DECISION_ACCEPT : DECISION_HIGH_PRIORITY;
    } else if (affinity >= _trueWill.rejectionThreshold) {
      return DECISION_LOW_PRIORITY;
    }
    return DECISION_REJECT;
  }

  /**
   * ¿Debería este nodo aceptar esta tarea?
   * 
   * Implementa el principio Thelemático: "Cada estrella en su órbita."
   * 
   * @param domain Dominio de la tarea solicitada
   * @return true si debería aceptar
   */
  bool shouldAcceptTask(DataDomain domain) {
    return evaluateTaskCost(domain) != DECISION_REJECT;
  }

  /**
   * Registra el procesamiento de datos, actualizando la Voluntad.
   * 
   * @param domain Dominio procesado
   * @param mse Error cuadrático medio (Q8.8)
   */
  void recordProcessing(DataDomain domain, int16_t mse_q8) {
    // Incrementar contador
    if (_trueWill.processingCount[domain] < 65535) {
      _trueWill.processingCount[domain]++;
    }
    
    // Actualizar afinidad basada en éxito
    // mse_q8 está en Q8.8, entonces 0x100 = 1.0
    if (mse_q8 < 0x1A) {  // < 0.1 - muy exitoso
      if (_trueWill.affinity[domain] < 250) {
        _trueWill.affinity[domain] += 5;
      }
    } else if (mse_q8 < 0x4D) {  // < 0.3 - aceptable
      if (_trueWill.affinity[domain] < 253) {
        _trueWill.affinity[domain] += 2;
      }
    } else if (mse_q8 > 0xB3) {  // > 0.7 - malo
      if (_trueWill.affinity[domain] > 3) {
        _trueWill.affinity[domain] -= 3;
      }
    }
    
    // Aumentar inercia con experiencia
    uint32_t totalExp = 0;
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      totalExp += _trueWill.processingCount[i];
    }
    _trueWill.inertia = min(243, (uint8_t)(128 + totalExp / 4));
  }

  /**
   * Obtiene el dominio de especialización del nodo.
   * 
   * @param level Puntero para almacenar nivel de especialización (0-255)
   * @return DataDomain de especialización
   */
  DataDomain getSpecialization(uint8_t *level) {
    uint8_t maxAffinity = 0;
    DataDomain specialized = _trueWill.genesisDomain;
    
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      if (_trueWill.affinity[i] > maxAffinity) {
        maxAffinity = _trueWill.affinity[i];
        specialized = (DataDomain)i;
      }
    }
    
    if (level) *level = maxAffinity;
    return specialized;
  }

  /**
   * Exporta el vector de Voluntad para sincronización (4 bytes comprimido)
   * 
   * @param buffer Buffer de salida (mínimo 4 bytes)
   * @return Bytes escritos
   */
  size_t exportWillCompressed(uint8_t *buffer) {
    // Byte 0: Genesis domain (4 bits) + inertia high (4 bits)
    buffer[0] = (_trueWill.genesisDomain & 0x0F) | ((_trueWill.inertia >> 4) << 4);
    
    // Byte 1-2: Top 2 affinities encoded
    uint8_t level;
    DataDomain spec1 = getSpecialization(&level);
    buffer[1] = (spec1 & 0x0F) | ((level >> 4) << 4);
    
    // Byte 2: Second highest affinity domain + level
    uint8_t secondMax = 0;
    DataDomain spec2 = DOMAIN_GENERIC;
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      if ((DataDomain)i != spec1 && _trueWill.affinity[i] > secondMax) {
        secondMax = _trueWill.affinity[i];
        spec2 = (DataDomain)i;
      }
    }
    buffer[2] = (spec2 & 0x0F) | ((secondMax >> 4) << 4);
    
    // Byte 3: Checksum
    buffer[3] = buffer[0] ^ buffer[1] ^ buffer[2];
    
    return 4;
  }

  /**
   * Obtiene el estado de la Voluntad Verdadera
   */
  TrueWillVector* getTrueWill() { return &_trueWill; }

  // =========================================================================
  // FUNCIONES DE RED (existentes)
  // =========================================================================

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
  // Vector de Voluntad Verdadera (Thelema)
  TrueWillVector _trueWill;

  /**
   * Inicializa el sistema de Voluntad Verdadera
   */
  void _initTrueWill(DataDomain genesisDomain) {
    _trueWill.genesisDomain = genesisDomain;
    _trueWill.inertia = 128;  // 50% inicial
    _trueWill.rejectionThreshold = 77;   // ~30%
    _trueWill.highCostThreshold = 128;   // ~50%
    
    // Inicializar afinidades
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      _trueWill.affinity[i] = 26;  // ~10% base
      _trueWill.processingCount[i] = 0;
    }
    
    // El dominio genesis comienza con máxima afinidad
    _trueWill.affinity[genesisDomain] = 255;
    _trueWill.processingCount[genesisDomain] = 1;
  }

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
