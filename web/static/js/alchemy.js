/**
 * Eón Web Interface - Alchemical Transmutation Visualization
 * 
 * ⚗️ OPUS MAGNUM - La Gran Obra
 * 
 * Visualiza el proceso de transmutación de datos en tiempo real:
 * - NIGREDO (⚫): Putrefacción - Datos crudos ingresados
 * - ALBEDO (⚪): Purificación - Filtrado y limpieza
 * - RUBEDO (🔴): Iluminación - Inferencia completada
 */

const Alchemy = {
  API_BASE: "",
  
  state: {
    currentPhase: 'MATERIA_PRIMA',
    progress: 0,
    isTransmuting: false,
    history: []
  },
  
  // Configuración visual de fases
  phases: {
    MATERIA_PRIMA: { 
      symbol: '🪨', 
      color: '#666666', 
      name: 'Materia Prima',
      description: 'Esperando datos crudos'
    },
    NIGREDO: { 
      symbol: '⚫', 
      color: '#1a1a1a', 
      name: 'Nigredo',
      description: 'Putrefacción - Ingesta de datos'
    },
    ALBEDO: { 
      symbol: '⚪', 
      color: '#f0f0f0', 
      name: 'Albedo',
      description: 'Purificación - Filtrado Kalman'
    },
    CITRINITAS: { 
      symbol: '🟡', 
      color: '#ffd700', 
      name: 'Citrinitas',
      description: 'Amarilleamiento - Pre-inferencia'
    },
    RUBEDO: { 
      symbol: '🔴', 
      color: '#dc143c', 
      name: 'Rubedo',
      description: 'Iluminación - Inferencia final'
    },
    OPUS_COMPLETE: { 
      symbol: '✨', 
      color: '#ffd700', 
      name: 'Opus Complete',
      description: '¡Piedra Filosofal obtenida!'
    }
  },
  
  /**
   * Inicializa el módulo de alquimia
   */
  init() {
    this.createVisualization();
    this.bindEvents();
    this.pollStatus();
  },
  
  /**
   * Crea el HTML para la visualización de alquimia
   */
  createVisualization() {
    const container = document.getElementById('alchemyContainer');
    if (!container) return;
    
    container.innerHTML = `
      <div class="alchemy-panel">
        <div class="alchemy-header">
          <span>⚗️ TRANSMUTACIÓN ALQUÍMICA</span>
          <span class="alchemy-cycle-count" id="alchemyCycleCount">0 ciclos</span>
        </div>
        
        <div class="alchemy-phases" id="alchemyPhases">
          <div class="phase-step" data-phase="NIGREDO">
            <div class="phase-icon">⚫</div>
            <div class="phase-name">Nigredo</div>
          </div>
          <div class="phase-connector"></div>
          <div class="phase-step" data-phase="ALBEDO">
            <div class="phase-icon">⚪</div>
            <div class="phase-name">Albedo</div>
          </div>
          <div class="phase-connector"></div>
          <div class="phase-step" data-phase="RUBEDO">
            <div class="phase-icon">🔴</div>
            <div class="phase-name">Rubedo</div>
          </div>
          <div class="phase-connector"></div>
          <div class="phase-step" data-phase="OPUS_COMPLETE">
            <div class="phase-icon">✨</div>
            <div class="phase-name">Opus</div>
          </div>
        </div>
        
        <div class="alchemy-progress">
          <div class="alchemy-progress-bar" id="alchemyProgressBar"></div>
        </div>
        
        <div class="alchemy-status" id="alchemyStatus">
          <div class="status-phase">
            <span id="alchemyPhaseSymbol">🪨</span>
            <span id="alchemyPhaseName">Materia Prima</span>
          </div>
          <div class="status-metrics">
            <div class="metric">
              <span class="metric-label">Muestras</span>
              <span class="metric-value" id="alchemySamples">0</span>
            </div>
            <div class="metric">
              <span class="metric-label">Ruido Eliminado</span>
              <span class="metric-value" id="alchemyNoise">0%</span>
            </div>
            <div class="metric">
              <span class="metric-label">Confianza</span>
              <span class="metric-value" id="alchemyConfidence">-</span>
            </div>
          </div>
        </div>
        
        <div class="alchemy-controls">
          <button class="alchemy-btn" id="alchemyDemoBtn">
            <i class="fa-solid fa-flask"></i> Demo Transmutación
          </button>
        </div>
      </div>
    `;
    
    this.injectStyles();
  },
  
  /**
   * Inyecta los estilos CSS para la visualización
   */
  injectStyles() {
    if (document.getElementById('alchemy-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'alchemy-styles';
    style.textContent = `
      .alchemy-panel {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
      }
      
      .alchemy-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'Orbitron', sans-serif;
        color: #ffd700;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
      }
      
      .alchemy-cycle-count {
        font-size: 0.75rem;
        color: #888;
      }
      
      .alchemy-phases {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.5rem;
      }
      
      .phase-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        opacity: 0.4;
        transition: all 0.3s ease;
      }
      
      .phase-step.active {
        opacity: 1;
        transform: scale(1.15);
      }
      
      .phase-step.completed {
        opacity: 0.8;
      }
      
      .phase-icon {
        font-size: 1.8rem;
        margin-bottom: 0.3rem;
      }
      
      .phase-name {
        font-size: 0.65rem;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      
      .phase-connector {
        width: 30px;
        height: 2px;
        background: linear-gradient(90deg, #333 0%, #666 50%, #333 100%);
        margin: 0 8px;
        position: relative;
      }
      
      .phase-connector.active {
        background: linear-gradient(90deg, #ffd700 0%, #ff6b6b 100%);
        animation: flow 1s ease-in-out infinite;
      }
      
      @keyframes flow {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
      }
      
      .alchemy-progress {
        height: 6px;
        background: #222;
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 1rem;
      }
      
      .alchemy-progress-bar {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, 
          #1a1a1a 0%, 
          #666 25%, 
          #f0f0f0 50%, 
          #dc143c 75%, 
          #ffd700 100%
        );
        transition: width 0.5s ease;
        border-radius: 3px;
      }
      
      .alchemy-status {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background: rgba(0,0,0,0.3);
        border-radius: 8px;
        margin-bottom: 1rem;
      }
      
      .status-phase {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      #alchemyPhaseSymbol {
        font-size: 1.5rem;
      }
      
      #alchemyPhaseName {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem;
        color: #ffd700;
      }
      
      .status-metrics {
        display: flex;
        gap: 1.5rem;
      }
      
      .metric {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      
      .metric-label {
        font-size: 0.6rem;
        color: #666;
        text-transform: uppercase;
      }
      
      .metric-value {
        font-family: 'Roboto Mono', monospace;
        font-size: 0.9rem;
        color: #0ff;
      }
      
      .alchemy-controls {
        display: flex;
        justify-content: center;
      }
      
      .alchemy-btn {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
        border: 1px solid #ffd700;
        color: #ffd700;
        padding: 0.6rem 1.5rem;
        border-radius: 6px;
        cursor: pointer;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem;
        transition: all 0.2s ease;
      }
      
      .alchemy-btn:hover {
        background: #ffd700;
        color: #1a1a2e;
        transform: translateY(-2px);
      }
      
      .alchemy-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      
      .alchemy-btn.transmuting {
        animation: glow 1.5s ease-in-out infinite;
      }
      
      @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px #ffd700; }
        50% { box-shadow: 0 0 20px #ffd700, 0 0 30px #ff6b6b; }
      }
    `;
    
    document.head.appendChild(style);
  },
  
  /**
   * Bindea eventos
   */
  bindEvents() {
    const demoBtn = document.getElementById('alchemyDemoBtn');
    if (demoBtn) {
      demoBtn.addEventListener('click', () => this.runDemo());
    }
  },
  
  /**
   * Actualiza la visualización según el estado
   */
  updateVisualization(state) {
    if (!state) return;
    
    this.state.currentPhase = state.phase;
    this.state.progress = state.progress;
    
    // Actualizar barra de progreso
    const progressBar = document.getElementById('alchemyProgressBar');
    if (progressBar) {
      progressBar.style.width = `${state.progress}%`;
    }
    
    // Actualizar fase actual
    const phaseSymbol = document.getElementById('alchemyPhaseSymbol');
    const phaseName = document.getElementById('alchemyPhaseName');
    if (phaseSymbol && phaseName) {
      const phaseInfo = this.phases[state.phase] || this.phases.MATERIA_PRIMA;
      phaseSymbol.textContent = phaseInfo.symbol;
      phaseName.textContent = phaseInfo.name;
    }
    
    // Actualizar indicadores de fase
    document.querySelectorAll('.phase-step').forEach(step => {
      const stepPhase = step.dataset.phase;
      const stepOrder = this.getPhaseOrder(stepPhase);
      const currentOrder = this.getPhaseOrder(state.phase);
      
      step.classList.remove('active', 'completed');
      
      if (stepPhase === state.phase) {
        step.classList.add('active');
      } else if (stepOrder < currentOrder) {
        step.classList.add('completed');
      }
    });
    
    // Actualizar conectores
    document.querySelectorAll('.phase-connector').forEach((conn, idx) => {
      const currentOrder = this.getPhaseOrder(state.phase);
      conn.classList.toggle('active', idx < currentOrder - 1);
    });
    
    // Actualizar métricas
    if (state.state) {
      const samples = document.getElementById('alchemySamples');
      const noise = document.getElementById('alchemyNoise');
      const confidence = document.getElementById('alchemyConfidence');
      const cycleCount = document.getElementById('alchemyCycleCount');
      
      if (samples) samples.textContent = state.state.nigredo_samples || 0;
      if (noise) noise.textContent = `${(state.state.noise_removed_percent || 0).toFixed(1)}%`;
      if (confidence) {
        const conf = state.state.prediction_confidence;
        confidence.textContent = conf > 0 ? `${(conf * 100).toFixed(0)}%` : '-';
      }
      if (cycleCount) {
        cycleCount.textContent = `${state.state.transmutation_count || 0} ciclos`;
      }
    }
  },
  
  /**
   * Obtiene el orden numérico de una fase
   */
  getPhaseOrder(phase) {
    const order = {
      MATERIA_PRIMA: 0,
      NIGREDO: 1,
      ALBEDO: 2,
      CITRINITAS: 3,
      RUBEDO: 4,
      OPUS_COMPLETE: 5
    };
    return order[phase] || 0;
  },
  
  /**
   * Ejecuta una demostración de transmutación
   */
  async runDemo() {
    const btn = document.getElementById('alchemyDemoBtn');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('transmuting');
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Transmutando...';
    }
    
    this.state.isTransmuting = true;
    
    try {
      // Generar datos de prueba ruidosos
      const rawData = [];
      for (let i = 0; i < 100; i++) {
        const t = i / 10;
        const clean = Math.sin(t) + 0.3 * Math.sin(3 * t);
        const noise = (Math.random() - 0.5) * 0.8;
        rawData.push(clean + noise);
      }
      
      // Fase 1: NIGREDO
      await this.animatePhase('NIGREDO', 500);
      const nigredoRes = await fetch(`${this.API_BASE}/api/alchemy/nigredo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: rawData })
      });
      const nigredoData = await nigredoRes.json();
      if (nigredoData.success) {
        this.updateVisualization(nigredoData.state);
      }
      
      await this.sleep(800);
      
      // Fase 2: ALBEDO
      await this.animatePhase('ALBEDO', 500);
      const albedoRes = await fetch(`${this.API_BASE}/api/alchemy/albedo`, {
        method: 'POST'
      });
      const albedoData = await albedoRes.json();
      if (albedoData.success) {
        this.updateVisualization(albedoData.state);
      }
      
      await this.sleep(800);
      
      // Fase 3: RUBEDO
      await this.animatePhase('RUBEDO', 500);
      const rubedoRes = await fetch(`${this.API_BASE}/api/alchemy/rubedo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ use_esn: false })
      });
      const rubedoData = await rubedoRes.json();
      if (rubedoData.success) {
        this.updateVisualization(rubedoData.state);
        
        // Mostrar resultado
        if (window.App && typeof window.App.addSystemMessage === 'function') {
          window.App.addSystemMessage(
            `⚗️ **Transmutación Completada**\n\n` +
            `✨ **Piedra Filosofal**: ${typeof rubedoData.gold === 'number' ? rubedoData.gold.toFixed(4) : rubedoData.gold}\n` +
            `📊 Confianza: ${(rubedoData.confidence * 100).toFixed(0)}%\n` +
            `🧹 Ruido eliminado: ${rubedoData.state?.state?.noise_removed_percent?.toFixed(1) || 0}%`
          );
        }
      }
      
    } catch (error) {
      console.error('Error en transmutación:', error);
    } finally {
      this.state.isTransmuting = false;
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('transmuting');
        btn.innerHTML = '<i class="fa-solid fa-flask"></i> Demo Transmutación';
      }
    }
  },
  
  /**
   * Anima la transición a una fase
   */
  async animatePhase(phase, duration) {
    const phaseInfo = this.phases[phase];
    if (!phaseInfo) return;
    
    const symbol = document.getElementById('alchemyPhaseSymbol');
    const name = document.getElementById('alchemyPhaseName');
    
    if (symbol) symbol.textContent = phaseInfo.symbol;
    if (name) name.textContent = phaseInfo.name;
    
    await this.sleep(duration);
  },
  
  /**
   * Utilidad para esperar
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },
  
  /**
   * Polling del estado de alquimia
   */
  async pollStatus() {
    try {
      const res = await fetch(`${this.API_BASE}/api/alchemy/status`);
      const data = await res.json();
      if (data.success && data.alchemy) {
        this.updateVisualization(data.alchemy);
      }
    } catch (e) {
      // Silencioso si el endpoint no está disponible
    }
    
    // Polling cada 2 segundos si hay transmutación activa
    if (this.state.isTransmuting) {
      setTimeout(() => this.pollStatus(), 2000);
    }
  },
  
  /**
   * Ejecuta transmutación completa con datos proporcionados
   */
  async transmute(rawData, useESN = false) {
    try {
      const res = await fetch(`${this.API_BASE}/api/alchemy/transmute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: rawData, use_esn: useESN })
      });
      
      const data = await res.json();
      
      if (data.success) {
        this.updateVisualization(data.state);
        return data.transmutation;
      }
      
      return null;
    } catch (error) {
      console.error('Error en transmutación:', error);
      return null;
    }
  }
};

// Inicializar cuando el DOM esté listo
window.addEventListener('DOMContentLoaded', () => {
  // Solo inicializar si existe el contenedor
  if (document.getElementById('alchemyContainer')) {
    Alchemy.init();
  }
});

// Exportar para uso global
window.Alchemy = Alchemy;
