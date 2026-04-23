/**
 * Proyecto Eón — EgregorVisualizer
 * ==================================
 * Animador de Canvas HTML5 para el estado del Egrégor.
 *
 * Recibe parámetros de estilo desde la API /api/egregore/art
 * (generados por EgregorArtist en web/egregore_art.py) y
 * los convierte en una animación procedural.
 *
 * ARQUITECTURA:
 * ─────────────
 *   EgregorArtist (Python) → /api/egregore/art → EgregorVisualizer (JS)
 *        ↓                                               ↓
 *   Parámetros JSON                              Canvas animado
 *
 * USO:
 * ────
 *   const canvas = document.getElementById('egregore-canvas');
 *   const viz = new EgregorVisualizer(canvas);
 *   viz.start();
 *   viz.setStyle(styleFromAPI);  // Cuando llega un nuevo estado
 *
 * (c) 2024 Proyecto Eón - Jeremy Arias Solano
 */

'use strict';

/** ─── Clase principal ─────────────────────────────────────────────────────── */
class EgregorVisualizer {
  /**
   * @param {HTMLCanvasElement} canvas
   * @param {Object} [options]
   * @param {number} [options.fps=30] - Fotogramas por segundo objetivo
   * @param {string} [options.apiUrl='/api/egregore/art'] - Endpoint de la API
   * @param {number} [options.pollInterval=5000] - Intervalo de actualización (ms)
   */
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.fps = options.fps ?? 30;
    this.apiUrl = options.apiUrl ?? '/api/egregore/art';
    this.pollInterval = options.pollInterval ?? 5000;

    this._running = false;
    this._frameId = null;
    this._lastFrameTime = 0;
    this._pollTimer = null;

    // Estado visual actual
    this._style = null;
    this._prevStyle = null;
    this._transitionT = 1.0;   // 0=inicio transición, 1=completado
    this._transitionSpeed = 0.02;

    // Sistema de partículas
    this._particles = [];

    // Campo de ruido simplificado (tabla aleatoria)
    this._noiseTable = new Float32Array(512);
    this._initNoise();

    // Tiempo acumulado para animación
    this._t = 0;

    // Resize adaptativo
    this._resizeObserver = new ResizeObserver(() => this._onResize());
    this._resizeObserver.observe(canvas);
    this._onResize();
  }

  // ─── Inicialización ────────────────────────────────────────────────────────

  _initNoise() {
    // Tabla de valores pseudo-aleatorios para el campo de ruido
    for (let i = 0; i < this._noiseTable.length; i++) {
      this._noiseTable[i] = Math.random();
    }
  }

  _onResize() {
    this.canvas.width = this.canvas.offsetWidth || 800;
    this.canvas.height = this.canvas.offsetHeight || 600;
    this._spawnParticles();
  }

  _spawnParticles() {
    const count = this._style?.motion?.particle_count ?? 80;
    this._particles = [];
    for (let i = 0; i < count; i++) {
      this._particles.push(this._newParticle());
    }
  }

  _newParticle() {
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    const angle = Math.random() * Math.PI * 2;
    const radius = Math.random() * Math.min(cx, cy) * 0.8;
    return {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      life: Math.random(),
      maxLife: 0.5 + Math.random() * 0.5,
      size: 1 + Math.random() * 3,
      trail: [],
    };
  }

  // ─── Control de animación ─────────────────────────────────────────────────

  start() {
    if (this._running) return;
    this._running = true;
    this._loop(performance.now());
    this._startPolling();
  }

  stop() {
    this._running = false;
    if (this._frameId) cancelAnimationFrame(this._frameId);
    if (this._pollTimer) clearInterval(this._pollTimer);
  }

  // ─── API pública ──────────────────────────────────────────────────────────

  /**
   * Actualiza el estilo visual con los datos del API.
   * @param {Object} style - Respuesta JSON de /api/egregore/art
   */
  setStyle(style) {
    this._prevStyle = this._style;
    this._style = style;
    this._transitionT = (this._prevStyle !== null) ? 0.0 : 1.0;

    // Ajustar cantidad de partículas
    const targetCount = style.motion?.particle_count ?? 80;
    while (this._particles.length < targetCount) {
      this._particles.push(this._newParticle());
    }
    if (this._particles.length > targetCount) {
      this._particles.length = targetCount;
    }
  }

  // ─── Bucle principal ──────────────────────────────────────────────────────

  _loop(now) {
    if (!this._running) return;
    const elapsed = now - this._lastFrameTime;
    const frameMs = 1000 / this.fps;

    if (elapsed >= frameMs) {
      this._lastFrameTime = now - (elapsed % frameMs);
      this._render();
      this._t += 1;
    }

    this._frameId = requestAnimationFrame(t => this._loop(t));
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  _render() {
    if (!this._style) {
      this._renderDefault();
      return;
    }

    const { ctx, canvas } = this;
    const style = this._style;
    const palette = style.palette;
    const motion = style.motion;
    const geometry = style.geometry;

    // Avanzar transición
    if (this._transitionT < 1.0) {
      this._transitionT = Math.min(1.0, this._transitionT + this._transitionSpeed);
    }

    // Fondo con desvanecimiento (efecto trail de partículas)
    ctx.fillStyle = palette.background + 'CC';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const baseR = Math.min(cx, cy) * geometry.base_radius;

    // Geometría sagrada
    this._drawGeometry(cx, cy, baseR, style);

    // Partículas
    this._updateAndDrawParticles(palette, motion);

    // Glow central
    this._drawGlow(cx, cy, baseR, palette, style);

    // Etiqueta del estado
    this._drawLabel(style.label ?? style.mood, palette);
  }

  _renderDefault() {
    const { ctx, canvas } = this;
    ctx.fillStyle = '#020408';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#2255AA44';
    ctx.font = '14px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Conectando con el Egrégor...', canvas.width / 2, canvas.height / 2);
  }

  _drawGeometry(cx, cy, baseR, style) {
    const { ctx } = this;
    const { geometry, palette, motion } = style;
    const sym = geometry.symmetry_order;
    const layers = geometry.num_layers;
    const rot = (this._t * geometry.rotation_speed) % (Math.PI * 2);
    const pulseScale = geometry.scale_pulse
      ? 1.0 + 0.05 * Math.sin(this._t * 0.1)
      : 1.0;

    for (let layer = 0; layer < layers; layer++) {
      const r = baseR * (1 - layer * 0.2) * pulseScale;
      const alpha = Math.max(0.05, 0.3 - layer * 0.08);
      ctx.beginPath();

      for (let i = 0; i <= sym * 4; i++) {
        const angle = (i / (sym * 4)) * Math.PI * 2 + rot + layer * 0.3;
        const noiseOffset = this._sampleNoise(i, this._t * 0.01) * motion.turbulence * 20;
        const px = cx + Math.cos(angle) * (r + noiseOffset);
        const py = cy + Math.sin(angle) * (r + noiseOffset);
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();

      ctx.strokeStyle = palette.primary + Math.round(alpha * 255).toString(16).padStart(2, '0');
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  _updateAndDrawParticles(palette, motion) {
    const { ctx, canvas } = this;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const speed = motion.speed;
    const turb = motion.turbulence;
    const trailLen = motion.trail_length;

    for (const p of this._particles) {
      // Atracción hacia el centro con variación de ruido
      const dx = cx - p.x;
      const dy = cy - p.y;
      const dist = Math.sqrt(dx * dx + dy * dy) + 1;

      const noiseAngle = this._sampleNoise(p.x * 0.01, p.y * 0.01 + this._t * 0.001) * Math.PI * 2;
      p.vx += (dx / dist) * 0.05 + Math.cos(noiseAngle) * turb * 0.5;
      p.vy += (dy / dist) * 0.05 + Math.sin(noiseAngle) * turb * 0.5;

      // Limitar velocidad
      const vmag = Math.sqrt(p.vx * p.vx + p.vy * p.vy) + 1e-6;
      if (vmag > speed) {
        p.vx = (p.vx / vmag) * speed;
        p.vy = (p.vy / vmag) * speed;
      }

      // Guardar en trail
      p.trail.push({ x: p.x, y: p.y });
      if (p.trail.length > trailLen) p.trail.shift();

      p.x += p.vx;
      p.y += p.vy;
      p.life += 0.005;

      // Renacer si sale del canvas o envejece
      if (p.x < 0 || p.x > canvas.width || p.y < 0 || p.y > canvas.height || p.life > p.maxLife) {
        const reset = this._newParticle();
        Object.assign(p, reset);
        continue;
      }

      // Dibujar trail
      if (p.trail.length > 1) {
        ctx.beginPath();
        ctx.moveTo(p.trail[0].x, p.trail[0].y);
        for (let i = 1; i < p.trail.length; i++) {
          ctx.lineTo(p.trail[i].x, p.trail[i].y);
        }
        const alpha = Math.round((1 - p.life / p.maxLife) * 120).toString(16).padStart(2, '0');
        ctx.strokeStyle = palette.secondary + alpha;
        ctx.lineWidth = p.size * 0.4;
        ctx.stroke();
      }

      // Punto de la partícula
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = palette.accent + 'CC';
      ctx.fill();
    }
  }

  _drawGlow(cx, cy, baseR, palette, style) {
    const { ctx } = this;
    const pf = style.motion.pulse_frequency;
    const pulse = 0.7 + 0.3 * Math.sin(this._t * pf * 0.1);
    const r = baseR * 1.2 * pulse;

    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    grad.addColorStop(0, palette.glow ?? palette.primary + '40');
    grad.addColorStop(1, 'transparent');

    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
  }

  _drawLabel(label, palette) {
    const { ctx, canvas } = this;
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = palette.accent + '99';
    ctx.fillText(label, canvas.width / 2, canvas.height - 16);
  }

  // ─── Campo de ruido ───────────────────────────────────────────────────────

  _sampleNoise(x, y) {
    const ix = Math.floor(Math.abs(x)) % 256;
    const iy = Math.floor(Math.abs(y)) % 256;
    return this._noiseTable[(ix + iy * 57) & 511];
  }

  // ─── Polling del API ─────────────────────────────────────────────────────

  _startPolling() {
    this._fetchStyle();  // Primera llamada inmediata
    this._pollTimer = setInterval(() => this._fetchStyle(), this.pollInterval);
  }

  async _fetchStyle() {
    try {
      const resp = await fetch(this.apiUrl);
      if (!resp.ok) return;
      const data = await resp.json();
      this.setStyle(data);
    } catch (_e) {
      // Red no disponible — continuar con el estilo actual
    }
  }
}

/** ─── Factory de inicialización rápida ────────────────────────────────────── */
function initEgregorVisualizer(canvasId, options) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.warn(`EgregorVisualizer: canvas #${canvasId} no encontrado`);
    return null;
  }
  const viz = new EgregorVisualizer(canvas, options);
  viz.start();
  return viz;
}

// Exportar para uso como módulo ES o script directo
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { EgregorVisualizer, initEgregorVisualizer };
} else if (typeof window !== 'undefined') {
  window.EgregorVisualizer = EgregorVisualizer;
  window.initEgregorVisualizer = initEgregorVisualizer;
}
