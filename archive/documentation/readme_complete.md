# 🎯 RFID Gate Access Control System

Sistema professionale di controllo accessi con lettori RFID, controllo relè e comunicazione MQTT per tornelli, cancelli e controlli accessi.

## ✨ Caratteristiche Principali

- 🔄 **Sistema Bidirezionale** - Lettori RFID ingresso/uscita indipendenti  
- ⚡ **Controllo Relè** - Gestione professionale relè con timing configurabile
- 📡 **Comunicazione MQTT** - Autenticazione real-time con server remoto
- 🌐 **Modalità Offline** - Funzionamento garantito anche senza connessione
- 🔓 **Apertura Manuale** - Controllo remoto e locale per situazioni speciali
- 📊 **Logging Completo** - Tracciamento dettagliato di tutti gli accessi
- 🔧 **Installazione Automatica** - Setup completo con un comando
- ⚙️ **Servizio Systemd** - Avvio automatico e gestione professionale

## 🏗️ Architettura Sistema

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   RFID Reader   │───▶│  Raspberry   │───▶│    Relè     │
│   (Ingresso)    │    │      Pi      │    │ (Cancello)  │
└─────────────────┘    │              │    └─────────────┘
┌─────────────────┐    │   Sistema    │    ┌─────────────┐
│   RFID Reader   │───▶│   Controllo  │───▶│    Relè     │
│   (Uscita)      │    │   Accessi    │    │ (Uscita)    │
└─────────────────┘    └──────┬───────┘    └─────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Server MQTT    │
                    │ (Autenticazione)│
                    └─────────────────┘
```

## 📦 Installazione Rapida

### 1. Download e Setup Iniziale

```bash
# Clone del repository
git clone <repository-url> rfid-gate-system
cd rfid-gate-system

# Installazione completa automatica
sudo bash scripts/install.sh
```

### 2. Configurazione

```bash
# Modifica configurazione
sudo nano /opt/rfid-gate/.env

# Test configurazione
sudo python3 /opt/rfid-gate/tools/manual_open_tool.py --test
```

### 3. Avvio Servizio

```bash
# Abilita e avvia servizio
sudo systemctl enable rfid-gate
sudo systemctl start rfid-gate

# Verifica stato
sudo systemctl status rfid-gate
```

## ⚙️ Configurazione Hardware

### 🔌 Collegamento RFID RC522

**Lettore Ingresso (Obbligatorio):**
```
RFID RC522    →    Raspberry Pi
VCC           →    3.3V (Pin 1)
RST           →    GPIO 22 (Pin 15) 
GND           →    GND (Pin 6)
MISO          →    GPIO 9 (Pin 21)
MOSI          →    GPIO 10 (Pin 19)
SCK           →    GPIO 11 (Pin 23)
SDA           →    GPIO 8 (Pin 24)
```

**Lettore Uscita (Opzionale):**
```
RFID RC522    →    Raspberry Pi
VCC           →    3.3V (Pin 17)
RST           →    GPIO 25 (Pin 22)
GND           →    GND (Pin 20)
MISO          →    GPIO 9 (Pin 21)  [Condiviso]
MOSI          →    GPIO 10 (Pin 19) [Condiviso]
SCK           →    GPIO 11 (Pin 23) [Condiviso]
SDA           →    GPIO 7 (Pin 26)
```

### ⚡ Collegamento Relè

**Relè Standard (Active HIGH):**
```
Relè Module   →    Raspberry Pi
VCC           →    5V (Pin 2)
GND           →    GND (Pin 14)
IN1           →    GPIO 18 (Pin 12)
IN2           →    GPIO 19 (Pin 35) [Opzionale]
```

**Relè con Optoaccoppiatore (Active LOW):**
- Stessa connessione fisica
- Configurazione: `RELAY_IN_ACTIVE_LOW=True`

## 🎛️ Configurazioni Comuni

### 📝 Configurazione 1: Solo Ingresso

```bash
# File .env
BIDIRECTIONAL_MODE=False
ENABLE_IN_READER=True
ENABLE_OUT_READER=False
RELAY_IN_ENABLE=True
RELAY_OUT_ENABLE=False
```

### 🔄 Configurazione 2: Sistema Bidirezionale

```bash
# File .env  
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=True
RELAY_IN_ENABLE=True
RELAY_OUT_ENABLE=True
```

### 🎛️ Configurazione 3: Due Lettori, Un Relè

```bash
# File .env
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=True
RELAY_IN_ENABLE=True
RELAY_OUT_ENABLE=False
```

## 🚀 Gestione Sistema

### 📊 Comandi Servizio

```bash
# Stato servizio
sudo systemctl status rfid-gate

# Avvio/Stop
sudo systemctl start rfid-gate
sudo systemctl stop rfid-gate
sudo systemctl restart rfid-gate

# Avvio automatico
sudo systemctl enable rfid-gate
sudo systemctl disable rfid-gate

# Log in tempo reale
sudo journalctl -fu rfid-gate
```

### 🔧 Script di Gestione

```bash
# Setup servizio
sudo bash scripts/setup_service.sh install

# Avvio manuale (debug)
sudo bash scripts/start.sh

# Stop sistema
sudo bash scripts/stop.sh

# Monitoring
sudo bash scripts/monitor.sh --continuous

# Backup configurazione
sudo bash scripts/backup.sh

# Aggiornamento sistema
sudo bash scripts/update.sh
```

### 🛠️ Tool di Utilità

```bash
# Status sistema offline
sudo python3 tools/offline_utils.py --status

# Apertura manuale locale
sudo python3 tools/manual_open_tool.py --local --duration 3

# Visualizza log accessi
sudo python3 tools/log_viewer.py --stats 7

# Stop emergenza tutti i relè
sudo python3 tools/emergency_stop.py all
```

## 📡 API MQTT

### 📤 Invio Dati Card

**Topic:** `gate/{TORNELLO_ID}/badge`

```json
{
  "card_uid": "A1B2C3D4",
  "identificativo_tornello": "tornello_01",
  "direzione": "in",
  "timestamp": "2024-12-20T10:30:00.000Z",
  "raw_id": "123456789",
  "card_data": "User Data",
  "hex_id": "0x75BCD15",
  "auth_required": true,
  "reader_id": "in"
}
```

### 📥 Risposta Autenticazione

**Topic:** `gate/{TORNELLO_ID}/auth_response`

```json
{
  "card_uid": "A1B2C3D4",
  "authorized": true,
  "message": "Accesso autorizzato",
  "timestamp": "2024-12-20T10:30:01.000Z"
}
```

### 🔓 Apertura Manuale

**Comando (App → Tornello):**  
**Topic:** `gate/{TORNELLO_ID}/manual_open`

```json
{
  "command_id": "cmd_1703123456",
  "direction": "in",
  "duration": 3,
  "user_id": "admin",
  "auth_token": "secure_token_123",
  "timestamp": "2024-12-20T10:30:00.000Z",
  "source": "mobile_app"
}
```

**Risposta (Tornello → App):**  
**Topic:** `gate/{TORNELLO_ID}/manual_response`

```json
{
  "command_id": "cmd_1703123456", 
  "success": true,
  "message": "Apertura eseguita con successo",
  "user_id": "admin",
  "timestamp": "2024-12-20T10:30:05.000Z",
  "tornello_id": "tornello_01"
}
```

## 📊 Sistema Offline

### 🌐 Funzionamento

Il sistema garantisce continuità operativa anche senza connessione internet:

1. **Rilevamento Automatico** - Rileva perdita connessione
2. **Autorizzazione Locale** - Consente accessi basati su configurazione
3. **Coda Persistente** - Salva dati per sincronizzazione futura  
4. **Sincronizzazione Automatica** - Invia dati quando connessione torna
5. **Recovery Completo** - Nessuna perdita di dati

### 📋 Gestione Coda Offline

```bash
# Visualizza stato
sudo python3 tools/offline_utils.py --status

# Mostra coda
sudo python3 tools/offline_utils.py --queue

# Forza sincronizzazione
sudo python3 tools/offline_utils.py --sync

# Export backup
sudo python3 tools/offline_utils.py --export backup.json

# Statistiche dettagliate
sudo python3 tools/offline_utils.py --stats
```

## 📈 Monitoring e Log

### 📊 Visualizzazione Log

```bash
# Statistiche accessi (ultimi 7 giorni)
sudo python3 tools/log_viewer.py --stats 7

# Accessi di oggi
sudo python3 tools/log_viewer.py --today

# Ultimi 20 accessi
sudo python3 tools/log_viewer.py --tail 20

# Filtra per card specifica
sudo python3 tools/log_viewer.py --card A1B2C3D4 --tail 10
```

### 🔍 File Log

- **`logs/system.log`** - Log eventi sistema
- **`logs/access_log.csv`** - Log accessi formato CSV
- **`logs/access_log.json`** - Log accessi formato JSON
- **Journal:** `sudo journalctl -u rfid-gate`

### 📈 Metriche Sistema

```bash
# Monitor in tempo reale
sudo bash scripts/monitor.sh --continuous

# Status servizio dettagliato
sudo bash scripts/setup_service.sh status

# Test completo sistema
sudo python3 tools/manual_open_tool.py --test
```

## 🔧 Risoluzione Problemi

### ❌ Problemi Comuni

**Servizio non si avvia:**
```bash
# Controlla log
sudo journalctl -u rfid-gate -n 50

# Test configurazione
sudo bash scripts/setup_service.sh test

# Verifica permessi
sudo chown -R rfid:rfid /opt/rfid-gate
```

**RFID non legge:**
```bash
# Verifica SPI abilitato
lsmod | grep spi

# Test hardware diretto
sudo python3 -c "from mfrc522 import SimpleMFRC522; print('RFID OK')"

# Controlla collegamento
sudo gpio readall
```

**Relè non scatta:**
```bash
# Test GPIO diretto
sudo python3 tools/emergency_stop.py 18  # Testa GPIO 18

# Verifica configurazione
grep RELAY_ /opt/rfid-gate/.env

# Test manuale
sudo python3 tools/manual_open_tool.py --local
```

**Connessione MQTT fallisce:**
```bash
# Test connessione broker
mosquitto_pub -h mqbrk.ddns.net -p 8883 -t test -m "test"

# Verifica certificati TLS
openssl s_client -connect mqbrk.ddns.net:8883

# Test offline
sudo python3 tools/offline_utils.py --test-connection
```

### 🛠️ Debug Avanzato

```bash
# Avvio in modalità debug
sudo -u rfid /opt/rfid-gate/venv/bin/python /opt/rfid-gate/src/main.py

# Log dettagliato
sudo sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' /opt/rfid-gate/.env

# Test moduli individuali
cd /opt/rfid-gate
sudo -u rfid ./venv/bin/python -c "
import sys; sys.path.append('src')
from rfid_manager import RFIDManager
from relay_manager import RelayManager  
from mqtt_client import MQTTClient
print('Tutti i moduli OK')
"
```

## 📁 Struttura Progetto

```
rfid-gate-system/
├── src/                    # Codice sorgente
│   ├── main.py            # Sistema principale
│   ├── config.py          # Configurazioni
│   ├── rfid_manager.py    # Gestione RFID
│   ├── relay_manager.py   # Gestione relè
│   ├── mqtt_client.py     # Client MQTT
│   ├── offline_manager.py # Sistema offline
│   └── manual_control.py  # Controllo manuale
├── tools/                  # Utility
│   ├── offline_utils.py   # Gestione offline
│   ├── manual_open_tool.py# Tool apertura manuale
│   ├── log_viewer.py      # Visualizzatore log
│   └── emergency_stop.py  # Stop emergenza
├── scripts/                # Scripts gestione
│   ├── install.sh         # Installazione
│   ├── setup_service.sh   # Gestione servizio
│   ├── start.sh           # Avvio manuale
│   └── monitor.sh         # Monitoring
├── config/                 # Configurazioni
│   └── .env.example       # Template config
├── logs/                   # Directory log
└── .env                    # Configurazione principale
```

## 🔐 Sicurezza

### 🛡️ Best Practices

- **Token Sicuri** - Minimo 8 caratteri per apertura manuale
- **TLS/SSL** - Connessioni MQTT sempre cifrate
- **Audit Logging** - Tracciamento completo di tutti gli accessi
- **Permessi Sistema** - Utente dedicato con privilegi minimi
- **Backup Automatici** - Salvataggio configurazioni e log

### 🚨 Funzioni di Emergenza

```bash
# Stop immediato tutti i relè
sudo python3 tools/emergency_stop.py all

# Stop servizio e relè
sudo bash scripts/stop.sh

# Ripristino configurazione
sudo bash scripts/backup.sh  # Prima crea backup
# Ripristina da backup precedente
```

## 📞 Supporto

### 📋 Prima di Richiedere Supporto

1. **Raccogli informazioni sistema:**
   ```bash
   sudo bash scripts/setup_service.sh status > debug_info.txt
   sudo python3 tools/manual_open_tool.py --test >> debug_info.txt
   sudo journalctl -u rfid-gate -n 100 >> debug_info.txt
   ```

2. **Testa componenti base:**
   ```bash
   # Test RFID
   sudo python3 -c "from mfrc522 import SimpleMFRC522; print('RFID OK')"
   
   # Test GPIO  
   sudo python3 tools/emergency_stop.py check
   ```

3. **Verifica configurazione hardware**

### 🏷️ Informazioni Sistema

- **Versione Sistema:** 1.0.0
- **Piattaforma:** Raspberry Pi (Debian/Ubuntu)
- **Python:** 3.7+
- **Hardware:** RFID RC522, Relè 5V/3.3V
- **Protocolli:** MQTT, TLS, SPI

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi file `LICENSE` per dettagli.

---

🚀 **Sistema RFID Gate Access Control** - Controllo accessi professionale per Raspberry Pi