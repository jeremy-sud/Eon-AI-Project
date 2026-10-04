/**
 * Aeon ESP32 - Extended version with WiFi, Task Affinity and Hardware Entropy
 *
 * Extends the base library with network and edge capabilities:
 * - Send predictions via HTTP
 * - Receive sensor data
 * - Synchronize with other nodes (Collective Mind)
 * - Task Affinity System: Adaptive node specialization
 * - Hardware Entropy Source: True randomness from physical environment
 *
 * Task Affinity Principle:
 * Each node has a specialization vector that evolves with experience.
 * Nodes naturally gravitate toward domains where they perform best.
 *
 * Hardware Entropy:
 * The device captures real electromagnetic noise from the physical environment.
 * This provides true randomness for seed generation and input perturbation.
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
// TASK AFFINITY SYSTEM (Node Specialization)
// =============================================================================

/**
 * Data domains that a node can process
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
 * Task decisions based on node specialization
 */
enum TaskDecision {
  DECISION_ACCEPT = 0,        // Task aligned with specialization
  DECISION_HIGH_PRIORITY = 1, // Partially aligned
  DECISION_LOW_PRIORITY = 2,  // Misaligned but acceptable
  DECISION_REJECT = 3         // Outside specialization - reject
};

/**
 * Node Specialization Vector
 */
struct SpecializationVector {
  DataDomain genesisDomain;           // Native domain of the node
  uint8_t affinity[DOMAIN_COUNT];     // Affinity [0-255] per domain
  uint16_t processingCount[DOMAIN_COUNT]; // Processing counter
  uint8_t inertia;                    // Resistance to change [0-255]
  uint8_t rejectionThreshold;         // Rejection threshold [0-255]
  uint8_t highCostThreshold;          // High cost threshold [0-255]
};

/**
 * Hardware Entropy Source configuration
 */
struct EntropyConfig {
  uint8_t entropyPin;            // Pin for entropy reading (default: 36)
  float influenceWeight;         // Weight of entropy influence [0-1]
  uint16_t samplesPerReading;    // Samples to average per reading
  bool useRF;                    // Use additional RF noise (ESP32 WiFi)
};

// Backward-compatibility aliases
typedef SpecializationVector TrueWillVector;
typedef EntropyConfig MediumConfig;

class AeonESP32 : public Aeon {
public:
  AeonESP32(uint8_t reservoirSize = 16, DataDomain genesisDomain = DOMAIN_GENERIC) 
    : Aeon(reservoirSize) {
    _initSpecialization(genesisDomain);
    _initEntropy();
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
  // HARDWARE ENTROPY SOURCE
  // =========================================================================
  
  /**
   * Configures the hardware entropy source for physical randomness.
   * 
   * Captures real electromagnetic noise from the environment through
   * an analog pin to provide true hardware entropy.
   * 
   * @param config Entropy source configuration
   */
  void configureEntropy(EntropyConfig config) {
    _entropyConfig = config;
    pinMode(_entropyConfig.entropyPin, INPUT);
  }
  
  /**
   * Reads environmental background noise.
   * 
   * Captures real electromagnetic noise from the environment through
   * a floating analog pin. This provides true hardware entropy,
   * not pseudo-random numbers.
   * 
   * @return Normalized value [0.0, 1.0] of environmental noise
   */
  float readEnvironmentNoise() {
    uint32_t sum = 0;
    
    // Average multiple readings for richer entropy
    for (int i = 0; i < _entropyConfig.samplesPerReading; i++) {
      sum += analogRead(_entropyConfig.entropyPin);
      delayMicroseconds(10);  // Allow variation
    }
    
    float raw = (float)sum / _entropyConfig.samplesPerReading;
    float normalized = raw / 4095.0;  // ESP32 has 12-bit ADC
    
    // Optionally mix with WiFi RF noise
    if (_entropyConfig.useRF && WiFi.status() == WL_CONNECTED) {
      int32_t rssi = WiFi.RSSI();
      // RSSI typically -30 to -90 dBm, normalize to [0, 1]
      float rfNoise = ((float)rssi + 90.0) / 60.0;
      rfNoise = constrain(rfNoise, 0.0, 1.0);
      // Mix: 70% physical pin, 30% RF
      normalized = normalized * 0.7 + rfNoise * 0.3;
    }
    
    _lastEntropyReading = normalized;
    return normalized;
  }
  
  /**
   * Updates the reservoir with hardware entropy influence.
   * 
   * The output emerges from the combination of:
   * - Mathematical structure (reservoir weights)
   * - Physical environment (electromagnetic noise)
   * 
   * @param input Sensor data input
   * @return New reservoir state
   */
  int16_t updateWithEntropyInfluence(int16_t input) {
    // 1. Read environmental noise
    float entropy = readEnvironmentNoise();
    
    // 2. Convert to Q8.8 (-128 to 127 range, centered at 0)
    int16_t entropyQ8 = (int16_t)((entropy - 0.5) * 256.0 * _entropyConfig.influenceWeight);
    
    // 3. Mix input with entropy influence
    int32_t influencedInput = (int32_t)input + entropyQ8;
    influencedInput = constrain(influencedInput, -32768, 32767);
    
    // 4. Update reservoir with influenced input
    return this->update((int16_t)influencedInput);
  }
  
  /**
   * Gets the last entropy reading.
   * @return Value [0.0, 1.0] of the last reading
   */
  float getLastEntropyReading() { return _lastEntropyReading; }
  
  /**
   * Generates a byte of true hardware entropy.
   * 
   * Useful for seed initialization or generation of
   * real cryptographic keys from physical randomness.
   * 
   * @return Byte of pure hardware entropy
   */
  uint8_t generateTrueEntropyByte() {
    uint8_t entropy = 0;
    for (int bit = 0; bit < 8; bit++) {
      // Read two samples and compare (Von Neumann extractor)
      uint16_t a = analogRead(_entropyConfig.entropyPin);
      delayMicroseconds(50);
      uint16_t b = analogRead(_entropyConfig.entropyPin);
      
      if (a != b) {
        // Valid bit
        if (a > b) {
          entropy |= (1 << bit);
        }
        // If a < b, bit = 0 (already 0)
      } else {
        // Retry this bit
        bit--;
      }
    }
    return entropy;
  }
  
  /**
   * Generates a 32-bit hardware entropy seed.
   * 
   * This seed comes directly from the physical environment,
   * not from a pseudo-random generator. It provides a true
   * coordinate in the mathematical space.
   * 
   * @return 32-bit hardware entropy seed
   */
  uint32_t discoverHardwareSeed() {
    uint32_t seed = 0;
    for (int i = 0; i < 4; i++) {
      seed |= ((uint32_t)generateTrueEntropyByte() << (i * 8));
    }
    return seed;
  }

  // =========================================================================
  // TASK AFFINITY SYSTEM (Node Specialization)
  // =========================================================================

  /**
   * Calculates the normalized specialization vector.
   * 
   * Returns the "affinity strength" toward each domain.
   * 
   * @param affinityVector Output array [DOMAIN_COUNT] with values 0-255
   */
  void calculateSpecializationVector(uint8_t *affinityVector) {
    uint32_t total = 0;
    uint16_t rawAffinity[DOMAIN_COUNT];
    
    // Calculate raw affinity per domain
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      // Normalized experience (processing / total)
      uint16_t totalProcessing = 0;
      for (int j = 0; j < DOMAIN_COUNT; j++) {
        totalProcessing += _spec.processingCount[j];
      }
      uint8_t experience = (totalProcessing > 0) 
        ? (_spec.processingCount[i] * 255 / totalProcessing) 
        : 0;
      
      // Affinity = base_affinity * (1 + experience/256)
      rawAffinity[i] = (uint16_t)_spec.affinity[i] * (256 + experience) / 256;
      total += rawAffinity[i];
    }
    
    // Normalize to 0-255
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      affinityVector[i] = (total > 0) ? (rawAffinity[i] * 255 / total) : 0;
    }
  }

  /**
   * Evaluates the cost of processing a task in a specific domain.
   * 
   * @param domain Requested domain
   * @return TaskDecision indicating whether to accept/reject
   */
  TaskDecision evaluateTaskCost(DataDomain domain) {
    uint8_t affinity = _spec.affinity[domain];
    
    if (affinity >= _spec.highCostThreshold) {
      return (affinity >= 200) ? DECISION_ACCEPT : DECISION_HIGH_PRIORITY;
    } else if (affinity >= _spec.rejectionThreshold) {
      return DECISION_LOW_PRIORITY;
    }
    return DECISION_REJECT;
  }

  /**
   * Should this node accept this task?
   * 
   * Implements node specialization: nodes perform best in their
   * native domain and reject tasks outside their expertise.
   * 
   * @param domain Domain of the requested task
   * @return true if should accept
   */
  bool shouldAcceptTask(DataDomain domain) {
    return evaluateTaskCost(domain) != DECISION_REJECT;
  }

  /**
   * Records data processing, updating the specialization vector.
   * 
   * @param domain Processed domain
   * @param mse_q8 Mean squared error (Q8.8)
   */
  void recordProcessing(DataDomain domain, int16_t mse_q8) {
    // Increment counter
    if (_spec.processingCount[domain] < 65535) {
      _spec.processingCount[domain]++;
    }
    
    // Update affinity based on success
    // mse_q8 is in Q8.8, so 0x100 = 1.0
    if (mse_q8 < 0x1A) {  // < 0.1 - very successful
      if (_spec.affinity[domain] < 250) {
        _spec.affinity[domain] += 5;
      }
    } else if (mse_q8 < 0x4D) {  // < 0.3 - acceptable
      if (_spec.affinity[domain] < 253) {
        _spec.affinity[domain] += 2;
      }
    } else if (mse_q8 > 0xB3) {  // > 0.7 - poor
      if (_spec.affinity[domain] > 3) {
        _spec.affinity[domain] -= 3;
      }
    }
    
    // Increase inertia with experience
    uint32_t totalExp = 0;
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      totalExp += _spec.processingCount[i];
    }
    _spec.inertia = min(243, (uint8_t)(128 + totalExp / 4));
  }

  /**
   * Gets the node's specialization domain.
   * 
   * @param level Pointer to store specialization level (0-255)
   * @return DataDomain of specialization
   */
  DataDomain getSpecialization(uint8_t *level) {
    uint8_t maxAffinity = 0;
    DataDomain specialized = _spec.genesisDomain;
    
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      if (_spec.affinity[i] > maxAffinity) {
        maxAffinity = _spec.affinity[i];
        specialized = (DataDomain)i;
      }
    }
    
    if (level) *level = maxAffinity;
    return specialized;
  }

  /**
   * Exports the specialization vector for sync (4 bytes compressed)
   * 
   * @param buffer Output buffer (minimum 4 bytes)
   * @return Bytes written
   */
  size_t exportSpecializationCompressed(uint8_t *buffer) {
    // Byte 0: Genesis domain (4 bits) + inertia high (4 bits)
    buffer[0] = (_spec.genesisDomain & 0x0F) | ((_spec.inertia >> 4) << 4);
    
    // Byte 1-2: Top 2 affinities encoded
    uint8_t level;
    DataDomain spec1 = getSpecialization(&level);
    buffer[1] = (spec1 & 0x0F) | ((level >> 4) << 4);
    
    // Byte 2: Second highest affinity domain + level
    uint8_t secondMax = 0;
    DataDomain spec2 = DOMAIN_GENERIC;
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      if ((DataDomain)i != spec1 && _spec.affinity[i] > secondMax) {
        secondMax = _spec.affinity[i];
        spec2 = (DataDomain)i;
      }
    }
    buffer[2] = (spec2 & 0x0F) | ((secondMax >> 4) << 4);
    
    // Byte 3: Checksum
    buffer[3] = buffer[0] ^ buffer[1] ^ buffer[2];
    
    return 4;
  }

  /**
   * Gets the node specialization state
   */
  SpecializationVector* getSpecializationVector() { return &_spec; }

  // Backward-compatibility aliases
  SpecializationVector* getTrueWill() { return &_spec; }
  void calculateTrueWillVector(uint8_t *affinityVector) { calculateSpecializationVector(affinityVector); }
  size_t exportWillCompressed(uint8_t *buffer) { return exportSpecializationCompressed(buffer); }

  // =========================================================================
  // NETWORK FUNCTIONS
  // =========================================================================

  /**
   * Send prediction to server
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
   * Get compressed weights (for sending to other nodes)
   * Protocol: 1-Bit Weight Exchange
   * Returns size in bytes
   */
  size_t getCompressedWeights(uint8_t *buffer, size_t bufferSize) {
    size_t needed = (this->_size + 7) / 8;
    if (bufferSize < needed)
      return 0;

    _quantizeWOut(buffer);
    return needed;
  }

  /**
   * Sync weights from another node (for Collective Mind)
   * Protocol: 1-Bit Weight Exchange
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
   * Get unique chip ID
   */
  String getChipId() { return String((uint32_t)ESP.getEfuseMac(), HEX); }

private:
  // Node Specialization Vector
  SpecializationVector _spec;
  
  // Hardware Entropy Source config
  EntropyConfig _entropyConfig;
  float _lastEntropyReading = 0.0;

  /**
   * Initializes the task affinity system
   */
  void _initSpecialization(DataDomain genesisDomain) {
    _spec.genesisDomain = genesisDomain;
    _spec.inertia = 128;  // 50% initial
    _spec.rejectionThreshold = 77;   // ~30%
    _spec.highCostThreshold = 128;   // ~50%
    
    // Initialize affinities
    for (int i = 0; i < DOMAIN_COUNT; i++) {
      _spec.affinity[i] = 26;  // ~10% base
      _spec.processingCount[i] = 0;
    }
    
    // Genesis domain starts with maximum affinity
    _spec.affinity[genesisDomain] = 255;
    _spec.processingCount[genesisDomain] = 1;
  }
  
  /**
   * Initializes the hardware entropy source with defaults
   */
  void _initEntropy() {
    _entropyConfig.entropyPin = 36;        // VP (GPIO36) - sensitive pin
    _entropyConfig.influenceWeight = 0.1;   // 10% entropy influence
    _entropyConfig.samplesPerReading = 8;   // 8 samples average
    _entropyConfig.useRF = true;            // Use WiFi noise too
    
    pinMode(_entropyConfig.entropyPin, INPUT);
  }

  /**
   * Decompresses 1-bit weights and updates W_out locally
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
   * Compresses W_out to 1-bit per weight
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
