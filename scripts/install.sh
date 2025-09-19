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
    usermod -a -G gpio,spi "$SERVICE_USER"
    echo -e "${GREEN}✅ Utente $SERVICE_USER creato${NC}"
else
    echo -e "${GREEN}✅ Utente $SERVICE_USER già esiste${NC}"
    usermod -a -G gpio,spi "$SERVICE_USER"
fi

# Crea directory progetto
echo -e "${YELLOW}📁 Creazione directory progetto...${NC}"
mkdir -p "$PROJECT_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

# Copia file progetto
echo -e "${YELLOW}📋 Copia file progetto...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Copia struttura src
cp -r "$SCRIPT_DIR/src" "$PROJECT_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"

# Crea directory tools e copia
mkdir -p "$PROJECT_DIR/tools"
[ -f "$SCRIPT_DIR/src/offline_utils.py" ] && cp "$SCRIPT_DIR/src/offline_utils.py" "$PROJECT_DIR/tools/"
[ -f "$SCRIPT_DIR/src/manual_open_tool.py" ] && cp "$SCRIPT_DIR/src/manual_open_tool.py" "$PROJECT_DIR/tools/"
[ -f "$SCRIPT_DIR/src/log_viewer.py" ] && cp "$SCRIPT_DIR/src/log_viewer.py" "$PROJECT_DIR/tools/"
[ -f "$SCRIPT_DIR/emergency_stop.py" ] && cp "$SCRIPT_DIR/emergency_stop.py" "$PROJECT_DIR/tools/"

# Crea directory scripts
mkdir -p "$PROJECT_DIR/scripts"
cp -r "$SCRIPT_DIR/scripts"/* "$PROJECT_DIR/scripts/" 2>/dev/null || true

# Crea directory config
mkdir -p "$PROJECT_DIR/config"
[ -f "$SCRIPT_DIR/config_examples.md" ] && cp "$SCRIPT_DIR/config_examples.md" "$PROJECT_DIR/config/"


# Crea directory logs
mkdir -p "$PROJECT_DIR/logs"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/logs"

# Imposta permessi
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/scripts"/*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/tools"/*.py

# Installa ambiente virtuale Python
echo -e "${YELLOW}🐍 Configurazione ambiente Python...${NC}"
cd "$PROJECT_DIR"

# Crea venv come utente rfid
sudo -u "$SERVICE_USER" python3 -m venv venv
sudo -u "$SERVICE_USER" ./venv/bin/pip install --upgrade pip

# Installa dipendenze Python
echo -e "${YELLOW}📦 Installazione dipendenze Python...${NC}"
sudo -u "$SERVICE_USER" ./venv/bin/pip install -r requirements.txt

# Verifica installazione mfrc522
if ! sudo -u "$SERVICE_USER" ./venv/bin/python -c "import mfrc522" 2>/dev/null; then
    echo -e "${YELLOW}📡 Installazione mfrc522 da source...${NC}"
    sudo -u "$SERVICE_USER" ./venv/bin/pip install https://github.com/pimylifeup/MFRC522-python/archive/master.zip
fi

# Crea file configurazione se non esiste
echo -e "${YELLOW}⚙️ Configurazione iniziale...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        cp "$SCRIPT_DIR/.env" "$PROJECT_DIR/.env"
    else
        # Crea configurazione base
        cat > "$PROJECT_DIR/.env" << 'EOF'
# Configurazione MQTT
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_USERNAME=palestraUser
MQTT_PASSWORD=28dade03$
MQTT_USE_TLS=True

# Configurazione Tornello
TORNELLO_ID=tornello_01

# Configurazione Sistema Bidirezionale
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=False

# Configurazione RFID Reader IN
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# Configurazione RFID Reader OUT (opzionale)
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=False

# Configurazione Relè IN
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=True
RELAY_IN_INITIAL_STATE=HIGH
RELAY_IN_ENABLE=True

# Configurazione Relè OUT (opzionale)
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
EOF
    fi
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
    echo -e "${GREEN}✅ File .env creato${NC}"
fi

# Crea file servizio systemd
echo -e "${YELLOW}🔧 Creazione servizio systemd...${NC}"
cat > /etc/systemd/system/rfid-gate.service << EOF
[Unit]
Description=RFID Gate Access Control System
Documentation=https://github.com/yourusername/rfid-gate
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
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
    su $SERVICE_USER $SERVICE_USER
}

$PROJECT_DIR/logs/*.csv {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su $SERVICE_USER $SERVICE_USER
}
EOF

# Ricarica systemd
systemctl daemon-reload

# Test installazione
echo -e "${YELLOW}🧪 Test installazione...${NC}"
cd "$PROJECT_DIR"
if sudo -u "$SERVICE_USER" ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
from config import Config
print('✅ Config caricata correttamente')
print(f'   Tornello ID: {Config.TORNELLO_ID}')
print(f'   MQTT Broker: {Config.MQTT_BROKER}')
"; then
    echo -e "${GREEN}✅ Test configurazione Python OK${NC}"
else
    echo -e "${RED}❌ Errore test configurazione${NC}"
    exit 1
fi

# Informazioni finali
echo -e "${GREEN}🎉 INSTALLAZIONE COMPLETATA!${NC}"
echo "=================================="
echo
echo -e "${BLUE}📁 Directory progetto:${NC} $PROJECT_DIR"
echo -e "${BLUE}👤 Utente sistema:${NC} $SERVICE_USER"
echo -e "${BLUE}⚙️ File configurazione:${NC} $PROJECT_DIR/.env"
echo
echo -e "${YELLOW}🔧 Prossimi passi:${NC}"
echo "1. Modifica configurazione:"
echo "   sudo nano $PROJECT_DIR/.env"
echo
echo "2. Abilita e avvia servizio:"
echo "   sudo systemctl enable rfid-gate"
echo "   sudo systemctl start rfid-gate"
echo
echo "3. Monitora stato:"
echo "   sudo systemctl status rfid-gate"
echo "   sudo journalctl -fu rfid-gate"
echo
echo "4. Tool di gestione:"
echo "   sudo python3 $PROJECT_DIR/tools/offline_utils.py --status"
echo "   sudo python3 $PROJECT_DIR/tools/manual_open_tool.py --test"
echo "   sudo python3 $PROJECT_DIR/tools/log_viewer.py --stats"
echo

if grep -q "dtparam=spi=on" /boot/config.txt && ! lsmod | grep -q spi_bcm; then
    echo -e "${RED}⚠️ RIAVVIO NECESSARIO per attivare SPI${NC}"
    echo "   Esegui: sudo reboot"
    echo
fi

echo -e "${GREEN}🚀 Sistema pronto per l'uso!${NC}"