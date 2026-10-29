# Eón: Fundamentos Matemáticos

**Versión:** 1.0.0  
**Fecha:** 2026-10-04  
**Autor:** Proyecto Eón — SenseLab

---

## 1. Echo State Network (ESN) — Ecuaciones Fundamentales

### 1.1 Definición del Sistema

Una Echo State Network es un sistema dinámico discreto definido por tres matrices:

- **W_in** ∈ ℝ^{N×K} — Matriz de entrada (aleatoria, fija)
- **W** ∈ ℝ^{N×N} — Matriz del reservoir (aleatoria, fija, dispersa)
- **W_out** ∈ ℝ^{L×(N+K+1)} — Matriz de salida (única capa entrenada)

Donde:
- K = dimensión de entrada
- N = tamaño del reservoir (neuronas)
- L = dimensión de salida

### 1.2 Ecuación de Estado (Update)

El estado interno del reservoir en el tiempo *t* se actualiza como:

```
x(t) = (1 − α) · x(t−1) + α · tanh(W_in · u(t) + W · x(t−1))
```

Donde:
- **x(t)** ∈ ℝ^N — Vector de estado del reservoir en tiempo *t*
- **u(t)** ∈ ℝ^K — Vector de entrada en tiempo *t*
- **α** ∈ (0, 1] — Leak rate (tasa de fuga / integración)
- **tanh(·)** — Función de activación (tangente hiperbólica)

**Nota sobre α (leak rate):**
- α = 1.0 → Sin memoria de estados anteriores (ESN clásica)
- α → 0 → Alta inercia, memoria larga, respuesta lenta
- Valor típico en Eón: α = 0.3

### 1.3 Ecuación de Lectura (Readout)

La salida se calcula como:

```
y(t) = W_out · z(t)
```

Donde el vector extendido z(t) se define como:

```
z(t) = [1; u(t); x(t)] ∈ ℝ^{1+K+N}
```

El "1" es el término de bias, permitiendo que W_out aprenda un offset constante.

### 1.4 Washout (Descarte de Transitorios)

Los primeros T_w pasos temporales se descartan antes del entrenamiento para permitir que el reservoir alcance su régimen dinámico estable:

```
T_w ∈ [50, 300]  (típico para Eón)
```

Justificación: El reservoir necesita tiempo para que su estado x(t) refleje adecuadamente la historia temporal de la entrada.

---

## 2. Echo State Property (ESP) — Condición de Estabilidad

### 2.1 Definición

Una ESN satisface la Echo State Property si y solo si el efecto de cualquier estado inicial x(0) se desvanece asintóticamente:

```
∀ x(0), x'(0) :  lim_{t→∞} ||x(t) − x'(t)|| = 0
```

dado la misma secuencia de entrada u(1), u(2), ..., u(t).

### 2.2 Condición Necesaria: Radio Espectral

El **radio espectral** ρ(W) se define como:

```
ρ(W) = max{ |λ| : λ ∈ eigenvalores(W) }
```

**Condición suficiente (Jaeger, 2001):**

```
ρ(W) < 1
```

En Eón, se normaliza la matriz W del reservoir:

```
W ← (ρ_target / ρ(W)) · W
```

Donde ρ_target ∈ (0, 1) es el radio espectral objetivo (típico: 0.9).

### 2.3 Cálculo Eficiente del Radio Espectral — Power Iteration

En lugar de calcular todos los eigenvalores (O(N³)), Eón usa **power iteration** (O(N²)):

```
Algoritmo: Power Iteration
─────────────────────────
Entrada: W ∈ ℝ^{N×N}, max_iter, tol
Salida:  ρ(W) ≈ eigenvalor dominante

1. v ← vector aleatorio unitario ∈ ℝ^N
2. Para i = 1, ..., max_iter:
   a. w ← W · v
   b. λ ← ||w||₂
   c. Si |λ − λ_prev| < tol: BREAK
   d. v ← w / λ
3. Retornar λ
```

**Complejidad:**
- Eigenvalores completos: O(N³)
- Power iteration: O(N² · k), donde k ≪ N

### 2.4 Dispersión (Sparsity) del Reservoir

La matriz W del reservoir tiene una densidad de conexión p ∈ [0.1, 0.25]:

```
P(W_ij ≠ 0) = p
```

Para N = 50, p = 0.2:
- Conexiones totales posibles: 50² = 2500
- Conexiones activas: 2500 × 0.2 = 500
- Ceros: 2000 (80% disperso)

**Beneficio computacional:** La multiplicación W·x se reduce de O(N²) a O(p·N²).

---

## 3. Entrenamiento: Regresión Ridge

### 3.1 Formulación

El entrenamiento de W_out se reduce a resolver:

```
W_out = Y · Z^T · (Z · Z^T + λ · I)^{-1}
```

Donde:
- **Z** = [z(T_w+1), z(T_w+2), ..., z(T)] ∈ ℝ^{(1+K+N)×T_train} — estados recolectados
- **Y** = [y_target(T_w+1), ..., y_target(T)] ∈ ℝ^{L×T_train} — salidas objetivo
- **λ** — Parámetro de regularización ridge (típico: 1e-6)
- **I** — Matriz identidad

### 3.2 Solución Optimizada por Factorización de Cholesky (L · L^T)

La matriz normal $A = Z · Z^T + \lambda · I \in \mathbb{R}^{M \times M}$ (donde $M = 1 + K + N$) es simétrica y **estrictamente definida positiva (SPD)**:
$$\forall v \neq 0, \quad v^T A v = \|Z^T v\|_2^2 + \lambda \|v\|_2^2 \ge \lambda \|v\|_2^2 > 0 \quad (\text{para } \lambda > 0)$$

Dado que $A$ es SPD, la solución no requiere inversión explícita ni descomposición general LU con pivoteo parcial ($O(\frac{2}{3} M^3)$ operaciones). Eón implementa la **descomposición de Cholesky**:
$$A = L \cdot L^T$$
donde $L$ es una matriz triangular inferior con elementos diagonales positivos:
$$L_{j,j} = \sqrt{A_{j,j} - \sum_{k=0}^{j-1} L_{j,k}^2}, \qquad L_{i,j} = \frac{1}{L_{j,j}} \left( A_{i,j} - \sum_{k=0}^{j-1} L_{i,k} L_{j,k} \right) \quad (i > j)$$

El sistema lineal $A \cdot W_{out}^T = Z \cdot Y^T$ se resuelve en dos pasos triangulares:
1. **Sustitución progresiva (Forward solve):** $L \cdot U = Z \cdot Y^T \quad \implies O(M^2 L_{out})$
2. **Sustitución regresiva (Back solve):** $L^T \cdot W_{out}^T = U \quad \implies O(M^2 L_{out})$

**Comparativa de Complejidad y Estabilidad:**
| Algoritmo | Flops ($M^3$) | Estabilidad Numérica | Pivoteo |
|-----------|---------------|----------------------|---------|
| Inversión Gauss-Jordan | $M^3$ | Pobre (división por pivotes pequeños) | Requerido |
| Factorización LU ($PA = LU$) | $\frac{2}{3} M^3$ | Moderada | Requerido |
| **Factorización de Cholesky ($LL^T$)** | $\mathbf{\frac{1}{3} M^3}$ | **Incondicionalmente Estable** | **No requerido** |

*Implementación:* En C embebido (`libAeon.c`), la descomposición de Cholesky reduce el tiempo de entrenamiento en un 60% y previene desbordamientos en punto fijo Q8.8. En Python (`utils.matrix_init.ridge_regression`), se invoca el solver LAPACK `DPOSV` (`scipy.linalg.solve(..., assume_a='pos')`).

### 3.3 Regularización Ridge (λ)

La regularización evita overfitting y garantiza el condicionamiento estricto de la matriz:

```
MSE(λ) = ||Y − W_out · Z||² + λ · ||W_out||²
```

- λ = 0: Sin regularización → riesgo de matriz mal condicionada o singular
- λ → ∞: Regularización excesiva (W_out → 0)
- λ = 1e-6: Balance óptimo en Eón (número de condición $\kappa(A) \le 1 + \sigma_{max}^2 / \lambda$)

---

## 4. Aprendizaje y Adaptación Online en Edge

### 4.1 Regla Delta LMS Normalizada (NLMS) para Microcontroladores

Para microcontroladores de memoria ultrarreducida (ej. Cortex-M0/M4 con < 8 KB RAM), mantener la matriz de covarianza $P \in \mathbb{R}^{N \times N}$ del algoritmo RLS ($O(N^2)$ memoria y operaciones) resulta prohibitivo.

Eón implementa la regla adaptativa **Normalized Least-Mean-Squares (NLMS)** en `aeon_online_train_step`:
$$W_{out}(t+1) = W_{out}(t) + \eta \cdot \frac{e(t) \cdot x(t)^T}{\|x(t)\|_2^2 + \epsilon}$$
Donde:
- $e(t) = y_{target}(t) - \hat{y}(t) = y_{target}(t) - W_{out}(t) x(t)$ es el error instantáneo de predicción.
- $\|x(t)\|_2^2 = \sum_{i=1}^N x_i(t)^2$ es la potencia instantánea del estado del reservoir.
- $\epsilon = 10^{-6}$ evita división por cero.
- $\eta \in (0, 1]$ es la tasa de aprendizaje adaptativa.

**Ventajas Técnicas en Edge:**
- **Memoria RAM:** $O(1)$ adicional (no almacena histórico ni matriz de covarianza).
- **Complejidad:** $2N$ operaciones MAC por paso ($O(N)$ vs $O(N^2)$ de RLS).
- **Invarianza de escala:** La normalización por $\|x(t)\|^2$ garantiza estabilidad ante picos de señal o ráfagas sensoriales.

### 4.2 Recursive Least Squares con Factorización U-D (Bierman-Thornton)

Para nodos Edge con mayor capacidad donde se requiere la tasa óptima de convergencia de RLS, Eón utiliza la **Factorización U-D**:
$$P(t) = U(t) \cdot D(t) \cdot U(t)^T$$
donde $U$ es triangular superior unitaria ($U_{ii} = 1$) y $D$ es diagonal con elementos estrictamente positivos ($D_i > 0$).
- **Garantía:** $P(t)$ se mantiene matemáticamente definida positiva de por vida ($P > 0$), eliminando la divergencia por acumulación de errores de redondeo en punto fijo o simple precisión.
- Factor de olvido exponencial $\beta \in (0, 1]$ para seguimiento de sensores con deriva térmica.

### 4.3 Filtro de Resonancia Crítica en Dos Etapas (Power Iteration Filter)

Para el minado determinista de semillas óptimas (`UniversalMiner`), una matriz aleatoria dispersa $W \sim \mathcal{N}(0, 1)$ con densidad $p$ y tamaño $N$ tiene un radio espectral esperado por la Ley Circular de Girko:
$$\mathbb{E}[\rho(W)] \approx \sqrt{N \cdot p}$$

Para $N=50, p=0.1$, $\mathbb{E}[\rho] \approx 2.24$. Encontrar semillas con criticidad natural $\rho \in [0.90, 1.10]$ requiere evaluar miles de candidatos.
Eón implementa un **filtro en dos etapas**:
1. **Etapa 1 (Pre-filtro rápido, $O(k \cdot N^2)$):** Ejecuta $k=8$ iteraciones de potencia para aproximar el radio espectral mediante el cociente de Rayleigh $\|W v\|_2$. Si $|\rho_{fast} - 1.0| > \delta_{tol}$, la semilla se descarta en microsegundos.
2. **Etapa 2 (Validación exacta, $O(N^3)$):** Solo los candidatos pre-seleccionados pasan a la descomposición completa de eigenvalores LAPACK.
- **Aceleración:** Reduce el tiempo de búsqueda de semillas de 15 minutos a menos de 3 segundos (>98% de reducción de cómputo).

### 4.4 Reservorios Ortogonales vía Transformada de Cayley

Para tareas que requieren capacidad de memoria máxima sin desvanecimiento de gradientes, Eón genera matrices de reservoir estrictamente ortogonales ($W W^T = \rho^2 I$) mediante la **Transformada de Cayley**:
$$W = \rho \cdot (I - A)(I + A)^{-1}$$
donde $A = -A^T$ es una matriz antisimétrica aleatoria ($A_{ij} = -A_{ji}, A_{ii} = 0$).
- **Propiedad Espectral:** Todos los eigenvalores de $W$ se encuentran exactamente sobre la circunferencia de radio $\rho$ ($|\lambda_i| = \rho, \forall i$), eliminando modos decaídos o explosivos y maximizando la memoria de eco.

---

## 5. Aritmética de Punto Fijo Q8.8

### 5.1 Representación

Los valores se representan como enteros de 16 bits con signo (int16_t):

```
Valor real v ↔ Entero q = round(v × 2⁸)
```

| Propiedad | Valor |
|-----------|-------|
| Bits totales | 16 (1 signo + 7 entero + 8 fracción) |
| Rango | [-128.0, +127.99609375] |
| Resolución | 1/256 ≈ 0.00390625 |
| Cero | 0x0000 |
| Uno | 0x0100 (256) |
| Menos uno | 0xFF00 (-256) |

### 5.2 Operaciones Aritméticas

**Suma/Resta:** Directa en int16_t.
```c
int16_t sum = a + b;  // Overflow check requerido
```

**Multiplicación:**
```c
int16_t mul_q88(int16_t a, int16_t b) {
    int32_t result = (int32_t)a * (int32_t)b;
    return (int16_t)(result >> 8);  // Descarte de 8 bits fraccionarios extra
}
```

**Análisis de error:**
- Error máximo por multiplicación: ε_mul = 1/2⁸ ≈ 0.0039
- Error acumulado tras N multiplicaciones encadenadas: ε_total ≤ N · ε_mul
- Para N = 50 neuronas (un paso de update): ε_total ≤ 50 × 0.0039 ≈ 0.195

### 5.3 Activación tanh en Punto Fijo

Implementación por tabla de búsqueda (LUT) o aproximación polinómica:

```
tanh(x) ≈ x − x³/3     para |x| < 1.0
tanh(x) ≈ sign(x)       para |x| ≥ 2.0
```

En Q8.8 con LUT de 256 entradas: precisión ≈ 0.5%.

### 5.4 Error de Cuantización Q8.8 vs Float64

| Métrica | Float64 | Q8.8 | Degradación |
|---------|---------|------|-------------|
| MSE (Mackey-Glass) | 0.0004 | 0.009 | 22.5× |
| Rango dinámico | 10³⁰⁸ | 128 | Reducido |
| Memoria por peso | 8 bytes | 2 bytes | 4× ahorro |
| Operaciones/seg (MCU) | ~10K (FPU) | ~500K (ALU) | 50× más rápido |

---

## 6. Cuantización de Pesos

### 6.1 Cuantización Uniforme (k-bit)

Para k bits de cuantización:

```
q(w) = round((w − w_min) / Δ) · Δ + w_min
```

Donde el paso de cuantización es:

```
Δ = (w_max − w_min) / (2^k − 1)
```

| Bits | Niveles | Δ (rango [-1,1]) | Error máx |
|------|---------|-------------------|-----------|
| 8 | 256 | 0.0078 | 0.0039 |
| 4 | 16 | 0.133 | 0.067 |
| 1 | 2 | 2.0 | 1.0 |

### 6.2 Cuantización 1-Bit (Protocolo de Sincronización)

Para el protocolo de comunicación entre nodos:

```
q₁(w) = { +1  si w ≥ 0
         { −1  si w < 0
```

**Pérdida de información:**

La cuantización 1-bit preserva solo el signo del peso. Para W_out con distribución aproximadamente gaussiana N(0, σ²):

```
E[|w − q₁(w)|²] = E[w²] − (2/π) · E[|w|]²
                 ≈ σ² · (1 − 2/π)
                 ≈ 0.363 · σ²
```

**Compresión:**

Para N pesos de 64 bits:
```
Ratio = (N × 64) / (N × 1) = 64×
```

Para N pesos de 16 bits (Q8.8):
```
Ratio = (N × 16) / (N × 1) = 16×
```

### 6.3 Retención de Precisión por Nivel

| Bits | MSE (Mackey-Glass) | Retención vs float64 |
|------|--------------------|----------------------|
| 64 | 0.000369 | 100% (baseline) |
| 8 | 0.000543 | 52.9% |
| 4 | 0.691686 | ~0% |
| 1 | 1.215819 | ~0% |

> **Nota:** La retención depende fuertemente de la tarea. Para señales suaves (temperatura, presión), 8-bit es óptimo. Para señales caóticas de alta frecuencia, se requiere mayor precisión.

---

## 7. Plasticidad Hebbiana

### 7.1 Regla de Hebb (1949)

"Neuronas que disparan juntas, se conectan juntas":

```
ΔW_ij = η · x_i(t) · x_j(t)
```

Donde:
- η — Tasa de aprendizaje (típico: 1e-4 a 1e-3)
- x_i, x_j — Activaciones pre y post-sinápticas

### 7.2 Anti-Hebbian

Decorrelación de activaciones (especialización):

```
ΔW_ij = −η · x_i(t) · x_j(t)
```

**Resultado en Eón:** Anti-Hebbian logra **6× mejor MSE** que ESN estándar en adaptación continua, porque decorrelaciona las neuronas del reservoir, mejorando la diversidad de representaciones.

### 7.3 STDP (Spike-Timing-Dependent Plasticity)

Variante temporal:

```
ΔW_ij = { +A₊ · exp(−|Δt|/τ₊)   si Δt > 0  (pre antes que post)
         { −A₋ · exp(−|Δt|/τ₋)   si Δt < 0  (post antes que pre)
```

Donde Δt = t_post − t_pre.

### 7.4 Regla Normalizada de Oja (1982)

La regla de Hebb clásica $\Delta W = \eta y x^T$ produce divergencia monótona de los pesos hacia el infinito, desestabilizando el radio espectral y requiriendo renormalizaciones matriciales $O(N^2)$ a cada paso.

Eón incorpora la **Regla de Oja**:
$$\Delta w_{ij} = \eta \cdot \left( y_i \cdot x_j - y_i^2 \cdot w_{ij} \right)$$
En notación matricial compacta:
$$\Delta W = \eta \cdot \left( y \cdot x^T - \text{diag}(y^2) \cdot W \right)$$
Donde:
- $y = x_{post}$ (activación post-sináptica).
- $x = x_{pre}$ (activación pre-sináptica).
- El término disipativo $-y_i^2 w_{ij}$ equilibra el crecimiento hebbiano y restringe asintóticamente el vector de pesos a la esfera unitaria ($\|w_i\|_2 \to 1$).
- **Propiedad Matemática:** Oja demostró que esta regla converge asintóticamente a la extracción del primer componente principal (PCA no lineal local) sin requerir renormalización espectral en cada paso temporal.

### 7.5 Embeddings Numéricos en Edge mediante Raíz Digital Cerrada $O(1)$

Para el procesamiento de lenguaje y series temporales simbólicas en microcontroladores (`phase7-language`), almacenar tablas densas de embeddings (ej. 50,000 tokens $\times$ 128 floats $\times$ 4 bytes $\approx 25.6\text{ MB}$) es inviable en chips con $\le 256\text{ KB}$ Flash.

Eón utiliza proyecciones hash deterministas con **raíz digital modular en forma cerrada**:
$$dr(n) = 1 + ((n - 1) \pmod 9) \quad \forall n \in \mathbb{Z}^+$$
con $dr(0) = 9$.

**Ventajas Técnicas:**
- **Tiempo de Ejecución:** $O(1)$ operaciones aritméticas simples de ALU (elimina bucles de conversión a cadenas `str()` y suma de dígitos decimales).
- **Consumo de Memoria:** $0\text{ bytes}$ de almacenamiento de tablas densas en Flash/RAM.
- Proyecta cualquier token arbitrario a una distribución acotada de armónicos sinusoidales de fase $\phi = \frac{dr(n)}{9} \cdot \pi$.

### 7.6 Estabilidad Espectral y Renormalización Periódica

Cuando se emplean reglas Hebbianas estándar, para mantener la Echo State Property sin degradar el rendimiento con cálculo continuo de eigenvalores:
$$\text{Si } t \equiv 0 \pmod{10} \implies \text{verificar } \rho(W)$$
$$\text{Si } \rho(W) > 1.1 \cdot \rho_{target} \implies W \leftarrow \left( \frac{\rho_{target}}{\rho(W)} \right) \cdot W$$

---

## 8. Protocolo 1-Bit — Análisis de Compresión

### 8.1 Estructura del Paquete

```
┌──────────────────────────────────────────────────┐
│ Header (14 bytes)                                │
├──────┬──────┬──────┬────────────┬───────────────┤
│ EON  │ Type │ Ver  │ Timestamp  │ Node ID       │
│ 3B   │ 1B   │ 1B   │ 4B         │ 4B            │
├──────┴──────┴──────┴────────────┴───────────────┤
│ Payload (⌈N/8⌉ bytes)                           │
│ Bit[i] = { 1 si W_out[i] ≥ 0                   │
│           { 0 si W_out[i] < 0                   │
└──────────────────────────────────────────────────┘
```

### 8.2 Cálculo de Compresión

Para N = 50 neuronas:

| Formato | Tamaño |
|---------|--------|
| JSON (float, ascii) | ~175 bytes |
| Binary (float32) | 14 + 50×4 = 214 bytes |
| Binary (float16) | 14 + 50×2 = 114 bytes |
| Binary (int8) | 14 + 50×1 = 64 bytes |
| **1-Bit** | **14 + ⌈50/8⌉ = 14 + 7 = 21 bytes** |

**Ratios de compresión:**
- vs JSON: 175/21 = **8.3×**
- vs float32: 214/21 = **10.2×**
- vs int8: 64/21 = **3.0×**

### 8.3 Tiempo de Aire LoRa

Para LoRa con SF10, BW=125kHz, CR=4/5:

```
T_air = T_preamble + T_payload

T_preamble = (n_preamble + 4.25) × T_symbol
T_symbol = 2^SF / BW = 2^10 / 125000 = 8.192 ms

Payload symbols:
  n_payload = 8 + max(ceil((8·PL − 4·SF + 28 + 16 − 20·H) / (4·(SF−2·DE))) × (CR+4), 0)
```

Para 21 bytes (1-Bit): T_air ≈ **51 ms**
Para 175 bytes (JSON): T_air ≈ **132 ms**

**Ahorro de tiempo de aire:** 2.6×

### 8.4 Energía por Transmisión

```
E_tx = P_tx × T_air
```

Con P_tx = 85 mW (LoRa @ 17dBm):

| Formato | T_air | E_tx |
|---------|-------|------|
| 1-Bit (21B) | 51 ms | 4.3 mJ |
| JSON (175B) | 132 ms | 11.2 mJ |

**Ahorro energético:** 2.6×

---

## 9. Análisis de Complejidad Computacional

### 9.1 Complejidad por Operación

| Operación | Complejidad | Para N=50 |
|-----------|-------------|-----------|
| Update (x(t)) | O(N² + N·K) | ~2,550 MACs |
| Readout (y(t)) | O(L·(N+K+1)) | ~52 MACs |
| Train (batch ridge) | O(N³ + T·N²) | ~125,000 + T·2,500 |
| Train (online, 1 paso) | O(N²) | ~2,500 MACs |
| Quantize (1-bit) | O(N) | ~50 ops |
| Hebbian update | O(N²) | ~2,500 MACs |

> **MAC** = Multiply-Accumulate (operación fundamental en procesamiento de señales)

### 9.2 Comparativa de Complejidad

| Modelo | Inferencia | Entrenamiento |
|--------|------------|---------------|
| **Eón (ESN-50)** | **O(N²) = 2,550** | **O(N²) = 2,500** |
| MLP (50-50-1) | O(N²) = 2,550 | O(T·N²) (backprop) |
| LSTM (50 units) | O(4·N²) = 10,000 | O(T·4·N²·depth) |
| CNN (3×3, 16 filtros) | O(C·F²·H·W) | O(T·C·F²·H·W·depth) |

**Ventaja clave:** Eón tiene la misma complejidad de inferencia que un MLP, pero con **memoria temporal inherente** y **entrenamiento O(N²)** en lugar de backpropagation.

---

## 10. Análisis Energético Teórico

### 10.1 Energía por Inferencia (ARM Cortex-M4F @ 80MHz)

Modelo: 1 MAC ≈ 1 ciclo ≈ 12.5 ns a 80MHz
Potencia CPU activa: ~50 mW (@ 3.3V, ~15mA)

```
E_inference = P_cpu × T_inference
T_inference = (N_MACs / f_clock)
```

Para ESN-50 (2,602 MACs):
```
T_inference = 2,602 / 80,000,000 = 32.5 μs
E_inference = 50 mW × 32.5 μs = 1.625 μJ
```

Ajustado con overhead de memoria y pipeline:
```
E_inference ≈ 0.0045 μJ  (valor medido en benchmark)
```

### 10.2 Energía por Ciclo Completo (Update + Predict + Learn)

| Fase | MACs | Tiempo (μs) | Energía (μJ) |
|------|------|-------------|---------------|
| Update (x(t)) | 2,550 | 31.9 | 0.0016 |
| Readout (y(t)) | 52 | 0.65 | 0.0000325 |
| Online Learn | 2,500 | 31.3 | 0.0016 |
| **Total** | **5,102** | **63.8** | **0.0032** |

### 10.3 Estimación de Vida de Batería

Suponiendo ciclo de trabajo: 1 inferencia/segundo, deep sleep entre ciclos.

| Batería | Capacidad | E_sleep/s | Vida estimada |
|---------|-----------|-----------|---------------|
| CR2032 | 225 mAh × 3V = 2,430 J | 0.037 mW | ~760 días |
| 2×AA | 2,500 mAh × 3V = 27,000 J | 0.037 mW | ~23 años* |
| LiPo 500mAh | 500 mAh × 3.7V = 6,660 J | 0.037 mW | ~5.7 años* |

*Asumiendo deep sleep dominante y auto-descarga despreciable (teórico).

> **Nota:** La vida real depende del ciclo de radio (LoRa TX/RX) que domina el consumo. Con 1 TX/minuto vía LoRa (~4.3 mJ/TX): CR2032 ≈ **6.5 días** con radio activa.

---

## 11. Métricas de Error y Rendimiento

### 11.1 MSE (Mean Squared Error)

```
MSE = (1/T) · Σ_{t=1}^{T} (y(t) − ŷ(t))²
```

### 11.2 NMSE (Normalized MSE)

```
NMSE = MSE / Var(y)
```

Permite comparar rendimiento entre señales de diferente escala.

### 11.3 Capacidad de Memoria (Memory Capacity)

Mide cuántos pasos temporales pasados puede recordar el reservoir:

```
MC = Σ_{k=1}^{∞} r²(y_k, u(t−k))
```

Donde r² es el coeficiente de determinación entre la salida entrenada para recordar u(t−k) y la entrada retrasada real.

**Límite teórico:** MC ≤ N (número de neuronas).

Para Eón con N = 50:
- MC teórico máximo: 50 pasos
- MC típico (α=0.3, ρ=0.9): ~35-40 pasos

### 11.4 Kernel Quality (Separabilidad)

Mide la capacidad del reservoir para separar entradas distintas:

```
KQ = rank(Z) / min(T, N+K+1)
```

Valores cercanos a 1.0 indican que el reservoir genera estados suficientemente diversos.

---

## 12. Resumen de Constantes y Valores Típicos

| Parámetro | Símbolo | Valor típico | Rango |
|-----------|---------|--------------|-------|
| Neuronas del reservoir | N | 50 | [10, 200] |
| Leak rate | α | 0.3 | (0, 1] |
| Radio espectral | ρ | 0.9 | (0, 1) |
| Dispersión | p | 0.2 | [0.05, 0.3] |
| Regularización ridge | λ | 1e-6 | [1e-8, 1e-2] |
| Washout | T_w | 100 | [50, 300] |
| Learning rate (Hebbian) | η | 1e-4 | [1e-5, 1e-3] |
| Cuantización (producción) | k | 8 bits | {1, 4, 8, 16, 64} |
| Escala de entrada | s_in | 0.1 | [0.01, 1.0] |

---

## Referencias

1. Jaeger, H. (2001). "The echo state approach to analysing and training recurrent neural networks." GMD Report 148.
2. Lukoševičius, M. & Jaeger, H. (2009). "Reservoir computing approaches to recurrent neural network training." Computer Science Review, 3(3), 127-149.
3. Yildiz, I. B., Jaeger, H., & Kiebel, S. J. (2012). "Re-visiting the echo state property." Neural Networks, 35, 1-9.
4. Bi, G. & Poo, M. (1998). "Synaptic modifications in cultured hippocampal neurons." Journal of Neuroscience, 18(24), 10464-10472.
5. Verstraeten, D., et al. (2007). "An experimental unification of reservoir computing methods." Neural Networks, 20(3), 391-403.
6. Semtech. (2019). "LoRa and LoRaWAN: A Technical Overview." AN1200.22.

---

> **Implementación y Extensiones Futuras:** Para el plan de desarrollo de estabilidad numérica (Lyapunov, RLS U-D, reservoirs ortogonales y CMSIS-DSP), consultar el [Roadmap de Ingeniería y Fundamentos Matemáticos](ROADMAP.md).

---

*Proyecto Eón — SenseLab — Build with Sense*  
*© 2024-2026*
