/**
 * Eón ESP32 - Métricas de Energía
 * ================================
 * 
 * Programa para medir el consumo energético del Protocolo 1-Bit sobre LoRa.
 * Mide consumo en diferentes estados: idle, TX, RX, deep sleep.
 * 
 * Hardware recomendado:
 * - ESP32 con módulo LoRa (TTGO LoRa32, Heltec, etc.)
 * - INA219 o INA3221 para medición de corriente (opcional)
 * - Batería LiPo 3.7V con capacidad conocida
 * 
 * Métricas calculadas:
 * - Consumo por transmisión (mJ)
 * - Duración estimada de batería
 * - Comparativa JSON vs 1-Bit
 * 
 * (c) 2024 SenseLab - Build with Sense
 */

#include <SPI.h>
#include <LoRa.h>
#include <esp_sleep.h>
#include <driver/adc.h>
#include <esp_adc_cal.h>

// ==============================================================
// CONFIGURACIÓN HARDWARE
// ==============================================================

// TTGO LoRa32 V1
#define LORA_SCK  5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_SS   18
#define LORA_RST  14
#define LORA_DIO0 26

// Pin de batería (ADC)
#define VBAT_PIN  35
#define VBAT_DIV  2.0  // Divisor resistivo

// LED indicador
#define LED_PIN   25

// Frecuencia LoRa
#define LORA_FREQ 915E6

// ==============================================================
// CONSTANTES DE CONSUMO (valores típicos ESP32 + LoRa)
// ==============================================================

// Corrientes típicas (mA) - ajustar según hardware real
const float CURRENT_IDLE = 10.0;       // ESP32 idle con WiFi/BT off
const float CURRENT_TX_LORA = 120.0;   // Transmitiendo LoRa @ 20dBm
const float CURRENT_RX_LORA = 15.0;    // Recibiendo LoRa
const float CURRENT_DEEP_SLEEP = 0.01; // Deep sleep
const float CURRENT_CPU_ACTIVE = 50.0; // CPU procesando

// Voltaje nominal batería LiPo
const float BATTERY_VOLTAGE = 3.7;

// Capacidades de batería comunes (mAh)
const float BATTERY_CAPACITY_500 = 500;
const float BATTERY_CAPACITY_1000 = 1000;
const float BATTERY_CAPACITY_3000 = 3000;

// ==============================================================
// PARÁMETROS DEL PROTOCOLO 1-BIT
// ==============================================================

#define RESERVOIR_SIZE 50
#define HEADER_SIZE 14

// Tamaño paquete 1-bit: header + ceil(50/8) = 14 + 7 = 21 bytes
#define PACKET_SIZE_1BIT (HEADER_SIZE + ((RESERVOIR_SIZE + 7) / 8))

// Tamaño equivalente en JSON: ~150-200 bytes para 50 floats
#define PACKET_SIZE_JSON 175

// ==============================================================
// ESTRUCTURAS DE DATOS
// ==============================================================

struct EnergyMeasurement {
    String operation;
    float durationMs;
    float currentMa;
    float energyMj;      // milijoules
    uint32_t bytes;
    float mjPerByte;
};

struct BatteryEstimate {
    float capacityMah;
    float hoursIdle;
    float txCount500mah;
    float txCount1000mah;
    float txCount3000mah;
};

// ==============================================================
// VARIABLES GLOBALES
// ==============================================================

EnergyMeasurement measurements[10];
int measurementCount = 0;

esp_adc_cal_characteristics_t adc_chars;
float batteryVoltage = 0;

// Tiempo de aire LoRa (calculado)
float timeOnAirMs_1bit = 0;
float timeOnAirMs_json = 0;

// ==============================================================
// FUNCIONES DE MEDICIÓN DE BATERÍA
// ==============================================================

void initBatteryADC() {
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC1_CHANNEL_7, ADC_ATTEN_DB_12);  // GPIO35
    esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_12, ADC_WIDTH_BIT_12, 
                             1100, &adc_chars);
}

float readBatteryVoltage() {
    uint32_t adc_reading = 0;
    // Multisampling para reducir ruido
    for (int i = 0; i < 16; i++) {
        adc_reading += adc1_get_raw(ADC1_CHANNEL_7);
    }
    adc_reading /= 16;
    
    uint32_t voltage = esp_adc_cal_raw_to_voltage(adc_reading, &adc_chars);
    return (voltage * VBAT_DIV) / 1000.0;  // Convertir a voltios
}

float batteryPercentage(float voltage) {
    // Aproximación lineal para LiPo 3.7V
    // 4.2V = 100%, 3.0V = 0%
    float percentage = (voltage - 3.0) / (4.2 - 3.0) * 100.0;
    return constrain(percentage, 0, 100);
}

// ==============================================================
// CÁLCULO DE TIEMPO DE AIRE LORA
// ==============================================================

float calculateTimeOnAir(int payloadBytes, int sf, float bw) {
    // Fórmula del tiempo de aire LoRa
    // Basado en la especificación Semtech SX1276/77/78/79
    
    int preambleSymbols = 8;  // Estándar
    bool explicitHeader = true;
    bool crcEnabled = true;
    int codingRate = 5;  // 4/5
    
    // Tiempo de símbolo
    float symbolTime = pow(2, sf) / bw * 1000;  // ms
    
    // Preámbulo
    float preambleTime = (preambleSymbols + 4.25) * symbolTime;
    
    // Payload
    int payloadSymbols;
    bool lowDataRateOptimize = (sf >= 11);
    
    float h = explicitHeader ? 0 : 1;
    float de = lowDataRateOptimize ? 1 : 0;
    
    int payload = 8 + max((int)ceil((8.0 * payloadBytes - 4.0 * sf + 28 + 
                                     16 * (crcEnabled ? 1 : 0) - 
                                     20 * h) / (4.0 * (sf - 2 * de))) * 
                          (codingRate), 0);
    
    float payloadTime = payload * symbolTime;
    
    return preambleTime + payloadTime;
}

// ==============================================================
// MEDICIÓN DE OPERACIONES
// ==============================================================

void measureOperation(const char* name, int packetSize, void (*operation)()) {
    unsigned long startTime = micros();
    
    operation();
    
    unsigned long endTime = micros();
    float durationMs = (endTime - startTime) / 1000.0;
    
    // Añadir tiempo de aire LoRa
    float toaMs = calculateTimeOnAir(packetSize, 10, 125000);
    float totalDurationMs = durationMs + toaMs;
    
    // Calcular energía
    float avgCurrent = (CURRENT_CPU_ACTIVE + CURRENT_TX_LORA) / 2;
    float energyMj = (avgCurrent / 1000.0) * BATTERY_VOLTAGE * totalDurationMs;
    
    // Guardar medición
    measurements[measurementCount].operation = name;
    measurements[measurementCount].durationMs = totalDurationMs;
    measurements[measurementCount].currentMa = avgCurrent;
    measurements[measurementCount].energyMj = energyMj;
    measurements[measurementCount].bytes = packetSize;
    measurements[measurementCount].mjPerByte = energyMj / packetSize;
    measurementCount++;
}

// ==============================================================
// OPERACIONES DE PRUEBA
// ==============================================================

void testTx1Bit() {
    uint8_t packet[PACKET_SIZE_1BIT];
    
    // Llenar paquete con datos de prueba
    packet[0] = 'E';
    packet[1] = 'O';
    packet[2] = 'N';
    packet[3] = 1;  // SYNC
    for (int i = 4; i < PACKET_SIZE_1BIT; i++) {
        packet[i] = random(256);
    }
    
    // Transmitir
    LoRa.beginPacket();
    LoRa.write(packet, PACKET_SIZE_1BIT);
    LoRa.endPacket();
}

void testTxJSON() {
    // Simular paquete JSON más grande
    char jsonPacket[PACKET_SIZE_JSON];
    
    // Construir JSON simulado
    snprintf(jsonPacket, sizeof(jsonPacket),
             "{\"t\":\"sync\",\"id\":\"ESP-%08X\",\"ts\":%lu,\"w\":[0.1,0.2,0.3,0.4,0.5,"
             "0.6,0.7,0.8,0.9,1.0,-0.1,-0.2,-0.3,-0.4,-0.5,-0.6,-0.7,-0.8,-0.9,-1.0,"
             "0.11,0.22,0.33,0.44,0.55]}",
             (uint32_t)ESP.getEfuseMac(), millis());
    
    // Transmitir
    LoRa.beginPacket();
    LoRa.write((uint8_t*)jsonPacket, PACKET_SIZE_JSON);
    LoRa.endPacket();
}

// ==============================================================
// ESTIMACIÓN DE BATERÍA
// ==============================================================

BatteryEstimate calculateBatteryLife(float energyPerTxMj, float txIntervalMs) {
    BatteryEstimate est;
    
    // Energía de batería (mWh -> mJ)
    float batteryEnergy500 = BATTERY_CAPACITY_500 * BATTERY_VOLTAGE * 3600;   // mJ
    float batteryEnergy1000 = BATTERY_CAPACITY_1000 * BATTERY_VOLTAGE * 3600;
    float batteryEnergy3000 = BATTERY_CAPACITY_3000 * BATTERY_VOLTAGE * 3600;
    
    // Consumo idle entre transmisiones
    float idleEnergyPerCycle = (CURRENT_IDLE / 1000.0) * BATTERY_VOLTAGE * txIntervalMs;
    
    // Energía total por ciclo
    float energyPerCycle = energyPerTxMj + idleEnergyPerCycle;
    
    // Número de transmisiones
    est.txCount500mah = batteryEnergy500 / energyPerCycle;
    est.txCount1000mah = batteryEnergy1000 / energyPerCycle;
    est.txCount3000mah = batteryEnergy3000 / energyPerCycle;
    
    // Horas en idle puro
    est.hoursIdle = BATTERY_CAPACITY_1000 / CURRENT_IDLE;
    
    return est;
}

// ==============================================================
// REPORTE DE RESULTADOS
// ==============================================================

void printEnergyReport() {
    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════════════════╗");
    Serial.println("║          EON - REPORTE DE MÉTRICAS DE ENERGÍA                    ║");
    Serial.println("╚══════════════════════════════════════════════════════════════════╝");
    Serial.println();
    
    // Estado de batería actual
    batteryVoltage = readBatteryVoltage();
    Serial.println("📊 ESTADO DE BATERÍA");
    Serial.println("────────────────────────────────────────────────────────────────────");
    Serial.printf("   Voltaje: %.2f V\n", batteryVoltage);
    Serial.printf("   Nivel: %.0f%%\n", batteryPercentage(batteryVoltage));
    Serial.println();
    
    // Tiempos de aire calculados
    timeOnAirMs_1bit = calculateTimeOnAir(PACKET_SIZE_1BIT, 10, 125000);
    timeOnAirMs_json = calculateTimeOnAir(PACKET_SIZE_JSON, 10, 125000);
    
    Serial.println("📡 TIEMPO DE AIRE LORA (SF10, 125kHz)");
    Serial.println("────────────────────────────────────────────────────────────────────");
    Serial.printf("   Paquete 1-Bit (%d bytes):  %.1f ms\n", PACKET_SIZE_1BIT, timeOnAirMs_1bit);
    Serial.printf("   Paquete JSON  (%d bytes): %.1f ms\n", PACKET_SIZE_JSON, timeOnAirMs_json);
    Serial.printf("   Ahorro tiempo de aire: %.1f%%\n", 
                  (1.0 - timeOnAirMs_1bit / timeOnAirMs_json) * 100);
    Serial.println();
    
    // Mediciones de operaciones
    Serial.println("⚡ CONSUMO POR OPERACIÓN");
    Serial.println("────────────────────────────────────────────────────────────────────");
    Serial.println("   Operación            | Duración | Corriente | Energía | mJ/byte");
    Serial.println("   ---------------------|----------|-----------|---------|--------");
    
    for (int i = 0; i < measurementCount; i++) {
        Serial.printf("   %-20s | %6.1f ms| %5.1f mA  | %5.2f mJ| %.4f\n",
                      measurements[i].operation.c_str(),
                      measurements[i].durationMs,
                      measurements[i].currentMa,
                      measurements[i].energyMj,
                      measurements[i].mjPerByte);
    }
    Serial.println();
    
    // Comparativa 1-Bit vs JSON
    if (measurementCount >= 2) {
        float savings = (1.0 - measurements[0].energyMj / measurements[1].energyMj) * 100;
        
        Serial.println("🔋 COMPARATIVA PROTOCOLO 1-BIT vs JSON");
        Serial.println("────────────────────────────────────────────────────────────────────");
        Serial.printf("   Tamaño 1-Bit: %d bytes\n", PACKET_SIZE_1BIT);
        Serial.printf("   Tamaño JSON:  %d bytes\n", PACKET_SIZE_JSON);
        Serial.printf("   Compresión:   %.1fx\n", (float)PACKET_SIZE_JSON / PACKET_SIZE_1BIT);
        Serial.println();
        Serial.printf("   Energía 1-Bit: %.2f mJ/tx\n", measurements[0].energyMj);
        Serial.printf("   Energía JSON:  %.2f mJ/tx\n", measurements[1].energyMj);
        Serial.printf("   Ahorro energía: %.1f%%\n", savings);
        Serial.println();
    }
    
    // Estimación de vida de batería
    Serial.println("🔋 ESTIMACIÓN VIDA DE BATERÍA (TX cada 30s)");
    Serial.println("────────────────────────────────────────────────────────────────────");
    
    if (measurementCount >= 2) {
        BatteryEstimate est1bit = calculateBatteryLife(measurements[0].energyMj, 30000);
        BatteryEstimate estJson = calculateBatteryLife(measurements[1].energyMj, 30000);
        
        Serial.println("   Capacidad     | TX 1-Bit      | TX JSON       | Mejora");
        Serial.println("   --------------|---------------|---------------|-------");
        Serial.printf("   500 mAh       | %10.0f tx | %10.0f tx | %.1fx\n",
                      est1bit.txCount500mah, estJson.txCount500mah,
                      est1bit.txCount500mah / estJson.txCount500mah);
        Serial.printf("   1000 mAh      | %10.0f tx | %10.0f tx | %.1fx\n",
                      est1bit.txCount1000mah, estJson.txCount1000mah,
                      est1bit.txCount1000mah / estJson.txCount1000mah);
        Serial.printf("   3000 mAh      | %10.0f tx | %10.0f tx | %.1fx\n",
                      est1bit.txCount3000mah, estJson.txCount3000mah,
                      est1bit.txCount3000mah / estJson.txCount3000mah);
        Serial.println();
        
        // Convertir a días
        float days1bit = est1bit.txCount1000mah * 30.0 / 3600 / 24;
        float daysJson = estJson.txCount1000mah * 30.0 / 3600 / 24;
        
        Serial.println("   Con batería 1000mAh y TX cada 30s:");
        Serial.printf("   - Protocolo 1-Bit: %.1f días\n", days1bit);
        Serial.printf("   - Protocolo JSON:  %.1f días\n", daysJson);
        Serial.printf("   - Días adicionales con 1-Bit: %.1f\n", days1bit - daysJson);
    }
    
    Serial.println();
    Serial.println("════════════════════════════════════════════════════════════════════");
    Serial.println();
}

// ==============================================================
// CONSUMO EN DIFERENTES MODOS
// ==============================================================

void printPowerModes() {
    Serial.println();
    Serial.println("💡 CONSUMO EN DIFERENTES MODOS");
    Serial.println("────────────────────────────────────────────────────────────────────");
    Serial.printf("   Deep Sleep:      %.2f mA (%.2f mW)\n", 
                  CURRENT_DEEP_SLEEP, CURRENT_DEEP_SLEEP * BATTERY_VOLTAGE);
    Serial.printf("   Idle (WiFi off): %.1f mA (%.1f mW)\n", 
                  CURRENT_IDLE, CURRENT_IDLE * BATTERY_VOLTAGE);
    Serial.printf("   LoRa RX:         %.1f mA (%.1f mW)\n", 
                  CURRENT_RX_LORA, CURRENT_RX_LORA * BATTERY_VOLTAGE);
    Serial.printf("   CPU Activo:      %.1f mA (%.1f mW)\n", 
                  CURRENT_CPU_ACTIVE, CURRENT_CPU_ACTIVE * BATTERY_VOLTAGE);
    Serial.printf("   LoRa TX @20dBm:  %.1f mA (%.1f mW)\n", 
                  CURRENT_TX_LORA, CURRENT_TX_LORA * BATTERY_VOLTAGE);
    Serial.println();
    
    // Estimación de vida en deep sleep
    float hoursDeepSleep = BATTERY_CAPACITY_1000 / CURRENT_DEEP_SLEEP;
    float yearsDeepSleep = hoursDeepSleep / 24 / 365;
    
    Serial.println("   Con batería 1000mAh:");
    Serial.printf("   - Deep Sleep: %.1f años\n", yearsDeepSleep);
    Serial.printf("   - Idle: %.1f horas (%.1f días)\n", 
                  BATTERY_CAPACITY_1000 / CURRENT_IDLE,
                  BATTERY_CAPACITY_1000 / CURRENT_IDLE / 24);
    Serial.println();
}

// ==============================================================
// SETUP
// ==============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial);
    delay(1000);
    
    pinMode(LED_PIN, OUTPUT);
    
    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════════════════╗");
    Serial.println("║    EON ESP32 - SISTEMA DE MÉTRICAS DE ENERGÍA                    ║");
    Serial.println("╚══════════════════════════════════════════════════════════════════╝");
    Serial.println();
    
    // Inicializar ADC para batería
    initBatteryADC();
    
    // Inicializar SPI y LoRa
    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
    LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
    
    if (!LoRa.begin(LORA_FREQ)) {
        Serial.println("✗ Error inicializando LoRa");
        while (1);
    }
    
    LoRa.setSpreadingFactor(10);
    LoRa.setSignalBandwidth(125000);
    LoRa.setTxPower(20);
    
    Serial.println("✓ LoRa inicializado");
    Serial.println("✓ ADC de batería configurado");
    Serial.println();
    
    // Mostrar modos de consumo
    printPowerModes();
    
    // Ejecutar mediciones
    Serial.println("⏱ Ejecutando mediciones de energía...");
    Serial.println();
    
    digitalWrite(LED_PIN, HIGH);
    measureOperation("TX 1-Bit", PACKET_SIZE_1BIT, testTx1Bit);
    delay(100);
    measureOperation("TX JSON", PACKET_SIZE_JSON, testTxJSON);
    digitalWrite(LED_PIN, LOW);
    
    // Generar reporte
    printEnergyReport();
    
    Serial.println("Comandos:");
    Serial.println("  'm' - Repetir mediciones");
    Serial.println("  'b' - Leer batería");
    Serial.println("  's' - Entrar en deep sleep (10s)");
    Serial.println();
}

// ==============================================================
// LOOP
// ==============================================================

void loop() {
    if (Serial.available()) {
        char cmd = Serial.read();
        
        switch (cmd) {
            case 'm':
            case 'M':
                measurementCount = 0;
                Serial.println("\n⏱ Repetiendo mediciones...\n");
                measureOperation("TX 1-Bit", PACKET_SIZE_1BIT, testTx1Bit);
                delay(100);
                measureOperation("TX JSON", PACKET_SIZE_JSON, testTxJSON);
                printEnergyReport();
                break;
                
            case 'b':
            case 'B':
                batteryVoltage = readBatteryVoltage();
                Serial.printf("\n🔋 Batería: %.2f V (%.0f%%)\n\n", 
                              batteryVoltage, batteryPercentage(batteryVoltage));
                break;
                
            case 's':
            case 'S':
                Serial.println("\n💤 Entrando en deep sleep por 10 segundos...\n");
                LoRa.sleep();
                esp_sleep_enable_timer_wakeup(10 * 1000000);  // 10 segundos
                esp_deep_sleep_start();
                break;
        }
    }
}
