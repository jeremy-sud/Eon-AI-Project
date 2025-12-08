# 🏛️ Architecture: The Eon Principle

> "La inteligencia no se crea, se descubre."

The Eon Project is built on the philosophy that complex behavior can emerge from simple, chaotic dynamical systems when observed correctly.

## Core Concepts

### 1. The Zero Moment (Momento Cero)

Unlike traditional Neural Networks that start with "random initialization" as a disposable step, Eon treats initialization as a **Birth**.

- **The Certificate**: Every Eon instance is born with a unique 16-byte hash derived from its birth time and seed.
- **Why?**: This supports the "Collective Mind" phase. If two nodes have the same seed, they mathematically have the exact same "mind" (reservoir dynamics) and can share learned weights ($W_{out}$) instantly without transmitting the entire model.

### 2. Reservoir Computing (The Liquid Brain)

The core engine is an **Echo State Network (ESN)**.

- **Input Layer ($W_{in}$)**: Projects low-dimensional sensory data into the high-dimensional reservoir. Random, fixed.
- **Reservoir ($W_{res}$)**: A sparse, recurrently connected "liquid" of neurons. It creates a complex, dynamic echo of the input history. Random, fixed.
- **Readout ($W_{out}$)**: The ONLY part that learns. It learns to combine the chaotic signals of the reservoir to produce the desired output.

### 3. Minimalist Memory Model

To run on 8-bit microcontrollers:

- **Fixed Point Arithmetic**: Uses Q8.8 fixed point math (optional) to avoid expensive floating point units (FPU).
- **On-the-fly Generation**: Instead of storing the massive $W_{res}$ matrix, we can regenerate weights procedurally using the seed (in extreme memory constraints), trading CPU for RAM. _Current implementation stores sparse generic weights._

## Data Flow

```mermaid
graph LR
    Input([Input]) -->|W_in| Reservoir
    Reservoir -->|Recurrent W_res| Reservoir
    Reservoir -->|W_out (Learned)| Output([Output])

    style Input fill:#f9f,stroke:#333
    style Reservoir fill:#bbf,stroke:#333
    style Output fill:#9f9,stroke:#333
```

1.  **Update**: $x(t) = (1-\alpha)x(t-1) + \alpha \tanh(W_{in}u(t) + W_{res}x(t-1))$ (Leaky integrator model option)
2.  **Predict**: $y(t) = W_{out} [1; u(t); x(t)]$
3.  **Learn**: Ridge Regression (Online or Batch) on $W_{out}$.

## "TinyLM" vs Eon Motor

- **Eon Motor**: Recurrent, continuous, signal processing, control, time-series prediction.
- **TinyLM**: Discrete, statistical, text generation.
  Current Phase 7 explores using the Eon Motor Principle for language (predicting next character embedding) rather than standard Transformers.
