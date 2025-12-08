/**
 * @file libAeon.h
 * @brief Proyecto Eón - Núcleo ESN Ultraligero
 * 
 * Implementación minimalista de Echo State Network en C puro
 * para hardware embebido con huella de memoria mínima.
 * 
 * "La Nada es Todo" - El reservoir aleatorio contiene
 * toda la computación necesaria.
 * 
 * @author Proyecto Eón
 * @date 2024
 */

#ifndef LIBAEON_H
#define LIBAEON_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>

/* ============================================================
 * CONFIGURACIÓN - Ajustar según hardware objetivo
 * ============================================================ */

/** Tamaño del reservoir (neuronas) */
#ifndef AEON_RESERVOIR_SIZE
#define AEON_RESERVOIR_SIZE 32
#endif

/** Número de entradas */
#ifndef AEON_INPUT_SIZE
#define AEON_INPUT_SIZE 1
#endif

/** Número de salidas */
#ifndef AEON_OUTPUT_SIZE
#define AEON_OUTPUT_SIZE 1
#endif

/** Escasez del reservoir (1 de cada N conexiones es no-cero) */
#ifndef AEON_SPARSITY_FACTOR
#define AEON_SPARSITY_FACTOR 4
#endif

/** Usar punto fijo en lugar de float (más eficiente en MCU) */
#ifndef AEON_USE_FIXED_POINT
#define AEON_USE_FIXED_POINT 1
#endif

/* ============================================================
 * TIPOS DE DATOS
 * ============================================================ */

#if AEON_USE_FIXED_POINT
    /** Punto fijo Q8.8 para pesos (-128 a 127 con 8 bits decimales) */
    typedef int16_t aeon_weight_t;
    /** Punto fijo Q16.16 para estado/acumuladores */
    typedef int32_t aeon_state_t;
    /** Factor de escala para punto fijo */
    #define AEON_SCALE 256
    #define AEON_SCALE_BITS 8
#else
    typedef float aeon_weight_t;
    typedef float aeon_state_t;
    #define AEON_SCALE 1.0f
#endif

/** Hash de nacimiento (16 bytes) */
typedef struct {
    uint8_t bytes[16];
} aeon_hash_t;

/** Certificado de nacimiento */
typedef struct {
    time_t birth_time;          /**< Timestamp UTC del nacimiento */
    aeon_hash_t birth_hash;     /**< Hash único */
    uint32_t reservoir_seed;    /**< Semilla del reservoir */
    uint16_t reservoir_size;    /**< Tamaño del reservoir */
    uint16_t version;           /**< Versión de libAeon */
} aeon_certificate_t;

/** Núcleo principal de Eón */
typedef struct {
    /* Certificado de nacimiento (inmutable después de init) */
    aeon_certificate_t certificate;
    
    /* Estado del reservoir */
    aeon_state_t state[AEON_RESERVOIR_SIZE];
    
    /* Matrices de pesos (compactas) */
    aeon_weight_t W_in[AEON_RESERVOIR_SIZE * AEON_INPUT_SIZE];
    aeon_weight_t W_reservoir[AEON_RESERVOIR_SIZE * AEON_RESERVOIR_SIZE / AEON_SPARSITY_FACTOR];
    aeon_weight_t W_out[AEON_OUTPUT_SIZE * AEON_RESERVOIR_SIZE];
    
    /* Índices de conexiones escasas del reservoir */
    uint16_t sparse_indices[AEON_RESERVOIR_SIZE * AEON_RESERVOIR_SIZE / AEON_SPARSITY_FACTOR];
    uint16_t sparse_count;
    
    /* Estadísticas */
    uint32_t samples_processed;
    uint32_t learning_sessions;
    bool is_trained;
    
} aeon_core_t;

/* ============================================================
 * FUNCIONES PRINCIPALES
 * ============================================================ */

/**
 * @brief Inicializa una nueva instancia de Eón (Momento Cero)
 * 
 * Esta función marca el nacimiento de la IA. El timestamp y hash
 * son inmutables después de esta llamada.
 * 
 * @param core Puntero a la estructura del núcleo
 * @param seed Semilla opcional (0 = usar timestamp)
 * @return 0 si éxito, código de error si falla
 */
int aeon_birth(aeon_core_t *core, uint32_t seed);

/**
 * @brief Cargar instancia desde archivo binario
 * 
 * @param core Puntero a la estructura del núcleo
 * @param filename Ruta al archivo
 * @return 0 si éxito
 */
int aeon_load(aeon_core_t *core, const char *filename);

/**
 * @brief Guardar instancia a archivo binario
 * 
 * @param core Puntero a la estructura del núcleo
 * @param filename Ruta al archivo
 * @return 0 si éxito
 */
int aeon_save(const aeon_core_t *core, const char *filename);

/**
 * @brief Actualiza el estado del reservoir con nueva entrada
 * 
 * @param core Puntero al núcleo
 * @param input Vector de entrada
 */
void aeon_update(aeon_core_t *core, const aeon_state_t *input);

/**
 * @brief Genera predicción basada en el estado actual
 * 
 * @param core Puntero al núcleo
 * @param output Vector de salida (debe tener AEON_OUTPUT_SIZE elementos)
 */
void aeon_predict(const aeon_core_t *core, aeon_state_t *output);

/**
 * @brief Entrena la capa de salida con datos
 * 
 * Usa regresión Ridge simplificada. Solo entrena W_out.
 * 
 * @param core Puntero al núcleo
 * @param inputs Datos de entrada (n_samples x AEON_INPUT_SIZE)
 * @param targets Objetivos (n_samples x AEON_OUTPUT_SIZE)
 * @param n_samples Número de muestras
 * @param washout Muestras iniciales a descartar
 * @return Error cuadrático medio
 */
float aeon_train(aeon_core_t *core, 
                 const aeon_state_t *inputs,
                 const aeon_state_t *targets,
                 uint16_t n_samples,
                 uint16_t washout);

/**
 * @brief Resetea el estado del reservoir a ceros
 * 
 * @param core Puntero al núcleo
 */
void aeon_reset(aeon_core_t *core);

/**
 * @brief Obtiene el uso de memoria en bytes
 * 
 * @param core Puntero al núcleo
 * @return Bytes utilizados
 */
uint32_t aeon_memory_usage(const aeon_core_t *core);

/**
 * @brief Obtiene edad en segundos desde el nacimiento
 * 
 * @param core Puntero al núcleo
 * @return Segundos desde nacimiento
 */
uint32_t aeon_age_seconds(const aeon_core_t *core);

/**
 * @brief Convierte hash a string hexadecimal
 * 
 * @param hash Puntero al hash
 * @param buffer Buffer de salida (mínimo 33 bytes)
 */
void aeon_hash_to_string(const aeon_hash_t *hash, char *buffer);

/* ============================================================
 * FUNCIONES DE UTILIDAD
 * ============================================================ */

/** Activación tanh aproximada (rápida) */
aeon_state_t aeon_tanh_approx(aeon_state_t x);

/** Generador de números pseudo-aleatorios (LCG) */
uint32_t aeon_random(uint32_t *state);

/** Versión de la librería */
#define AEON_VERSION_MAJOR 1
#define AEON_VERSION_MINOR 0
#define AEON_VERSION ((AEON_VERSION_MAJOR << 8) | AEON_VERSION_MINOR)

#endif /* LIBAEON_H */
