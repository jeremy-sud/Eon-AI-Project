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
    this.initSSO(); // Real SSO initialization & cookie sync
    this.addSystemMessage("Eón está activo. ¿En qué puedo ayudarte?");
    this._isProcessing = false;
  },

  bindEvents() {
    // Navigation
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const view = e.currentTarget.dataset.view;
        if (view) this.switchView(view);

        // Auto-close sidebar drawer on mobile after clicking
        const sidebar = document.querySelector(".sidebar");
        const backdrop = document.getElementById("sidebarBackdrop");
        if (sidebar && sidebar.classList.contains("open")) {
          sidebar.classList.remove("open");
          if (backdrop) backdrop.classList.remove("active");
        }
      });
    });

    // Mobile Menu Toggle bindings
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const sidebar = document.querySelector(".sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    
    if (sidebar && backdrop) {
      if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", () => {
          sidebar.classList.toggle("open");
          backdrop.classList.toggle("active");
        });
      }

      if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener("click", () => {
          sidebar.classList.remove("open");
          backdrop.classList.remove("active");
        });
      }

      backdrop.addEventListener("click", () => {
        sidebar.classList.remove("open");
        backdrop.classList.remove("active");
      });

      // Swipe gestures on sidebar to close it
      let touchStartX = 0;
      let touchEndX = 0;
      
      sidebar.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });
      
      sidebar.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        if (touchStartX - touchEndX > 50) { // Swiped left at least 50px
          sidebar.classList.remove("open");
          backdrop.classList.remove("active");
        }
      }, { passive: true });
    }

    const mobileProfileBtn = document.getElementById("mobileProfileBtn");
    if (mobileProfileBtn) {
      mobileProfileBtn.addEventListener("click", () => {
        this.switchView("profile");
      });
    }

    // Chat
    const chatInput = document.getElementById("chatInput");
    const charCounter = document.getElementById("charCounter");

    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Auto-resize textarea
    chatInput.addEventListener("input", () => {
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + "px";

      // Char counter
      const len = chatInput.value.length;
      if (charCounter) {
        charCounter.textContent = `${len} / 2000`;
        charCounter.className = "char-counter" + (len > 0 ? " visible" : "") + (len > 1800 ? " danger" : len > 1500 ? " warn" : "");
      }
    });

    // Scroll-to-bottom button
    const chatContainer = document.getElementById("chatContainer");
    const scrollBtn = document.getElementById("scrollToBottomBtn");
    if (chatContainer && scrollBtn) {
      chatContainer.addEventListener("scroll", () => {
        const isNearBottom = chatContainer.scrollHeight - chatContainer.scrollTop - chatContainer.clientHeight < 80;
        scrollBtn.style.display = isNearBottom ? "none" : "flex";
      });
      scrollBtn.addEventListener("click", () => {
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: "smooth" });
      });
    }

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

    // Learning system buttons
    const forceConsolidateBtn = document.getElementById("forceConsolidateBtn");
    if (forceConsolidateBtn) {
      forceConsolidateBtn.addEventListener("click", () => this.forceConsolidation());
    }
    
    const viewMemoryBtn = document.getElementById("viewMemoryBtn");
    if (viewMemoryBtn) {
      viewMemoryBtn.addEventListener("click", () => this.viewMemory());
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
    // Check authentication
    const userStr = localStorage.getItem("senselab_session_user");
    if (!userStr && viewName !== "profile" && viewName !== "help") {
      this.addSystemMessage("Acceso Denegado. Por favor, inicia sesión con tu Senselab ID primero.");
      this.switchView("profile");
      return;
    }

    // Update nav
    document
      .querySelectorAll(".nav-item")
      .forEach((el) => el.classList.remove("active"));
    const activeNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
    if (activeNav) activeNav.classList.add("active");

    // Hide all views
    ["chatView", "dreamView", "statusView", "ecosystemView", "genesisView", "helpView", "profileView"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.style.display = "none";
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
    const dot = document.getElementById("connDot");
    const label = document.getElementById("connLabel");
    try {
      const res = await fetch(`${this.API_BASE}/api/status`);
      const data = await res.json();
      if (data.success) {
        this.updateStatusUI(data.status);
        if (dot) { dot.className = "conn-dot online"; }
        if (label) label.textContent = "Backend activo";
      }
    } catch (e) {
      console.error("Status check failed", e);
      if (dot) { dot.className = "conn-dot offline"; }
      if (label) label.textContent = "Sin conexión";
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
    if (this._isProcessing) return;
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    // Add user message
    this.addMessage(text, "user");
    input.value = "";
    input.style.height = "auto";

    // Reset char counter
    const charCounter = document.getElementById("charCounter");
    if (charCounter) charCounter.className = "char-counter";

    // Process logic
    this.processMessage(text);
  },

  async processMessage(text) {
    // Detectar si es una solicitud de imagen
    if (this.detectImageRequest(text)) {
      const prompt = text.replace(/^(crea|genera|dibuja|haz|dame|quiero)\s*(una?\s*)?(imagen|foto|dibujo|arte|ilustraci[oó]n)?\s*(de\s*)?/i, '').trim() || text;
      await this.generateImage(prompt);
      return;
    }

    // Guardar mensaje del usuario para feedback
    this._lastUserMessage = text;

    // Disable send & show typing indicator
    this._isProcessing = true;
    const sendBtn = document.getElementById("sendBtn");
    const typingIndicator = document.getElementById("typingIndicator");
    if (sendBtn) sendBtn.disabled = true;
    if (typingIndicator) typingIndicator.style.display = "flex";

    try {
      const res = await fetch(`${this.API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      if (data.success) {
        setTimeout(() => {
          if (typingIndicator) typingIndicator.style.display = "none";
          this.addMessage(data.reply, "ai", true);

          if (data.learned) {
            this.loadLearningStats();
          }
        }, 300 + Math.random() * 500);
      } else {
        if (typingIndicator) typingIndicator.style.display = "none";
        this.addMessage("Error procesando la solicitud.", "ai");
      }
    } catch (e) {
      console.error(e);
      if (typingIndicator) typingIndicator.style.display = "none";
      this.addMessage("Error de conexión con el núcleo.", "ai");
    } finally {
      this._isProcessing = false;
      if (sendBtn) sendBtn.disabled = false;
    }
  },

  addMessage(text, type, showFeedback = false) {
    const container = document.getElementById("chatContainer") || document.querySelector(".chat-container");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${type}`;

    const header = document.createElement("div");
    header.className = "message-header";
    header.textContent = type === "user" ? "USUARIO" : "EÓN";

    const content = document.createElement("div");
    content.textContent = text;

    // Timestamp
    const timeEl = document.createElement("span");
    timeEl.className = "message-time";
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString('es-CR', { hour: '2-digit', minute: '2-digit' });

    msgDiv.appendChild(header);
    msgDiv.appendChild(content);
    msgDiv.appendChild(timeEl);

    // Añadir botones de feedback para mensajes de Eón
    if (type === "ai" && showFeedback) {
      const feedbackDiv = document.createElement("div");
      feedbackDiv.className = "message-feedback";
      
      const thumbsUp = document.createElement("button");
      thumbsUp.className = "feedback-btn";
      thumbsUp.innerHTML = "👍";
      thumbsUp.title = "Buena respuesta";
      thumbsUp.onclick = () => this.sendFeedback(text, true, feedbackDiv);
      
      const thumbsDown = document.createElement("button");
      thumbsDown.className = "feedback-btn";
      thumbsDown.innerHTML = "👎";
      thumbsDown.title = "Respuesta mejorable";
      thumbsDown.onclick = () => this.sendFeedback(text, false, feedbackDiv);
      
      feedbackDiv.appendChild(thumbsUp);
      feedbackDiv.appendChild(thumbsDown);
      msgDiv.appendChild(feedbackDiv);
    }

    container.appendChild(msgDiv);

    // Auto-scroll only if already near bottom
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 120;
    if (isNearBottom) {
      container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    }
  },

  async sendFeedback(botResponse, isPositive, feedbackDiv) {
    try {
      const res = await fetch(`${this.API_BASE}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_message: this._lastUserMessage || "",
          bot_response: botResponse,
          is_positive: isPositive
        }),
      });
      const data = await res.json();
      
      if (data.success) {
        // Reemplazar botones con mensaje de agradecimiento
        feedbackDiv.innerHTML = `<span style="font-size: 12px; color: var(--text-muted);">${isPositive ? '✓ ¡Gracias!' : '✓ Anotado'}</span>`;
        this.loadLearningStats();
      }
    } catch (e) {
      console.error("Error sending feedback:", e);
    }
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

  // === SISTEMA DE APRENDIZAJE ===
  
  async loadLearningStats() {
    try {
      const res = await fetch(`${this.API_BASE}/api/learning-stats`);
      const data = await res.json();
      
      if (data.success && data.learning) {
        const learn = data.learning;
        
        // Actualizar indicadores en UI
        const el = (id) => document.getElementById(id);
        
        if (el('learnEvents')) el('learnEvents').textContent = learn.learning_events || 0;
        if (el('learnUsers')) el('learnUsers').textContent = learn.memory?.users_known || 0;
        if (el('learnFacts')) el('learnFacts').textContent = learn.memory?.facts_learned || 0;
        if (el('learnFeedback')) el('learnFeedback').textContent = learn.feedback?.total_feedbacks || 0;
        
        const approval = learn.feedback?.positive_rate;
        if (el('learnApproval')) {
          el('learnApproval').textContent = approval !== undefined 
            ? `${(approval * 100).toFixed(0)}%` 
            : '-%';
        }
        
        if (el('learnConsolidations')) {
          el('learnConsolidations').textContent = learn.consolidation?.consolidation_count || 0;
        }
      }
    } catch (e) {
      console.error("Error loading learning stats:", e);
    }
  },
  
  async forceConsolidation() {
    const btn = document.getElementById("forceConsolidateBtn");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Consolidando...';
    }
    
    try {
      const res = await fetch(`${this.API_BASE}/api/consolidate`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (data.success) {
        this.addSystemMessage("💤 Consolidación de memoria completada. Eón ha procesado sus experiencias.");
        this.loadLearningStats();
      }
    } catch (e) {
      this.addSystemMessage("Error en la consolidación.");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-moon"></i> Consolidar Memoria';
      }
    }
  },
  
  async viewMemory() {
    try {
      const res = await fetch(`${this.API_BASE}/api/memory?type=all`);
      const data = await res.json();
      
      if (data.success && data.memory) {
        const mem = data.memory;
        
        let message = "📚 **Estado de la Memoria**\n\n";
        
        // Usuarios conocidos
        if (mem.users && mem.users.length > 0) {
          message += `👥 Usuarios conocidos (${mem.users.length}):\n`;
          mem.users.slice(0, 5).forEach(u => {
            const isCreator = u.is_creator ? ' ⭐' : '';
            message += `  • ${u.name}${isCreator} (${u.interaction_count} interacciones)\n`;
          });
          if (mem.users.length > 5) message += `  ... y ${mem.users.length - 5} más\n`;
        } else {
          message += "👥 No hay usuarios registrados aún.\n";
        }
        
        message += "\n";
        
        // Hechos aprendidos
        if (mem.facts && mem.facts.length > 0) {
          message += `📝 Hechos aprendidos (${mem.facts.length}):\n`;
          mem.facts.slice(0, 3).forEach(f => {
            message += `  • "${f.fact}" (confianza: ${(f.confidence * 100).toFixed(0)}%)\n`;
          });
          if (mem.facts.length > 3) message += `  ... y ${mem.facts.length - 3} más\n`;
        } else {
          message += "📝 No hay hechos aprendidos aún.\n";
        }
        
        // Stats
        if (mem.stats) {
          message += `\n📊 Edad de la memoria: ${mem.stats.memory_age_days?.toFixed(1) || 0} días`;
          message += `\n📊 Total interacciones: ${mem.stats.total_interactions || 0}`;
        }
        
        this.addSystemMessage(message);
      }
    } catch (e) {
      this.addSystemMessage("Error al cargar la memoria.");
    }
  },

  initSSO() {
    this.ssoProfiles = {
      admin: {
        id: 1,
        name: "Ing. Jeremy Arias Solano",
        email: "admin@scisenselab.com",
        company_name: "Fundación SenselabCR S.A.",
        tenant_id: "sl_tenant_000001",
        plan: "business",
        twofa_enabled: true
      },
      pro: {
        id: 3,
        name: "Lic. Andrea Vargas Castro",
        email: "cliente@senselab.com",
        company_name: "Distribuidora del Norte",
        tenant_id: "sl_tenant_000003",
        plan: "pro",
        twofa_enabled: true
      },
      sandbox: {
        id: 4,
        name: "Tec. Carlos Mendoza Rojas",
        email: "dev@scisenselab.com",
        company_name: "Mendoza Dev Studio",
        tenant_id: "sl_tenant_000004",
        plan: "free",
        twofa_enabled: false
      }
    };

    // Bind events for authentication UI elements
    const sidebarLogoutBtn = document.getElementById("sidebarLogoutBtn");
    if (sidebarLogoutBtn) {
      sidebarLogoutBtn.addEventListener("click", () => this.logout(true));
    }

    const profileLogoutBtn = document.getElementById("profileLogoutBtn");
    if (profileLogoutBtn) {
      profileLogoutBtn.addEventListener("click", () => this.logout(true));
    }

    const ssoSyncBtn = document.getElementById("ssoSyncBtn");
    if (ssoSyncBtn) {
      ssoSyncBtn.addEventListener("click", () => {
        this.addSystemMessage("Sincronizando estado SSO con los subdominios...");
        this.syncSessionFromCookies();
      });
    }

    const loginForm = document.getElementById("ssoLoginForm");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const email = document.getElementById("sso-email").value.trim();
        const password = document.getElementById("sso-password").value.trim();
        
        let matchedRole = null;
        for (const [role, profile] of Object.entries(this.ssoProfiles)) {
          if (profile.email === email) {
            matchedRole = role;
            break;
          }
        }

        if (matchedRole) {
          const profile = this.ssoProfiles[matchedRole];
          const mockToken = "sl_mock_session_token_" + Math.random().toString(36).substring(2);
          this.login(profile, mockToken);
        } else {
          // Allow custom user
          const customProfile = {
            id: Math.floor(1000 + Math.random() * 9000),
            name: email.split('@')[0].toUpperCase(),
            email: email,
            company_name: "Empresa Personal",
            tenant_id: "sl_tenant_" + Math.floor(100000 + Math.random() * 900000),
            plan: "free",
            twofa_enabled: false
          };
          const mockToken = "sl_mock_session_token_" + Math.random().toString(36).substring(2);
          this.login(customProfile, mockToken);
        }
      });
    }

    // Quick login buttons removed

    // Bind click events to tenant options in ecosystem view
    document.querySelectorAll(".tenant-option").forEach((option) => {
      option.addEventListener("click", (e) => {
        const role = e.currentTarget.dataset.role;
        if (role && this.ssoProfiles[role]) {
          const profile = this.ssoProfiles[role];
          const mockToken = "sl_mock_session_token_123456";
          this.login(profile, mockToken);
        }
      });
    });

    // Set up BroadcastChannel
    try {
      this.authChannel = new BroadcastChannel('senselab_session_sync');
      this.authChannel.onmessage = (event) => {
        if (!event.data) return;
        if (event.data.type === 'LOGOUT') {
          this.logout(false);
        } else if (event.data.type === 'LOGIN' || event.data.type === 'TENANT_CHANGE') {
          const userObj = typeof event.data.user === 'string' ? JSON.parse(event.data.user) : event.data.user;
          const userToken = event.data.token || "sl_mock_session_token_123456";
          
          this.state.user = userObj;
          localStorage.setItem('senselab_session_token', userToken);
          localStorage.setItem('senselab_session_user', JSON.stringify(userObj));
          
          this.updateAuthUI(userObj);
          this.switchView('chat');
        }
      };
    } catch (err) {
      console.error("BroadcastChannel sync disabled", err);
    }

    // Load initial session
    this.syncSessionFromCookies();
  },

  syncSessionFromCookies() {
    let token = this.getCookie('senselab_session_token');
    let userStr = this.getCookie('senselab_session_user');

    if (token && userStr) {
      localStorage.setItem('senselab_session_token', token);
      localStorage.setItem('senselab_session_user', userStr);
    } else {
      token = localStorage.getItem('senselab_session_token');
      userStr = localStorage.getItem('senselab_session_user');
      
      if (token && userStr) {
        this.setCookie('senselab_session_token', token);
        this.setCookie('senselab_session_user', userStr);
      }
    }

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        this.state.user = user;
        this.updateAuthUI(user);
        
        // Only redirect to chat if currently on profile page
        if (this.state.currentView === 'profile') {
          this.switchView('chat');
        }
      } catch (e) {
        console.error("Error loading user session", e);
        this.logout(false);
      }
    } else {
      this.logout(false);
    }
  },

  login(profile, token) {
    this.state.user = profile;
    localStorage.setItem('senselab_session_token', token);
    localStorage.setItem('senselab_session_user', JSON.stringify(profile));
    
    // Set wildcard cookies for *.scisenselab.com SSO compatibility
    this.setCookie('senselab_session_token', token);
    this.setCookie('senselab_session_user', JSON.stringify(profile));
    this.setCookie('senselab_tenant_id', profile.tenant_id);

    // Broadcast to other tabs
    try {
      if (this.authChannel) {
        this.authChannel.postMessage({
          type: 'LOGIN',
          token: token,
          user: profile
        });
      }
    } catch (e) {}

    this.updateAuthUI(profile);
    this.addSystemMessage(`✓ Acceso concedido como ${profile.name}. Bienvenido a Eón.`);
    
    // Switch to chat if login is triggered from profile page
    if (this.state.currentView === 'profile') {
      this.switchView('chat');
    }
  },

  logout(postBroadcast = true) {
    this.state.user = null;
    localStorage.removeItem('senselab_session_token');
    localStorage.removeItem('senselab_session_user');
    
    this.eraseCookie('senselab_session_token');
    this.eraseCookie('senselab_session_user');
    this.eraseCookie('senselab_tenant_id');

    if (postBroadcast) {
      try {
        if (this.authChannel) {
          this.authChannel.postMessage({ type: 'LOGOUT' });
        }
      } catch (e) {}
    }

    // Hide sidebar user card
    const userCard = document.getElementById("sidebarUserCard");
    if (userCard) userCard.style.display = "none";

    // Update mobile profile button
    const mobileProfileBtn = document.getElementById("mobileProfileBtn");
    if (mobileProfileBtn) {
      mobileProfileBtn.innerHTML = '<i class="fa-regular fa-user"></i>';
      mobileProfileBtn.classList.remove("logged-in");
    }

    // Toggle screens
    const loginScreen = document.getElementById("ssoLoginScreen");
    const profileScreen = document.getElementById("ssoProfileScreen");
    if (loginScreen) loginScreen.style.display = "block";
    if (profileScreen) profileScreen.style.display = "none";

    // Lock navigation items visually
    document.querySelectorAll(".nav-item").forEach(item => {
      const view = item.dataset.view;
      if (view !== 'profile' && view !== 'help') {
        item.style.opacity = "0.5";
      } else {
        item.style.opacity = "1";
      }
    });

    this.switchView('profile');
  },

  updateAuthUI(profile) {
    // Show user card in sidebar
    const userCard = document.getElementById("sidebarUserCard");
    if (userCard) {
      userCard.style.display = "flex";
      document.getElementById("sidebarUserName").textContent = profile.name;
      document.getElementById("sidebarUserPlan").textContent = `Plan ${profile.plan.toUpperCase()}`;
    }

    // Update mobile profile button
    const mobileProfileBtn = document.getElementById("mobileProfileBtn");
    if (mobileProfileBtn) {
      mobileProfileBtn.innerHTML = '<i class="fa-solid fa-user-astronaut text-accent"></i><span class="active-dot"></span>';
      mobileProfileBtn.classList.add("logged-in");
    }

    // Update profile view screen
    const loginScreen = document.getElementById("ssoLoginScreen");
    const profileScreen = document.getElementById("ssoProfileScreen");
    if (loginScreen) loginScreen.style.display = "none";
    if (profileScreen) {
      profileScreen.style.display = "block";
      
      document.getElementById("profile-name").textContent = profile.name;
      document.getElementById("profile-email").textContent = profile.email;
      document.getElementById("profile-company").textContent = profile.company_name;
      
      const mfaEl = document.getElementById("profile-mfa");
      if (mfaEl) {
        mfaEl.textContent = profile.twofa_enabled ? "Activo" : "Inactivo";
        mfaEl.className = "stat-value " + (profile.twofa_enabled ? "highlight" : "text-muted");
      }
      
      const planBadge = document.getElementById("profile-plan-badge");
      if (planBadge) {
        planBadge.textContent = profile.plan.toUpperCase();
        planBadge.className = "tenant-badge " + (profile.plan === 'business' ? 'admin' : (profile.plan === 'pro' ? 'pro' : 'sandbox'));
      }
      
      const tenantBadge = document.getElementById("profile-tenant-badge");
      if (tenantBadge) tenantBadge.textContent = profile.tenant_id;
      
      // Simulated token usage based on plan
      let currentTokens = 1250;
      let maxTokens = 5000;
      if (profile.plan === 'business') {
        currentTokens = 4528;
        maxTokens = 50000;
      } else if (profile.plan === 'pro') {
        currentTokens = 8412;
        maxTokens = 15000;
      }
      
      const tokenUsageEl = document.getElementById("profile-token-usage-txt");
      if (tokenUsageEl) tokenUsageEl.textContent = `${currentTokens.toLocaleString()} / ${maxTokens.toLocaleString()}`;
      
      const progressEl = document.getElementById("profile-token-progress");
      if (progressEl) progressEl.style.width = `${(currentTokens / maxTokens * 100).toFixed(1)}%`;
      
      const cookieTokenEl = document.getElementById("profile-cookie-token");
      if (cookieTokenEl) cookieTokenEl.textContent = this.getCookie('senselab_session_token') ? "Sincronizado" : "No Encontrado";
    }

    // Unlock navbar items
    document.querySelectorAll(".nav-item").forEach(item => {
      item.style.opacity = "1";
    });

    // Update ecosystem view UI
    const ssoUserName = document.getElementById("sso-user-name");
    const ssoUserEmail = document.getElementById("sso-user-email");
    const ssoUserTenant = document.getElementById("sso-user-tenant");
    const ssoUserPlan = document.getElementById("sso-user-plan");

    if (ssoUserName) ssoUserName.textContent = profile.name;
    if (ssoUserEmail) ssoUserEmail.textContent = profile.email;
    if (ssoUserTenant) ssoUserTenant.textContent = profile.tenant_id;
    if (ssoUserPlan) {
      ssoUserPlan.textContent = profile.plan.toUpperCase();
      ssoUserPlan.className = "tenant-badge " + (profile.plan === 'business' ? 'admin' : (profile.plan === 'pro' ? 'pro' : 'sandbox'));
    }

    let role = "admin";
    if (profile.email === "cliente@senselab.com") role = "pro";
    else if (profile.email === "dev@scisenselab.com") role = "sandbox";

    document.querySelectorAll(".tenant-option").forEach((opt) => {
      opt.classList.remove("active");
      if (opt.dataset.role === role) {
        opt.classList.add("active");
      }
    });
  },

  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
    return null;
  },

  setCookie(name, value, days = 30) {
    let expires = "";
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
    }
    const hostname = window.location.hostname;
    let domain = "";
    if (hostname.includes("scisenselab.com")) {
      domain = "; domain=.scisenselab.com";
    } else if (hostname.includes("scisenselab.local")) {
      domain = "; domain=.scisenselab.local";
    }
    document.cookie = `${name}=${encodeURIComponent(value)}${expires}; path=/; Secure; SameSite=Lax${domain}`;
  },

  eraseCookie(name) {
    const hostname = window.location.hostname;
    let domain = "";
    if (hostname.includes("scisenselab.com")) {
      domain = "; domain=.scisenselab.com";
    } else if (hostname.includes("scisenselab.local")) {
      domain = "; domain=.scisenselab.local";
    }
    document.cookie = `${name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; Secure; SameSite=Lax${domain}`;
  },
};

window.addEventListener("DOMContentLoaded", () => {
  App.init();
  
  // Cargar estadísticas de aprendizaje al inicio
  App.loadLearningStats();
  
  // Actualizar estadísticas cada 30 segundos
  setInterval(() => {
    App.loadStats();
    App.loadLearningStats();
  }, 30000);
});
