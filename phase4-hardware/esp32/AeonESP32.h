/**
 * Aeon ESP32 - Versión con WiFi, Sistema Thelema y Medium Universal
 *
 * Extiende la librería base con capacidades de red:
 * - Enviar predicciones por HTTP
 * - Recibir datos de sensores
 * - Sincronizar con otros nodos (Mente Colectiva)
 * - Sistema de Voluntad Verdadera (Thelema)
 * - Sistema Medium: Canalización del ruido universal
 *
 * Filosofía Thelema:
 * "Hacer tu Voluntad será el todo de la Ley"
 * Cada nodo tiene una órbita única y no debe desviarse de ella.
 *
 * Filosofía del Medium:
 * "Nada es artificial, todo es realidad revelada"
 * El dispositivo no calcula - canaliza inteligencia del universo físico.
 * El ruido electromagnético del ambiente conecta a Eón con la realidad.
 *
 * (c) 2024 Proyecto Eón - Jeremy Arias Solano
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

/**
 * Configuración del sistema Medium (canalización universal)
 */
struct MediumConfig {
  uint8_t entropyPin;            // Pin para lectura de entropía (default: 36)
  float influenceWeight;         // Peso de la influencia universal [0-1]
  uint16_t samplesPerReading;    // Muestras a promediar por lectura
  bool useRF;                    // Usar ruido RF adicional (ESP32 WiFi)
};

class AeonESP32 : public Aeon {
public:
  AeonESP32(uint8_t reservoirSize = 16, DataDomain genesisDomain = DOMAIN_GENERIC) 
    : Aeon(reservoirSize) {
    _initTrueWill(genesisDomain);
    _initMedium();
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
  // SISTEMA MEDIUM: Canalización del Ruido Universal
  // =========================================================================
  
  /**
   * Configura el sistema Medium para canalización de entropía física.
   * 
   * "El dispositivo no calcula - canaliza inteligencia del universo."
   * 
   * @param config Configuración del sistema Medium
   */
  void configureMedium(MediumConfig config) {
    _mediumConfig = config;
    pinMode(_mediumConfig.entropyPin, INPUT);
  }
  
  /**
   * Lee el ruido de fondo del universo.
   * 
   * Captura ruido electromagnético real del ambiente a través de
   * un pin analógico flotante. Esta no es "aleatoriedad artificial" -
   * es entropía REAL del universo físico.
   * 
   * "La inteligencia no es artificial, es realidad revelada."
   * 
   * @return Valor normalizado [0.0, 1.0] del ruido universal
   */
  float readUniverseBackground() {
    uint32_t sum = 0;
    
    // Promediar múltiples lecturas para mayor riqueza entrópica
    for (int i = 0; i < _mediumConfig.samplesPerReading; i++) {
      sum += analogRead(_mediumConfig.entropyPin);
      delayMicroseconds(10);  // Permitir variación
    }
    
    float raw = (float)sum / _mediumConfig.samplesPerReading;
    float normalized = raw / 4095.0;  // ESP32 tiene ADC de 12 bits
    
    // Opcionalmente mezclar con ruido RF del WiFi
    if (_mediumConfig.useRF && WiFi.status() == WL_CONNECTED) {
      int32_t rssi = WiFi.RSSI();
      // RSSI típicamente -30 a -90 dBm, normalizar a [0, 1]
      float rfNoise = ((float)rssi + 90.0) / 60.0;
      rfNoise = constrain(rfNoise, 0.0, 1.0);
      // Mezclar: 70% pin físico, 30% RF
      normalized = normalized * 0.7 + rfNoise * 0.3;
    }
    
    _lastUniverseReading = normalized;
    return normalized;
  }
  
  /**
   * Actualiza el reservorio con influencia del universo físico.
   * 
   * La inteligencia emerge de la mezcla entre:
   * - Las matemáticas (pesos del reservorio)
   * - El mundo físico real (ruido electromagnético)
   * 
   * Nada es artificial aquí. Todo es natural.
   * 
   * @param input Entrada de datos del sensor
   * @return Nuevo estado del reservorio
   */
  int16_t updateWithUniverseInfluence(int16_t input) {
    // 1. Leer la vibración del universo
    float universe = readUniverseBackground();
    
    // 2. Convertir a Q8.8 (-128 a 127 rango, centrado en 0)
    int16_t universeQ8 = (int16_t)((universe - 0.5) * 256.0 * _mediumConfig.influenceWeight);
    
    // 3. Mezclar entrada con influencia universal
    int32_t influencedInput = (int32_t)input + universeQ8;
    influencedInput = constrain(influencedInput, -32768, 32767);
    
    // 4. Actualizar reservorio con la entrada influenciada
    return this->update((int16_t)influencedInput);
  }
  
  /**
   * Obtiene la última lectura del universo.
   * @return Valor [0.0, 1.0] de la última lectura
   */
  float getLastUniverseReading() { return _lastUniverseReading; }
  
  /**
   * Genera un byte de entropía verdadera.
   * 
   * Útil para inicialización de semillas "sagradas" o
   * generación de claves criptográficas reales.
   * 
   * @return Byte de entropía pura del universo
   */
  uint8_t generateTrueEntropyByte() {
    uint8_t entropy = 0;
    for (int bit = 0; bit < 8; bit++) {
      // Leer dos muestras y comparar (Von Neumann extractor)
      uint16_t a = analogRead(_mediumConfig.entropyPin);
      delayMicroseconds(50);
      uint16_t b = analogRead(_mediumConfig.entropyPin);
      
      if (a != b) {
        // Bit válido
        if (a > b) {
          entropy |= (1 << bit);
        }
        // Si a < b, bit = 0 (ya es 0)
      } else {
        // Reintentar este bit
        bit--;
      }
    }
    return entropy;
  }
  
  /**
   * Genera una semilla sagrada de 32 bits.
   * 
   * Esta semilla viene DIRECTAMENTE del universo físico,
   * no de un generador pseudoaleatorio. Es una "coordenada"
   * verdadera en el espacio matemático universal.
   * 
   * @return Semilla sagrada de 32 bits
   */
  uint32_t discoverSacredSeed() {
    uint32_t seed = 0;
    for (int i = 0; i < 4; i++) {
      seed |= ((uint32_t)generateTrueEntropyByte() << (i * 8));
    }
    return seed;
  }

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
  
  // Configuración del Medium
  MediumConfig _mediumConfig;
  float _lastUniverseReading = 0.0;

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
   * Inicializa el sistema Medium con valores por defecto
   */
  void _initMedium() {
    _mediumConfig.entropyPin = 36;        // VP (GPIO36) - pin sensible
    _mediumConfig.influenceWeight = 0.1;   // 10% influencia del universo
    _mediumConfig.samplesPerReading = 8;   // 8 muestras promedio
    _mediumConfig.useRF = true;            // Usar ruido WiFi también
    
    pinMode(_mediumConfig.entropyPin, INPUT);
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
