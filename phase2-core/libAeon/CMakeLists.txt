cmake_minimum_required(VERSION 3.10)
project(EonAI-Core C)

# ==========================================
# Configuration Options
# ==========================================
option(AEON_USE_FIXED_POINT "Use fixed-point arithmetic (recommended for embedded)" ON)
set(AEON_RESERVOIR_SIZE "32" CACHE STRING "Size of the reservoir (neurons)")
set(AEON_SPARSITY_FACTOR "4" CACHE STRING "Sparsity factor (1/N connections)")

# ==========================================
# Compiler Flags
# ==========================================
if(MSVC)
    add_compile_options(/W3 /O2)
else()
    add_compile_options(-Wall -Wextra -O2 -std=c99)
endif()

# ==========================================
# Library Target: aeon
# ==========================================
add_library(aeon STATIC libAeon.c)

# Define compile definitions for the library
target_compile_definitions(aeon PUBLIC
    AEON_RESERVOIR_SIZE=${AEON_RESERVOIR_SIZE}
    AEON_SPARSITY_FACTOR=${AEON_SPARSITY_FACTOR}
    AEON_USE_FIXED_POINT=$<BOOL:${AEON_USE_FIXED_POINT}>
)

# ==========================================
# Executable Target: aeon_demo
# ==========================================
add_executable(aeon_demo demo.c)
target_link_libraries(aeon_demo PRIVATE aeon)

# Link math library if needed (standard on Linux/Unix)
if(UNIX AND NOT APPLE)
    target_link_libraries(aeon_demo PRIVATE m)
endif()

# ==========================================
# Info
# ==========================================
message(STATUS "Build Configuration:")
message(STATUS "  Reservoir Size: ${AEON_RESERVOIR_SIZE}")
message(STATUS "  Sparsity:       ${AEON_SPARSITY_FACTOR}")
message(STATUS "  Fixed Point:    ${AEON_USE_FIXED_POINT}")
