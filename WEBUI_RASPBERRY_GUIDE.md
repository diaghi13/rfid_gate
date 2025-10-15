# 🍓 RFID Gate WebUI - Guida Completa per Raspberry Pi

## 🌟 Interfaccia Web Completa Ripristinata!

Hai di nuovo accesso alla **bellissima interfaccia web originale** con:

- 📊 **Dashboard real-time** con animazioni e statistiche
- 🎮 **Controllo manuale** per apertura tornello remota
- 📋 **Gestione log avanzata** con filtri e export
- ⚙️ **Configurazione sistema** completa via web
- 🔐 **Sistema di autenticazione** sicuro
- 📱 **Design responsive** ottimizzato per mobile/tablet

## 🔧 Problemi Risolti (Fix 404 e Routing)

### ✅ **Correzioni Applicate**

- **🔗 Percorsi template**: Fix dei percorsi relativi per funzionare dalla directory principale
- **🎯 Routing homepage**: Corretta l'homepage per usare `index.html` invece di `dashboard.html`
- **📄 Route dashboard**: Aggiunta route separata `/dashboard` per il dashboard
- **🌐 Favicon**: Aggiunto favicon per evitare errori 404
- **📋 Redirect login**: Corretti i redirect che puntavano a percorsi inesistenti
- **📁 Static files**: Fix percorsi assoluti per CSS/JS/immagini

### � **Errori 404 Eliminati**

- ❌ `/templates/dashboard.html` → ✅ `/dashboard`
- ❌ `/favicon.ico` → ✅ Favicon servito correttamente
- ❌ Template non trovati → ✅ Percorsi corretti

### 🎯 **Routing Completo**

- **🏠 `/`** → Homepage con panoramica sistema
- **📊 `/dashboard`** → Dashboard real-time completo
- **🔑 `/login`** → Pagina di autenticazione
- **⚙️ `/config`** → Gestione configurazione base (48 campi)
- **� `/config/advanced`** → **NUOVO!** Configurazione avanzata (95+ campi)
- **�📋 `/logs`** → Visualizzazione log accessi
- **🎮 `/control`** → Controllo manuale tornello

## 🆕 **NOVITÀ: Configurazione Avanzata Completa!**

### 🔧 **Nuova Pagina: `/config/advanced`**

- **✨ Accesso a TUTTE le 95+ configurazioni** del sistema
- **📂 Organizzazione per sezioni**: MQTT, Sistema, Lettori, Sync, Timing, UID, Debug
- **🔍 Ricerca intelligente** tra le configurazioni
- **💾 Backup automatico** prima delle modifiche
- **✅ Validazione in tempo reale** dei valori
- **📊 Tracking delle modifiche** con indicatori visivi

### 🎯 **Sezioni Configurazione Avanzata:**

#### 🔗 **MQTT (Completo)**

- Broker, porta, credenziali, TLS
- Topics personalizzati (card_read, auth_response, manual_open)
- Keep-alive e connection settings

#### 🏗️ **Sistema (Esteso)**

- TORNELLO_ID, modalità bidirezionale
- **⭐ BIDIRECTIONAL_TIMEOUT_HOURS** (nuovo!)
- Lettori IN/OUT, GPIO settings

#### 📡 **Lettori RFID (Avanzato)**

- Configurazione PN532/MFRC522 completa
- Interfacce I2C/SPI/UART con parametri dettagliati
- Timeout, retry, error handling

#### 🔄 **Sincronizzazione (Offline-First)**

- **⭐ SYNC_SERVER_URL, SYNC_INTERVAL_MINUTES**
- SYNC_DAILY_TIME, retry logic
- Offline mode e fallback

#### ⏱️ **Timing & Performance**

- Relay timing, read intervals
- PN532 performance tuning
- Connection timeouts

#### 🆔 **UID Formatting**

- **⭐ UID_FORMAT_MODE** (hex/dec/bytes)
- UID_PREFIX, UID_SUFFIX personalizzati
- Customer ID processing

#### 🐛 **Debug & Logging**

- DEBUG_MODE, LOG_LEVEL avanzato
- Log retention, file management
- Performance monitoring

---

### 1️⃣ **Avvio Rapido (Script Automatico)**

```bash
cd /path/to/rfid_gate
./start_raspberry.sh
```

### 2️⃣ **Avvio Manuale**

```bash
cd /path/to/rfid_gate
source .venv/bin/activate
python3 start_webui_remote.py
```

---

## 🌐 Accesso da Computer Remoto

Quando il Raspberry Pi avvia la WebUI, vedrai informazioni simili a:

```
🖥️  Accesso da Computer Remoto:
   🌍 Dashboard: http://192.168.1.100:8080
   🔧 Config: http://192.168.1.100:8080/config
   📊 Logs: http://192.168.1.100:8080/logs
   🎮 Control: http://192.168.1.100:8080/control
```

### 🔗 **URL Principali**

- **🏠 Home Page**: `http://[IP_RASPBERRY]:8080`
- **📊 Dashboard**: `http://[IP_RASPBERRY]:8080/dashboard`
- **⚙️ Configurazione**: `http://[IP_RASPBERRY]:8080/config`
- **📋 Log Accessi**: `http://[IP_RASPBERRY]:8080/logs`
- **🎮 Controllo Manuale**: `http://[IP_RASPBERRY]:8080/control`
- **🔑 Login**: `http://[IP_RASPBERRY]:8080/login`

---

## 🔑 Credenziali di Accesso

### 🚪 **Login Predefinito**

- **👤 Username**: `admin`
- **🔐 Password**: `rfidgate2024`

> ⚠️ **IMPORTANTE**: Cambia la password dopo il primo accesso per sicurezza!

---

## 🎯 Funzionalità WebUI

### 📊 **Dashboard Real-time**

- Stato hardware (lettori RFID, relè, GPIO)
- Statistiche accessi in tempo reale
- Connessione MQTT e rete
- Grafici interattivi

### 🎮 **Controllo Manuale**

- **Apertura tornello remota** con durata personalizzabile
- **Controlli di emergenza**
- **Cronologia comandi** eseguiti
- **Test hardware** (lettori, relè)

### 📋 **Gestione Log**

- **Visualizzazione accessi** in tempo reale
- **Filtri avanzati** (data, UID, stato, direzione)
- **Export CSV/JSON** per analisi
- **Ricerca per customer_id**
- **Log sistema** e errori

### ⚙️ **Configurazione Sistema**

Accesso completo a tutte le **95+ configurazioni**:

#### 🔗 **MQTT**

- Broker, porta, credenziali
- Topics personalizzati
- Configurazione TLS

#### 🏗️ **Sistema**

- ID tornello
- Modalità bidirezionale
- Timeout configurabile (24h default)

#### 📡 **Lettori RFID**

- Configurazione PN532/MFRC522
- Interfacce (I2C/SPI/UART)
- Parametri timing e retry

#### 🔄 **Sincronizzazione**

- URL server, intervalli
- Modalità offline-first
- Backup e retry

#### ⏱️ **Timing**

- Delay apertura/chiusura
- Intervalli lettura
- Timeout vari

#### 🆔 **Formato UID**

- Modalità esadecimale/decimale
- Prefissi e suffissi personalizzati

#### 🐛 **Debug**

- Livelli di logging
- Conservazione file
- Modalità debug

---

## 🔒 Configurazione di Sicurezza

### 🛡️ **Firewall (se necessario)**

```bash
# Apri porta WebUI
sudo ufw allow 8080/tcp
sudo ufw reload
```

### 🔐 **Accesso Esterno (Router)**

Se vuoi accedere da internet (sconsigliato senza HTTPS):

1. Configura **port forwarding** sul router: `8080 → IP_RASPBERRY:8080`
2. Usa **DynDNS** per IP dinamico
3. Considera **VPN** per sicurezza maggiore

---

## 🔄 Avvio Automatico (Systemd)

### 1️⃣ **Crea Service File**

```bash
sudo nano /etc/systemd/system/rfid-webui.service
```

### 2️⃣ **Configurazione Service**

```ini
[Unit]
Description=RFID Gate WebUI
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rfid_gate
Environment=PATH=/home/pi/rfid_gate/.venv/bin
ExecStart=/home/pi/rfid_gate/.venv/bin/python start_webui_remote.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3️⃣ **Attiva Service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable rfid-webui
sudo systemctl start rfid-webui
```

### 4️⃣ **Controllo Status**

```bash
sudo systemctl status rfid-webui
sudo journalctl -u rfid-webui -f  # Log in tempo reale
```

---

## 📱 Accesso Mobile

La WebUI è **completamente responsive**:

- **📱 Smartphone**: Interfaccia ottimizzata touch
- **📱 Tablet**: Layout adattivo
- **💻 Desktop**: Esperienza completa

### 🌙 **Dark/Light Mode**

- Supporto per tema scuro/chiaro
- Rilevamento automatico preferenze sistema
- Switch manuale nell'interfaccia

---

## 🛠️ Troubleshooting

### ❌ **Server non si avvia**

```bash
# Controlla dipendenze
source .venv/bin/activate
pip install fastapi uvicorn jinja2 python-jose passlib bcrypt

# Controlla porta occupata
sudo netstat -tlnp | grep 8080

# Cambia porta se necessario
export WEBUI_PORT=8081
python start_webui_remote.py
```

### 🌐 **Impossibile accedere da remoto**

```bash
# Verifica IP del Raspberry
ip addr show

# Testa connessione locale
curl http://localhost:8080

# Verifica firewall
sudo ufw status
```

### 🔑 **Problemi di login**

- Usa le credenziali default: `admin / rfidgate2024`
- Cancella cache browser
- Controlla maiuscole/minuscole

### 📊 **Dashboard non si aggiorna**

- Verifica connessione WebSocket
- Ricarica pagina (F5)
- Controlla console browser per errori

---

## 🎉 Caratteristiche Avanzate

### 📊 **API REST Completa**

- **Documentazione Swagger**: `http://[IP]:8080/docs`
- **Endpoint JSON**: `/api/config`, `/api/logs`, `/api/status`
- **WebSocket real-time**: `/ws` per aggiornamenti live

### 💾 **Backup Configurazione**

- **Backup automatico** prima delle modifiche
- **Cronologia versioni** con timestamp
- **Ripristino** configurazioni precedenti

### 🔄 **Sincronizzazione Real-time**

- **WebSocket** per aggiornamenti istantanei
- **Notifiche** per accessi e errori
- **Stato hardware** in tempo reale

---

## 📞 Supporto

La WebUI ora include tutte le funzionalità necessarie per:

- ✅ **Gestione completa sistema RFID**
- ✅ **Configurazione remota** da qualsiasi dispositivo
- ✅ **Monitoraggio real-time** accessi e hardware
- ✅ **Controllo sicuro** con autenticazione
- ✅ **Interfaccia moderna** e responsive

**🎯 Tutto accessibile dal tuo computer mentre il Raspberry lavora headless!** 🚀
