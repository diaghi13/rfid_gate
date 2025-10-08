// ========================================================================
// 🚀 RFID Gate Web UI - Demo Mode JavaScript
// ========================================================================
// Versione semplificata senza autenticazione per test e demo

// ===========================================
// 🌐 GLOBAL STATE & CONFIGURATION (DEMO)
// ===========================================

class RFIDGateUI {
  constructor() {
    this.wsConnection = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;

    // 🔓 DEMO MODE: Bypass authentication
    this.token = "demo-token-12345";
    this.user = { username: "Demo User", role: "admin" };

    console.log("🎭 DEMO MODE: Authentication bypassed");

    // Set demo token in localStorage for consistency
    localStorage.setItem("access_token", this.token);
    localStorage.setItem("user", JSON.stringify(this.user));

    this.initializeWebSocket();
    this.updateUserInterface();
  }

  // ===========================================
  // 🔓 DEMO AUTHENTICATION (BYPASSED)
  // ===========================================

  checkAuthentication() {
    // Always authenticated in demo mode
    return true;
  }

  updateUserInterface() {
    // Update username in header
    const usernameElement = document.getElementById("username");
    if (usernameElement) {
      usernameElement.textContent = this.user.username + " (Demo)";
    }
  }

  redirectToLogin() {
    // No redirect in demo mode
    console.log("🎭 DEMO: Login redirect bypassed");
  }

  logout() {
    // No logout in demo mode, just reload
    console.log("🎭 DEMO: Logout bypassed, reloading page");
    location.reload();
  }

  // ===========================================
  // 📡 WEBSOCKET CONNECTION (DEMO)
  // ===========================================

  initializeWebSocket() {
    // Skip WebSocket in demo mode for now
    console.log("🎭 DEMO: WebSocket connection skipped");
    this.wsConnection = null;
  }

  // ===========================================
  // 🔧 API UTILITIES (SIMPLIFIED FOR DEMO)
  // ===========================================

  async apiRequest(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("🚨 API Error:", error);
      this.showNotification(`Errore API: ${error.message}`, "error");
      throw error;
    }
  }

  // ===========================================
  // 📊 DASHBOARD FUNCTIONALITY
  // ===========================================

  async loadDashboard() {
    console.log("📊 Loading dashboard...");
    try {
      // Carica stato sistema
      await this.loadSystemStatus();

      // Carica log recenti
      await this.loadRecentLogs();

      // Avvia aggiornamento automatico
      this.startDashboardRefresh();
    } catch (error) {
      console.error("❌ Errore caricamento dashboard:", error);
      this.showNotification("Errore caricamento dashboard", "error");
    }
  }

  async loadSystemStatus() {
    try {
      const response = await this.apiRequest("/api/status");
      if (response.status === "success") {
        this.updateSystemStatus(response.data);
      }
    } catch (error) {
      console.error("❌ Errore caricamento status:", error);
      // Usa dati demo se l'API non è disponibile
      this.updateSystemStatus({
        server: "running",
        config_manager: "active",
        timestamp: new Date().toISOString(),
      });
    }
  }

  updateSystemStatus(data) {
    // Aggiorna stato sistema nella UI
    const statusElements = {
      server: document.getElementById("server-status"),
      readers: document.getElementById("readers-status"),
      network: document.getElementById("network-status"),
    };

    // Server status
    if (statusElements.server) {
      statusElements.server.innerHTML = `
        <i class="fas fa-circle status-online"></i>
        <span>Online</span>
      `;
    }

    // Readers status (demo data)
    if (statusElements.readers) {
      statusElements.readers.innerHTML = `
        <i class="fas fa-circle status-online"></i>
        <span>2/2 Attivi</span>
      `;
    }

    // Network status (demo data)
    if (statusElements.network) {
      statusElements.network.innerHTML = `
        <i class="fas fa-circle status-online"></i>
        <span>Connesso</span>
      `;
    }

    // Raspberry Pi status (demo data)
    this.updateRaspberryPiStatus();

    // Aggiorna timestamp
    const timestampElement = document.getElementById("last-update");
    if (timestampElement) {
      timestampElement.textContent = new Date().toLocaleString("it-IT");
    }
  }

  updateRaspberryPiStatus() {
    // Simula dati reali della temperatura del Raspberry Pi
    const cpuTemp = (45 + Math.random() * 15).toFixed(1); // 45-60°C
    const cpuLoad = (10 + Math.random() * 30).toFixed(0); // 10-40%
    const diskUsage = (25 + Math.random() * 20).toFixed(0); // 25-45%

    // Aggiorna temperatura CPU
    const tempElement = document.getElementById("cpu-temperature");
    if (tempElement) {
      const tempColor =
        cpuTemp > 70
          ? "status-error"
          : cpuTemp > 60
          ? "status-warning"
          : "status-online";
      tempElement.innerHTML = `<span class="${tempColor}">${cpuTemp}°C</span>`;
    }

    // Aggiorna carico CPU
    const loadElement = document.getElementById("cpu-load");
    if (loadElement) {
      const loadColor =
        cpuLoad > 80
          ? "status-error"
          : cpuLoad > 60
          ? "status-warning"
          : "status-online";
      loadElement.innerHTML = `<span class="${loadColor}">${cpuLoad}%</span>`;
    }

    // Aggiorna spazio disco
    const diskElement = document.getElementById("disk-usage");
    if (diskElement) {
      const diskColor =
        diskUsage > 80
          ? "status-error"
          : diskUsage > 70
          ? "status-warning"
          : "status-online";
      diskElement.innerHTML = `<span class="${diskColor}">${diskUsage}%</span>`;
    }

    // Aggiorna indicatore status Raspberry Pi
    const rpiStatusElement = document.getElementById("rpi-status");
    if (rpiStatusElement) {
      const overallStatus =
        cpuTemp > 70 || cpuLoad > 80 || diskUsage > 80
          ? "status-error"
          : cpuTemp > 60 || cpuLoad > 60 || diskUsage > 70
          ? "status-warning"
          : "status-online";
      rpiStatusElement.innerHTML = `<i class="fas fa-circle ${overallStatus}"></i>`;
    }
  }

  async loadRecentLogs() {
    // Dati demo per i log
    const demoLogs = [
      {
        timestamp: new Date(Date.now() - 300000).toISOString(),
        user_name: "Mario Rossi",
        uid: "04:12:34:56",
        access_granted: true,
        reader_id: "reader_1",
      },
      {
        timestamp: new Date(Date.now() - 600000).toISOString(),
        user_name: "Anna Verdi",
        uid: "04:56:78:90",
        access_granted: true,
        reader_id: "reader_2",
      },
      {
        timestamp: new Date(Date.now() - 900000).toISOString(),
        user_name: "Utente Sconosciuto",
        uid: "04:AA:BB:CC",
        access_granted: false,
        reader_id: "reader_1",
      },
    ];

    this.displayRecentLogs(demoLogs);
  }

  displayRecentLogs(logs) {
    const container = document.getElementById("recent-logs");
    if (!container) return;

    container.innerHTML = logs
      .map(
        (log) => `
      <div class="log-entry ${log.access_granted ? "success" : "error"}">
        <div class="log-time">${new Date(log.timestamp).toLocaleTimeString(
          "it-IT"
        )}</div>
        <div class="log-user">${log.user_name}</div>
        <div class="log-uid">${log.uid}</div>
        <div class="log-status">
          <i class="fas ${
            log.access_granted ? "fa-check-circle" : "fa-times-circle"
          }"></i>
          ${log.access_granted ? "Accesso" : "Negato"}
        </div>
      </div>
    `
      )
      .join("");
  }

  startDashboardRefresh() {
    // Aggiorna ogni 30 secondi
    setInterval(() => {
      this.loadSystemStatus();
    }, 30000);
  }

  // ===========================================
  // ⚙️ CONFIGURATION FUNCTIONALITY
  // ===========================================

  async loadConfiguration() {
    console.log("⚙️ Loading configuration...");
    try {
      const response = await this.apiRequest("/api/config");
      if (response.status === "success") {
        this.populateConfigForm(response.data);
      }
    } catch (error) {
      console.error("❌ Errore caricamento configurazione:", error);
      this.showNotification("Errore caricamento configurazione", "error");
    }
  }

  populateConfigForm(config) {
    // Mappa i campi della configurazione ai form fields
    const fieldMap = {
      // Sistema
      TORNELLO_ID: "tornello_id",
      BIDIRECTIONAL_MODE: "bidirectional_mode",

      // Lettori RFID
      READER_1_ENABLED: "reader_1_enabled",
      READER_1_SPI_BUS: "reader_1_spi_bus",
      READER_1_SPI_DEVICE: "reader_1_spi_device",
      READER_1_IRQ_PIN: "reader_1_irq_pin",
      READER_1_RESET_PIN: "reader_1_reset_pin",

      READER_2_ENABLED: "reader_2_enabled",
      READER_2_SPI_BUS: "reader_2_spi_bus",
      READER_2_SPI_DEVICE: "reader_2_spi_device",
      READER_2_IRQ_PIN: "reader_2_irq_pin",
      READER_2_RESET_PIN: "reader_2_reset_pin",

      // Relè
      RELAY_IN_ENABLE: "relay_in_enable",
      RELAY_IN_PIN: "relay_in_pin",
      RELAY_IN_ACTIVE_TIME: "relay_in_active_time",
      RELAY_IN_ACTIVE_LOW: "relay_in_active_low",
      RELAY_OUT_ENABLE: "relay_out_enable",
      RELAY_OUT_PIN: "relay_out_pin",
      RELAY_OUT_ACTIVE_TIME: "relay_out_active_time",
      RELAY_OUT_ACTIVE_LOW: "relay_out_active_low",

      // Rete
      MQTT_BROKER: "mqtt_broker",
      MQTT_PORT: "mqtt_port",
      MQTT_USERNAME: "mqtt_username",
      MQTT_PASSWORD: "mqtt_password",
      MQTT_TOPIC_BASE: "mqtt_topic_base",
    };

    // Popola i campi del form
    Object.entries(fieldMap).forEach(([envKey, fieldName]) => {
      const element = document.getElementById(fieldName);
      if (element && config[envKey] !== undefined) {
        if (element.type === "checkbox") {
          element.checked =
            config[envKey] === "true" || config[envKey] === true;
        } else {
          element.value = config[envKey];
        }
      }
    });
  }

  async saveConfiguration() {
    console.log("💾 Saving configuration...");

    const form = document.getElementById("config-form");
    if (!form) {
      this.showNotification("Form di configurazione non trovato", "error");
      return;
    }

    // Raccogli i dati dal form
    const formData = new FormData(form);
    const configData = {};

    // Mappa inversa: da field name a env variable
    const fieldMap = {
      tornello_id: "TORNELLO_ID",
      bidirectional_mode: "BIDIRECTIONAL_MODE",

      reader_1_enabled: "READER_1_ENABLED",
      reader_1_spi_bus: "READER_1_SPI_BUS",
      reader_1_spi_device: "READER_1_SPI_DEVICE",
      reader_1_irq_pin: "READER_1_IRQ_PIN",
      reader_1_reset_pin: "READER_1_RESET_PIN",

      reader_2_enabled: "READER_2_ENABLED",
      reader_2_spi_bus: "READER_2_SPI_BUS",
      reader_2_spi_device: "READER_2_SPI_DEVICE",
      reader_2_irq_pin: "READER_2_IRQ_PIN",
      reader_2_reset_pin: "READER_2_RESET_PIN",

      relay_in_enable: "RELAY_IN_ENABLE",
      relay_in_pin: "RELAY_IN_PIN",
      relay_in_active_time: "RELAY_IN_ACTIVE_TIME",
      relay_in_active_low: "RELAY_IN_ACTIVE_LOW",
      relay_out_enable: "RELAY_OUT_ENABLE",
      relay_out_pin: "RELAY_OUT_PIN",
      relay_out_active_time: "RELAY_OUT_ACTIVE_TIME",
      relay_out_active_low: "RELAY_OUT_ACTIVE_LOW",

      mqtt_broker: "MQTT_BROKER",
      mqtt_port: "MQTT_PORT",
      mqtt_username: "MQTT_USERNAME",
      mqtt_password: "MQTT_PASSWORD",
      mqtt_topic_base: "MQTT_TOPIC_BASE",
    };

    // Converti FormData in oggetto usando la mappa
    for (const [fieldName, envKey] of Object.entries(fieldMap)) {
      const element = document.getElementById(fieldName);
      if (element) {
        if (element.type === "checkbox") {
          configData[envKey] = element.checked.toString();
        } else {
          configData[envKey] = element.value;
        }
      }
    }

    try {
      const response = await this.apiRequest("/api/config", {
        method: "POST",
        body: JSON.stringify(configData),
      });

      if (response.status === "success") {
        this.showNotification(
          "Configurazione salvata con successo!",
          "success"
        );
      } else {
        throw new Error(response.message || "Errore sconosciuto");
      }
    } catch (error) {
      console.error("❌ Errore salvataggio configurazione:", error);
      this.showNotification(`Errore salvataggio: ${error.message}`, "error");
    }
  }

  // ===========================================
  // 🎛️ CONTROL FUNCTIONALITY
  // ===========================================

  async openGate() {
    console.log("🚪 Opening gate...");
    this.showNotification("🎭 DEMO: Comando apertura cancello", "info");
  }

  async emergencyStop() {
    console.log("🛑 Emergency stop...");
    this.showNotification("🎭 DEMO: Arresto di emergenza", "warning");
  }

  // ===========================================
  // 📋 LOGS FUNCTIONALITY
  // ===========================================

  async loadLogs() {
    console.log("📋 Loading logs...");
    // Usa dati demo per i log
    const demoLogs = Array.from({ length: 20 }, (_, i) => ({
      timestamp: new Date(Date.now() - i * 900000).toISOString(),
      user_name: `Utente ${i + 1}`,
      uid: `04:${(10 + i).toString(16).toUpperCase()}:${(20 + i)
        .toString(16)
        .toUpperCase()}:${(30 + i).toString(16).toUpperCase()}`,
      access_granted: Math.random() > 0.2,
      reader_id: `reader_${(i % 2) + 1}`,
    }));

    this.displayLogs(demoLogs);
  }

  displayLogs(logs) {
    const container = document.getElementById("logs-container");
    if (!container) return;

    container.innerHTML = logs
      .map(
        (log) => `
      <tr class="${log.access_granted ? "success" : "error"}">
        <td>${new Date(log.timestamp).toLocaleString("it-IT")}</td>
        <td>${log.user_name}</td>
        <td><code>${log.uid}</code></td>
        <td>
          <span class="status-badge ${
            log.access_granted ? "success" : "error"
          }">
            <i class="fas ${log.access_granted ? "fa-check" : "fa-times"}"></i>
            ${log.access_granted ? "Accesso" : "Negato"}
          </span>
        </td>
        <td>${log.reader_id}</td>
      </tr>
    `
      )
      .join("");
  }

  // ===========================================
  // 🔔 NOTIFICATION SYSTEM
  // ===========================================

  showNotification(message, type = "info") {
    // Crea elemento notifica
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <i class="fas ${this.getNotificationIcon(type)}"></i>
      <span>${message}</span>
      <button onclick="this.parentElement.remove()" class="btn-close">
        <i class="fas fa-times"></i>
      </button>
    `;

    // Aggiungi al container notifiche
    let container = document.getElementById("notifications");
    if (!container) {
      container = document.createElement("div");
      container.id = "notifications";
      container.className = "notifications-container";
      document.body.appendChild(container);
    }

    container.appendChild(notification);

    // Rimuovi automaticamente dopo 5 secondi
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 5000);
  }

  getNotificationIcon(type) {
    const icons = {
      success: "fa-check-circle",
      error: "fa-exclamation-circle",
      warning: "fa-exclamation-triangle",
      info: "fa-info-circle",
    };
    return icons[type] || icons.info;
  }
}

// ===========================================
// 🚀 INITIALIZATION
// ===========================================

// Inizializza l'app quando il DOM è pronto
document.addEventListener("DOMContentLoaded", () => {
  console.log("🎭 RFID Gate Demo UI - Initializing...");

  // Crea istanza globale
  window.rfidGateUI = new RFIDGateUI();

  // Funzioni globali per i template
  window.logout = () => window.rfidGateUI.logout();
  window.openGate = () => window.rfidGateUI.openGate();
  window.emergencyStop = () => window.rfidGateUI.emergencyStop();
  window.saveConfig = () => window.rfidGateUI.saveConfiguration();

  // Carica contenuto basato sulla pagina corrente
  const currentPage = window.location.pathname;

  if (currentPage === "/" || currentPage === "/dashboard") {
    window.rfidGateUI.loadDashboard();
  } else if (currentPage === "/config") {
    window.rfidGateUI.loadConfiguration();
  } else if (currentPage === "/logs") {
    window.rfidGateUI.loadLogs();
  }

  console.log("✅ RFID Gate Demo UI - Ready!");
});
