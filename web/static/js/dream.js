/**
 * Eón Dream Logic
 * Adapts neural visualization for the web interface
 */

let aeonChart = null;
let dreamCtx = null;
let dreamCanvas = null;
let dreamWidth, dreamHeight;
let dreamMode = "grid"; // 'grid' | 'path'
let dreamPulse = true;
let dreamPhase = 0;
let dreamPath = [];
const MAX_DREAM_PATH = 500;
let dreamLoopId = null;

// Initialize Eón Core for Dream (Client-side simulation)
// In a real scenario, this would ideally sync with backend,
// but for 'Dream' visualizer we keep it responsive locally.
const dreamAeon = new Aeon({
  reservoirSize: 100,
  inputSize: 1,
  outputSize: 1,
  spectralRadius: 0.95,
  sparsity: 0.8,
});

function initDream() {
  dreamCanvas = document.getElementById("dreamCanvas");
  if (!dreamCanvas) return;

  dreamCtx = dreamCanvas.getContext("2d");

  // Resize handler
  window.addEventListener("resize", resizeDream);
  resizeDream();

  // Start loop
  if (!dreamLoopId) {
    animateDream();
  }
}

function resizeDream() {
  if (!dreamCanvas) return;
  dreamWidth = dreamCanvas.width = window.innerWidth;
  dreamHeight = dreamCanvas.height = window.innerHeight;
}

function setDreamMode(mode) {
  dreamMode = mode;
  dreamPath = [];

  // Update buttons
  document.querySelectorAll(".dream-btn").forEach((btn) => {
    btn.classList.remove("active");
    if (btn.dataset.mode === mode) btn.classList.add("active");
  });

  if (dreamCtx) {
    dreamCtx.fillStyle = "#000";
    dreamCtx.fillRect(0, 0, dreamWidth, dreamHeight);
  }
}

function togglePulse() {
  dreamPulse = !dreamPulse;
  const btn = document.getElementById("btnPulse");
  if (btn) btn.innerHTML = dreamPulse ? "PULSE: ON" : "PULSE: OFF";
}

function animateDream() {
  dreamLoopId = requestAnimationFrame(animateDream);

  // If view is hidden, skip rendering to save resources
  if (document.getElementById("dreamView").style.display === "none") return;

  // 1. Update Physics
  if (dreamPulse) {
    const input = Math.sin(dreamPhase) * 0.5;
    dreamAeon.update([input]);
    dreamPhase += 0.05;
  } else {
    dreamAeon.update([(Math.random() - 0.5) * 0.1]);
  }

  // 2. Render
  if (dreamMode === "grid") {
    renderDreamGrid();
  } else {
    renderDreamPath();
  }
}

function renderDreamGrid() {
  if (!dreamCtx) return;

  const cols = 10;
  const cellW = dreamWidth / cols;
  const cellH = dreamHeight / 10; // 10 rows

  dreamCtx.fillStyle = "rgba(0, 0, 0, 0.1)"; // Fade effect
  // dreamCtx.fillRect(0, 0, dreamWidth, dreamHeight); // Optional: trail

  for (let i = 0; i < 100; i++) {
    const x = (i % cols) * cellW;
    const y = Math.floor(i / cols) * cellH;

    const val = dreamAeon.states[i];
    const hue = (i * 3.6 + dreamPhase * 10) % 360;
    const lit = ((val + 1) / 2) * 60 + 20;

    dreamCtx.fillStyle = `hsl(${hue}, 80%, ${lit}%)`;

    if (Math.abs(val) > 0.6) {
      dreamCtx.shadowBlur = 15;
      dreamCtx.shadowColor = dreamCtx.fillStyle;
    } else {
      dreamCtx.shadowBlur = 0;
    }

    dreamCtx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);
  }
}

function renderDreamPath() {
  if (!dreamCtx) return;

  dreamCtx.shadowBlur = 0;
  dreamCtx.fillStyle = "rgba(0, 0, 0, 0.05)";
  dreamCtx.fillRect(0, 0, dreamWidth, dreamHeight);

  const x = ((dreamAeon.states[0] + 1) / 2) * dreamWidth;
  const y = ((dreamAeon.states[1] + 1) / 2) * dreamHeight;

  dreamPath.push({
    x,
    y,
    color: `hsl(${(dreamPhase * 20) % 360}, 100%, 50%)`,
  });

  if (dreamPath.length > MAX_DREAM_PATH) dreamPath.shift();

  if (dreamPath.length > 1) {
    dreamCtx.beginPath();
    dreamCtx.moveTo(dreamPath[0].x, dreamPath[0].y);
    for (let i = 1; i < dreamPath.length; i++) {
      dreamCtx.lineTo(dreamPath[i].x, dreamPath[i].y);
    }
    dreamCtx.strokeStyle = `hsl(${(dreamPhase * 20) % 360}, 100%, 50%)`;
    dreamCtx.lineWidth = 2;
    dreamCtx.lineJoin = "round";
    dreamCtx.stroke();
  }
}

// Export for main app
window.initDream = initDream;
window.setDreamMode = setDreamMode;
window.togglePulse = togglePulse;
