# 🎯 RFID Gate Access Control System

Sistema professionale di controllo accessi per Raspberry Pi con lettori RFID, controllo relè e comunicazione MQTT.

## ⚡ Installazione Rapida

```bash
# Clona repository
git clone <repository-url> rfid-gate-system
cd rfid-gate-system

# Installazione automatica
sudo bash scripts/install.sh

# Configurazione
sudo nano /opt/rfid-gate/.env

# Avvio servizio
sudo systemctl enable rfid-gate
sudo systemctl start rfid-gate
```

## 🔧 Gestione Sistema

```bash
# Stato servizio
sudo systemctl status rfid-gate

# Log in tempo reale
sudo journalctl -fu rfid-gate

# Tool di utilità
sudo python3 /opt/rfid-gate/tools/manual_open_tool.py --test
sudo python3 /opt/rfid-gate/tools/offline_utils.py --status
sudo python3 /opt/rfid-gate/tools/log_viewer.py --stats
```

## 📚 Documentazione

- **[Documentazione Completa](docs/README.md)** - Guida completa al sistema
- **[Configurazione](docs/CONFIGURATION_EXAMPLES.md)** - Esempi di configurazioni
- **[Controllo Manuale](docs/MANUAL_CONTROL.md)** - Guida apertura manuale
- **[Sistema Offline](docs/OFFLINE_SYSTEM.md)** - Funzionamento offline

## ⚙️ Caratteristiche

- 🔄 Sistema bidirezionale (ingresso/uscita)
- ⚡ Controllo relè professionale
- 📡 Comunicazione MQTT sicura
- 🌐 Modalità offline garantita
- 🔓 Apertura manuale remota/locale
- 📊 Logging completo accessi
- 🛠️ Installazione automatica
- ⚙️ Servizio systemd integrato

## 🏗️ Hardware Supportato

- **Raspberry Pi** (tutti i modelli con GPIO)
- **RFID RC522** (SPI)
- **Relè 5V/3.3V** (Active HIGH/LOW)
- **Connessione Internet** (WiFi/Ethernet)

## 📞 Supporto

Per problemi e supporto, consultare la documentazione completa in `docs/`.

---
🚀 **RFID Gate System** - Controllo accessi professionale
