/**
 * Eón Web Interface - Main Application Logic
 */

const App = {
  API_BASE: "",
  state: {
    currentView: "chat",
    status: null,
    config: {},
    isReady: false,
    chatHistory: [],
  },

  init() {
    this.bindEvents();
    this.startStatusPolling();
    this.loadConfig();
    this.addSystemMessage("Conectando con el núcleo Eón...");
  },

  bindEvents() {
    // Navigation
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const view = e.currentTarget.dataset.view;
        if (view) this.switchView(view);
      });
    });

    // Chat
    const chatInput = document.getElementById("chatInput");
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    document
      .getElementById("sendBtn")
      .addEventListener("click", () => this.sendMessage());

    // Dream controls
    document
      .getElementById("btnGrid")
      .addEventListener("click", () => window.setDreamMode("grid"));
    document
      .getElementById("btnPath")
      .addEventListener("click", () => window.setDreamMode("path"));
    document
      .getElementById("btnPulse")
      .addEventListener("click", () => window.togglePulse());

    // Config Controls
    ["temp", "radius", "leak"].forEach((key) => {
      const input = document.getElementById(`cfg-${key}`);
      if (input) {
        input.addEventListener("input", (e) => {
          document.getElementById(`val-${key}`).textContent = e.target.value;
        });
      }
    });

    const saveBtn = document.getElementById("saveConfigBtn");
    if (saveBtn) saveBtn.addEventListener("click", () => this.saveConfig());
  },

  switchView(viewName) {
    // Update nav
    document
      .querySelectorAll(".nav-item")
      .forEach((el) => el.classList.remove("active"));
    document
      .querySelector(`.nav-item[data-view="${viewName}"]`)
      .classList.add("active");

    // Hide all views
    ["chatView", "dreamView", "statusView"].forEach((id) => {
      document.getElementById(id).style.display = "none";
    });

    // Update state
    this.state.currentView = viewName;

    // Show selected
    const viewId = viewName + "View";
    const viewEl = document.getElementById(viewId);
    if (viewEl) {
      viewEl.style.display = viewName === "chat" ? "flex" : "block";
    }

    // Special handlers
    if (viewName === "dream") {
      if (!window.dreamInitialized) {
        window.initDream();
        window.dreamInitialized = true;
      }
    }
  },

  async loadConfig() {
    try {
      const res = await fetch(`${this.API_BASE}/api/config`);
      const data = await res.json();
      if (data.success) {
        this.state.config = data.config;
        // Update UI
        this.updateConfigUI(data.config);
      }
    } catch (e) {
      console.error("Config load failed", e);
    }
  },

  updateConfigUI(config) {
    if (config.temperature) {
      document.getElementById("cfg-temp").value = config.temperature;
      document.getElementById("val-temp").textContent = config.temperature;
    }
    if (config.spectral_radius) {
      document.getElementById("cfg-radius").value = config.spectral_radius;
      document.getElementById("val-radius").textContent =
        config.spectral_radius;
    }
    if (config.leak_rate) {
      document.getElementById("cfg-leak").value = config.leak_rate;
      document.getElementById("val-leak").textContent = config.leak_rate;
    }
  },

  async saveConfig() {
    const config = {
      temperature: document.getElementById("cfg-temp").value,
      spectral_radius: document.getElementById("cfg-radius").value,
      leak_rate: document.getElementById("cfg-leak").value,
    };

    try {
      const res = await fetch(`${this.API_BASE}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      const data = await res.json();
      if (data.success) {
        this.addSystemMessage("Configuración actualizada correctamente.");
      }
    } catch (e) {
      this.addSystemMessage("Error al guardar configuración.");
    }
  },

  startStatusPolling() {
    // Poll immediately once
    this.checkStatus();
    setInterval(() => this.checkStatus(), 2000);
  },

  async checkStatus() {
    try {
      const res = await fetch(`${this.API_BASE}/api/status`);
      const data = await res.json();
      if (data.success) {
        this.state.isReady = true;
        this.updateStatusUI(data.status);
      }
    } catch (e) {
      // console.error("Status check failed", e);
    }
  },

  updateStatusUI(status) {
    this.state.status = status;

    document.getElementById("statusName").textContent = status.name;
    document.getElementById("statusAge").textContent = status.age;
    document.getElementById("statusMemory").textContent =
      status.memory_kb.toFixed(2) + " KB";

    const samplesEl = document.getElementById("statusSamples");
    if (samplesEl) samplesEl.textContent = status.total_samples_learned;
  },

  sendMessage() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    // Add user message
    this.addMessage(text, "user");
    input.value = "";

    // Process logic
    this.processMessage(text);
  },

  async processMessage(text) {
    let responseText = "";

    if (!this.state.isReady) {
      responseText = "Conectando con Eón... por favor espera.";
    } else {
      // Determine pattern for prediction based on keywords
      let pattern = "sine"; // default
      if (text.toLowerCase().includes("caos")) pattern = "mackey_glass";
      if (text.toLowerCase().includes("random")) pattern = "random";

      try {
        // Feed into Eon
        const res = await fetch(`${this.API_BASE}/api/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pattern: pattern, samples: 20 }),
        });
        const data = await res.json();

        if (data.success) {
          const preview = data.predictions
            .slice(0, 5)
            .map((n) => n.toFixed(3))
            .join(", ");
          responseText = `[Eón v1.0] Entendido. Patrón detectado: ${pattern}.\nRespuesta Neuronal: [${preview}...]`;
        } else {
          responseText = "Error procesando la solicitud.";
        }
      } catch (e) {
        console.error(e);
        responseText = "Error de conexión con el núcleo.";
      }
    }

    setTimeout(() => {
      this.addMessage(responseText, "ai");
    }, 500);
  },

  addMessage(text, type) {
    const container = document.querySelector(".chat-container");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${type}`;

    const header = document.createElement("div");
    header.className = "message-header";
    header.textContent = type === "user" ? "USUARIO" : "EÓN";

    const content = document.createElement("div");
    content.textContent = text;

    msgDiv.appendChild(header);
    msgDiv.appendChild(content);

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
  },

  addSystemMessage(text) {
    this.addMessage(text, "ai");
    const lastMsg = document.querySelector(".chat-container").lastElementChild;
    if (lastMsg)
      lastMsg.querySelector(".message-header").textContent = "SISTEMA";
  },
};

window.addEventListener("DOMContentLoaded", () => {
  App.init();
});
