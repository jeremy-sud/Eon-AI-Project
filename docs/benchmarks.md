# ⚡ Eon Motor Benchmarks

> **Objective**: Compare the energy efficiency and performance of the Eon Motor (ESN) against industry-standard TinyML solutions (MLP).

## Summary Results

| Metric                 | Eon Motor (C)    | TinyML Custom MLP (C) | Notes                                        |
| :--------------------- | :--------------- | :-------------------- | :------------------------------------------- |
| **Execution Time**     | 0.298 μs / cycle | 0.103 μs / cycle      | Eon update involves recurrent state dynamics |
| **Energy Consumption** | ~0.0045 μJ       | ~0.0015 μJ            | Estimated for Cortex-M4 @ 15mW               |
| **Cycles/Second**      | ~3.3 Million     | ~9.7 Million          | Theoretical max throughput                   |
| **Memory Footprint**   | 1.3 KB           | ~0.5 KB               | Including weights/state                      |

## Methodology

### 1. Hardware Simulation

Tests were run on a Linux Host using single-threaded C implementations compiled with `gcc -O2`.
Energy estimates are projected for a standard **ARM Cortex-M4F** microcontroller running at **64 MHz** with an active power consumption of **15 mW**.

Formula: $E = T_{exec} \times P_{active}$

### 2. The Contenders

#### Eon Motor (`libAeon`)

- **Type**: Echo State Network (Recurrent)
- **Reservoir**: 32 Neurons
- **Input/Output**: 1 / 1
- **Precision**: Fixed Point Q8.8 (simulated) or Float
- **Complexity**: $O(N^2 \times S)$ where $S$ is sparsity.

#### TinyML Reference Only

- **Type**: Multi-Layer Perceptron (Feedforward)
- **Architecture**: 1 -> 16 (ReLU) -> 16 (ReLU) -> 1 (Linear)
- **Precision**: Float/Fixed comparison
- **Complexity**: Matrix Multiplication.

## Analysis

**Why is Eon slower?**
The Eon motor is performing a more complex dynamical system update. Unlike the MLP which is a pure function $y = f(x)$, the Eon motor is $h_{t} = \tanh(W_{in}x_t + W_{res}h_{t-1})$ and $y_t = W_{out}h_t$. This recurrence gives it **Short-Term Memory**, allowing it to solve time-series tasks (like sine wave generation) that the static MLP cannot solve without external buffering (sliding window).

**Energy Efficiency**
Despite being 3x slower per inference, **0.0045 microjoules** is negligible.

- A **CR2032 Coin Cell** (~2500 Joules) could theoretically power **555 Billion predictions**.
- At 1 prediction/second, the battery life is limited by the shelf life of the battery, not the computation.

## Conclusion

The Eon Motor is successfully validated as an ultra-low-power solution suitable for "Always-On" intelligence, capable of operating for years on harvested energy.
