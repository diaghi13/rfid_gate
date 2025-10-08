# 🚪 RFID Gate Control System

Sistema completo per controllo tornelli con tecnologia RFID, progettato per Raspberry Pi con supporto per multiple interfacce hardware e gestione avanzata.

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Pass-green.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Async%20Modular-brightgreen.svg)](#architettura)
[![WebUI](https://img.shields.io/badge/WebUI-FastAPI-orange.svg)](#web-interface)

## ✨ Caratteristiche Principali

🔹 **Multi-Reader Support**: MFRC522 (SPI) e PN532 (I2C/SPI/UART)  
🔹 **Interfaccia Web**: Dashboard moderna con controllo real-time  
🔹 **MQTT Integration**: Comunicazione IoT con broker esterni  
🔹 **Modalità Offline**: Funzionamento autonomo con sincronizzazione  
🔹 **Installazione Automatica**: Script completi per setup Nginx/SSL  
🔹 **Sistema Modulare**: Architettura scalabile e manutenibile  

## 🚀 Quick Start

### **🎯 Installazione Automatica**

```bash
# Clona e installa con scelta interattiva
git clone https://github.com/diaghi13/rfid_gate.git
cd rfid_gate
sudo bash scripts/install.sh

# Opzioni disponibili:
# 1️⃣ Sistema base (solo RFID Gate)
# 2️⃣ Sistema completo (+ Web UI) [consigliato]
# 3️⃣ Sistema avanzato (+ Nginx + SSL)
```

### **📋 Requisiti Hardware**

| Componente | Specifiche | Note |
|------------|------------|------|
| **SBC** | Raspberry Pi 3B+ o superiore | ARM64 raccomandato |
| **Lettore RFID** | MFRC522 o PN532 | Supporto multi-interface |
| **Relè** | 5V compatibile GPIO | Per controllo tornello |
| **Alimentazione** | 5V 3A minimo | Considerare carico relè |

### **🔧 Configurazione Rapida**

1. **Setup iniziale**:
   ```bash
   cp .env.example .env
   nano .env  # Configura secondo il tuo hardware
   ```

2. **Avvia sistema principale**:
   ```bash
   python3 main.py
   ```

3. **Test del sistema**:
   ```bash
   python3 tests/test_refactored_system.py
   ```

### **🌐 Web UI Dashboard**

```bash
# Avvia server di sviluppo
cd webui && python3 app_demo.py
# Dashboard: http://localhost:8080

# Avvia server di produzione (con Gunicorn)
cd webui && gunicorn -c gunicorn.conf.py app:app
# Dashboard: http://localhost:8000
```

**Funzionalità Web UI:**
- 📊 Dashboard real-time con stato sistema
- ⚙️ Configurazione .env tramite interfaccia grafica  
- 📋 Log di accesso e monitoraggio eventi
- 🎮 Controllo manuale tornello
- 🔧 Diagnostica lettori RFID

## 📍 Navigazione Rapida

| Sezione | Descrizione | Link |
|---------|-------------|------|
| 🏗️ **Architettura** | Struttura modulare del sistema | [⬇️ Vai alla sezione](#️-architettura-modulare) |
| 📚 **Documentazione** | Guide complete e tutorial | [⬇️ Vai alla sezione](#-documentazione) |
| 🌐 **Web UI Setup** | Installazione interfaccia web | [📖 Guida completa](docs/WEBUI_INSTALLATION.md) |
| ⚙️ **Configurazione** | Esempi di configurazione | [📖 Configuration Guide](docs/CONFIGURATION_EXAMPLES.md) |
| 🧪 **Testing** | Test e validazione | [⬇️ Vai alla sezione](#testing) |
| 🔧 **Troubleshooting** | Risoluzione problemi | [📖 Troubleshooting](docs/PN532_QUICK_GUIDE.md) |

# Oppure server demo semplice
cd webui && python3 simple_server.py
# Demo: http://localhost:8082
```

**🎯 Funzionalità Web UI:**

- 📊 **Dashboard**: Monitoraggio real-time stato sistema
- 🎮 **Controllo**: Apertura manuale tornello da remoto
- 📋 **Log Manager**: Visualizzazione log accessi con filtri avanzati
- ⚙️ **Configurazione**: Gestione completa file `.env` da web interface
- � **Backup System**: Backup automatici e ripristino configurazioni
- 📱 **Responsive**: Design ottimizzato per mobile/tablet
- 🔒 **Sicurezza**: Autenticazione JWT e validazione configurazioni

## 📋 Features

- ✅ **Dual Reader Support**: MFRC522 + PN532 (I2C/SPI/UART)
- ✅ **Bidirectional Control**: Lettori IN/OUT indipendenti
- ✅ **MQTT Integration**: Autenticazione server remota
- ✅ **Offline Mode**: Funzionamento senza connessione
- ✅ **Type Safe Config**: Configurazione con validazione
- ✅ **Async Architecture**: Performance ottimizzate
- ✅ **Anti-Crosstalk**: Debounce globale avanzato
- ✅ **Hardware Abstraction**: Supporto multi-platform
- 🆕 **Web UI**: Interfaccia web moderna per gestione completa
- 🆕 **Config Manager**: Gestione file .env da interfaccia web

## 📁 Struttura Progetto (Post-Refactor)

```
rfid_gate/
├── 📂 rfid_gate/           # 🏗️ Core system modules
│   ├── config/             # ⚙️ Configuration management
│   ├── core/               # 🎯 Business logic
│   ├── hardware/           # 🔧 Hardware abstraction
│   ├── network/            # 📡 MQTT & networking
│   ├── logging/            # 📊 Logging system
│   └── utils/              # 🛠️ Utilities
├── 📂 webui/               # 🌐 Web interface
│   ├── templates/          # 📄 HTML templates
│   ├── static/             # 🎨 CSS/JS/Assets
│   ├── app.py              # 🚀 FastAPI server
│   ├── app_demo.py         # 🧪 Demo server
│   ├── simple_server.py    # 📡 Simple HTTP server
│   └── config_manager.py   # ⚙️ .env file manager
├── 📂 tests/               # 🧪 Test suite
├── 📂 tools/               # 🔧 Utility scripts
├── 📂 scripts/             # 📜 Management scripts
├── 📂 docs/                # 📚 Documentation
├── 📂 logs/                # 📋 System logs
├── 📂 backups/config/      # 💾 Configuration backups
├── 🐍 main.py              # 🚀 Main entry point
└── ⚙️ .env                 # 🔧 Configuration file
```

## 📚 Documentazione

### 📖 **Guide Complete**
- 🌐 **[Installazione Web UI](docs/WEBUI_INSTALLATION.md)** - Setup completo WebUI con Nginx e SSL
- ⚙️ **[Esempi Configurazione](docs/CONFIGURATION_EXAMPLES.md)** - Configurazioni per diversi scenari
- 🎮 **[Controllo Manuale](docs/MANUAL_CONTROL.md)** - Apertura manuale e comandi
- 📡 **[Sistema Offline](docs/OFFLINE_SYSTEM.md)** - Funzionamento senza connessione
- 🔧 **[Guida PN532](docs/PN532_QUICK_GUIDE.md)** - Setup rapido lettori PN532

### 🛠️ **Script e Tool**
- 📦 **[Scripts di Installazione](scripts/)** - Installazione automatica completa
- 🔧 **[Tool di Gestione](tools/)** - Utility per manutenzione e debug
- 🧪 **[Test Suite](tests/)** - Test automatizzati e validazione

## 🏗️ Architettura Modulare

### 🎯 **Core Business Logic**
```
rfid_gate/core/
├── access_control.py      # Sistema controllo accessi centrale
├── gate_manager.py        # Gestione stato tornello
└── authentication.py     # Logica autenticazione RFID
```

### 🔌 **Hardware Abstraction Layer**
```
rfid_gate/hardware/
├── readers/               # 📡 Lettori RFID
│   ├── base.py           # Interfaccia comune
│   ├── mfrc522.py        # Reader MFRC522
│   ├── pn532.py          # Reader PN532 multi-interface
│   └── factory.py        # Factory pattern per reader
└── relays/               # ⚡ Controller Relè
    ├── base.py           # Interfaccia comune  
    └── gpio.py           # GPIO Raspberry Pi
```

### 🌐 **Network & Communication**
```
rfid_gate/network/
├── mqtt.py               # Client MQTT asincrono
├── api_client.py         # Client API REST
└── websocket.py          # WebSocket real-time
```

### ⚙️ **Configuration Management**
```
rfid_gate/config/
├── settings.py           # Type-safe configuration
├── validation.py         # Validazione configurazioni
└── migration.py          # Migrazione configurazioni legacy
```

### 🌐 **Web Interface**
```
webui/
├── app.py                # FastAPI application
├── app_demo.py           # Demo/development server
├── config_manager.py     # .env file management
├── templates/            # Jinja2 HTML templates
├── static/              # CSS, JavaScript, assets
└── gunicorn.conf.py     # Production server config
```

## ⚙️ Configurazione

### File `.env` (compatibile con sistema precedente)

```bash
# Sistema
TORNELLO_ID=tornello_01
BIDIRECTIONAL_MODE=true

# MQTT
MQTT_BROKER=your-broker.com
MQTT_PORT=8883
MQTT_USERNAME=your-user
MQTT_PASSWORD=your-password
MQTT_USE_TLS=true

# Lettori RFID
ENABLE_IN_READER=true
ENABLE_OUT_READER=true
RFID_IN_READER_TYPE=pn532      # mfrc522 | pn532
RFID_OUT_READER_TYPE=pn532     # mfrc522 | pn532

# PN532 Configuration
RFID_IN_PN532_INTERFACE=i2c    # i2c | spi | uart
RFID_IN_PN532_I2C_ADDRESS=0x24
RFID_OUT_PN532_INTERFACE=spi
RFID_OUT_PN532_SPI_BUS=0

# Relè
RELAY_IN_PIN=18
RELAY_OUT_PIN=19
RELAY_IN_ACTIVE_TIME=2
RELAY_OUT_ACTIVE_TIME=2

# Formato UID
UID_FORMAT_MODE=remove_suffix  # remove_suffix | fixed_length | raw
UID_CHARS_COUNT=2
```

## 📡 Lettori Supportati

### MFRC522

```python
# GPIO standard Raspberry Pi
RFID_IN_READER_TYPE=mfrc522
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
```

### PN532 Multi-Interface

```python
# I2C (default)
RFID_IN_READER_TYPE=pn532
RFID_IN_PN532_INTERFACE=i2c
RFID_IN_PN532_I2C_ADDRESS=0x24

# SPI (per dual reader)
RFID_OUT_READER_TYPE=pn532
RFID_OUT_PN532_INTERFACE=spi
RFID_OUT_PN532_SPI_BUS=0

# UART
RFID_IN_PN532_INTERFACE=uart
RFID_IN_PN532_UART_PORT=/dev/serial0
```

## 🔧 API Programming

### Uso Programmatico

```python
from rfid_gate import AccessControlSystem, RFIDGateConfig

# Configurazione type-safe
config = RFIDGateConfig.from_env()

# Sistema di controllo
system = AccessControlSystem()

# Callbacks custom
def on_card_read(event):
    print(f"Carta: {event.card_uid} - {event.decision}")

system.on_access_event = on_card_read

# Avvio asincrono
await system.run()
```

### Factory Pattern per Lettori

```python
from rfid_gate.hardware.readers.factory import ReaderFactory

# Crea lettori dinamicamente
mfrc522 = ReaderFactory.create_reader_legacy(
    'mfrc522', 'reader_in', 'in', rst_pin=22
)

pn532 = ReaderFactory.create_reader_legacy(
    'pn532', 'reader_out', 'out', interface='spi'
)

# Configurazione dual reader automatica
readers = ReaderFactory.create_dual_readers(
    config.rfid_in, config.rfid_out
)
```

## 🧪 Testing

```bash
# Test completo sistema
python3 tests/test_refactored_system.py

# Test specifici per moduli
python3 -m pytest tests/unit/ -v
python3 -m pytest tests/integration/ -v

# Test copertura completa
python3 -m pytest tests/ --cov=rfid_gate --cov-report=html
```

**Risultati Test Attuali**: ✅ 7/7 Passati (100%)

### Test Disponibili
- ✅ **Unit Tests**: Moduli individuali
- ✅ **Integration Tests**: Sistema completo  
- ✅ **Hardware Mock Tests**: Simulazione hardware
- ✅ **MQTT Integration**: Test connettività
- ✅ **Configuration Validation**: Test configurazioni

## 📊 Monitoring

### Status Sistema

```python
status = system.get_system_status()
# {
#   'mode': 'online',
#   'stats': {'access_events': 142, 'access_granted': 89},
#   'readers': {'in': {...}, 'out': {...}},
#   'relays': {'in': {...}, 'out': {...}},
#   'mqtt': {...}
# }
```

### Apertura Manuale

```python
# API programmatica
await system.manual_open('in', duration=3.0)

# Comando MQTT
# Topic: gate/tornello_01/manual_open
# Payload: {"direction": "in", "duration": 3}
```

## 🔄 Migrazione dal Sistema Precedente

Il sistema è **100% compatibile** con la configurazione esistente:

1. ✅ Stesso file `.env`
2. ✅ Stesso comportamento
3. ✅ Stesse API MQTT
4. ✅ Stessa logica business

**Upgrade Path**:

```bash
# Backup (opzionale, già in archive/)
cp main.py main_old.py

# Switch al sistema refactored
# (già fatto - main.py è il nuovo sistema)
python3 main.py
```

## 📁 File Archiviati

Il sistema precedente è stato archiviato in `archive/` per:

- 📚 Riferimento storico
- 🔧 Debug e troubleshooting
- 📋 Documentazione processo sviluppo
- 💾 Backup sicurezza

Vedi [`archive/README.md`](archive/README.md) per dettagli.

## 🛠️ Sviluppo

### Aggiungere Nuovo Lettore

```python
# 1. Crea classe reader
class MyReader(BaseRFIDReader):
    def get_reader_type(self): return "my_reader"
    async def _hardware_init(self): ...
    async def _hardware_read(self): ...

# 2. Registra in factory
ReaderFactory.register_reader('my_reader', MyReader)

# 3. Usa in configurazione
RFID_IN_READER_TYPE=my_reader
```

### Estendere Sistema

- 🔌 **Hardware**: Nuovi reader/relè in `hardware/`
- 🌐 **Network**: Protocolli aggiuntivi in `network/`
- 📊 **Logging**: Custom loggers in `logging/`
- 🎯 **Business Logic**: Estendi `AccessControlSystem`

## 📋 Requirements

```bash
# Installazione dipendenze
pip install -r requirements.txt

# Hardware Libraries (Raspberry Pi)
pip install RPi.GPIO mfrc522 adafruit-circuitpython-pn532 paho-mqtt
```

## 🎯 Performance

- ⚡ **Async I/O**: Non-blocking hardware operations
- 🔄 **Connection Pooling**: MQTT auto-reconnect
- 📦 **Message Queuing**: Offline message storage
- 🚫 **Debounce**: Anti-crosstalk globale < 1ms
- 💾 **Memory**: < 50MB usage tipico

## 🔮 Roadmap

- [ ] Web dashboard per monitoring
- [ ] Database integration (SQLite/PostgreSQL)
- [ ] REST API per integrazione esterna
- [ ] Docker containerization
- [ ] HA/Clustering support
- [ ] Biometric readers support

## 📞 Support & Contributing

### 🐛 **Troubleshooting**
1. Controlla `logs/system.log` per errori
2. Esegui diagnostica: `python3 tests/test_refactored_system.py`
3. Verifica configurazione: `python3 tools/rfid_diagnostic.py`
4. Consulta [PN532 Quick Guide](docs/PN532_QUICK_GUIDE.md) per problemi hardware

### 🤝 **Contributing**
1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit delle modifiche (`git commit -m 'Add amazing feature'`)
4. Push del branch (`git push origin feature/amazing-feature`)
5. Apri una Pull Request

### 📄 **License**
Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per dettagli.

### 👥 **Authors**
- **Davide Donghi** - *Sviluppo iniziale e refactor* - [@diaghi13](https://github.com/diaghi13)

---

### 🎯 **Project Status**
- 🟢 **Production Ready**: Sistema testato e funzionante
- 🟢 **Actively Maintained**: Aggiornamenti regolari
- 🟢 **Full Documentation**: Guide complete disponibili
- 🟢 **Modern Architecture**: Codice pulito e modulare

_Sistema refactored completato il 6 ottobre 2025_  
_Compatibilità totale mantenuta con architettura moderna_
