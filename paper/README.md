# Academic Paper: Eón Project (English Version)

## Title
**Eón: Ultra-Lightweight Neuromorphic Intelligence via Exact Cholesky Factorization and Adaptive Reservoir Computing for Edge Microcontrollers**

## Abstract & Scope
This paper demonstrates that robust temporal machine learning does not require multi-gigabyte deep learning models or high-power GPUs. Eón operates deterministically on sub-\$3 edge microcontrollers with **1.3 KB RAM and 14 KB Flash**, achieving chaotic time-series prediction and real-time adaptation at **12.8 µJ per inference**.

## Modular Document Structure
```
paper/
├── main.tex                    # Master LaTeX file
├── main.pdf                    # Compiled 10-page academic publication
├── references.bib              # Complete BibTeX citations
├── sections/
│   ├── abstract.tex            # Abstract with core findings & energy metrics
│   ├── introduction.tex        # Motivation, TinyML trade-offs, and 7 contributions
│   ├── methodology.tex         # Exact Cholesky derivation, NLMS delta rule, Cayley transform
│   ├── experiments.tex         # Mackey-Glass, solver benchmarks, energy breakdown, bio/voice
│   └── conclusion.tex          # Formal summary, silicon implications, future work
└── README.md                   # This documentation
```

## Mathematical & Technical Highlights
1. **Exact Cholesky Factorization ($A = L L^T$)**: Proves regularized ESN covariance matrix is strictly Symmetric Positive-Definite (SPD). Solves readout weights with $\frac{1}{3} M^3$ flops ($2.98\times$ faster on Cortex-M4) with zero pivoting and unconditional numerical stability.
2. **Streaming NLMS Online Adaptation**: Constant $O(M)$ memory and time complexity for continuous learning without covariance accumulation.
3. **Cayley Transform Orthogonal Reservoirs**: $W = \rho (I - A)(I + A)^{-1}$ where $A = -A^T$, keeping all eigenvalues on the circle $|\lambda| = \rho$ to prevent mode decay.
4. **Spectral Criticality Filter**: Two-stage evaluation using Gerschgorin row-sum bound followed by Rayleigh power iteration ($O(k N^2)$ vs $O(N^3)$).
5. **Oja's Normalized Synaptic Plasticity**: Guarantees $\|w_i\|_2 \to 1$ without per-step matrix eigendecomposition.
6. **Decentralized Swarm Synchronization**: Deterministic LCG seed sharing with 1-bit sign quantization achieving $8.3\times$ payload reduction and $2.6\times$ energy savings over LoRa links.

## Compilation Instructions

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The resulting `main.pdf` is mirrored to `web/static/eon-paper.pdf` to be served directly through the web UI.

---
(c) 2024-2026 SenseLab Research
