# Fase 5: Aplicaciones y Prototipos IoT

Esta fase demuestra la utilidad práctica del Motor Eón en escenarios del mundo real, enfocándose en Salud, Voz e Industria.

## Prototipos

### 1. Bio Monitor (Salud) 🫀

**Directorio**: `bio-monitor/`

Sistema de detección de arritmias cardíacas que privacidad total (sin nube).

- **Input**: Intervalos RR (latido a latido).
- **Modelo**: ESN aprende la variabilidad normal del usuario (RSA).
- **Resultado**: Detecta anomalías (PVCs, latidos perdidos) con <2KB RAM.
- **Estado**: Simulación funcional (`simulate_rr.py` + `bio_monitor.c`).

### 2. Eón Voice (Voz) 🗣️

**Directorio**: `voice-command/`

Spotting de palabras clave ("Keyword Spotting") ultraligero.

- **Palabra Clave**: "EÓN".
- **Input**: 4 bandas de frecuencia (espectrograma simplificado a 50Hz).
- **Resultado**: Detecta la firma temporal fonética de la palabra.
- **Estado**: Simulación funcional (`simulate_audio.py` + `voice_kws.c`).

### 3. Temperature Predictor (Industria) 🌡️

**Archivo**: `temperature_predictor.py`

Predicción de anomalías en sensores industriales.

- Detecta desviaciones en series temporales de temperatura.
- Caso de uso: Mantenimiento predictivo.

## Nota de Implementación

Todos los prototipos en C están diseñados para ser portables a **Cortex-M4 (STM32, nRF52)** o **ESP32**, utilizando la librería `libAeon` de la Fase 2.
