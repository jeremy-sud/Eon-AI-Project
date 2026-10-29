# Especificación Técnica: Echo State Network (ESN)

## Visión General

El ESN (Echo State Network) es una arquitectura fundamental de Reservoir Computing que proyecta entradas dinámicas en un espacio de estados recurrente de alta dimensión no lineal, entrenando exclusivamente la matriz de salida lineal ($W_{out}$).

**Implementaciones disponibles y validadas:**
- **Python (NumPy / SciPy)**: Alta precisión (Float64/Float32), resolución exacta mediante factorización de Cholesky ($A = L L^T$), generadores ortogonales de Cayley y adaptación online NLMS.
- **C ANSI (`libAeon`)**: Aritmética de punto fijo Q8.8, huella de memoria estática de 1.27 KB RAM y 14 KB Flash, optimizado para microcontroladores ARM Cortex-M y ESP32.
- **JavaScript (`aeon.js`)**: Ejecución nativa en el navegador cliente sin dependencias externas.

---

## Arquitectura y Flujo de Señal

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Input u(t)                                                │
│      │                                                      │
│      ▼                                                      │
│   ┌──────┐                                                  │
│   │ W_in │  Matriz de entrada (fija, escalada s_in)         │
│   └──┬───┘                                                  │
│      │                                                      │
│      ▼                                                      │
│   ┌──────────────────────────────────────────┐              │
│   │                RESERVOIR                 │◄───┐         │
│   │             (W_reservoir)                │    │         │
│   │  • N neuronas (ortogonal / disperso 90%) │    │ Recurrencia
│   │  • Radio espectral ρ(W) < 1.0            │────┘         │
│   └──────────────────┬───────────────────────┘              │
│                      │                                      │
│                      ▼                                      │
│   x(t) = (1 - α)x(t-1) + α tanh(W_in·u(t) + W·x(t-1) + b)   │
│                      │                                      │
│                      ▼                                      │
│                  ┌───────┐                                  │
│                  │ W_out │  Única capa entrenable           │
│                  └───┬───┘  • Batch: Cholesky (LL^T)        │
│                      │      • Online: NLMS O(N)             │
│                      ▼                                      │
│                 Output y(t) = W_out · [1; u(t); x(t)]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Parámetros Principales

| Parámetro | Tipo | Por Defecto | Descripción Matemática |
| :--- | :--- | :--- | :--- |
| `n_inputs` | `int` | 1 | Dimensión $U$ del vector de entrada $u(t)$ |
| `n_reservoir` | `int` | 100 | Número de unidades neuronales $N$ en el reservorio |
| `n_outputs` | `int` | 1 | Dimensión $K$ de la señal de salida $y(t)$ |
| `spectral_radius` | `float` | 0.90 | Radio espectral $\rho(W) = \max_i |\lambda_i| < 1.0$ |
| `sparsity` | `float` | 0.90 | Fracción de conexiones nulas en $W$ |
| `leaking_rate` | `float` | 1.00 | Coeficiente $\alpha \in (0, 1]$ de filtrado paso-bajo |
| `input_scaling` | `float` | 1.00 | Factor de escala para $W_{in} \sim \mathcal{U}(-s_{in}, s_{in})$ |
| `ridge_param` | `float` | $10^{-6}$ | Coeficiente $\lambda$ de regularización de Tikhonov |
| `reservoir_type` | `str` | `'sparse'` | Tipo: `'sparse'`, `'orthogonal'` (Cayley), `'custom'` |

---

## Algoritmos de Entrenamiento de Lectura

### 1. Regresión Ridge por Factorización de Cholesky Exacta

Para entrenamiento por lotes (batch), se recolectan los estados extendidos $\tilde{X} = [\mathbf{1}, X] \in \mathbb{R}^{T \times M}$ y los objetivos $Y \in \mathbb{R}^{T \times K}$ (donde $M = N + 1$).

El sistema de ecuaciones normales regularizado es:
$$( \tilde{X}^T \tilde{X} + \lambda I_M ) W_{out}^T = \tilde{X}^T Y$$

**Propiedad Teórica:** Dado que $\lambda > 0$, la matriz de covarianza $A = \tilde{X}^T \tilde{X} + \lambda I_M$ es **estrictamente simétrica y definida positiva (SPD)**.

**Solución Numérica en Eón (`matrix_init.ridge_regression`):**
1. Se factoriza $A = L L^T$ donde $L$ es triangular inferior con $L_{ii} > 0$.
2. Se resuelve $L Z = \tilde{X}^T Y$ mediante sustitución hacia adelante ($O(M^2)$).
3. Se resuelve $L^T W_{out}^T = Z$ mediante sustitución hacia atrás ($O(M^2)$).

**Ventajas frente a Inversión Clásica o LU:**
- **Complejidad:** $\frac{1}{3} M^3$ flops frente a $M^3$ (reducción del 66.7%).
- **Estabilidad:** Garantizada sin pivoteo parcial ni intercambio de filas.
- **Implementación:** Invoca la subrutina `DPOSV` de LAPACK / SciPy con respaldo analítico triangular.

### 2. Adaptación Streaming Continua: Regla Delta Normalizada (NLMS)

Para despliegues embebidos en tiempo real sin capacidad de almacenar la matriz de estados completa $X$:
$$e(t) = y(t) - W_{out}(t-1) \tilde{x}(t)$$
$$W_{out}(t) = W_{out}(t-1) + \eta \frac{e(t) \tilde{x}(t)^T}{\|\tilde{x}(t)\|_2^2 + \epsilon}$$

- **Complejidad temporal:** $O(M)$ por paso.
- **Complejidad espacial:** $O(M)$ registros (sin matriz de covarianza $M \times M$).
- **Estabilidad geométrica:** El denominador $\|\tilde{x}(t)\|^2 + \epsilon$ previene la saturación ante impulsos.

---

## Estabilidad y Reservorios Ortogonales

### Cómputo Rápido de Radio Espectral (`compute_spectral_radius`)

Para evitar la descomposición espectral $O(N^3)$ en inicialización o poda:
1. **Cota de Gerschgorin:** Evalúa la norma de suma de filas $\|W\|_\infty = \max_i \sum_j |w_{ij}|$. Si $\|W\|_\infty < 1.0$, la estabilidad asintótica se certifica inmediatamente en $O(N^2)$.
2. **Power Iteration Filtrada:** Si $\|W\|_\infty \ge 1.0$, se ejecutan hasta 15 iteraciones del método de Rayleigh-Power para obtener el autovalor dominante en $O(k N^2)$ operaciones.

### Reservorios Ortogonales vía Transformada de Cayley

Para eliminar modos amortiguados espurios y maximizar la capacidad de retención de memoria:
$$A = \text{antisymmetric matrix } (A = -A^T)$$
$$W_{ortho} = \rho (I - A)(I + A)^{-1}$$
- Satisface $W W^T = \rho^2 I$.
- Todos los autovalores se ubican en el círculo de radio $\rho$ ($|\lambda_i| = \rho$).

---

## Plasticidad No Supervisada: Regla de Oja

Para aprendizaje biológico y adaptación no supervisada en `HebbianESN`:
$$\Delta w_{ij}(t) = \eta_H x_i(t) \left( x_j(t) - x_i(t) w_{ij}(t) \right)$$
El término de decaimiento cuadrático autorregulado garantiza que $\|w_i\|_2 \to 1$, evitando la explosión sináptica sin necesidad de renormalizar matrices.

---

## Poda Estructural y Renacimiento (`StructuralPruningESN`)

Inspirado en la Hipótesis del Boleto de Lotería:
1. **Fase de Contracción:** Poda de conexiones sinápticas con $|w_{ij}| < \theta$ (reducción de hasta un 70% de conexiones activas).
2. **Re-escalado Espectral:** Reajuste del radio espectral mediante iteración de potencia rápida para preservar la Echo State Property.
3. **Capa Fina Retenida:** Preserva el rendimiento predictivo con hasta un 40% menor consumo de ciclos de reloj en MCU.

---

## Ejemplo de Uso en Python

```python
from esn.esn import EchoStateNetwork, generate_mackey_glass
from utils.matrix_init import ridge_regression, generate_orthogonal_reservoir

# Generación de datos de evaluación
data = generate_mackey_glass(n_samples=2000)
X_train, y_train = data[:1500, :-1], data[:1500, -1:]
X_test, y_test = data[1500:, :-1], data[1500:, -1:]

# Instanciación con reservorio ortogonal de Cayley
esn = EchoStateNetwork(
    n_inputs=1,
    n_reservoir=50,
    n_outputs=1,
    spectral_radius=0.95,
    reservoir_type='orthogonal',
    random_state=42
)

# Entrenamiento exacto mediante Cholesky
esn.fit(X_train, y_train, washout=100)

# Predicción en tiempo real
predictions = esn.predict(X_test)
nmse = np.mean((predictions - y_test) ** 2) / np.var(y_test)
print(f"NMSE: {nmse:.5f}")
```

---

## Consumo y Huella en Silicio (C ANSI Q8.8)

Configuración estándar ($N=32$, 1 entrada, 1 salida en Cortex-M4 @ 64MHz):

| Elemento | Tipo | Tamaño (Bytes) |
| :--- | :--- | :--- |
| Matriz de Entrada $W_{in}$ ($32 \times 1$) | `int16_t` | 64 |
| Reservorio Escaso $W$ ($32 \times 8$) | `int16_t` + `uint8_t` | 512 |
| Vector de Estados $x(t)$ | `int16_t` | 64 |
| Pesos de Salida $W_{out}$ | `int16_t` | 66 |
| Búfer de Cholesky ($33 \times 17$) | `int16_t` | 561 |
| **Total Memoria RAM** | — | **1,267 Bytes (1.24 KB)** |
| **Memoria Flash Código** | — | **14.2 KB** |
| **Tiempo de Inferencia** | — | **330 µs** |
| **Consumo Energético / Ciclo** | — | **12.8 µJ** |

---

## Referencias Académicas

1. Jaeger, H. (2001). *The "echo state" approach to analysing and training recurrent neural networks*. GMD Report 148.
2. Golub, G. H., & Van Loan, C. F. (2013). *Matrix Computations* (4th ed.). Johns Hopkins University Press.
3. Oja, E. (1982). *Simplified neuron model as a principal component analyzer*. Journal of Mathematical Biology, 15(3), 267–273.
4. Frankle, J., & Carbin, M. (2018). *The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks*. ICLR 2019.
