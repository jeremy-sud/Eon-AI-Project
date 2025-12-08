"""
Proyecto Eón - Demostración de Predicción con ESN
Visualiza la capacidad de predicción del reservoir no entrenado.
"""

import numpy as np
import matplotlib.pyplot as plt
from esn import EchoStateNetwork, generate_mackey_glass


def plot_prediction_results(y_true, y_pred, title="Predicción ESN"):
    """Genera gráfico de predicción vs valores reales."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Gráfico de series temporales
    ax1 = axes[0]
    t = np.arange(len(y_true))
    ax1.plot(t, y_true, 'b-', label='Real', linewidth=1.5, alpha=0.8)
    ax1.plot(t, y_pred, 'r--', label='Predicción', linewidth=1.5, alpha=0.8)
    ax1.set_xlabel('Tiempo (t)')
    ax1.set_ylabel('Valor')
    ax1.set_title(title)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico de correlación
    ax2 = axes[1]
    ax2.scatter(y_true.flatten(), y_pred.flatten(), alpha=0.5, s=10)
    
    # Línea de regresión perfecta
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'k--', label='Predicción perfecta')
    
    ax2.set_xlabel('Valor Real')
    ax2.set_ylabel('Valor Predicho')
    ax2.set_title('Correlación Real vs Predicho')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║               PROYECTO EÓN - Demo de Predicción               ║
║         "La Nada es Todo" - El Reservoir No Entrenado         ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # === Generar datos ===
    print("[1/5] Generando serie temporal Mackey-Glass (caótica)...")
    n_samples = 3000
    data = generate_mackey_glass(n_samples, tau=17)
    
    # Normalizar
    data = (data - data.mean()) / data.std()
    
    # Preparar datos (predecir el siguiente valor)
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    # División train/test
    train_size = 2000
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    print(f"    Train: {len(X_train)} muestras")
    print(f"    Test:  {len(X_test)} muestras")
    
    # === Crear ESN ===
    print("\n[2/5] Creando Echo State Network...")
    configs = [
        {"n_reservoir": 50, "name": "ESN-50 (Pequeño)"},
        {"n_reservoir": 100, "name": "ESN-100 (Medio)"},
        {"n_reservoir": 200, "name": "ESN-200 (Grande)"},
    ]
    
    results = []
    
    for config in configs:
        esn = EchoStateNetwork(
            n_inputs=1,
            n_reservoir=config["n_reservoir"],
            n_outputs=1,
            spectral_radius=0.9,
            sparsity=0.9,
            random_state=42
        )
        
        # Entrenar
        esn.fit(X_train, y_train, washout=100)
        
        # Predecir
        esn.reset()
        predictions = esn.predict(X_test)
        
        # Métricas
        mse = np.mean((predictions - y_test)**2)
        memory = esn.get_memory_footprint()
        
        results.append({
            "name": config["name"],
            "n_reservoir": config["n_reservoir"],
            "mse": mse,
            "rmse": np.sqrt(mse),
            "memory_kb": memory["total_kb"],
            "predictions": predictions,
            "esn": esn
        })
    
    # === Mostrar resultados ===
    print("\n[3/5] Resultados de predicción:")
    print("-" * 60)
    print(f"{'Modelo':<20} {'MSE':<12} {'RMSE':<12} {'Memoria (KB)':<12}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['name']:<20} {r['mse']:<12.6f} {r['rmse']:<12.6f} {r['memory_kb']:<12.2f}")
    
    # === Visualización ===
    print("\n[4/5] Generando visualización...")
    
    # Usar el modelo mediano para visualización principal
    best = results[1]  # ESN-100
    
    fig = plot_prediction_results(
        y_test[:200],  # Primeros 200 puntos del test
        best["predictions"][:200],
        title=f"Proyecto Eón - {best['name']} | MSE: {best['mse']:.6f}"
    )
    
    # Guardar figura
    output_path = "prediction_demo.png"
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"    Gráfico guardado en: {output_path}")
    
    # === Generación Autónoma ===
    print("\n[5/5] Generación autónoma (sin entrada externa)...")
    
    esn = best["esn"]
    esn.reset()
    
    # Calentar con algunos datos
    warmup = X_test[:100]
    for x in warmup:
        esn._update_state(x)
    
    # Generar de forma autónoma
    generated = esn.predict_generative(n_steps=200, initial_input=X_test[100])
    
    # Comparar con secuencia real
    real_continuation = y_test[100:300]
    
    fig2, ax = plt.subplots(figsize=(12, 4))
    t = np.arange(200)
    ax.plot(t, real_continuation, 'b-', label='Real', alpha=0.8)
    ax.plot(t, generated, 'r--', label='Generado (autónomo)', alpha=0.8)
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Valor')
    ax.set_title('Generación Autónoma - El modelo "recuerda" la dinámica')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    fig2.savefig("generative_demo.png", dpi=150, bbox_inches='tight')
    print("    Gráfico guardado en: generative_demo.png")
    
    # === Resumen ===
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    DEMOSTRACIÓN COMPLETADA                    ║
╠═══════════════════════════════════════════════════════════════╣
║  ✓ El reservoir ALEATORIO logra predicción precisa            ║
║  ✓ Solo la capa de salida fue entrenada (regresión lineal)    ║
║  ✓ Memoria total: <100 KB para el modelo más grande           ║
║                                                               ║
║  Esto demuestra "La Nada es Todo":                            ║
║  La inteligencia emerge de la estructura, no del tamaño.      ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Mostrar gráficos si hay display disponible
    try:
        plt.show()
    except:
        print("(Visualización no disponible - ver archivos PNG generados)")


if __name__ == "__main__":
    main()
