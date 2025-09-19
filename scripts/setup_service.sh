#!/bin/bash
# 🔧 Setup e Gestione Servizio RFID Gate System

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
SERVICE_USER="rfid"

echo -e "${BLUE}🔧 GESTIONE SERVIZIO RFID GATE${NC}"
echo "================================"

# Controllo privilegi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    echo "💡 Usa: sudo bash scripts/setup_service.sh"
    exit 1
fi

# Funzione per mostrare help
show_help() {
    echo -e "${YELLOW}Opzioni disponibili:${NC}"
    echo "  install   - Installa e abilita servizio"
    echo "  start     - Avvia servizio"
    echo "  stop      - Ferma servizio"
    echo "  restart   - Riavvia servizio"
    echo "  status    - Stato servizio"
    echo "  enable    - Abilita avvio automatico"
    echo "  disable   - Disabilita avvio automatico"
    echo "  logs      - Visualizza log in tempo reale"
    echo "  test      - Test configurazione"
    echo "  uninstall - Rimuove servizio"
    echo
    echo -e "${YELLOW}Esempi:${NC}"
    echo "  sudo bash scripts/setup_service.sh install"
    echo "  sudo bash scripts/setup_service.sh status"
    echo "  sudo bash scripts/setup_service.sh logs"
}

# Funzione per installare servizio
install_service() {
    echo -e "${YELLOW}📦 Installazione servizio...${NC}"
    
    # Verifica che il progetto sia installato
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}❌ Directory progetto non trovata: $PROJECT_DIR${NC}"
        echo "💡 Eseguire prima: sudo bash scripts/install.sh"
        exit 1
    fi
    
    # Crea file servizio
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=RFID Gate Access Control System
Documentation=https://github.com/yourusername/rfid-gate
After=network.target network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=$PROJECT_DIR/src
ExecStartPre=/bin/sleep 5
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/main.py
ExecStop=/bin/kill -INT \$MAINPID
ExecStopPost=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/tools/emergency_stop.py all

# Restart policy
Restart=always
RestartSec=15
TimeoutStartSec=60
TimeoutStopSec=30

# Output
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rfid-gate

# Sicurezza
NoNewPrivileges=no
PrivateTmp=yes
ProtectHome=read-only
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR /dev/spidev0.0 /dev/spidev0.1 /sys/class/gpio /dev/mem
SupplementaryGroups=gpio spi

[Install]
WantedBy=multi-user.target
EOF

    # Ricarica systemd
    systemctl daemon-reload
    
    echo -e "${GREEN}✅ Servizio installato${NC}"
    
    # Abilita servizio
    systemctl enable ${SERVICE_NAME}
    echo -e "${GREEN}✅ Avvio automatico abilitato${NC}"
    
    # Mostra stato
    show_service_status
}

# Funzione per mostrare stato
show_service_status() {
    echo -e "${YELLOW}📊 Stato servizio:${NC}"
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "${GREEN}🟢 Stato: ATTIVO${NC}"
    else
        echo -e "${RED}🔴 Stato: INATTIVO${NC}"
    fi
    
    if systemctl is-enabled --quiet ${SERVICE_NAME}; then
        echo -e "${GREEN}⚡ Avvio automatico: ABILITATO${NC}"
    else
        echo -e "${YELLOW}⏸️ Avvio automatico: DISABILITATO${NC}"
    fi
    
    echo
    systemctl status ${SERVICE_NAME} --no-pager -l || true
}

# Funzione per test configurazione
test_configuration() {
    echo -e "${YELLOW}🧪 Test configurazione...${NC}"
    
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo -e "${RED}❌ File .env non trovato${NC}"
        return 1
    fi
    
    # Test caricamento Python
    cd "$PROJECT_DIR"
    if sudo -u "$SERVICE_USER" ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
try:
    from config import Config
    print('✅ Configurazione Python caricata')
    print(f'   Tornello ID: {Config.TORNELLO_ID}')
    print(f'   MQTT: {Config.MQTT_BROKER}:{Config.MQTT_PORT}')
    print(f'   Relè IN: GPIO {Config.RELAY_IN_PIN}')
    print(f'   RFID IN: RST={Config.RFID_IN_RST_PIN}, SDA={Config.RFID_IN_SDA_PIN}')
    
    # Test import moduli
    from rfid_manager import RFIDManager
    from relay_manager import RelayManager
    from mqtt_client import MQTTClient
    print('✅ Tutti i moduli importati correttamente')
    
except Exception as e:
    print(f'❌ Errore: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"; then
        echo -e "${GREEN}✅ Test configurazione OK${NC}"
        return 0
    else
        echo -e "${RED}❌ Test configurazione FALLITO${NC}"
        return 1
    fi
}

# Funzione per visualizzare log
show_logs() {
    echo -e "${YELLOW}📊 Log servizio in tempo reale...${NC}"
    echo -e "${YELLOW}Premi Ctrl+C per uscire${NC}"
    echo
    
    journalctl -fu ${SERVICE_NAME}
}

# Funzione per rimuovere servizio
uninstall_service() {
    echo -e "${YELLOW}🗑️ Rimozione servizio...${NC}"
    
    # Ferma servizio
    systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    
    # Disabilita
    systemctl disable ${SERVICE_NAME} 2>/dev/null || true
    
    # Rimuovi file
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    
    # Ricarica systemd
    systemctl daemon-reload
    systemctl reset-failed
    
    echo -e "${GREEN}✅ Servizio rimosso${NC}"
}

# Gestione argomenti
case "${1:-help}" in
    install)
        install_service
        ;;
    start)
        echo -e "${YELLOW}🚀 Avvio servizio...${NC}"
        systemctl start ${SERVICE_NAME}
        show_service_status
        ;;
    stop)
        echo -e "${YELLOW}🛑 Fermata servizio...${NC}"
        systemctl stop ${SERVICE_NAME}
        show_service_status
        ;;
    restart)
        echo -e "${YELLOW}🔄 Riavvio servizio...${NC}"
        systemctl restart ${SERVICE_NAME}
        show_service_status
        ;;
    status)
        show_service_status
        ;;
    enable)
        echo -e "${YELLOW}⚡ Abilitazione avvio automatico...${NC}"
        systemctl enable ${SERVICE_NAME}
        echo -e "${GREEN}✅ Avvio automatico abilitato${NC}"
        ;;
    disable)
        echo -e "${YELLOW}⏸️ Disabilitazione avvio automatico...${NC}"
        systemctl disable ${SERVICE_NAME}
        echo -e "${YELLOW}⏸️ Avvio automatico disabilitato${NC}"
        ;;
    logs)
        show_logs
        ;;
    test)
        test_configuration
        ;;
    uninstall)
        read -p "Rimuovere servizio $SERVICE_NAME? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            uninstall_service
        else
            echo "Operazione annullata"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opzione non valida: $1${NC}"
        echo
        show_help
        exit 1
        ;;
esac