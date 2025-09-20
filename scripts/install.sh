#!/bin/bash
# 📦 Installazione Automatica RFID Gate System
# Questo script installa tutto il necessario per il sistema di controllo accessi

set -e  # Esce se qualsiasi comando fallisce

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directory progetto
PROJECT_DIR="/opt/rfid-gate"
SERVICE_USER="rfid"

echo -e "${BLUE}🚀 INSTALLAZIONE RFID GATE SYSTEM${NC}"
echo "================================="

# Controllo privilegi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Questo script deve essere eseguito come root${NC}"
    echo "💡 Usa: sudo bash scripts/install.sh"
    exit 1
fi

echo -e "${YELLOW}📋 Controllo sistema...${NC}"

# Verifica Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Sistema non rilevato come Raspberry Pi${NC}"
    read -p "Continuare comunque? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Aggiornamento sistema
echo -e "${YELLOW}📦 Aggiornamento sistema...${NC}"
apt update -qq
apt upgrade -y -qq

# Installazione dipendenze sistema
echo -e "${YELLOW}📦 Installazione dipendenze sistema...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-rpi.gpio \
    git \
    curl \
    rsync \
    logrotate \
    mosquitto-clients \
    build-essential \
    python3-spidev \
    libbcm2835-dev \
    --no-install-recommends

# Abilita SPI se non già fatto
echo -e "${YELLOW}🔧 Configurazione SPI...${NC}"
if ! grep -q "dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" >> /boot/config.txt
    echo -e "${GREEN}✅ SPI abilitato in /boot/config.txt${NC}"
    echo -e "${YELLOW}⚠️ RIAVVIO NECESSARIO dopo installazione${NC}"
else
    echo -e "${GREEN}✅ SPI già abilitato${NC}"
fi

# Crea utente di sistema se non esiste
echo -e "${YELLOW}👤 Configurazione utente sistema...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$SERVICE_USER"
    usermod -a -G gpio,spi,dialout "$SERVICE_USER"
    echo -e "${GREEN}✅ Utente $SERVICE_USER creato${NC}"
else
    echo -e "${GREEN}✅ Utente $SERVICE_USER già esiste${NC}"
    usermod -a -G gpio,spi,dialout "$SERVICE_USER"
fi

# Crea directory progetto
echo -e "${YELLOW}📁 Creazione directory progetto...${NC}"
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"
mkdir -p "$PROJECT_DIR/config/examples"
mkdir -p "$PROJECT_DIR/tools"
mkdir -p "$PROJECT_DIR/scripts"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

# Copia file progetto
echo -e "${YELLOW}📋 Copia file progetto...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Copia struttura src
if [ -d "$SCRIPT_DIR/src" ]; then
    cp -r "$SCRIPT_DIR/src" "$PROJECT_DIR/"
    echo -e "${GREEN}✅ Copiato directory src${NC}"
else
    echo -e "${RED}❌ Directory src non trovata${NC}"
    exit 1
fi

# Copia requirements.txt
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    cp "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"
    echo -e "${GREEN}✅ Copiato requirements.txt${NC}"
else
    echo -e "${RED}❌ File requirements.txt non trovato${NC}"
    exit 1
fi

# Copia file tools
echo -e "${YELLOW}📋 Copia file tools...${NC}"
TOOL_FILES=(
    "src/offline_utils.py"
    "src/manual_open_tool.py" 
    "src/log_viewer.py"
    "src/emergency_stop.py"
    "tools/emergency_stop.py"
    "tools/offline_diagnostics.py"
    "tools/offline_utils.py"
    "tools/log_viewer.py"
    "tools/manual_open_tool.py"
)

for tool_file in "${TOOL_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$tool_file" ]; then
        cp "$SCRIPT_DIR/$tool_file" "$PROJECT_DIR/tools/"
        echo -e "${GREEN}✅ Copiato $tool_file${NC}"
    fi
done

# Copia script di gestione
echo -e "${YELLOW}📋 Copia script di gestione...${NC}"
if [ -d "$SCRIPT_DIR/scripts" ]; then
    cp -r "$SCRIPT_DIR/scripts"/* "$PROJECT_DIR/scripts/" 2>/dev/null || true
    echo -e "${GREEN}✅ Copiati script di gestione${NC}"
fi

# Copia file configurazione esempi
echo -e "${YELLOW}📋 Copia file configurazione...${NC}"
CONFIG_FILES=(
    "config/examples/bidirezionale.env"
    "config/examples/unidirezionale.env"
    "docs/CONFIGURATION_EXAMPLES.md"
    "docs/MANUAL_CONTROL.md"
    "docs/OFFLINE_SYSTEM.md"
    "scripts/config_example.md"
    "scripts/config_example.sh"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$config_file" ]; then
        target_dir="$PROJECT_DIR/$(dirname "$config_file")"
        mkdir -p "$target_dir"
        cp "$SCRIPT_DIR/$config_file" "$target_dir/"
        echo -e "${GREEN}✅ Copiato $config_file${NC}"
    fi
done

# Imposta permessi corretti
echo -e "${YELLOW}🔧 Impostazione permessi...${NC}"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/scripts"/*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/tools"/*.py 2>/dev/null || true

# Installa ambiente virtuale Python
echo -e "${YELLOW}🐍 Configurazione ambiente Python...${NC}"
cd "$PROJECT_DIR"

# Crea venv come utente rfid
sudo -u "$SERVICE_USER" python3 -m venv venv
sudo -u "$SERVICE_USER" ./venv/bin/pip install --upgrade pip

# Installa dipendenze Python
echo -e "${YELLOW}📦 Installazione dipendenze Python...${NC}"
sudo -u "$SERVICE_USER" ./venv/bin/pip install -r requirements.txt

# Installa dipendenze aggiuntive per RFID
echo -e "${YELLOW}📡 Installazione dipendenze RFID...${NC}"
sudo -u "$SERVICE_USER" ./venv/bin/pip install spidev
sudo -u "$SERVICE_USER" ./venv/bin/pip install RPi.GPIO

# Verifica e installa mfrc522 da source se necessario
if ! sudo -u "$SERVICE_USER" ./venv/bin/python -c "import mfrc522" 2>/dev/null; then
    echo -e "${YELLOW}📡 Installazione mfrc522 da source...${NC}"
    sudo -u "$SERVICE_USER" ./venv/bin/pip install https://github.com/pimylifeup/MFRC522-python/archive/master.zip
fi

# Crea file configurazione se non esiste
echo -e "${YELLOW}⚙️ Configurazione iniziale...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        cp "$SCRIPT_DIR/.env" "$PROJECT_DIR/.env"
        echo -e "${GREEN}✅ Copiato file .env esistente${NC}"
    else
        # Crea configurazione base per un solo lettore RFID
        cat > "$PROJECT_DIR/.env" << 'EOF'
# Configurazione MQTT
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_USERNAME=palestraUser
MQTT_PASSWORD=28dade03$
MQTT_USE_TLS=True

# Configurazione Tornello
TORNELLO_ID=tornello_01

# Configurazione Sistema Unidirezionale (un solo lettore per iniziare)
BIDIRECTIONAL_MODE=False
ENABLE_IN_READER=True
ENABLE_OUT_READER=False

# Configurazione RFID Reader IN
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# Configurazione RFID Reader OUT (disabilitato)
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=False

# Configurazione Relè IN
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=True
RELAY_IN_INITIAL_STATE=HIGH
RELAY_IN_ENABLE=True

# Configurazione Relè OUT (disabilitato)
RELAY_OUT_PIN=19
RELAY_OUT_ACTIVE_TIME=2
RELAY_OUT_ACTIVE_LOW=True
RELAY_OUT_INITIAL_STATE=HIGH
RELAY_OUT_ENABLE=False

# Configurazione Autenticazione
AUTH_ENABLED=True
AUTH_TIMEOUT=10
AUTH_TOPIC_SUFFIX=auth_response

# Configurazione Apertura Manuale
MANUAL_OPEN_ENABLED=True
MANUAL_OPEN_TOPIC_SUFFIX=manual_open
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response
MANUAL_OPEN_TIMEOUT=10
MANUAL_OPEN_AUTH_REQUIRED=True

# Configurazione Fallback Offline
OFFLINE_MODE_ENABLED=True
OFFLINE_ALLOW_ACCESS=True
OFFLINE_SYNC_ENABLED=True
OFFLINE_STORAGE_FILE=offline_queue.json
OFFLINE_MAX_QUEUE_SIZE=1000
CONNECTION_CHECK_INTERVAL=30
CONNECTION_RETRY_ATTEMPTS=3

# Configurazione Logging
LOG_DIRECTORY=logs
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
ENABLE_CONSOLE_LOG=False

# Configurazione RFID Debounce
RFID_DEBOUNCE_TIME=2.0

# Configurazione UID Processing (opzionale)
UID_FORMAT_MODE=remove_suffix
UID_CHARS_COUNT=2
UID_TARGET_LENGTH=8
UID_DEBUG_MODE=False
EOF
        echo -e "${GREEN}✅ File .env creato con configurazione base${NC}"
    fi
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
fi

# Crea file servizio systemd con utente root per accesso GPIO
echo -e "${YELLOW}🔧 Creazione servizio systemd...${NC}"
cat > /etc/systemd/system/rfid-gate.service << EOF
[Unit]
Description=RFID Gate Access Control System
Documentation=https://github.com/yourusername/rfid-gate
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/main.py
ExecStop=/bin/kill -INT \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rfid-gate

# Sicurezza
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=read-only
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

# Configura logrotate
echo -e "${YELLOW}📊 Configurazione logrotate...${NC}"
cat > /etc/logrotate.d/rfid-gate << EOF
$PROJECT_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}

$PROJECT_DIR/logs/*.csv {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}
EOF

# Ricarica systemd
systemctl daemon-reload

# Test installazione
echo -e "${YELLOW}🧪 Test installazione...${NC}"
cd "$PROJECT_DIR"

# Test caricamento configurazione
if sudo ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
try:
    from config import Config
    print('✅ Config caricata correttamente')
    print(f'   Tornello ID: {Config.TORNELLO_ID}')
    print(f'   MQTT Broker: {Config.MQTT_BROKER}')
    print(f'   RFID IN abilitato: {Config.RFID_IN_ENABLE}')
    print(f'   RFID OUT abilitato: {Config.RFID_OUT_ENABLE}')
    print(f'   Relay IN abilitato: {Config.RELAY_IN_ENABLE}')
except Exception as e:
    print(f'❌ Errore: {e}')
    exit(1)
"; then
    echo -e "${GREEN}✅ Test configurazione Python OK${NC}"
else
    echo -e "${RED}❌ Errore test configurazione${NC}"
    exit 1
fi

# Test dipendenze RFID
echo -e "${YELLOW}🧪 Test dipendenze RFID...${NC}"
if sudo ./venv/bin/python -c "
try:
    import mfrc522
    import RPi.GPIO as GPIO
    import spidev
    print('✅ Dipendenze RFID OK')
except ImportError as e:
    print(f'❌ Dipendenza mancante: {e}')
    exit(1)
"; then
    echo -e "${GREEN}✅ Test dipendenze RFID OK${NC}"
else
    echo -e "${RED}❌ Errore dipendenze RFID${NC}"
fi

# Informazioni finali
echo -e "${GREEN}🎉 INSTALLAZIONE COMPLETATA!${NC}"
echo "=================================="
echo
echo -e "${BLUE}📁 Directory progetto:${NC} $PROJECT_DIR"
echo -e "${BLUE}👤 Utente servizio:${NC} root (per accesso GPIO)"
echo -e "${BLUE}⚙️ File configurazione:${NC} $PROJECT_DIR/.env"
echo
echo -e "${YELLOW}🔧 Prossimi passi:${NC}"
echo "1. Verifica configurazione:"
echo "   sudo nano $PROJECT_DIR/.env"
echo
echo "2. Test manuale:"
echo "   cd $PROJECT_DIR"
echo "   sudo ./venv/bin/python src/main.py"
echo
echo "3. Abilita e avvia servizio:"
echo "   sudo systemctl enable rfid-gate"
echo "   sudo systemctl start rfid-gate"
echo
echo "4. Monitora stato:"
echo "   sudo systemctl status rfid-gate"
echo "   sudo journalctl -fu rfid-gate"
echo
echo "5. Tool di gestione:"
echo "   sudo python3 $PROJECT_DIR/tools/offline_utils.py --status"
echo "   sudo python3 $PROJECT_DIR/tools/manual_open_tool.py --test"
echo "   sudo python3 $PROJECT_DIR/tools/log_viewer.py --stats"
echo

# Mostra configurazioni esempio disponibili
if [ -d "$PROJECT_DIR/config/examples" ]; then
    echo -e "${BLUE}📋 Configurazioni esempio disponibili:${NC}"
    ls -la "$PROJECT_DIR/config/examples/"
    echo
    echo -e "${YELLOW}💡 Per copiare una configurazione esempio:${NC}"
    echo "   sudo cp $PROJECT_DIR/config/examples/unidirezionale.env $PROJECT_DIR/.env"
    echo "   sudo cp $PROJECT_DIR/config/examples/bidirezionale.env $PROJECT_DIR/.env"
    echo
fi

if grep -q "dtparam=spi=on" /boot/config.txt && ! lsmod | grep -q spi_bcm; then
    echo -e "${RED}⚠️ RIAVVIO NECESSARIO per attivare SPI${NC}"
    echo "   Esegui: sudo reboot"
    echo
fi

echo -e "${GREEN}🚀 Sistema pronto per l'uso!${NC}"