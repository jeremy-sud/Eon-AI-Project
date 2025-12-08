# Proyecto Eón - Makefile para libAeon
# Compilación ultraligera para hardware embebido

CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99
LDFLAGS = -lm

# Configuración del reservoir (ajustar según hardware)
RESERVOIR_SIZE ?= 32
SPARSITY ?= 4

DEFINES = -DAEON_RESERVOIR_SIZE=$(RESERVOIR_SIZE) \
          -DAEON_SPARSITY_FACTOR=$(SPARSITY) \
          -DAEON_USE_FIXED_POINT=1

# Archivos
SRC = libAeon.c demo.c
OBJ = $(SRC:.c=.o)
TARGET = aeon_demo

.PHONY: all clean size run float

# Compilación por defecto (punto fijo)
all: $(TARGET)
	@echo ""
	@echo "✓ Compilado: $(TARGET)"
	@echo "  Reservoir: $(RESERVOIR_SIZE) neuronas"
	@echo "  Escasez: 1/$(SPARSITY)"
	@echo ""

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(DEFINES) -o $@ $^ $(LDFLAGS)

# Compilación con float (para comparación)
float: DEFINES = -DAEON_RESERVOIR_SIZE=$(RESERVOIR_SIZE) \
                 -DAEON_SPARSITY_FACTOR=$(SPARSITY) \
                 -DAEON_USE_FIXED_POINT=0
float: $(TARGET)
	@echo "  Modo: Punto flotante (float)"

# Ejecutar demo
run: $(TARGET)
	@./$(TARGET)

# Mostrar tamaño del binario
size: $(TARGET)
	@echo ""
	@echo "=== Tamaño del binario ==="
	@size $(TARGET)
	@echo ""
	@ls -lh $(TARGET)
	@echo ""

# Limpiar
clean:
	rm -f $(TARGET) $(OBJ) *.bin

# Compilación para diferentes tamaños de reservoir
tiny: RESERVOIR_SIZE=16
tiny: SPARSITY=8
tiny: all
	@echo "  Modo: Ultra-pequeño (16 neuronas)"

small: RESERVOIR_SIZE=32
small: all
	@echo "  Modo: Pequeño (32 neuronas)"

medium: RESERVOIR_SIZE=64
medium: all
	@echo "  Modo: Mediano (64 neuronas)"

large: RESERVOIR_SIZE=128
large: all
	@echo "  Modo: Grande (128 neuronas)"

# Análisis de memoria
memory-analysis: $(TARGET)
	@echo ""
	@echo "=== Análisis de Memoria ==="
	@echo "Estructura aeon_core_t:"
	@echo "  - Certificado: ~48 bytes"
	@echo "  - Estado: $(RESERVOIR_SIZE) * 4 = $$(( $(RESERVOIR_SIZE) * 4 )) bytes"
	@echo "  - W_in: $(RESERVOIR_SIZE) * 2 = $$(( $(RESERVOIR_SIZE) * 2 )) bytes"
	@echo "  - W_reservoir: ~$$(( $(RESERVOIR_SIZE) * $(RESERVOIR_SIZE) / $(SPARSITY) * 2 )) bytes (escaso)"
	@echo "  - W_out: $(RESERVOIR_SIZE) * 2 = $$(( $(RESERVOIR_SIZE) * 2 )) bytes"
	@echo ""
	@echo "Ejecutando para medición real..."
	@./$(TARGET) 2>&1 | grep -E "(Memoria|bytes)"
	@echo ""

# Ayuda
help:
	@echo "Proyecto Eón - libAeon Makefile"
	@echo ""
	@echo "Uso:"
	@echo "  make          - Compilar con configuración por defecto"
	@echo "  make run      - Compilar y ejecutar demo"
	@echo "  make size     - Mostrar tamaño del binario"
	@echo "  make clean    - Limpiar archivos"
	@echo ""
	@echo "Configuraciones:"
	@echo "  make tiny     - 16 neuronas (ultra-pequeño)"
	@echo "  make small    - 32 neuronas"
	@echo "  make medium   - 64 neuronas"
	@echo "  make large    - 128 neuronas"
	@echo "  make float    - Usar punto flotante"
	@echo ""
	@echo "Variables:"
	@echo "  RESERVOIR_SIZE=N  - Tamaño del reservoir"
	@echo "  SPARSITY=N        - Factor de escasez (1/N conexiones)"
	@echo ""
