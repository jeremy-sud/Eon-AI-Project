/**
 * @file mock_mqtt.c
 * @brief Simulates MQTT packet generation for Eon 1-Bit Weight Exchange.
 */

#include "quantization.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Protocol Definition
// Header: [ 'E', 'O', 'N', TYPE ]
// Type 0x01: W_OUT_UPDATE_1BIT
// Seed: 4 bytes (uint32_t little endian)
// Payload: Quantized bits

#define PACKET_TYPE_UPDATE 0x01
#define SEED 0xDEADBEEF // Example seed

typedef struct __attribute__((packed)) {
  char magic[3];
  uint8_t type;
  uint32_t seed;
  uint16_t num_weights;
  // Payload follows
} eon_packet_header_t;

void mock_mqtt_publish(const char *topic, const uint8_t *payload, size_t len) {
  printf("[MQTT] Publish to '%s' (%zu bytes):\n", topic, len);
  printf("       Header: %c%c%c Type:0x%02X Seed:0x%08X\n", payload[0],
         payload[1], payload[2], payload[3], *(uint32_t *)(payload + 4));

  // Show first few bytes of payload
  printf("       Data (hex): ");
  for (int i = 0; i < (len > 20 ? 20 : len); i++) {
    printf("%02X ", payload[i]);
  }
  printf("...\n");
}

int main() {
  printf("Eon 1-Bit Weight Exchange Simulation (ESP32)\n");

  // Simulate training weights (N=100)
  int n_weights = 100;
  float weights[100];
  srand(time(NULL));

  printf("Generated %d weights (Float32): %lu bytes\n", n_weights,
         n_weights * sizeof(float));

  for (int i = 0; i < n_weights; i++) {
    weights[i] = ((float)rand() / (float)(RAND_MAX)) - 0.5f; // -0.5 to 0.5
  }

  // Prepare Packet
  size_t payload_size = (n_weights + 7) / 8;
  size_t packet_size = sizeof(eon_packet_header_t) + payload_size;

  uint8_t *packet = malloc(packet_size);
  eon_packet_header_t *header = (eon_packet_header_t *)packet;

  // Fill Header
  header->magic[0] = 'E';
  header->magic[1] = 'O';
  header->magic[2] = 'N';
  header->type = PACKET_TYPE_UPDATE;
  header->seed = SEED;
  header->num_weights = (uint16_t)n_weights;

  // Fill Payload (Quantize)
  int bytes_written =
      quantize_1bit(weights, n_weights, packet + sizeof(eon_packet_header_t));

  printf("Compressed Payload: %d bytes\n", bytes_written);
  printf("Total Packet: %zu bytes (Compression Ratio: %.1f x)\n", packet_size,
         (float)(n_weights * sizeof(float)) / packet_size);

  // Send
  mock_mqtt_publish("eon/hive/update", packet, packet_size);

  // Verify Decompression (Receiver Code)
  printf("\n[Receiver] Decompressing...\n");
  float recovered[100];
  dequantize_1bit(packet + sizeof(eon_packet_header_t), n_weights, recovered,
                  0.25f); // Assume scale 0.25

  // Check signal correlation
  int matching_signs = 0;
  for (int i = 0; i < n_weights; i++) {
    if ((weights[i] >= 0 && recovered[i] > 0) ||
        (weights[i] < 0 && recovered[i] < 0)) {
      matching_signs++;
    }
  }
  printf("Sign Consistency: %d / %d (%.1f%%)\n", matching_signs, n_weights,
         (float)matching_signs * 100.0f / n_weights);

  free(packet);
  return 0;
}
