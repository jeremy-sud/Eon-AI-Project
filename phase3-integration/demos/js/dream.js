/**
 * Eón Dream - Generative Art Logic
 */

// Initialize Eón Core
const aeon = new Aeon({
  reservoirSize: 100,
  inputSize: 1,
  outputSize: 1,
  spectralRadius: 0.95, // High radius for long memory/chaos
  sparsity: 0.8,
});

// Canvas Setup
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let width, height;

function resize() {
  width = canvas.width = window.innerWidth;
  height = canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();

// UI State
let mode = "grid"; // 'grid' | 'path'
let autoPulse = true;
let pulsePhase = 0;

// Path Mode State
let pathPoints = [];
const MAX_PATH = 500;

// Input Handling
const inputBox = document.getElementById("inputBox");
inputBox.addEventListener("input", (e) => {
  if (e.data) {
    // Convert char code to -1..1 input
    const val = (e.data.charCodeAt(0) % 256) / 128.0 - 1.0;
    aeon.update([val]);
  }
});

// UI Buttons
document.getElementById("btnGrid").onclick = () => {
  mode = "grid";
  resetUI();
  document.getElementById("btnGrid").classList.add("mode-active");
};
document.getElementById("btnPath").onclick = () => {
  mode = "path";
  resetUI();
  document.getElementById("btnPath").classList.add("mode-active");
};
document.getElementById("btnPulse").onclick = (e) => {
  autoPulse = !autoPulse;
  e.target.innerText = "Pulse: " + (autoPulse ? "ON" : "OFF");
};

function resetUI() {
  document
    .querySelectorAll("button")
    .forEach((b) => b.classList.remove("mode-active"));
  pathPoints = [];
  // Clear canvas
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, width, height);
}

// Animation Loop
function animate() {
  requestAnimationFrame(animate);

  // 1. Auto Pulse Input
  if (autoPulse) {
    // Slow sine wave input
    const input = Math.sin(pulsePhase) * 0.5;
    aeon.update([input]);
    pulsePhase += 0.05;
  } else {
    // Slight noise to keep it alive even without input
    aeon.update([(Math.random() - 0.5) * 0.1]);
  }

  // 2. Render
  if (mode === "grid") {
    renderGrid();
  } else {
    renderPath();
  }

  // Stats
  document.getElementById("stats").innerText = `Neurons: ${
    aeon.neurons.length
  } | Energy: ${getEnergy().toFixed(3)}`;
}

function getEnergy() {
  return (
    aeon.states.reduce((sum, val) => sum + Math.abs(val), 0) /
    aeon.states.length
  );
}

function renderGrid() {
  // 10x10 Grid
  const cols = 10;
  const rows = 10;
  const cellW = width / cols;
  const cellH = height / rows;

  for (let i = 0; i < 100; i++) {
    const x = (i % cols) * cellW;
    const y = Math.floor(i / cols) * cellH;

    // State is -1 to 1. Map to Lightness 10-90%
    const activation = aeon.states[i]; // Assuming access to internal state array
    // aeon.js exposes 'states' (Float32Array)

    const hue = (i * 3.6) % 360; // Unique hue for each neuron
    const sat = 80;
    const lit = ((activation + 1) / 2) * 80 + 10; // 10% to 90%

    ctx.fillStyle = `hsl(${hue}, ${sat}%, ${lit}%)`;

    // Add "glow" if highly active
    if (Math.abs(activation) > 0.8) {
      ctx.shadowBlur = 20;
      ctx.shadowColor = ctx.fillStyle;
    } else {
      ctx.shadowBlur = 0;
    }

    ctx.fillRect(x, y, cellW, cellH);
  }
}

function renderPath() {
  // Fade out effect
  ctx.shadowBlur = 0;
  ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
  ctx.fillRect(0, 0, width, height);

  // Map first 2 neurons to X,Y
  // Map -1..1 to screen coords
  const x = ((aeon.states[0] + 1) / 2) * width;
  const y = ((aeon.states[1] + 1) / 2) * height;

  pathPoints.push({
    x,
    y,
    color: `hsl(${(pulsePhase * 20) % 360}, 100%, 50%)`,
  });
  if (pathPoints.length > MAX_PATH) pathPoints.shift();

  if (pathPoints.length > 1) {
    ctx.beginPath();
    ctx.moveTo(pathPoints[0].x, pathPoints[0].y);

    for (let i = 1; i < pathPoints.length; i++) {
      ctx.lineTo(pathPoints[i].x, pathPoints[i].y);
    }

    ctx.strokeStyle = `hsl(${(pulsePhase * 20) % 360}, 100%, 50%)`;
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.stroke();
  }

  // Draw Head
  ctx.fillStyle = "#FFF";
  ctx.beginPath();
  ctx.arc(x, y, 5, 0, Math.PI * 2);
  ctx.fill();
}

// Start
animate();
