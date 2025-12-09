/**
 * Eón Web Interface - Main Application Logic
 */

const App = {
  API_BASE: "",
  state: {
    currentView: "chat",
    status: null,
    config: {},
    chatHistory: [],
    stats: {},
  },

  init() {
    this.bindEvents();
    this.startStatusPolling();
    this.loadConfig();
    this.loadStats();
    this.addSystemMessage("Eón está activo. ¿En qué puedo ayudarte?");
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

    // Action buttons
    const imageBtn = document.getElementById("imageBtn");
    if (imageBtn) {
      imageBtn.addEventListener("click", () => this.promptForImage());
    }
    
    const uploadBtn = document.getElementById("uploadBtn");
    if (uploadBtn) {
      uploadBtn.addEventListener("click", () => this.handleUpload());
    }
    
    // Clear history button
    const clearHistoryBtn = document.getElementById("clearHistoryBtn");
    if (clearHistoryBtn) {
      clearHistoryBtn.addEventListener("click", () => this.clearHistory());
    }

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
    ["temp", "radius", "leak", "topp", "tokens", "lr"].forEach((key) => {
      const input = document.getElementById(`cfg-${key}`);
      if (input) {
        input.addEventListener("input", (e) => {
          document.getElementById(`val-${key}`).textContent = e.target.value;
        });
      }
    });

    const saveBtn = document.getElementById("saveConfigBtn");
    if (saveBtn) saveBtn.addEventListener("click", () => this.saveConfig());
    
    // Personality selector
    const personalitySelect = document.getElementById("cfg-personality");
    if (personalitySelect) {
      personalitySelect.addEventListener("change", () => this.savePersonality());
    }
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
    if (config.temperature !== undefined) {
      document.getElementById("cfg-temp").value = config.temperature;
      document.getElementById("val-temp").textContent = config.temperature;
    }
    if (config.spectral_radius !== undefined) {
      document.getElementById("cfg-radius").value = config.spectral_radius;
      document.getElementById("val-radius").textContent = config.spectral_radius;
    }
    if (config.leak_rate !== undefined) {
      document.getElementById("cfg-leak").value = config.leak_rate;
      document.getElementById("val-leak").textContent = config.leak_rate;
    }
    if (config.top_p !== undefined) {
      document.getElementById("cfg-topp").value = config.top_p;
      document.getElementById("val-topp").textContent = config.top_p;
    }
    if (config.max_tokens !== undefined) {
      document.getElementById("cfg-tokens").value = config.max_tokens;
      document.getElementById("val-tokens").textContent = config.max_tokens;
    }
    if (config.learning_rate !== undefined) {
      document.getElementById("cfg-lr").value = config.learning_rate;
      document.getElementById("val-lr").textContent = config.learning_rate;
    }
  },

  async saveConfig() {
    const config = {
      temperature: document.getElementById("cfg-temp").value,
      spectral_radius: document.getElementById("cfg-radius").value,
      leak_rate: document.getElementById("cfg-leak").value,
      top_p: document.getElementById("cfg-topp").value,
      max_tokens: document.getElementById("cfg-tokens").value,
      learning_rate: document.getElementById("cfg-lr").value,
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
        this.updateStatusUI(data.status);
      }
    } catch (e) {
      console.error("Status check failed", e);
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
    // Detectar si es una solicitud de imagen
    if (this.detectImageRequest(text)) {
      // Extraer el tema de la imagen del texto
      const prompt = text.replace(/^(crea|genera|dibuja|haz|dame|quiero)\s*(una?\s*)?(imagen|foto|dibujo|arte|ilustraci[oó]n)?\s*(de\s*)?/i, '').trim() || text;
      await this.generateImage(prompt);
      return;
    }

    try {
      // Usar el endpoint de chat para conversación
      const res = await fetch(`${this.API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      if (data.success) {
        setTimeout(() => {
          this.addMessage(data.reply, "ai");
        }, 300 + Math.random() * 500); // Delay natural
      } else {
        this.addMessage("Error procesando la solicitud.", "ai");
      }
    } catch (e) {
      console.error(e);
      this.addMessage("Error de conexión con el núcleo.", "ai");
    }
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

  promptForImage() {
    const input = document.getElementById("chatInput");
    const currentText = input.value.trim();
    if (currentText) {
      // Si hay texto, usarlo como prompt
      this.generateImage(currentText);
      input.value = "";
    } else {
      // Pedir al usuario que escriba algo
      input.placeholder = "Describe la imagen que quieres generar...";
      input.focus();
      this.addSystemMessage("Escribe una descripción para generar arte neuronal.");
    }
  },

  async generateImage(prompt) {
    this.addMessage(`Genera una imagen: ${prompt}`, "user");
    this.addSystemMessage("Generando arte neuronal... Por favor espera.");
    
    try {
      const res = await fetch(`${this.API_BASE}/api/generate-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt, size: 256 }),
      });
      const data = await res.json();

      if (data.success) {
        this.addImageMessage(data.image, data.message);
      } else {
        this.addSystemMessage(`Error: ${data.error || 'No se pudo generar la imagen'}`);
      }
    } catch (e) {
      console.error(e);
      this.addSystemMessage("Error de conexión al generar imagen.");
    }
  },

  addImageMessage(imageSrc, caption) {
    const container = document.querySelector(".chat-container");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message ai";

    const header = document.createElement("div");
    header.className = "message-header";
    header.textContent = "EÓN";

    const imgWrapper = document.createElement("div");
    imgWrapper.style.cssText = "margin: 0.5rem 0; border-radius: 8px; overflow: hidden;";
    
    const img = document.createElement("img");
    img.src = imageSrc;
    img.alt = caption;
    img.style.cssText = "max-width: 100%; height: auto; display: block;";
    
    const captionEl = document.createElement("div");
    captionEl.style.cssText = "font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;";
    captionEl.textContent = caption;

    imgWrapper.appendChild(img);
    msgDiv.appendChild(header);
    msgDiv.appendChild(imgWrapper);
    msgDiv.appendChild(captionEl);

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
  },

  detectImageRequest(text) {
    const lowerText = text.toLowerCase();
    
    // Patrones específicos para solicitar imágenes (más precisos)
    const imagePatterns = [
      /\b(genera|crea|dibuja|haz|hazme|dame|quiero|necesito|puedes (hacer|crear|generar|dibujar))\s+(una?\s+)?(imagen|foto|dibujo|ilustraci[oó]n|arte|picture|image)/i,
      /\b(imagen|foto|dibujo|ilustraci[oó]n|picture|image)\s+(de|del|sobre|con)\b/i,
      /\bdibuja(me)?\s+(un|una|algo|el|la)\b/i,
      /\bgenera(me)?\s+arte\b/i,
      /\bcrea(me)?\s+algo\s+(visual|artístico)/i,
    ];
    
    return imagePatterns.some(pattern => pattern.test(lowerText));
  },

  handleUpload() {
    // Crear input de archivo oculto
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt,.md,.py,.js,.json,.csv';
    fileInput.style.display = 'none';
    
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      this.addSystemMessage(`Procesando archivo: ${file.name}...`);
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const res = await fetch(`${this.API_BASE}/api/upload`, {
          method: 'POST',
          body: formData
        });
        
        const data = await res.json();
        
        if (data.success) {
          this.addSystemMessage(`✓ ${data.message}`);
          if (data.learned) {
            this.addSystemMessage("El contenido ha sido procesado para aprendizaje.");
          }
          this.loadStats(); // Actualizar estadísticas
        } else {
          this.addSystemMessage(`Error: ${data.error}`);
        }
      } catch (err) {
        this.addSystemMessage(`Error al subir el archivo: ${err.message}`);
      }
      
      document.body.removeChild(fileInput);
    });
    
    document.body.appendChild(fileInput);
    fileInput.click();
  },
  
  async loadStats() {
    try {
      const res = await fetch(`${this.API_BASE}/api/stats`);
      const data = await res.json();
      if (data.success) {
        this.state.stats = data.stats;
        this.updateStatsUI(data.stats);
      }
    } catch (e) {
      console.error("Stats load failed", e);
    }
  },
  
  updateStatsUI(stats) {
    // Actualizar elementos de estadísticas si existen
    const messagesEl = document.getElementById("statMessages");
    if (messagesEl) messagesEl.textContent = stats.total_messages || 0;
    
    const imagesEl = document.getElementById("statImages");
    if (imagesEl) imagesEl.textContent = stats.total_images_generated || 0;
    
    const filesEl = document.getElementById("statFiles");
    if (filesEl) filesEl.textContent = stats.total_files_processed || 0;
    
    const uptimeEl = document.getElementById("statUptime");
    if (uptimeEl) uptimeEl.textContent = stats.session_uptime_formatted || "0h 0m";
    
    const lmStatusEl = document.getElementById("statLmStatus");
    if (lmStatusEl) {
      lmStatusEl.textContent = stats.lm_available ? "Activo" : "Inactivo";
      lmStatusEl.style.color = stats.lm_available ? "var(--primary)" : "var(--text-secondary)";
    }
  },
  
  async clearHistory() {
    if (!confirm("¿Estás seguro de querer limpiar el historial de conversación?")) {
      return;
    }
    
    try {
      const res = await fetch(`${this.API_BASE}/api/history`, {
        method: 'DELETE'
      });
      const data = await res.json();
      
      if (data.success) {
        // Limpiar UI de chat
        const container = document.querySelector(".chat-container");
        container.innerHTML = '';
        this.addSystemMessage("Historial limpiado. Comenzando nueva conversación.");
      }
    } catch (e) {
      this.addSystemMessage("Error al limpiar historial.");
    }
  },
  
  async savePersonality() {
    const personalitySelect = document.getElementById("cfg-personality");
    const verbositySelect = document.getElementById("cfg-verbosity");
    
    if (!personalitySelect) return;
    
    try {
      const res = await fetch(`${this.API_BASE}/api/personality`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          personality: personalitySelect.value,
          verbosity: verbositySelect ? verbositySelect.value : 'normal'
        })
      });
      const data = await res.json();
      
      if (data.success) {
        this.addSystemMessage(`Personalidad actualizada: ${data.personality}`);
      }
    } catch (e) {
      console.error("Error saving personality", e);
    }
  },
};

window.addEventListener("DOMContentLoaded", () => {
  App.init();
  
  // Actualizar estadísticas cada 30 segundos
  setInterval(() => App.loadStats(), 30000);
});
