# 🗺️ Eón AI: Roadmap de Ingeniería y Fundamentos Matemáticos (v2.5 – v3.5)

**Versión:** 2.5.0-dev  
**Fecha de actualización:** 2026-10-04  
**Estado:** Activo / En ejecución  
**Autores:** SenseLab — Equipo de Arquitectura e Investigación Edge AI  

---

## 🎯 Visión y Objetivos Estratégicos

El Proyecto Eón ha consolidado sus fundamentos teóricos y experimentales:
- Núcleo ANSI C ultraligero de **1.3 KB** en memoria ([`libAeon`](../phase2-core/libAeon/)).
- Formalización matemática completa en [MATHEMATICS.md](MATHEMATICS.md) (ESN, ESP, Q8.8, compresión 1-Bit).
- Ecosistema de firmware y actualización over-the-air consolidado en [FIRMWARE_OTA.md](FIRMWARE_OTA.md).
- Nuevo patrón de benchmark y desglose energético riguroso en [benchmarks.md](benchmarks.md).

Este roadmap establece la ruta de evolución técnica para transformar a Eón en el **estándar industrial de TinyML con aprendizaje continuo on-device**. La estrategia se basa en rigor matemático, optimización DSP a nivel de silicio, resiliencia distribuida en redes mesh y herramientas de compilación AOT (*Ahead-Of-Time*).

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                 EÓN ROADMAP                                  │
├───────────────────┬───────────────────┬───────────────────┬──────────────────┤
│   Fase 13 (v2.5)  │   Fase 14 (v2.6)  │   Fase 15 (v2.7)  │   Fase 16 (v3.0) │
│  Control Numérico │  Aceleración DSP  │ Edge Mesh & OTA   │ Tooling & TinyML │
│  & Estabilidad    │    & Hardware     │  Resiliente       │  Certificación   │
├───────────────────┼───────────────────┼───────────────────┼──────────────────┤
│ • Radio espectral │ • SIMD CMSIS-DSP  │ • Delta-RLE LoRa  │ • Compilador     │
│   online (Lyapunov)│ • ESP32-S3 Vector │ • FedAvg 1-Bit    │   eon2c AOT      │
│ • RLS + Olvido    │ • Block Float Q15 │ • Firma Ed25519   │ • Bit-exact HIL  │
│ • Capacidad Mem.  │ • Wakeup por      │ • LoRa ADR        │ • MLCommons      │
│ • Reservoirs Ort. │   eventos neuro   │   (Rate adaptativo│   TinyML Perf    │
└───────────────────┴───────────────────┴───────────────────┴──────────────────┘
```

---

## 🔬 Fase 13 (v2.5): Control Numérico y Estabilidad Dinámica

### 13.1 Monitor Online de Estabilidad (Lyapunov & Spectral Radius Guard)
* **Problema:** En adaptación continua (aprendizaje online Hebbiano o Recursive Ridge), las modificaciones dinámicas en $W$ o la presencia de ráfagas de entrada de alta amplitud pueden desestabilizar el reservoir, violando la Echo State Property ($\rho(W) \ge 1$) y generando oscilaciones caóticas indeseadas o saturación de estados.
* **Fundamento Matemático:**
  - Estimación en tiempo real del Máximo Exponente de Lyapunov local ($\lambda_{\max}$):
    $$\lambda_{\max} \approx \frac{1}{\tau} \ln \left( \frac{\|\delta x(t + \tau)\|}{\|\delta x(t)\|} \right)$$
  - Condición de estabilidad asintótica: $\lambda_{\max} < 0$.
  - Algoritmo de Power Iteration incremental $O(N^2)$ cada $K$ ciclos para monitorear $\rho(W)$:
    $$w^{(k+1)} = \frac{W x^{(k)}}{\|W x^{(k)}\|_2}, \quad \lambda^{(k+1)} = (w^{(k+1)})^T W w^{(k+1)}$$
* **Implementación:**
  - Si $\rho(W) > \rho_{\text{target}}$ (típicamente $0.90$), aplicar contracción instantánea $W \leftarrow \left(\frac{\rho_{\text{target}}}{\rho(W)}\right) W$.
  - Módulo: `phase1-foundations/python/esn/stability_guard.py` y función C `aeon_check_stability()` en `libAeon.c`.
* **Criterio de Aceptación:** Cero divergencias de estados en series Mackey-Glass caóticas tras $10^6$ pasos con plasticidad activa.

### 13.2 Optimización Analítica de Capacidad de Memoria ($MC$)
* **Problema:** Los hiperparámetros $(\alpha, \rho, s_{in})$ se eligen frecuentemente por heurística empírica, lo que subutiliza el potencial temporal del reservoir para señales con retardo largo.
* **Fundamento Matemático:**
  - Capacidad de memoria lineal de Jaeger:
    $$MC = \sum_{k=1}^{k_{\max}} \frac{\text{Cov}^2(u(t-k), y_k(t))}{\text{Var}(u(t-k)) \cdot \text{Var}(y_k(t))} \le N$$
  - Sintonización acoplada de la tasa de fuga $\alpha$ con la autocorrelación de la señal de entrada $R_{uu}(\tau)$:
    $$\alpha_{\text{opt}} \approx 1 - \exp\left(-\frac{\Delta t}{\tau_{\text{corr}}}\right)$$
* **Implementación:**
  - Calibrador automático en `phase1-foundations/python/esn/memory_tuner.py` que calcula $R_{uu}(\tau)$ de una ventana de calibración y ajusta automáticamente $(\alpha, \rho)$ antes del deployment.
* **Criterio de Aceptación:** Maximización de $MC \ge 0.75 \cdot N$ para $N=50$ neuronas en señales con correlación temporal prolongada.

### 13.3 Recursive Least Squares (RLS) con Factor de Olvido Exponencial y Descomposición U-D
* **Problema:** La actualización recursiva estándar acumula errores de redondeo en aritmética de 32 bits, perdiendo la propiedad de matriz definida positiva de $P(t)$, causando inestabilidad numérica en despliegues de meses sin reinicio.
* **Fundamento Matemático:**
  - RLS con factor de olvido exponencial $\beta \in [0.98, 0.9995]$:
    $$k(t) = \frac{P(t-1) z(t)}{\beta + z(t)^T P(t-1) z(t)}$$
    $$W_{\text{out}}(t) = W_{\text{out}}(t-1) + e(t) k(t)^T$$
    $$P(t) = \frac{1}{\beta} \left[ P(t-1) - k(t) z(t)^T P(t-1) \right]$$
  - Factorización $P(t) = U(t) D(t) U(t)^T$ (Bierman-Thornton UD Factorization) para garantizar numéricamente $P(t) \succ 0$ en microcontroladores de precisión limitada.
* **Implementación:**
  - Implementación en `phase1-foundations/python/learning/ud_rls.py` y port nativo en C `libAeon_rls_ud.c`.
* **Criterio de Aceptación:** MSE acotado sin degradación ni NaN tras 100,000 ciclos de aprendizaje continuo en Cortex-M4F sin FPU de 64 bits.

### 13.4 Reservoirs Ortogonales y Simplécticos
* **Problema:** Los reservoirs generados con pesos gaussianos aleatorios tienen una distribución de eigenvalores en el plano complejo con alta varianza, provocando modos resonantes espurios y amortiguamiento desbalanceado.
* **Fundamento Matemático:**
  - Matriz ortogonal estricta $W W^T = I$, con eigenvalores sobre el círculo unitario $|\lambda_i| = 1$.
  - Escalado exacto $W \leftarrow \rho \cdot W$ asegura que todos los modos decaigan a la tasa idéntica $\rho^t$.
  - Generación mediante transformadas de Cayley a partir de matrices antisimétricas $A = -A^T$:
    $$W = (I - A)(I + A)^{-1}$$
* **Implementación:**
  - Generador ortogonal en `phase1-foundations/python/utils/matrix_init.py`.
* **Criterio de Aceptación:** Retención de memoria $MC$ un 25% superior a reservoirs gaussianos idénticos en tamaño.

---

## ⚡ Fase 14 (v2.6): Aceleración DSP Hardware y Optimización SIMD

### 14.1 Vectorización CMSIS-DSP para ARM Cortex-M4/M7/M33
* **Problema:** La multiplicación matriz-vector en C plano compila a instrucciones escalares convencionales, desperdiciando las unidades SIMD de 32 bits presentes en ARM Cortex-M.
* **Implementación:**
  - Uso de directivas intrínsecas de CMSIS-DSP:
    - `arm_dot_prod_q15()` / `arm_mat_vec_mult_q15()` para el update del reservoir:
      $$x_i(t) = (1-\alpha) x_i(t-1) + \alpha \cdot \text{tanh\_q15}\left( \text{dot\_q15}(W_{in, i}, u) + \text{sparse\_dot\_q15}(W_i, x) \right)$$
    - Uso de instrucciones de hardware de ciclo único `__SMLAD` (Dual 16-bit Signed Multiply with 32-bit Accumulate).
* **Impacto Energético Proyectado:**
  | Plataforma | Implementación | Latencia ($N=50$) | Energía / Inferencia |
  |------------|----------------|-------------------|----------------------|
  | Cortex-M4F @ 80MHz | C genérico actual | 31.9 µs | 0.00160 µJ |
  | Cortex-M4F @ 80MHz | **CMSIS-DSP SIMD** | **8.4 µs** (3.8× más rápido) | **0.00042 µJ** (3.8× ahorro) |
* **Criterio de Aceptación:** Inferencia sub-10 µs en STM32F401 / Due.

### 14.2 Instrucciones Vectoriales para ESP32-S3 (ESP-DSP PIE)
* **Problema:** El ESP32-S3 dispone de extensiones vectoriales de punto fijo (PIE - Processor Instruction Extension), pero `AeonESP32.h` opera con aritmética escalar estándar.
* **Implementación:**
  - Integrar `dsps_dotprod_s16()` y aceleración por tabla para la función $\tanh$ no lineal.
  - Soporte de doble núcleo: Núcleo 0 para sensor stream y radio LoRa/WiFi; Núcleo 1 dedicado exclusivamente al reservoir update en tiempo real estricto.
* **Criterio de Aceptación:** Tasa de procesamiento sostenida $> 50,000$ inferencias/segundo en ESP32-S3 a 240 MHz.

### 14.3 Aritmética Block Floating Point (BFP Q15 / Q4.12)
* **Problema:** El formato fijo Q8.8 asigna 8 bits a la parte entera, cuando las activaciones $\tanh(x)$ están estrictamente confinadas en el intervalo $[-1.0, 1.0]$. Esto desperdicia resolución útil.
* **Fundamento Matemático:**
  - Adopción de Q1.14 o Q0.15 para el vector de estados $x(t) \in [-1, 1]$.
  - Exponente de bloque común compartido para las entradas $u(t)$ y los pesos de entrada $W_{in}$, eliminando overflows sin sacrificar precisión.
* **Criterio de Aceptación:** Reducción del error de cuantización MSE de $0.009$ (Q8.8) a $< 0.0008$ (Q1.14), aproximándose al 98% de la precisión de float64.

### 14.4 Despertar por Evento Neuromórfico (Zero-Power Event Gating)
* **Problema:** Muestrear el sensor y ejecutar el ciclo ESN a frecuencia fija gasta batería en períodos donde la señal no contiene variaciones relevantes.
* **Implementación:**
  - Interrupción de hardware por umbral dinámico o filtro de derivada analógica de ultrabajo consumo ($< 1$ µA).
  - Solo cuando la variación $\|\Delta u\| > \epsilon$, el microcontrolador sale de Deep Sleep, actualiza los transitorios del reservoir y genera predicciones.
* **Impacto en Vida Útil:**
  - En monitorización de fallos estructurales o vibración de maquinaria industrial: extensión de vida de batería CR2032 de **760 días a > 5 años**.

---

## 📡 Fase 15 (v2.7): Edge Mesh Distribuido, Sincronización y OTA Seguro

### 15.1 Compresión Diferencial Delta-RLE para LoRa
* **Problema:** Transmitir los 21 bytes del vector 1-Bit completo en cada evento de sincronización es redundante si solo una pequeña fracción de neuronas cambió de signo.
* **Fundamento Matemático:**
  - Vector de cambio binario: $\Delta b(t) = b(t) \oplus b(t-1)$, donde $b(t) = \text{sign}(W_{out}(t))$.
  - Codificación por longitud de series (Run-Length Encoding - RLE) de los ceros entre cambios de signo.
* **Eficiencia de Transmisión:**
  | Tasa de cambio de pesos | Tamaño Payload | Tiempo de aire (SF10) | Energía LoRa TX |
  |-------------------------|----------------|-----------------------|-----------------|
  | Estándar 1-Bit (100%)   | 21 bytes       | 51.0 ms               | 4.33 mJ         |
  | Delta $\le 10\%$ cambios| **4 – 6 bytes**| **25.6 ms** (2×)      | **2.17 mJ** (2×)|
* **Criterio de Aceptación:** Aumento de la autonomía de batería de un nodo sensor con LoRa activo (1 sync/min) de 6.5 días a **> 18 días** con una única batería CR2032.

### 15.2 Federated Averaging Descentralizado (Decentralized FedAvg) sobre Consenso 1-Bit
* **Problema:** Las arquitecturas federadas convencionales requieren un servidor central agregador (star topology), punto único de fallo en entornos de campo (agricultura, minería, rescate).
* **Fundamento Matemático:**
  - Promediado descentralizado por consenso de vecindad de grafos $G=(V, E)$:
    $$W_{\text{out}, i}^{(t+1)} = W_{\text{out}, i}^{(t)} + \gamma \sum_{j \in \mathcal{N}_i} a_{ij} \left( \mathcal{Q}^{-1}(b_j) - W_{\text{out}, i}^{(t)} \right)$$
  - Operador de des-cuantización probabilística basado en la señal de signo recibida $b_j \in \{-1, +1\}^N$.
* **Implementación:**
  - Protocolo P2P mesh en `phase6-collective/mesh_consensus.py` y soporte en `phase4-hardware/esp32/examples/Mesh_FedAvg.ino`.
* **Criterio de Aceptación:** Convergencia del error global del enjambre al error del modelo centralizado con un error relativo $< 8\%$ tras 20 rondas de difusión ad-hoc.

### 15.3 Integridad Criptográfica y OTA Blindado (Ed25519)
* **Problema:** En redes IoT inalámbricas, la difusión OTA y la recepción de pesos externos son vulnerables a inyección de código malicioso o alteración de modelos (*data poisoning*).
* **Implementación:**
  - Micro-librería de firma criptográfica de curva elíptica Ed25519 (Monocypher o micro-ecc, footprint $< 2$ KB ROM).
  - Cada actualización OTA `.bin` y cada paquete de pesos LoRa contiene una firma de 64 bytes generada con clave privada del laboratorio SenseLab.
  - Verificación en hardware antes de conmutar el bootloader hacia la partición `app1` o escribir en la memoria NVS.
* **Criterio de Aceptación:** Rechazo verificado del 100% de paquetes corruptos o firmados con claves ilegítimas sin impacto medible en latencia de inferencia.

### 15.4 Adaptative Data Rate (ADR) para LoRa
* **Implementación:**
  - Ajuste dinámico de Spreading Factor ($SF7$ a $SF12$), Bandwidth y Potencia de Transmisión ($2$ dBm a $20$ dBm) evaluando el SNR y RSSI de los acuses de recibo (ACK).
  - Maximización del ahorro energético cuando el nodo está próximo al gateway o a otros nodos repetidores.

---

## 🛠️ Fase 16 (v3.0): Tooling de Producción, Interoperabilidad y Certificación

### 16.1 Compilador `eon2c` — Zero-Dependency AOT C Generator
* **Objetivo:** Permitir que investigadores entrenen y calibren modelos Eón en Python, y con un único comando exporten un código C99 puro, estático y autocontenido listo para compilar con GCC/Clang/IAR/Keil.
* **Flujo de Trabajo:**
  ```bash
  python -m eon.compiler --model trained_model.npz --target cortex-m4 --precision q15 --output model_deploy/
  ```
* **Características del Código C Generado:**
  - Sin dependencias externas (cero `malloc`, cero llamadas a librerías dinámicas).
  - Matrices $W$ y $W_{in}$ alojadas como arrays constantes `const int16_t[]` en Flash (Flash ROM zero RAM footprint).
  - Solo el vector de estados $x(t)$ y $W_{out}$ consumen SRAM ($< 250$ bytes para $N=50$).
* **Criterio de Aceptación:** Compilación limpia con `-Wall -Wextra -pedantic` en GCC para ARM y AVR.

### 16.2 Harness de Co-Simulación Bit-Exact (Python ↔ C)
* **Problema:** Las discrepancias entre los cálculos de punto flotante de Python y la aritmética entera de los microcontroladores complican la validación de modelos en producción.
* **Implementación:**
  - Emulador en Python `phase1-foundations/python/esn/bit_exact_simulator.py` que modela el truncamiento bit a bit, overflows de 16/32 bits y tablas de $\tanh$ idénticas al firmware C.
  - Validación automatizada en CI/CD: para cada commit, se corre una suite que compara el output de Python contra el binario C compilado ejecutado en emulador QEMU ARM Cortex-M.
* **Criterio de Aceptación:** Discrepancia matemática estricta: $\max |y_{\text{python}} - y_{\text{C}}| = 0$ LSBs.

### 16.3 Suite de Certificación TinyML Perf / MLCommons
* **Objetivo:** Medición estandarizada y auditable del rendimiento de Eón frente a los líderes del sector (TFLite Micro, CMSIS-NN, Edge Impulse).
* **Benchmarks a Certificar:**
  1. **Predicción de Series Temporales Caóticas (Mackey-Glass Benchmark)**: Métricas de MSE, latencia por muestra y energía por inferencia.
  2. **Detección de Anomalías Industriales (Vibración IMS Bearings Dataset)**: AUC-ROC, latencia de detección y consumo de RAM.
  3. **Bioseñales ECG (MIT-BIH Arrhythmia Database)**: Detección en tiempo real con $< 2$ KB de RAM.
* **Criterio de Aceptación:** Publicación de resultados auditables en el repositorio oficial y documentación comparativa.

### 16.4 Bindings para Zephyr RTOS y MicroPython
* **Implementación:**
  - Driver nativo para Zephyr RTOS (`zephyr/modules/eon_ai`), facilitando integración en proyectos automotrices e industriales basados en RTOS estándar.
  - Módulo C para MicroPython / CircuitPython para prototipado rápido en placas RP2040, ESP32 y nRF52840.

---

## 📊 Matriz de Priorización e Impacto Técnico

| Fase | Tarea / Módulo | Complejidad | Impacto Rendimiento | Impacto Energético | Prioridad |
|:----:|:---------------|:-----------:|:-------------------:|:------------------:|:---------:|
| **13** | **13.1** Stability Guard (Lyapunov) | Media | ⭐⭐⭐⭐ (Previene fallos) | Neutro | **P0 (Inmediata)** |
| **13** | **13.2** Memory Capacity Auto-Tuning | Media | ⭐⭐⭐⭐⭐ (+30% MC) | Neutro | **P0 (Inmediata)** |
| **13** | **13.3** RLS con Olvido & Factorización U-D | Alta | ⭐⭐⭐⭐⭐ (Anti-drift) | Neutro | **P0 (Inmediata)** |
| **13** | **13.4** Reservoirs Ortogonales / Cayley | Media | ⭐⭐⭐⭐ (+25% retención)| Neutro | **P1 (Alta)** |
| **14** | **14.1** CMSIS-DSP Vectorization (M4) | Media | ⭐⭐⭐⭐⭐ (3.8× velocidad) | ⭐⭐⭐⭐⭐ (3.8× ahorro) | **P0 (Inmediata)** |
| **14** | **14.2** ESP32-S3 Vector Extension | Media | ⭐⭐⭐⭐ (5× velocidad) | ⭐⭐⭐⭐ (3× ahorro) | **P1 (Alta)** |
| **14** | **14.3** Block Floating Point (Q1.14) | Media | ⭐⭐⭐⭐ (Precisión 98%) | Neutro | **P1 (Alta)** |
| **14** | **14.4** Event-Driven Wakeup Gating | Alta | ⭐⭐⭐ (Menor latencia) | ⭐⭐⭐⭐⭐ (>5 años bat.)| **P0 (Inmediata)** |
| **15** | **15.1** Delta-RLE LoRa Sync | Baja | ⭐⭐⭐ (Menor tráfico) | ⭐⭐⭐⭐⭐ (2.6× ahorro LoRa)| **P0 (Inmediata)** |
| **15** | **15.2** Decentralized FedAvg 1-Bit | Alta | ⭐⭐⭐⭐⭐ (Mesh colaborativo)| ⭐⭐⭐ (P2P eficiente) | **P1 (Alta)** |
| **15** | **15.3** Firma Criptográfica Ed25519 | Media | ⭐⭐⭐⭐⭐ (Seguridad militar) | Leve overhead (<1%) | **P1 (Alta)** |
| **16** | **16.1** Compilador `eon2c` AOT | Alta | ⭐⭐⭐⭐⭐ (Cero footprint)| ⭐⭐⭐⭐ (Zero overhead) | **P0 (Inmediata)** |
| **16** | **16.2** Harness Bit-Exact HIL (QEMU) | Media | ⭐⭐⭐⭐⭐ (Calidad CI/CD) | N/A (Tooling) | **P1 (Alta)** |
| **16** | **16.3** Suite MLCommons TinyML Perf | Media | ⭐⭐⭐⭐⭐ (Visibilidad) | N/A (Benchmark) | **P1 (Alta)** |

---

## 📈 Métricas Globales de Éxito del Roadmap (Target v3.0)

1. **Eficiencia Energética:** Reducción de la energía por inferencia en ARM Cortex-M4 a **$< 0.0005$ µJ** (actualmente $0.0016$ µJ).
2. **Huella de Memoria Flash:** Mantener el núcleo C en **$< 4$ KB de Flash** y el reservoir $N=50$ en **$< 250$ bytes de RAM** para inferencia pura en modo AOT.
3. **Autonomía Operativa de Batería:** Superar los **10 años** de operación continua en monitorización con celda de litio no recargable y **$> 20$ días** en transmisión de telemetría LoRa activa periódica.
4. **Resiliencia Numérica:** Cero desbordamientos, valores NaN o degradación de estabilidad demostrados tras 1,000,000 de ciclos continuos de adaptación online.
5. **Ecosistema y Adopción:** Suite de pruebas con cobertura $> 95\%$ e integración bit-exact validada por hardware en bucle continuo.

---

*Proyecto Eón — SenseLab — Build with Sense*  
*Documento aprobado para ejecución técnica en versiones 2.5 a 3.5*
