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
# Security Check: GENESIS.json Integrity
# ==========================================
set(GENESIS_FILE "${CMAKE_SOURCE_DIR}/../../GENESIS.json")
set(EXPECTED_HASH "bc61c2c907d20db695cf0a59b05f3066c51711d29cac1c5122ed28e9b49b9dda")

if(EXISTS "${GENESIS_FILE}")
    file(SHA256 "${GENESIS_FILE}" CURRENT_HASH)
    message(STATUS "Verifying GENESIS.json integrity...")
    message(STATUS "  Expected: ${EXPECTED_HASH}")
    message(STATUS "  Current:  ${CURRENT_HASH}")
    
    if(NOT "${CURRENT_HASH}" STREQUAL "${EXPECTED_HASH}")
        message(FATAL_ERROR "\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            "!!! SECURITY BREACH DETECTED                                !!!\n"
            "!!! GENESIS.json HAS BEEN TAMPERED WITH                     !!!\n"
            "!!!                                                         !!!\n"
            "!!! This file is the sacred certificate of the project.     !!!\n"
            "!!! You cannot modify it. Revert changes immediately.       !!!\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        )
    else()
        message(STATUS "  [OK] GENESIS.json is valid.")
    endif()
else()
    message(WARNING "GENESIS.json not found at ${GENESIS_FILE}. Security check skipped (Dev Mode).")
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

# ==========================================
# Testing
# ==========================================
enable_testing()
add_executable(test_aeon test_aeon.c)
target_link_libraries(test_aeon PRIVATE aeon)

if(UNIX AND NOT APPLE)
    target_link_libraries(test_aeon PRIVATE m)
endif()

add_test(NAME CoreRegressionTest COMMAND test_aeon)

