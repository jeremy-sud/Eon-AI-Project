/**
 * Eón ESP32 + LoRa - Protocolo 1-Bit
 * ==================================
 * 
 * Demo de transmisión LoRa del Protocolo 1-Bit entre nodos ESP32.
 * Ideal para redes de sensores IoT con conectividad limitada.
 * 
 * Hardware requerido:
 * - ESP32 con módulo LoRa (SX1276/SX1278)
 * - Ej: TTGO LoRa32, Heltec WiFi LoRa 32
 * 
 * Librerías requeridas:
 * - LoRa by Sandeep Mistry
 * - ArduinoJson
 * 
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#include <SPI.h>
#include <LoRa.h>
#include <ArduinoJson.h>

// ==============================================================
// CONFIGURACIÓN HARDWARE
// ==============================================================

// Pines LoRa (ajustar según placa)
// TTGO LoRa32 V1
#define LORA_SCK  5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_SS   18
#define LORA_RST  14
#define LORA_DIO0 26

// Heltec WiFi LoRa 32 (descomentar si usa esta placa)
// #define LORA_SCK  5
// #define LORA_MISO 19
// #define LORA_MOSI 27
// #define LORA_SS   18
// #define LORA_RST  23
// #define LORA_DIO0 26

// Frecuencia LoRa (ajustar según región)
// 433E6 para Asia
// 868E6 para Europa
// 915E6 para América
#define LORA_FREQ 915E6

// ==============================================================
// PROTOCOLO 1-BIT
// ==============================================================

// Tipos de paquete
#define PKT_SYNC   1  // Sincronización de pesos
#define PKT_REQ    2  // Solicitud de pesos
#define PKT_ACK    3  // Confirmación
#define PKT_PING   4  // Heartbeat
#define PKT_STATUS 5  // Estado del nodo

// Tamaño máximo de payload LoRa
#define MAX_PAYLOAD 255

// ==============================================================
// EON CORE - Reservoir Ultraligero
// ==============================================================

#define RESERVOIR_SIZE 32  // Mantener pequeño para LoRa

class AeonLoRa {
private:
    // Reservoir state (Q8.8 fixed-point)
    int16_t state[RESERVOIR_SIZE];
    int16_t W_in[RESERVOIR_SIZE];
    int16_t W_out[RESERVOIR_SIZE];
    uint32_t seed;
    
    // Estadísticas
    uint32_t samplesLearned;
    uint32_t syncsSent;
    uint32_t syncsReceived;
    
    // PRNG xorshift32
    uint32_t xorshift32() {
        seed ^= seed << 13;
        seed ^= seed >> 17;
        seed ^= seed << 5;
        return seed;
    }
    
    // Conversión Q8.8
    int16_t floatToQ8(float x) {
        return (int16_t)(x * 256.0f);
    }
    
    float q8ToFloat(int16_t x) {
        return x / 256.0f;
    }
    
    // tanh aproximado (Padé)
    int16_t tanhQ8(int16_t x) {
        // tanh(x) ≈ x / (1 + |x|/2) para pequeños
        int32_t absX = (x < 0) ? -x : x;
        int32_t denom = 256 + (absX >> 1);  // 1 + |x|/2 en Q8.8
        return (int16_t)((int32_t)x * 256 / denom);
    }
    
public:
    char nodeId[13];  // 12 chars + null
    
    AeonLoRa(uint32_t nodeSeed = 12345) {
        seed = nodeSeed;
        samplesLearned = 0;
        syncsSent = 0;
        syncsReceived = 0;
        
        // Generar ID único
        snprintf(nodeId, sizeof(nodeId), "%08X", nodeSeed);
        
        // Inicializar pesos
        for (int i = 0; i < RESERVOIR_SIZE; i++) {
            state[i] = 0;
            W_in[i] = (int16_t)((xorshift32() % 512) - 256);  // [-1, 1] en Q8.8
            W_out[i] = 0;
        }
    }
    
    // Actualizar estado del reservoir
    void update(float input) {
        int16_t inQ8 = floatToQ8(input);
        
        for (int i = 0; i < RESERVOIR_SIZE; i++) {
            // state[i] = tanh(W_in[i] * input + leak * state[i])
            int32_t activation = ((int32_t)W_in[i] * inQ8) >> 8;
            activation += ((int32_t)state[i] * 230) >> 8;  // leak = 0.9
            state[i] = tanhQ8((int16_t)activation);
        }
        
        samplesLearned++;
    }
    
    // Predecir siguiente valor
    float predict() {
        int32_t output = 0;
        for (int i = 0; i < RESERVOIR_SIZE; i++) {
            output += ((int32_t)W_out[i] * state[i]) >> 8;
        }
        return q8ToFloat((int16_t)output);
    }
    
    // ==============================================================
    // PROTOCOLO 1-BIT - Exportación
    // ==============================================================
    
    /**
     * Exportar pesos en formato 1-bit binario.
     * 
     * Formato del paquete:
     *   Byte 0-2:   Magic "EON" (3 bytes)
     *   Byte 3:     Type (1=SYNC)
     *   Byte 4-7:   Seed (uint32)
     *   Byte 8:     Count (uint8) - número de pesos
     *   Byte 9+:    Bits empaquetados (ceil(count/8) bytes)
     * 
     * @param buffer Buffer de salida
     * @param bufferSize Tamaño máximo del buffer
     * @return Tamaño del paquete en bytes
     */
    size_t exportWeights1Bit(uint8_t* buffer, size_t bufferSize) {
        size_t headerSize = 9;  // Magic(3) + Type(1) + Seed(4) + Count(1)
        size_t bitsSize = (RESERVOIR_SIZE + 7) / 8;
        size_t totalSize = headerSize + bitsSize;
        
        if (bufferSize < totalSize) return 0;
        
        // Header
        buffer[0] = 'E';
        buffer[1] = 'O';
        buffer[2] = 'N';
        buffer[3] = PKT_SYNC;
        
        // Seed (big-endian)
        buffer[4] = (seed >> 24) & 0xFF;
        buffer[5] = (seed >> 16) & 0xFF;
        buffer[6] = (seed >> 8) & 0xFF;
        buffer[7] = seed & 0xFF;
        
        // Count
        buffer[8] = RESERVOIR_SIZE;
        
        // Bits empaquetados (signo de W_out)
        memset(buffer + 9, 0, bitsSize);
        for (int i = 0; i < RESERVOIR_SIZE; i++) {
            if (W_out[i] >= 0) {
                buffer[9 + i/8] |= (1 << (7 - (i % 8)));
            }
        }
        
        syncsSent++;
        return totalSize;
    }
    
    // ==============================================================
    // PROTOCOLO 1-BIT - Importación
    // ==============================================================
    
    /**
     * Importar pesos desde paquete 1-bit.
     * 
     * @param buffer Buffer con paquete recibido
     * @param length Tamaño del buffer
     * @return true si la importación fue exitosa
     */
    bool importWeights1Bit(const uint8_t* buffer, size_t length) {
        // Verificar tamaño mínimo
        if (length < 10) return false;
        
        // Verificar magic
        if (buffer[0] != 'E' || buffer[1] != 'O' || buffer[2] != 'N') {
            return false;
        }
        
        // Verificar tipo
        if (buffer[3] != PKT_SYNC) return false;
        
        // Leer seed del remitente
        uint32_t remoteSeed = ((uint32_t)buffer[4] << 24) |
                              ((uint32_t)buffer[5] << 16) |
                              ((uint32_t)buffer[6] << 8) |
                              buffer[7];
        
        // Leer count
        uint8_t count = buffer[8];
        if (count != RESERVOIR_SIZE) {
            Serial.printf("⚠ Tamaño incompatible: %d vs %d\n", count, RESERVOIR_SIZE);
            return false;
        }
        
        // Desempaquetar bits
        int16_t remoteWeights[RESERVOIR_SIZE];
        int16_t scale = 128;  // 0.5 en Q8.8
        
        for (int i = 0; i < RESERVOIR_SIZE; i++) {
            uint8_t byteIdx = 9 + i / 8;
            uint8_t bitIdx = 7 - (i % 8);
            bool sign = (buffer[byteIdx] >> bitIdx) & 1;
            
            remoteWeights[i] = sign ? scale : -scale;
        }
        
        // Fusionar con pesos locales (promedio)
        for (int i = 0; i < RESERVOIR_SIZE; i++) {
            W_out[i] = (W_out[i] + remoteWeights[i]) / 2;
        }
        
        syncsReceived++;
        return true;
    }
    
    // ==============================================================
    // LORA TRANSMISIÓN
    // ==============================================================
    
    /**
     * Transmitir pesos por LoRa.
     * @return true si la transmisión fue exitosa
     */
    bool transmitWeights() {
        uint8_t buffer[MAX_PAYLOAD];
        size_t len = exportWeights1Bit(buffer, sizeof(buffer));
        
        if (len == 0) {
            Serial.println("✗ Error exportando pesos");
            return false;
        }
        
        LoRa.beginPacket();
        LoRa.write(buffer, len);
        int result = LoRa.endPacket();
        
        if (result) {
            Serial.printf("📤 [%s] TX: %d bytes (compresión %.1fx)\n", 
                          nodeId, len, (float)(RESERVOIR_SIZE * 2) / len);
            return true;
        } else {
            Serial.println("✗ Error transmitiendo");
            return false;
        }
    }
    
    /**
     * Procesar paquete LoRa recibido.
     * @param buffer Buffer con datos recibidos
     * @param length Tamaño del buffer
     * @return true si se procesó correctamente
     */
    bool processReceived(const uint8_t* buffer, size_t length) {
        if (importWeights1Bit(buffer, length)) {
            Serial.printf("📥 [%s] RX: %d bytes sincronizados\n", nodeId, length);
            return true;
        }
        return false;
    }
    
    // ==============================================================
    // ESTADÍSTICAS
    // ==============================================================
    
    void printStats() {
        Serial.println("\n=== ESTADÍSTICAS EON ===");
        Serial.printf("Node ID:        %s\n", nodeId);
        Serial.printf("Reservoir:      %d neuronas\n", RESERVOIR_SIZE);
        Serial.printf("Muestras:       %lu\n", samplesLearned);
        Serial.printf("Syncs enviados: %lu\n", syncsSent);
        Serial.printf("Syncs recibidos:%lu\n", syncsReceived);
        Serial.printf("Memoria:        %d bytes\n", sizeof(*this));
        Serial.println("========================\n");
    }
    
    uint32_t getSamplesLearned() { return samplesLearned; }
    uint32_t getSyncsSent() { return syncsSent; }
    uint32_t getSyncsReceived() { return syncsReceived; }
};

// ==============================================================
// INSTANCIA GLOBAL
// ==============================================================

AeonLoRa aeon((uint32_t)ESP.getEfuseMac());

// ==============================================================
// SETUP
// ==============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial);
    
    Serial.println();
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║  EON ESP32 + LORA - PROTOCOLO 1-BIT    ║");
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println();
    
    // Inicializar SPI con pines personalizados
    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
    
    // Inicializar LoRa
    LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
    
    if (!LoRa.begin(LORA_FREQ)) {
        Serial.println("✗ Error inicializando LoRa");
        while (1);
    }
    
    // Configurar LoRa para máximo rango
    LoRa.setSpreadingFactor(10);      // SF7-SF12, mayor = más rango
    LoRa.setSignalBandwidth(125E3);   // 125kHz estándar
    LoRa.setCodingRate4(5);           // 4/5 coding rate
    LoRa.setTxPower(20);              // Máxima potencia (20dBm)
    
    Serial.printf("✓ LoRa inicializado @ %.2f MHz\n", LORA_FREQ / 1E6);
    Serial.printf("✓ Node ID: %s\n", aeon.nodeId);
    Serial.println();
    Serial.println("Comandos disponibles:");
    Serial.println("  't' - Transmitir pesos");
    Serial.println("  's' - Mostrar estadísticas");
    Serial.println("  'f' - Alimentar valor (0-100)");
    Serial.println();
    Serial.println("Esperando paquetes...\n");
}

// ==============================================================
// LOOP
// ==============================================================

unsigned long lastTx = 0;
unsigned long txInterval = 30000;  // Transmitir cada 30 segundos

void loop() {
    // Procesar comandos Serial
    if (Serial.available()) {
        char cmd = Serial.read();
        
        switch (cmd) {
            case 't':
            case 'T':
                aeon.transmitWeights();
                break;
                
            case 's':
            case 'S':
                aeon.printStats();
                break;
                
            case 'f':
            case 'F':
                // Alimentar valor de sensor simulado
                {
                    float value = random(0, 100) / 100.0f;
                    aeon.update(value);
                    float pred = aeon.predict();
                    Serial.printf("Feed: %.2f -> Predicción: %.2f\n", value, pred);
                }
                break;
        }
    }
    
    // Recibir paquetes LoRa
    int packetSize = LoRa.parsePacket();
    if (packetSize > 0) {
        uint8_t buffer[MAX_PAYLOAD];
        int len = 0;
        
        while (LoRa.available() && len < MAX_PAYLOAD) {
            buffer[len++] = LoRa.read();
        }
        
        Serial.printf("📶 Paquete recibido: %d bytes, RSSI: %d\n", 
                      len, LoRa.packetRssi());
        
        aeon.processReceived(buffer, len);
    }
    
    // Transmisión periódica automática
    if (millis() - lastTx > txInterval) {
        lastTx = millis();
        
        // Alimentar con valor de sensor (simulado)
        float sensorValue = analogRead(34) / 4095.0f;  // GPIO34 como ADC
        aeon.update(sensorValue);
        
        // Transmitir si hay suficientes muestras
        if (aeon.getSamplesLearned() >= 10) {
            aeon.transmitWeights();
        }
    }
}
