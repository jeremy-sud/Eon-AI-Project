/**
 * Eón ESP32 + LoRa - Test de Alcance
 * ===================================
 * 
 * Programa para pruebas de campo del Protocolo 1-Bit sobre LoRa.
 * Mide alcance efectivo, RSSI, SNR y tasa de pérdida de paquetes.
 * 
 * Hardware:
 * - 2x ESP32 con módulo LoRa (TTGO LoRa32 o Heltec)
 * - Un dispositivo como TX, otro como RX
 * 
 * Uso:
 * 1. Subir este código a ambos ESP32
 * 2. En Serial Monitor, escribir 'tx' para modo transmisor
 * 3. En el otro, escribir 'rx' para modo receptor
 * 4. Alejar los dispositivos y observar métricas
 * 
 * (c) 2024 Sistemas Ursol - Jeremy Arias Solano
 */

#include <SPI.h>
#include <LoRa.h>
#include <WiFi.h>

// ==============================================================
// CONFIGURACIÓN HARDWARE (ajustar según placa)
// ==============================================================

// TTGO LoRa32 V1
#define LORA_SCK  5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_SS   18
#define LORA_RST  14
#define LORA_DIO0 26

// Frecuencia LoRa (ajustar según región)
#define LORA_FREQ 915E6  // 433E6, 868E6, o 915E6

// ==============================================================
// CONFIGURACIÓN DEL TEST
// ==============================================================

#define TX_INTERVAL_MS    2000     // Intervalo entre transmisiones
#define TX_POWER          20       // Potencia TX (2-20 dBm)
#define SPREADING_FACTOR  10       // SF7-SF12 (mayor = más alcance)
#define BANDWIDTH         125E3    // 125kHz estándar
#define CODING_RATE       5        // 4/5 coding rate

// Protocolo 1-Bit - Tamaño de paquete
#define RESERVOIR_SIZE    50       // Neuronas en el reservoir
#define HEADER_SIZE       14       // Bytes del header
#define PAYLOAD_SIZE      ((RESERVOIR_SIZE + 7) / 8)
#define PACKET_SIZE       (HEADER_SIZE + PAYLOAD_SIZE)

// ==============================================================
// ESTRUCTURA DE PAQUETE DE TEST
// ==============================================================

struct TestPacket {
    char magic[3];      // "EON"
    uint8_t type;       // 1 = SYNC
    uint32_t seq;       // Número de secuencia
    uint32_t timestamp; // millis() del transmisor
    uint16_t count;     // Número de pesos
    uint8_t payload[PAYLOAD_SIZE];
};

// ==============================================================
// VARIABLES GLOBALES
// ==============================================================

enum Mode { MODE_IDLE, MODE_TX, MODE_RX };
Mode currentMode = MODE_IDLE;

// Estadísticas TX
uint32_t txPacketCount = 0;
uint32_t txBytesSent = 0;

// Estadísticas RX
uint32_t rxPacketCount = 0;
uint32_t rxPacketsLost = 0;
uint32_t rxBytesReceived = 0;
int32_t lastRSSI = 0;
float lastSNR = 0;
uint32_t lastSeqReceived = 0;

// Historial de RSSI para promedios
#define RSSI_HISTORY_SIZE 100
int32_t rssiHistory[RSSI_HISTORY_SIZE];
float snrHistory[RSSI_HISTORY_SIZE];
int rssiHistoryIndex = 0;
int rssiHistoryCount = 0;

// Temporizadores
unsigned long lastTxTime = 0;
unsigned long testStartTime = 0;

// ID único del dispositivo
String deviceId;

// ==============================================================
// FUNCIONES AUXILIARES
// ==============================================================

void printHeader() {
    Serial.println();
    Serial.println("╔════════════════════════════════════════════════════════╗");
    Serial.println("║    EON LORA RANGE TEST - PROTOCOLO 1-BIT               ║");
    Serial.println("╚════════════════════════════════════════════════════════╝");
    Serial.println();
}

String getDeviceId() {
    uint64_t mac = ESP.getEfuseMac();
    char id[13];
    snprintf(id, sizeof(id), "%04X%08X", (uint16_t)(mac >> 32), (uint32_t)mac);
    return String(id);
}

void createTestPacket(TestPacket* pkt, uint32_t seq) {
    pkt->magic[0] = 'E';
    pkt->magic[1] = 'O';
    pkt->magic[2] = 'N';
    pkt->type = 1;  // SYNC
    pkt->seq = seq;
    pkt->timestamp = millis();
    pkt->count = RESERVOIR_SIZE;
    
    // Generar payload pseudo-aleatorio (simula pesos 1-bit)
    for (int i = 0; i < PAYLOAD_SIZE; i++) {
        pkt->payload[i] = random(256);
    }
}

bool validatePacket(TestPacket* pkt) {
    return (pkt->magic[0] == 'E' && 
            pkt->magic[1] == 'O' && 
            pkt->magic[2] == 'N' &&
            pkt->type == 1);
}

void updateRSSIHistory(int32_t rssi, float snr) {
    rssiHistory[rssiHistoryIndex] = rssi;
    snrHistory[rssiHistoryIndex] = snr;
    rssiHistoryIndex = (rssiHistoryIndex + 1) % RSSI_HISTORY_SIZE;
    if (rssiHistoryCount < RSSI_HISTORY_SIZE) rssiHistoryCount++;
}

float getAverageRSSI() {
    if (rssiHistoryCount == 0) return 0;
    int64_t sum = 0;
    for (int i = 0; i < rssiHistoryCount; i++) {
        sum += rssiHistory[i];
    }
    return (float)sum / rssiHistoryCount;
}

float getAverageSNR() {
    if (rssiHistoryCount == 0) return 0;
    float sum = 0;
    for (int i = 0; i < rssiHistoryCount; i++) {
        sum += snrHistory[i];
    }
    return sum / rssiHistoryCount;
}

float getPacketLossRate() {
    if (rxPacketCount == 0 && rxPacketsLost == 0) return 0;
    return (float)rxPacketsLost / (rxPacketCount + rxPacketsLost) * 100.0;
}

String estimateRange(float avgRSSI) {
    // Estimación basada en RSSI típico de LoRa
    // Estos valores son aproximados y dependen del entorno
    if (avgRSSI > -80) return "<100m (excelente)";
    if (avgRSSI > -100) return "100-500m (bueno)";
    if (avgRSSI > -110) return "500m-1km (aceptable)";
    if (avgRSSI > -120) return "1-3km (límite)";
    return ">3km (débil)";
}

// ==============================================================
// MODO TRANSMISOR
// ==============================================================

void runTransmitter() {
    if (millis() - lastTxTime < TX_INTERVAL_MS) return;
    lastTxTime = millis();
    
    TestPacket pkt;
    createTestPacket(&pkt, txPacketCount);
    
    // Transmitir
    LoRa.beginPacket();
    LoRa.write((uint8_t*)&pkt, sizeof(pkt));
    int result = LoRa.endPacket();
    
    if (result) {
        txPacketCount++;
        txBytesSent += sizeof(pkt);
        
        // Mostrar progreso cada 10 paquetes
        if (txPacketCount % 10 == 0) {
            Serial.printf("📤 TX #%lu | Total: %lu bytes | Rate: %.1f pkt/s\n",
                          txPacketCount, txBytesSent,
                          (float)txPacketCount / ((millis() - testStartTime) / 1000.0));
        }
    } else {
        Serial.println("✗ Error TX");
    }
}

// ==============================================================
// MODO RECEPTOR
// ==============================================================

void runReceiver() {
    int packetSize = LoRa.parsePacket();
    if (packetSize == 0) return;
    
    // Leer paquete
    TestPacket pkt;
    int bytesRead = 0;
    while (LoRa.available() && bytesRead < sizeof(pkt)) {
        ((uint8_t*)&pkt)[bytesRead++] = LoRa.read();
    }
    
    // Validar
    if (!validatePacket(&pkt)) {
        Serial.println("⚠ Paquete inválido recibido");
        return;
    }
    
    // Obtener métricas
    lastRSSI = LoRa.packetRssi();
    lastSNR = LoRa.packetSnr();
    updateRSSIHistory(lastRSSI, lastSNR);
    
    // Detectar paquetes perdidos
    if (rxPacketCount > 0 && pkt.seq > lastSeqReceived + 1) {
        uint32_t lost = pkt.seq - lastSeqReceived - 1;
        rxPacketsLost += lost;
        Serial.printf("⚠ %lu paquetes perdidos (seq %lu-%lu)\n", 
                      lost, lastSeqReceived + 1, pkt.seq - 1);
    }
    lastSeqReceived = pkt.seq;
    
    rxPacketCount++;
    rxBytesReceived += bytesRead;
    
    // Calcular latencia (aproximada, sin sync de relojes)
    uint32_t latency = millis() - pkt.timestamp;
    
    // Mostrar métricas cada paquete
    Serial.println("────────────────────────────────────────");
    Serial.printf("📥 RX #%lu | Seq: %lu\n", rxPacketCount, pkt.seq);
    Serial.printf("   RSSI: %d dBm | SNR: %.1f dB\n", lastRSSI, lastSNR);
    Serial.printf("   Avg RSSI: %.1f dBm | Avg SNR: %.1f dB\n", 
                  getAverageRSSI(), getAverageSNR());
    Serial.printf("   Pérdida: %.1f%% | Bytes: %lu\n", 
                  getPacketLossRate(), rxBytesReceived);
    Serial.printf("   Rango estimado: %s\n", estimateRange(getAverageRSSI()).c_str());
    Serial.printf("   Latencia aprox: %lu ms\n", latency);
}

// ==============================================================
// REPORTE DE ESTADÍSTICAS
// ==============================================================

void printStats() {
    float elapsed = (millis() - testStartTime) / 1000.0;
    
    Serial.println();
    Serial.println("╔════════════════════════════════════════════════════════╗");
    Serial.println("║              REPORTE DE PRUEBA DE ALCANCE              ║");
    Serial.println("╠════════════════════════════════════════════════════════╣");
    Serial.printf("║ Dispositivo: %-43s ║\n", deviceId.c_str());
    Serial.printf("║ Modo: %-49s ║\n", 
                  currentMode == MODE_TX ? "TRANSMISOR" : "RECEPTOR");
    Serial.printf("║ Duración: %.1f segundos %32s ║\n", elapsed, "");
    Serial.println("╠════════════════════════════════════════════════════════╣");
    
    if (currentMode == MODE_TX) {
        Serial.printf("║ Paquetes TX: %-42lu ║\n", txPacketCount);
        Serial.printf("║ Bytes TX: %-45lu ║\n", txBytesSent);
        Serial.printf("║ Rate: %.1f pkt/s %40s ║\n", 
                      txPacketCount / elapsed, "");
    } else {
        Serial.printf("║ Paquetes RX: %-42lu ║\n", rxPacketCount);
        Serial.printf("║ Paquetes perdidos: %-36lu ║\n", rxPacketsLost);
        Serial.printf("║ Tasa de pérdida: %.1f%% %36s ║\n", getPacketLossRate(), "");
        Serial.printf("║ RSSI promedio: %.1f dBm %33s ║\n", getAverageRSSI(), "");
        Serial.printf("║ SNR promedio: %.1f dB %35s ║\n", getAverageSNR(), "");
        Serial.printf("║ Rango estimado: %-39s ║\n", estimateRange(getAverageRSSI()).c_str());
    }
    
    Serial.println("╠════════════════════════════════════════════════════════╣");
    Serial.println("║ CONFIGURACIÓN LORA                                     ║");
    Serial.printf("║   Frecuencia: %.2f MHz %34s ║\n", LORA_FREQ / 1E6, "");
    Serial.printf("║   Spreading Factor: SF%d %32s ║\n", SPREADING_FACTOR, "");
    Serial.printf("║   Bandwidth: %.0f kHz %36s ║\n", BANDWIDTH / 1E3, "");
    Serial.printf("║   TX Power: %d dBm %38s ║\n", TX_POWER, "");
    Serial.printf("║   Tamaño paquete: %d bytes %29s ║\n", PACKET_SIZE, "");
    Serial.println("╚════════════════════════════════════════════════════════╝");
    Serial.println();
}

// ==============================================================
// SETUP
// ==============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial);
    
    deviceId = getDeviceId();
    printHeader();
    
    Serial.printf("Device ID: %s\n", deviceId.c_str());
    Serial.println();
    
    // Inicializar SPI
    SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
    
    // Inicializar LoRa
    LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
    
    if (!LoRa.begin(LORA_FREQ)) {
        Serial.println("✗ Error inicializando LoRa");
        while (1);
    }
    
    // Configurar LoRa
    LoRa.setSpreadingFactor(SPREADING_FACTOR);
    LoRa.setSignalBandwidth(BANDWIDTH);
    LoRa.setCodingRate4(CODING_RATE);
    LoRa.setTxPower(TX_POWER);
    
    Serial.printf("✓ LoRa inicializado @ %.2f MHz, SF%d\n", 
                  LORA_FREQ / 1E6, SPREADING_FACTOR);
    Serial.println();
    Serial.println("Comandos:");
    Serial.println("  'tx' - Iniciar modo transmisor");
    Serial.println("  'rx' - Iniciar modo receptor");
    Serial.println("  's'  - Mostrar estadísticas");
    Serial.println("  'r'  - Reiniciar contadores");
    Serial.println();
}

// ==============================================================
// LOOP
// ==============================================================

void loop() {
    // Procesar comandos Serial
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        cmd.toLowerCase();
        
        if (cmd == "tx") {
            currentMode = MODE_TX;
            testStartTime = millis();
            txPacketCount = 0;
            txBytesSent = 0;
            Serial.println("\n📡 MODO TRANSMISOR ACTIVO");
            Serial.printf("   Intervalo: %d ms | Potencia: %d dBm\n", TX_INTERVAL_MS, TX_POWER);
            Serial.println("   Presione 's' para ver estadísticas\n");
            
        } else if (cmd == "rx") {
            currentMode = MODE_RX;
            testStartTime = millis();
            rxPacketCount = 0;
            rxPacketsLost = 0;
            rxBytesReceived = 0;
            rssiHistoryCount = 0;
            lastSeqReceived = 0;
            Serial.println("\n📻 MODO RECEPTOR ACTIVO");
            Serial.println("   Esperando paquetes...\n");
            
        } else if (cmd == "s") {
            printStats();
            
        } else if (cmd == "r") {
            txPacketCount = 0;
            txBytesSent = 0;
            rxPacketCount = 0;
            rxPacketsLost = 0;
            rxBytesReceived = 0;
            rssiHistoryCount = 0;
            testStartTime = millis();
            Serial.println("✓ Contadores reiniciados");
        }
    }
    
    // Ejecutar modo actual
    switch (currentMode) {
        case MODE_TX:
            runTransmitter();
            break;
        case MODE_RX:
            runReceiver();
            break;
        default:
            break;
    }
}
