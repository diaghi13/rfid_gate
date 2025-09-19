#!/bin/bash
# 🧹 Script per pulire e riorganizzare il progetto
# Questo script rimuove i file di test e organizza la struttura finale

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 PULIZIA E RIORGANIZZAZIONE PROGETTO${NC}"
echo "====================================="

# Directory corrente del progetto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "${YELLOW}📁 Directory progetto: $PROJECT_ROOT${NC}"

cd "$PROJECT_ROOT"

# ========================================
# 🗑️ RIMOZIONE FILE DI TEST E DEBUG
# ========================================

echo -e "\n${YELLOW}🗑️ Rimozione file di test e debug...${NC}"

# File di test da rimuovere
TEST_FILES=(
    "test_gpio_direct.py"
    "test_relay.py"
    "test_relay_simple.py"
    "test_simple.py"
    "test_simple_minimal.py"
    "test_offline.py"
    "app.py"
    "src/test_offline.py"
    "src/gpio_utils.py"
    "src/relay_controller.py.bku"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Rimosso: $file"
    fi
done

# ========================================
# 📁 CREAZIONE STRUTTURA DIRECTORY
# ========================================

echo -e "\n${YELLOW}📁 Creazione struttura directory...${NC}"

# Crea directory se non esistono
mkdir -p tools
mkdir -p scripts
mkdir -p config
mkdir -p config/examples
mkdir -p docs
mkdir -p logs
mkdir -p tests

echo "   ✅ Directory create"

# ========================================
# 📋 SPOSTAMENTO FILE NEI TOOL
# ========================================

echo -e "\n${YELLOW}📋 Organizzazione file tool...${NC}"

# Sposta file da src a tools
TOOL_FILES=(
    "src/offline_utils.py:tools/offline_utils.py"
    "src/manual_open_tool.py:tools/manual_open_tool.py"
    "src/log_viewer.py:tools/log_viewer.py"
    "emergency_stop.py:tools/emergency_stop.py"
)

for entry in "${TOOL_FILES[@]}"; do
    IFS=':' read -r source dest <<< "$entry"
    if [ -f "$source" ]; then
        mv "$source" "$dest"
        echo "   ✅ Spostato: $source → $dest"
    fi
done

# ========================================
# ⚙️ CREAZIONE FILE CONFIGURAZIONE
# ========================================

echo -e "\n${YELLOW}⚙️ Creazione file configurazione...${NC}"

# Crea .env.example
if [ ! -f "config/.env.example" ]; then
    cat > config/.env.example << 'EOF'
# Configurazione MQTT
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_USERNAME=palestraUser
MQTT_PASSWORD=28dade03$
MQTT_USE_TLS=True

# Configurazione Tornello
TORNELLO_ID=tornello_01

# Sistema Bidirezionale
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=False

# RFID Reader IN
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# RFID Reader OUT (opzionale)
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=False

# Relè IN
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=True
RELAY_IN_INITIAL_STATE=HIGH
RELAY_IN_ENABLE=True

# Relè OUT (opzionale)
RELAY_OUT_PIN=19
RELAY_OUT_ACTIVE_TIME=2
RELAY_OUT_ACTIVE_LOW=True
RELAY_OUT_INITIAL_STATE=HIGH
RELAY_OUT_ENABLE=False

# Autenticazione
AUTH_ENABLED=True
AUTH_TIMEOUT=10
AUTH_TOPIC_SUFFIX=auth_response

# Apertura Manuale
MANUAL_OPEN_ENABLED=True
MANUAL_OPEN_TOPIC_SUFFIX=manual_open
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response
MANUAL_OPEN_TIMEOUT=10
MANUAL_OPEN_AUTH_REQUIRED=True

# Sistema Offline
OFFLINE_MODE_ENABLED=True
OFFLINE_ALLOW_ACCESS=True
OFFLINE_SYNC_ENABLED=True
OFFLINE_STORAGE_FILE=offline_queue.json
OFFLINE_MAX_QUEUE_SIZE=1000
CONNECTION_CHECK_INTERVAL=30
CONNECTION_RETRY_ATTEMPTS=3

# Logging
LOG_DIRECTORY=logs
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
ENABLE_CONSOLE_LOG=False

# RFID Debounce
RFID_DEBOUNCE_TIME=2.0
EOF
    echo "   ✅ Creato: config/.env.example"
fi

# Esempi configurazioni
if [ ! -f "config/examples/unidirezionale.env" ]; then
    cat > config/examples/unidirezionale.env << 'EOF'
# Configurazione Solo Ingresso (Unidirezionale)
BIDIRECTIONAL_MODE=False
ENABLE_IN_READER=True
ENABLE_OUT_READER=False
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True
RFID_OUT_ENABLE=False
RELAY_IN_PIN=18
RELAY_IN_ENABLE=True
RELAY_OUT_ENABLE=False
EOF
    echo "   ✅ Creato: config/examples/unidirezionale.env"
fi

if [ ! -f "config/examples/bidirezionale.env" ]; then
    cat > config/examples/bidirezionale.env << 'EOF'
# Configurazione Sistema Bidirezionale Completo
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=True
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=True
RELAY_IN_PIN=18
RELAY_IN_ENABLE=True
RELAY_OUT_PIN=19
RELAY_OUT_ENABLE=True
EOF
    echo "   ✅ Creato: config/examples/bidirezionale.env"
fi

# ========================================
# 📄 CREAZIONE DOCUMENTAZIONE
# ========================================

echo -e "\n${YELLOW}📄 Creazione documentazione...${NC}"

# Sposta documentazione esistente
if [ -f "config_examples.md" ]; then
    mv "config_examples.md" "docs/CONFIGURATION_EXAMPLES.md"
    echo "   ✅ Spostato: config_examples.md → docs/"
fi

if [ -f "manual_control_guide.md" ]; then
    mv "manual_control_guide.md" "docs/MANUAL_CONTROL.md"
    echo "   ✅ Spostato: manual_control_guide.md → docs/"
fi

if [ -f "offline_guide.md" ]; then
    mv "offline_guide.md" "docs/OFFLINE_SYSTEM.md"
    echo "   ✅ Spostato: offline_guide.md → docs/"
fi

# ========================================
# 🔧 AGGIUSTAMENTO PERMESSI
# ========================================

echo -e "\n${YELLOW}🔧 Impostazione permessi...${NC}"

# Rendi eseguibili gli script
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x tools/*.py 2>/dev/null || true

echo "   ✅ Permessi impostati"

# ========================================
# 📊 PULIZIA SCRIPT DUPLICATI
# ========================================

echo -e "\n${YELLOW}📊 Pulizia script duplicati...${NC}"

# Rimuovi script duplicati/vecchi
OLD_SCRIPTS=(
    "scripts/offline_tool.sh"
    "scripts/setup_venv.sh"
)

for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        rm -f "$script"
        echo "   ✅ Rimosso script obsoleto: $script"
    fi
done

# ========================================
# 📋 CREAZIONE REQUIREMENTS.TXT PULITO
# ========================================

echo -e "\n${YELLOW}📋 Aggiornamento requirements.txt...${NC}"

cat > requirements.txt << 'EOF'
# RFID Access Control System Dependencies
# Versione ottimizzata per Raspberry Pi

# Core RFID Support
mfrc522==0.0.7

# GPIO Control (Raspberry Pi)
RPi.GPIO==0.7.1

# MQTT Communication
paho-mqtt==1.6.1

# Configuration Management
python-dotenv==1.0.0
EOF

echo "   ✅ Requirements.txt aggiornato"

# ========================================
# 🎯 CREAZIONE README PRINCIPALE
# ========================================

echo -e "\n${YELLOW}🎯 Creazione README.md...${NC}"

if [ ! -f "README.md" ]; then
    cat > README.md << 'EOF'
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
EOF
    echo "   ✅ Creato: README.md"
fi

# ========================================
# 🧪 CREAZIONE TEST SEMPLICE
# ========================================

echo -e "\n${YELLOW}🧪 Creazione test base...${NC}"

if [ ! -f "tests/test_basic.py" ]; then
    cat > tests/test_basic.py << 'EOF'
#!/usr/bin/env python3
"""
Test base per verificare installazione sistema
"""
import sys
import os

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test import moduli base"""
    try:
        from config import Config
        from rfid_manager import RFIDManager
        from relay_manager import RelayManager
        from mqtt_client import MQTTClient
        from offline_manager import OfflineManager
        from manual_control import ManualControl
        print("✅ Tutti i moduli importati correttamente")
        return True
    except Exception as e:
        print(f"❌ Errore import: {e}")
        return False

def test_config():
    """Test configurazione"""
    try:
        from config import Config
        errors = Config.validate_config()
        if errors:
            print("❌ Errori configurazione:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print("✅ Configurazione valida")
            return True
    except Exception as e:
        print(f"❌ Errore test config: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TEST BASE SISTEMA")
    print("===================")
    
    success = True
    success &= test_imports()
    success &= test_config()
    
    if success:
        print("\n✅ Tutti i test superati!")
        sys.exit(0)
    else:
        print("\n❌ Alcuni test falliti!")
        sys.exit(1)
EOF
    echo "   ✅ Creato: tests/test_basic.py"
fi

# ========================================
# 📋 RIEPILOGO FINALE
# ========================================

echo -e "\n${GREEN}🎉 PULIZIA COMPLETATA!${NC}"
echo "====================="
echo -e "${YELLOW}📊 Struttura finale progetto:${NC}"

find . -type f -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.txt" -o -name "*.env" | \
grep -v __pycache__ | grep -v .git | sort | while read file; do
    echo "   📄 $file"
done

echo
echo -e "${BLUE}🚀 Prossimi passi:${NC}"
echo "1. Verifica che tutti i file siano al posto giusto"
echo "2. Testa installazione: sudo bash scripts/install.sh"
echo "3. Configura sistema: sudo nano /opt/rfid-gate/.env"
echo "4. Avvia servizio: sudo systemctl start rfid-gate"

echo
echo -e "${GREEN}✨ Progetto pronto per il deployment!${NC}"