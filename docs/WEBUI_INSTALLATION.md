# 🌐 RFID Gate System - Installazione Web UI

# ==========================================

## 🚀 Guida ### 🔒 Sicurezza e Produzione

#### 🌐 Reverse Proxy (Nginx)

```bash
# Installazione completa con Nginx
sudo bash scripts/install.sh  # Scegli opzione 3

# Configurazione SSL post-installazione
sudo bash scripts/setup_ssl.sh

# Configurazione sicurezza completa
sudo bash scripts/setup_security.sh
```

#### 🛡️ Configurazioni Sicurezza

- **Firewall UFW**: Porte specifiche RFID Gate
- **SSL/TLS**: Certificati Let's Encrypt automatici
- **Fail2Ban**: Protezione brute-force
- **SSH Hardening**: Configurazioni sicure
- **Auto-updates**: Aggiornamenti sistema automatici

#### 🔧 Produzione vs Sviluppo

- **Sviluppo**: Uvicorn diretto (porta 8080)
- **Produzione**: Gunicorn + Nginx (porta 80/443)
- **SSL**: Automatico con Let's Encrypt
- **Performance**: Workers multipli, caching, compressione Completa

### 📋 Prerequisiti

- Raspberry Pi con Raspberry Pi OS
- Accesso root/sudo
- Connessione internet

### 🎯 Opzioni di Installazione

#### 1. **Installazione Automatica Completa** (Raccomandato)

```bash
# Clona repository
git clone https://github.com/diaghi13/rfid_gate.git
cd rfid_gate

# Installazione con scelta interattiva
sudo bash scripts/install.sh
# Opzioni:
# 1. Sistema base (solo RFID Gate)
# 2. Sistema completo (+ Web UI) [default]
# 3. Sistema avanzato (+ Nginx reverse proxy)
```

#### 2. **Installazione Step-by-Step**

```bash
# 1. Installa sistema base
sudo bash scripts/install.sh

# 2. Installa Web UI
sudo bash scripts/setup_webui_service.sh install
```

#### 3. **Solo Web UI** (Sistema già installato)

```bash
sudo bash scripts/setup_webui_service.sh install
```

## 🌐 Configurazione Web UI

### 📡 Accesso

- **URL**: http://localhost:8080
- **Demo URL**: http://localhost:8082 (server demo)

### 🔧 Servizi SystemD

#### Servizio Principal

```bash
# Status
sudo systemctl status rfid-gate

# Avvio/Stop
sudo systemctl start rfid-gate
sudo systemctl stop rfid-gate

# Log
sudo journalctl -fu rfid-gate
```

#### Servizio Web UI

```bash
# Status
sudo systemctl status rfid-gate-webui

# Avvio/Stop
sudo systemctl start rfid-gate-webui
sudo systemctl stop rfid-gate-webui

# Log
sudo journalctl -fu rfid-gate-webui
```

### ⚙️ Configurazione

#### File Principali

- **Sistema**: `/opt/rfid-gate/.env`
- **Backup**: `/opt/rfid-gate/backups/config/`
- **Log**: `/opt/rfid-gate/logs/`

#### Gestione da Web UI

1. Accedi a http://localhost:8080
2. Vai alla sezione "Configurazione"
3. Modifica i parametri
4. Salva (backup automatico)

## 🛠️ Script di Gestione

### 📦 Installazione

```bash
# Installazione interattiva con scelta
sudo bash scripts/install.sh

# Installazione completa guidata
sudo bash scripts/install_full.sh

# Solo Web UI (sistema già installato)
sudo bash scripts/setup_webui_service.sh install
```

### 🔒 Sicurezza e SSL

```bash
# Configurazione SSL con Let's Encrypt
sudo bash scripts/setup_ssl.sh

# Configurazione sicurezza completa
sudo bash scripts/setup_security.sh
```

### 🛠️ Comandi Makefile

```bash
# Server demo WebUI
make webui-demo

# Server FastAPI completo
make webui-server

# Test configurazione WebUI
make webui-test

# Installa dipendenze WebUI
make webui-deps
```

## 🔒 Sicurezza

### 🌐 Accesso Remoto

Per accesso da rete locale, modifica bind address:

```python
# In webui/app_demo.py
uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 🔑 Autenticazione

- JWT tokens per API
- Sessioni sicure
- Backup automatici delle modifiche

## 📊 Funzionalità Web UI

### 🎯 Dashboard

- ✅ Stato sistema real-time
- ✅ Statistiche accessi
- ✅ Monitor lettori RFID
- ✅ Stato connessioni MQTT

### 🎮 Controllo

- ✅ Apertura manuale tornello
- ✅ Test lettori RFID
- ✅ Reset sistema
- ✅ Modalità manutenzione

### 📋 Log Manager

- ✅ Visualizzazione log accessi
- ✅ Filtri avanzati
- ✅ Export CSV/JSON
- ✅ Statistiche dettagliate

### ⚙️ Configurazione

- ✅ Gestione parametri .env
- ✅ Backup automatici
- ✅ Validazione configurazione
- ✅ Ripristino da backup

## 🔧 Troubleshooting

### 🚫 Problemi Comuni

#### WebUI non accessibile

```bash
# Verifica servizio
sudo systemctl status rfid-gate-webui

# Verifica porta
sudo netstat -tlnp | grep :8080

# Riavvia servizio
sudo systemctl restart rfid-gate-webui
```

#### Errori configurazione

```bash
# Test ConfigManager
cd /opt/rfid-gate
./venv/bin/python -c "from webui.config_manager import ConfigManager; ConfigManager().load_env_config()"
```

#### Dipendenze mancanti

```bash
# Reinstalla dipendenze WebUI
sudo bash scripts/setup_webui_service.sh install
```

### 📱 Log Debugging

```bash
# Log WebUI dettagliati
sudo journalctl -fu rfid-gate-webui --since "10 minutes ago"

# Log sistema principale
sudo journalctl -fu rfid-gate --since "10 minutes ago"
```

## 🎉 Installazione Completata

Dopo l'installazione:

1. ✅ Sistema RFID operativo
2. ✅ Web UI accessibile su porta 8080
3. ✅ Backup automatici configurati
4. ✅ Servizi abilitati per avvio automatico

**🌐 Accedi alla Web UI: http://localhost:8080**
