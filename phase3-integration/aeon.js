/**
 * Proyecto Eón - AeonJS
 * Implementación JavaScript pura del núcleo ESN
 *
 * "La inteligencia no se crea, se descubre."
 *
 * Esta versión es compatible con navegadores sin necesidad de WASM.
 * Para producción, usar la versión compilada con Emscripten.
 */

class AeonCore {
  /**
   * Configuración por defecto
   */
  static DEFAULT_CONFIG = {
    reservoirSize: 32,
    inputSize: 1,
    outputSize: 1,
    sparsityFactor: 4,
    spectralRadius: 0.9,
  };

  /**
   * Crea una nueva instancia de Eón (Momento Cero)
   */
  constructor(config = {}) {
    this.config = { ...AeonCore.DEFAULT_CONFIG, ...config };

    // === MOMENTO CERO ===
    this.birthTimestamp = new Date();
    this.birthHash = this._generateHash();
    this.reservoirSeed = Date.now() % 0xffffffff;

    // Inicializar RNG
    this._rngState = this.reservoirSeed;

    // Estado del reservoir
    this.state = new Float32Array(this.config.reservoirSize);

    // Matrices de pesos
    this.W_in = new Float32Array(
      this.config.reservoirSize * this.config.inputSize
    );
    this.W_out = new Float32Array(
      this.config.outputSize * this.config.reservoirSize
    );

    // Conexiones escasas del reservoir
    this.sparseIndices = [];
    this.sparseWeights = [];

    // Estado de aprendizaje
    this.isTrained = false;
    this.samplesProcessed = 0;
    this.learningSessions = 0;

    // Inicializar reservoir
    this._initializeReservoir();
  }

  /**
   * Genera hash único de nacimiento
   */
  _generateHash() {
    const data = `${Date.now()}-${Math.random()}-${
      navigator?.userAgent || "node"
    }`;
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(16, "0").slice(0, 16);
  }

  /**
   * Generador LCG
   */
  _random() {
    this._rngState = (this._rngState * 1103515245 + 12345) & 0x7fffffff;
    return this._rngState / 0x7fffffff;
  }

  /**
   * Inicializa el reservoir aleatorio
   */
  _initializeReservoir() {
    const { reservoirSize, inputSize, sparsityFactor } = this.config;

    // W_in: Pesos de entrada aleatorios [-1, 1]
    for (let i = 0; i < reservoirSize * inputSize; i++) {
      this.W_in[i] = this._random() * 2 - 1;
    }

    // W_reservoir: Conexiones escasas
    const totalConnections = reservoirSize * reservoirSize;
    const targetConnections = Math.floor(totalConnections / sparsityFactor);

    const usedIndices = new Set();
    for (let i = 0; i < targetConnections; i++) {
      let idx;
      do {
        idx = Math.floor(this._random() * totalConnections);
      } while (usedIndices.has(idx));

      usedIndices.add(idx);
      this.sparseIndices.push(idx);
      this.sparseWeights.push(this._random() * 2 - 1);
    }

    // Escalar pesos para radio espectral (aproximación)
    const scale =
      this.config.spectralRadius / Math.sqrt(targetConnections / reservoirSize);
    for (let i = 0; i < this.sparseWeights.length; i++) {
      this.sparseWeights[i] *= scale;
    }
  }

  /**
   * Aproximación rápida de tanh
   */
  _tanh(x) {
    if (x > 2) return 1;
    if (x < -2) return -1;
    const x2 = x * x;
    return x * (1 - x2 / 3 + (x2 * x2) / 15);
  }

  /**
   * Actualiza el estado del reservoir
   */
  update(input) {
    const { reservoirSize, inputSize } = this.config;
    const newState = new Float32Array(reservoirSize);

    // Contribución de entrada
    for (let i = 0; i < reservoirSize; i++) {
      let sum = 0;
      for (let j = 0; j < inputSize; j++) {
        sum += this.W_in[i * inputSize + j] * input[j];
      }
      newState[i] = sum;
    }

    // Contribución del reservoir (escaso)
    for (let k = 0; k < this.sparseIndices.length; k++) {
      const idx = this.sparseIndices[k];
      const i = Math.floor(idx / reservoirSize);
      const j = idx % reservoirSize;
      newState[i] += this.sparseWeights[k] * this.state[j];
    }

    // Aplicar no-linealidad
    for (let i = 0; i < reservoirSize; i++) {
      this.state[i] = this._tanh(newState[i]);
    }

    this.samplesProcessed++;
  }

  /**
   * Genera predicción
   */
  predict() {
    const { reservoirSize, outputSize } = this.config;
    const output = new Float32Array(outputSize);

    for (let o = 0; o < outputSize; o++) {
      let sum = 0;
      for (let j = 0; j < reservoirSize; j++) {
        sum += this.W_out[o * reservoirSize + j] * this.state[j];
      }
      output[o] = sum;
    }

    return output;
  }

  /**
   * Entrena con datos
   */
  train(inputs, targets, washout = 50) {
    if (inputs.length <= washout) {
      throw new Error("Insufficient training data");
    }

    const { reservoirSize, outputSize } = this.config;
    const trainSamples = inputs.length - washout;

    // Reset
    this.reset();

    // Acumuladores para regresión
    const StS = [];
    const StY = [];

    for (let i = 0; i < reservoirSize; i++) {
      StS[i] = new Float32Array(reservoirSize);
      StS[i][i] = 1e-4; // Regularización
      StY[i] = new Float32Array(outputSize);
    }

    // Recolectar estados
    for (let t = 0; t < inputs.length; t++) {
      this.update([inputs[t]]);

      if (t >= washout) {
        const target = targets[t];

        // Acumular S^T * S y S^T * Y
        for (let i = 0; i < reservoirSize; i++) {
          for (let j = i; j < reservoirSize; j++) {
            const prod = this.state[i] * this.state[j];
            StS[i][j] += prod;
            if (i !== j) StS[j][i] += prod;
          }
          for (let o = 0; o < outputSize; o++) {
            StY[i][o] += this.state[i] * target;
          }
        }
      }
    }

    // Invertir StS usando Gauss-Jordan
    const inv = [];
    for (let i = 0; i < reservoirSize; i++) {
      inv[i] = new Float32Array(reservoirSize);
      inv[i][i] = 1;
    }

    for (let col = 0; col < reservoirSize; col++) {
      // Pivoteo
      let maxRow = col;
      for (let row = col + 1; row < reservoirSize; row++) {
        if (Math.abs(StS[row][col]) > Math.abs(StS[maxRow][col])) {
          maxRow = row;
        }
      }

      if (maxRow !== col) {
        [StS[col], StS[maxRow]] = [StS[maxRow], StS[col]];
        [inv[col], inv[maxRow]] = [inv[maxRow], inv[col]];
      }

      const pivot = StS[col][col] || 1e-10;
      for (let k = 0; k < reservoirSize; k++) {
        StS[col][k] /= pivot;
        inv[col][k] /= pivot;
      }

      for (let row = 0; row < reservoirSize; row++) {
        if (row !== col) {
          const factor = StS[row][col];
          for (let k = 0; k < reservoirSize; k++) {
            StS[row][k] -= factor * StS[col][k];
            inv[row][k] -= factor * inv[col][k];
          }
        }
      }
    }

    // Calcular W_out = inv * StY
    for (let o = 0; o < outputSize; o++) {
      for (let i = 0; i < reservoirSize; i++) {
        let sum = 0;
        for (let k = 0; k < reservoirSize; k++) {
          sum += inv[i][k] * StY[k][o];
        }
        // Limitar magnitud
        sum = Math.max(-2, Math.min(2, sum));
        this.W_out[o * reservoirSize + i] = sum;
      }
    }

    this.isTrained = true;
    this.learningSessions++;

    // Calcular MSE
    this.reset();
    let mse = 0;

    for (let t = washout; t < inputs.length; t++) {
      this.update([inputs[t]]);
      const pred = this.predict();
      const diff = pred[0] - targets[t];
      mse += diff * diff;
    }

    return mse / trainSamples;
  }

  /**
   * Resetea estado
   */
  reset() {
    this.state.fill(0);
  }

  /**
   * Edad en segundos
   */
  get ageSeconds() {
    return Math.floor((Date.now() - this.birthTimestamp.getTime()) / 1000);
  }

  /**
   * Memoria aproximada en bytes
   */
  get memoryBytes() {
    return (
      this.W_in.byteLength +
      this.W_out.byteLength +
      this.state.byteLength +
      this.sparseWeights.length * 4 +
      this.sparseIndices.length * 4
    );
  }

  /**
   * Estado serializable
   */
  getStatus() {
    return {
      name: `Aeon-${this.birthHash.slice(0, 8)}`,
      birthTimestamp: this.birthTimestamp.toISOString(),
      birthHash: this.birthHash,
      age: this._formatAge(),
      ageSeconds: this.ageSeconds,
      isTrained: this.isTrained,
      samplesProcessed: this.samplesProcessed,
      learningSessions: this.learningSessions,
      reservoirSize: this.config.reservoirSize,
      memoryKB: (this.memoryBytes / 1024).toFixed(2),
      sparseConnections: this.sparseIndices.length,
    };
  }

  _formatAge() {
    const s = this.ageSeconds;
    if (s < 60) return `${s} segundos`;
    if (s < 3600) return `${(s / 60).toFixed(1)} minutos`;
    if (s < 86400) return `${(s / 3600).toFixed(1)} horas`;
    return `${(s / 86400).toFixed(1)} días`;
  }

  /**
   * Exportar a JSON
   */
  toJSON() {
    return {
      config: this.config,
      birthTimestamp: this.birthTimestamp.toISOString(),
      birthHash: this.birthHash,
      reservoirSeed: this.reservoirSeed,
      W_in: Array.from(this.W_in),
      W_out: Array.from(this.W_out),
      sparseIndices: this.sparseIndices,
      sparseWeights: this.sparseWeights,
      isTrained: this.isTrained,
      samplesProcessed: this.samplesProcessed,
      learningSessions: this.learningSessions,
    };
  }

  /**
   * Cargar desde JSON
   */
  static fromJSON(data) {
    const core = new AeonCore(data.config);
    core.birthTimestamp = new Date(data.birthTimestamp);
    core.birthHash = data.birthHash;
    core.reservoirSeed = data.reservoirSeed;
    core.W_in = new Float32Array(data.W_in);
    core.W_out = new Float32Array(data.W_out);
    core.sparseIndices = data.sparseIndices;
    core.sparseWeights = data.sparseWeights;
    core.isTrained = data.isTrained;
    core.samplesProcessed = data.samplesProcessed;
    core.learningSessions = data.learningSessions;
    return core;
  }
}

// Exportar para Node.js y navegador
if (typeof module !== "undefined" && module.exports) {
  module.exports = { AeonCore };
}
if (typeof window !== "undefined") {
  window.AeonCore = AeonCore;
}
