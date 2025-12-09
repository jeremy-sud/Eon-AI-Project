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
  },

  init() {
    this.bindEvents();
    this.startStatusPolling();
    this.loadConfig();
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
    const imageKeywords = [
      'imagen', 'image', 'genera', 'crea', 'dibuja', 'draw', 
      'picture', 'foto', 'ilustra', 'visualiza', 'arte', 'art'
    ];
    const lowerText = text.toLowerCase();
    return imageKeywords.some(keyword => lowerText.includes(keyword));
  },

  handleUpload() {
    // Crear input de archivo oculto
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt,.json,.csv';
    fileInput.style.display = 'none';
    
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      this.addSystemMessage(`Archivo seleccionado: ${file.name}`);
      
      try {
        const text = await file.text();
        // Mostrar preview del contenido
        const preview = text.substring(0, 200) + (text.length > 200 ? '...' : '');
        this.addSystemMessage(`Contenido (${text.length} caracteres):\n${preview}`);
        
        // En el futuro, aquí se podría enviar al servidor para aprendizaje
        this.addSystemMessage("El archivo ha sido recibido. La función de aprendizaje desde archivos estará disponible próximamente.");
      } catch (err) {
        this.addSystemMessage(`Error al leer el archivo: ${err.message}`);
      }
      
      document.body.removeChild(fileInput);
    });
    
    document.body.appendChild(fileInput);
    fileInput.click();
  },
};

window.addEventListener("DOMContentLoaded", () => {
  App.init();
});
