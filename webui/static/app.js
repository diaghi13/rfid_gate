// ========================================================================
// 🚀 RFID Gate Web UI - Modern JavaScript Framework
// ========================================================================

// ===========================================
// 🌐 GLOBAL STATE & CONFIGURATION
// ===========================================

class RFIDGateUI {
  constructor() {
    this.wsConnection = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.token = localStorage.getItem("access_token");
    this.user = JSON.parse(localStorage.getItem("user") || "{}");

    this.initializeWebSocket();
    this.checkAuthentication();
  }

  // ===========================================
  // 🔐 AUTHENTICATION
  // ===========================================

  checkAuthentication() {
    // Skip auth check for login page
    if (window.location.pathname === "/login") {
      return;
    }

    if (!this.token) {
      this.redirectToLogin();
      return;
    }

    // Update username in header
    const usernameElement = document.getElementById("username");
    if (usernameElement && this.user.username) {
      usernameElement.textContent = this.user.username;
    }
  }

  redirectToLogin() {
    window.location.href = "/login";
  }

  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    this.redirectToLogin();
  }

  // ===========================================
  // 📡 WEBSOCKET CONNECTION
  // ===========================================

  initializeWebSocket() {
    if (!this.token) return;

    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onopen = () => {
        console.log("🔗 WebSocket connected");
        this.reconnectAttempts = 0;
        showToast("Connesso al server", "success");
      };

      this.wsConnection.onmessage = (event) => {
        this.handleWebSocketMessage(event.data);
      };

      this.wsConnection.onclose = () => {
        console.log("🔌 WebSocket disconnected");
        this.handleWebSocketReconnect();
      };

      this.wsConnection.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        showToast("Errore di connessione WebSocket", "error");
      };
    } catch (error) {
      console.error("❌ Failed to initialize WebSocket:", error);
    }
  }

  handleWebSocketMessage(data) {
    try {
      // Handle both JSON and plain text messages
      let message;
      try {
        message = JSON.parse(data);
      } catch {
        message = { type: "text", data: data };
      }

      console.log("📨 WebSocket message:", message);

      // Handle different message types
      if (typeof message === "string") {
        if (message.startsWith("manual_open:")) {
          const [, direction, duration] = message.split(":");
          this.handleManualOpenNotification(direction, duration);
        } else if (message === "config_updated") {
          this.handleConfigUpdateNotification();
        }
      } else if (message.type) {
        switch (message.type) {
          case "status_update":
            this.handleStatusUpdate(message.data);
            break;
          case "new_access":
            this.handleNewAccess(message.data);
            break;
          case "system_alert":
            this.handleSystemAlert(message.data);
            break;
        }
      }
    } catch (error) {
      console.error("❌ Error handling WebSocket message:", error);
    }
  }

  handleWebSocketReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `🔄 Attempting WebSocket reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
      );

      setTimeout(() => {
        this.initializeWebSocket();
      }, this.reconnectDelay);
    } else {
      showToast("Connessione persa. Ricarica la pagina", "error");
    }
  }

  handleManualOpenNotification(direction, duration) {
    showToast(`Tornello aperto ${direction} per ${duration}s`, "info");
    // Refresh status if on dashboard
    if (typeof refreshStatus === "function") {
      setTimeout(refreshStatus, 1000);
    }
  }

  handleConfigUpdateNotification() {
    showToast("Configurazione aggiornata", "info");
    // Reload config if on config page
    if (typeof loadConfig === "function") {
      setTimeout(loadConfig, 1000);
    }
  }

  handleStatusUpdate(data) {
    // Update status indicators in real-time
    console.log("📊 Status update:", data);
  }

  handleNewAccess(data) {
    // Show notification for new access
    const status = data.authorized ? "autorizzato" : "negato";
    const icon = data.authorized ? "✅" : "❌";
    showToast(
      `${icon} Accesso ${status}: ${data.card_uid}`,
      data.authorized ? "success" : "warning"
    );

    // Refresh logs if on logs page
    if (typeof refreshLogs === "function") {
      setTimeout(refreshLogs, 1000);
    }
  }

  handleSystemAlert(data) {
    showToast(data.message, data.level || "warning");
  }
}

// ===========================================
// 🌐 HTTP UTILITIES
// ===========================================

async function authorizedFetch(url, options = {}) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    window.location.href = "/login";
    throw new Error("No authentication token");
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expired or invalid
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
    throw new Error("Authentication expired");
  }

  return response;
}

// ===========================================
// 🍞 TOAST NOTIFICATIONS
// ===========================================

function showToast(message, type = "info", duration = 5000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icons = {
    success: "fas fa-check-circle",
    error: "fas fa-times-circle",
    warning: "fas fa-exclamation-triangle",
    info: "fas fa-info-circle",
  };

  toast.innerHTML = `
        <i class="${icons[type]} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="removeToast(this)">&times;</button>
    `;

  container.appendChild(toast);

  // Auto remove after duration
  setTimeout(() => {
    removeToast(toast.querySelector(".toast-close"));
  }, duration);
}

function removeToast(closeButton) {
  const toast = closeButton.closest(".toast");
  if (toast) {
    toast.style.animation = "slideOut 0.3s ease-in";
    setTimeout(() => {
      toast.remove();
    }, 300);
  }
}

// Add slideOut animation
const style = document.createElement("style");
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===========================================
// ⏳ LOADING UTILITIES
// ===========================================

function showLoading() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) {
    overlay.style.display = "flex";
  }
}

function hideLoading() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) {
    overlay.style.display = "none";
  }
}

// ===========================================
// 📊 DASHBOARD FUNCTIONS
// ===========================================

async function initDashboard() {
  console.log("📊 Initializing dashboard...");

  try {
    await refreshStatus();
    await refreshLogs();

    // Set up periodic refresh
    setInterval(refreshStatus, 30000); // Every 30 seconds
    setInterval(refreshLogs, 60000); // Every minute
  } catch (error) {
    console.error("❌ Dashboard initialization error:", error);
    showToast("Errore nell'inizializzazione della dashboard", "error");
  }
}

async function refreshStatus() {
  try {
    const response = await authorizedFetch("/api/system/status");
    const data = await response.json();

    updateSystemStatus(data);
    showToast("Stato aggiornato", "info");
  } catch (error) {
    console.error("❌ Error refreshing status:", error);
    showToast("Errore nell'aggiornamento dello stato", "error");
  }
}

function updateSystemStatus(data) {
  // Update system info
  if (data.system) {
    updateElement(
      "system-running",
      data.system.running ? "In esecuzione" : "Fermato"
    );
    updateElement("system-uptime", data.system.uptime || "N/A");
    updateElement("system-memory", data.system.memory_usage || "N/A");
    updateStatusIndicator(
      "system-status",
      data.system.running ? "online" : "offline"
    );
  }

  // Update hardware info
  if (data.hardware) {
    updateReadersStatus(data.hardware.readers || []);
    updateElement("relay-status", data.hardware.relay?.status || "N/A");

    const hardwareOk =
      data.hardware.readers?.every((r) => r.status === "connected") &&
      data.hardware.relay?.status === "ready";
    updateStatusIndicator("hardware-status", hardwareOk ? "online" : "warning");
  }

  // Update network info
  if (data.network) {
    updateElement(
      "mqtt-status",
      data.network.mqtt?.connected ? "Connesso" : "Disconnesso"
    );
    updateElement(
      "internet-status",
      data.network.internet?.connected ? "Connesso" : "Disconnesso"
    );
    updateElement(
      "offline-queue",
      `${data.network.offline_queue?.items || 0} elementi`
    );

    const networkOk =
      data.network.mqtt?.connected && data.network.internet?.connected;
    updateStatusIndicator("network-status", networkOk ? "online" : "warning");
  }

  // Update statistics
  if (data.stats) {
    updateElement("today-accesses", data.stats.today_accesses || 0);
    updateElement("today-authorized", data.stats.authorized || 0);
    updateElement("today-denied", data.stats.denied || 0);
    updateElement("today-manual", data.stats.manual_opens || 0);
  }
}

function updateReadersStatus(readers) {
  const container = document.getElementById("readers-list");
  if (!container) return;

  container.innerHTML = readers
    .map(
      (reader) => `
        <div class="stat">
            <span class="stat-label">${reader.id}:</span>
            <span class="stat-value ${
              reader.status === "connected" ? "text-success" : "text-danger"
            }">
                ${reader.status === "connected" ? "Connesso" : "Disconnesso"}
            </span>
        </div>
    `
    )
    .join("");
}

function updateElement(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function updateStatusIndicator(id, status) {
  const indicator = document.getElementById(id);
  if (indicator) {
    indicator.className = `status-indicator ${status}`;
  }
}

async function refreshLogs() {
  try {
    const response = await authorizedFetch("/api/system/logs/recent?limit=10");
    const data = await response.json();

    updateRecentLogs(data.logs || []);
  } catch (error) {
    console.error("❌ Error refreshing logs:", error);
  }
}

function updateRecentLogs(logs) {
  const container = document.getElementById("recent-logs");
  if (!container) return;

  if (logs.length === 0) {
    container.innerHTML =
      '<p class="text-secondary">Nessun accesso recente</p>';
    return;
  }

  container.innerHTML = logs
    .slice(0, 5)
    .map(
      (log) => `
        <div class="log-item ${log.authorized ? "authorized" : "denied"}">
            <div class="log-time">${formatTime(log.timestamp)}</div>
            <div class="log-info">
                <span class="card-uid">${log.card_uid}</span>
                <span class="direction ${log.direction}">
                    <i class="fas fa-arrow-${
                      log.direction === "in" ? "right" : "left"
                    }"></i>
                    ${log.direction === "in" ? "In" : "Out"}
                </span>
                <span class="status ${
                  log.authorized ? "authorized" : "denied"
                }">
                    <i class="fas fa-${log.authorized ? "check" : "times"}"></i>
                    ${log.authorized ? "OK" : "Negato"}
                </span>
            </div>
        </div>
    `
    )
    .join("");
}

// ===========================================
// 🎮 CONTROL FUNCTIONS
// ===========================================

async function quickOpen(direction) {
  const duration = 3; // Default duration

  try {
    const response = await authorizedFetch("/api/control/open", {
      method: "POST",
      body: JSON.stringify({ direction, duration }),
    });

    const data = await response.json();

    if (response.ok) {
      showToast(data.message, "success");
      // Refresh status after a short delay
      setTimeout(refreshStatus, 1000);
    } else {
      showToast(data.detail || "Errore durante l'apertura", "error");
    }
  } catch (error) {
    console.error("❌ Error in quick open:", error);
    showToast("Errore di connessione", "error");
  }
}

function viewLogs() {
  window.location.href = "/logs";
}

// ===========================================
// 🔧 UTILITY FUNCTIONS
// ===========================================

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleDateString("it-IT");
}

function formatDateTime(timestamp) {
  return new Date(timestamp).toLocaleString("it-IT");
}

// ===========================================
// 🌐 NAVIGATION FUNCTIONS
// ===========================================

function logout() {
  if (window.rfidGateUI) {
    window.rfidGateUI.logout();
  } else {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }
}

// ===========================================
// 🚀 APPLICATION INITIALIZATION
// ===========================================

document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 RFID Gate Web UI Starting...");

  // Initialize global UI instance
  window.rfidGateUI = new RFIDGateUI();

  // Set up global error handler
  window.addEventListener("error", function (event) {
    console.error("🚨 Global error:", event.error);
    showToast("Si è verificato un errore imprevisto", "error");
  });

  // Set up offline/online handlers
  window.addEventListener("offline", function () {
    showToast("Connessione persa", "warning");
  });

  window.addEventListener("online", function () {
    showToast("Connessione ripristinata", "success");
    // Reconnect WebSocket
    if (window.rfidGateUI) {
      window.rfidGateUI.initializeWebSocket();
    }
  });

  console.log("✅ RFID Gate Web UI Initialized");
});

// ===========================================
// 📱 RESPONSIVE UTILITIES
// ===========================================

// Handle mobile navigation
function toggleMobileNav() {
  const nav = document.querySelector(".nav");
  if (nav) {
    nav.classList.toggle("mobile-open");
  }
}

// Add mobile navigation styles
if (window.innerWidth <= 1024) {
  const style = document.createElement("style");
  style.textContent = `
        .nav {
            position: fixed;
            top: 80px;
            left: -250px;
            width: 250px;
            height: calc(100vh - 80px);
            background: var(--bg-primary);
            border-right: 1px solid var(--border-color);
            transition: left 0.3s ease;
            z-index: 999;
        }
        
        .nav.mobile-open {
            left: 0;
        }
        
        .mobile-nav-toggle {
            display: block;
            background: none;
            border: none;
            font-size: 1.5rem;
            color: var(--primary-color);
            cursor: pointer;
        }
        
        @media (min-width: 1025px) {
            .nav {
                position: static;
                left: auto;
            }
            
            .mobile-nav-toggle {
                display: none;
            }
        }
    `;
  document.head.appendChild(style);

  // Add mobile nav toggle button to header
  const header = document.querySelector(".header-content");
  if (header) {
    const toggleBtn = document.createElement("button");
    toggleBtn.className = "mobile-nav-toggle";
    toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
    toggleBtn.onclick = toggleMobileNav;
    header.insertBefore(toggleBtn, header.firstChild);
  }
}

// ===========================================
// 🔍 SEARCH & FILTER UTILITIES
// ===========================================

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ===========================================
// 📊 CHART UTILITIES (for future use)
// ===========================================

function createSimpleChart(canvasId, data, type = "line") {
  // Placeholder for chart creation
  // Could integrate with Chart.js or similar library
  console.log(`📊 Creating ${type} chart for ${canvasId}:`, data);
}

// ===========================================
// 🔔 NOTIFICATION PERMISSIONS
// ===========================================

function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission().then((permission) => {
      if (permission === "granted") {
        showToast("Notifiche abilitate", "success");
      }
    });
  }
}

function showSystemNotification(title, message, type = "info") {
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, {
      body: message,
      icon: "/static/icon.png", // Add an icon if available
      badge: "/static/badge.png",
    });
  }
}

// ===========================================
// 🎯 KEYBOARD SHORTCUTS
// ===========================================

document.addEventListener("keydown", function (event) {
  // Only handle shortcuts when not typing in input fields
  if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA") {
    return;
  }

  // Ctrl/Cmd + R: Refresh status
  if ((event.ctrlKey || event.metaKey) && event.key === "r") {
    event.preventDefault();
    if (typeof refreshStatus === "function") {
      refreshStatus();
    }
  }

  // Ctrl/Cmd + L: Go to logs
  if ((event.ctrlKey || event.metaKey) && event.key === "l") {
    event.preventDefault();
    window.location.href = "/logs";
  }

  // Ctrl/Cmd + D: Go to dashboard
  if ((event.ctrlKey || event.metaKey) && event.key === "d") {
    event.preventDefault();
    window.location.href = "/";
  }

  // Escape: Close modals
  if (event.key === "Escape") {
    const modals = document.querySelectorAll(".modal");
    modals.forEach((modal) => {
      if (modal.style.display === "flex") {
        modal.style.display = "none";
      }
    });
  }
});

// Show keyboard shortcuts info
function showKeyboardShortcuts() {
  showToast(
    "Scorciatoie: Ctrl+R (Aggiorna), Ctrl+L (Log), Ctrl+D (Dashboard)",
    "info",
    8000
  );
}

// ===========================================
// 🔧 DEVELOPMENT UTILITIES
// ===========================================

// Debug mode utilities
if (localStorage.getItem("rfid_debug") === "true") {
  console.log("🐛 Debug mode enabled");

  // Add debug panel
  const debugPanel = document.createElement("div");
  debugPanel.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 9999;
        max-width: 300px;
    `;
  debugPanel.innerHTML = `
        <div><strong>Debug Panel</strong></div>
        <div>Token: ${
          localStorage.getItem("access_token") ? "Present" : "Missing"
        }</div>
        <div>WebSocket: <span id="ws-status">Disconnected</span></div>
        <div>Last Update: <span id="last-update">Never</span></div>
    `;
  document.body.appendChild(debugPanel);

  // Update debug info
  setInterval(() => {
    const wsStatus = document.getElementById("ws-status");
    const lastUpdate = document.getElementById("last-update");

    if (wsStatus && window.rfidGateUI?.wsConnection) {
      wsStatus.textContent =
        window.rfidGateUI.wsConnection.readyState === WebSocket.OPEN
          ? "Connected"
          : "Disconnected";
    }

    if (lastUpdate) {
      lastUpdate.textContent = new Date().toLocaleTimeString();
    }
  }, 1000);
}
