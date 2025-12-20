# Fase 2: Núcleo Ultra-Lightweight (C)

Esta fase es la implementación "real" del motor Eón, diseñada para microcontroladores y sistemas embebidos.

## Features

- **C Puro**: Sin dependencias externas.
- **Memory Estática**: No usa `malloc` dinámico en el núcleo.
- **Punto Fijo**: Soporte opcional para Q8.8 (sin FPU).
- **Portable**: Compila en GCC, Clang, AVR-GCC, ARM-GCC.

## Structure

- `libAeon/src`: Código fuente.
- `libAeon/include`: Headers públicos.
- `libAeon/demo.c`: Ejemplo de uso completo.

## Compilación y Uso

```bash
cd libAeon
make
./aeon_demo
```

## Benchmarks

El núcleo consume aproximadamente **0.298 μs** por predicción en un host moderno, lo que se traduce a **~0.0045 μJ** en un Cortex-M4. Ver [Benchmarks](../../docs/benchmarks.md).
