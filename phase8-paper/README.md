# Paper Académico - Proyecto Eón (Versión en Español)

## Título
**Eón: Arquitectura Neuromórfica Extremadamente Compacta con Factorización de Cholesky y Aprendizaje Adaptativo en Microcontroladores Edge**

## Estructura del Módulo

```
phase8-paper/
├── paper.tex          # Documento principal LaTeX expandido con derivaciones formales
├── paper.pdf          # PDF compilado (5 páginas, formato twocolumn IEEE/TinyML)
├── figures/           # Gráficos y diagramas de arquitectura
├── experiments/       # Scripts de experimentos reproducibles
└── README.md          # Este archivo
```

## Aportes Matemáticos y de Ingeniería Documentados
1. **Factorización Exacta de Cholesky ($A = L L^T$)**: Demostración de simetría y definición positiva (SPD) de la matriz de covarianza regularizada para el entrenamiento de lectura ($O(\frac{1}{3} M^3)$ flops vs $M^3$).
2. **Adaptación Continua Streaming (NLMS $O(M)$)**: Regla delta en tiempo real para microcontroladores con recursos mínimos.
3. **Reservorios Ortogonales de Cayley**: $W = \rho (I - A)(I + A)^{-1}$ con $A = -A^T$ para maximizar la capacidad de memoria temporal.
4. **Filtro Espectral de Dos Etapas**: Cota de Gerschgorin y Rayleigh Power Iteration $O(k N^2)$.
5. **Plasticidad de Oja Normalizada**: Convergencia de norma sináptica $\|w_i\|_2 \to 1$.
6. **Benchmarks Rigurosos**: Mackey-Glass en 5 representaciones, comparación de tiempos de cómputo en Cortex-M4 y desglose de energía con autonomía plurianual en baterías CR2032.

## Compilar Localmente

```bash
cd phase8-paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
```

## Papers Disponibles en el Repositorio
- **Versión en Inglés (10 páginas completa)**: [`paper/main.pdf`](../paper/main.pdf) (y copia para la interfaz web en [`web/static/eon-paper.pdf`](../web/static/eon-paper.pdf)).
- **Versión en Español (5 páginas condensada)**: [`phase8-paper/paper.pdf`](paper.pdf).

---

(c) 2024-2026 SenseLab — Build with Sense
