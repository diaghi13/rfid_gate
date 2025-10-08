#!/bin/bash
# 🌐 Setup Servizio Web UI per RFID Gate System

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate-webui"
SERVICE_USER="rfid"
WEBUI_PORT="8080"

echo -e "${BLUE}🌐 SETUP SERVIZIO WEB UI RFID GATE${NC}"
echo "=================================="

# Controllo privilegi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    echo "💡 Usa: sudo bash scripts/setup_webui_service.sh"
    exit 1
fi

# Funzione per mostrare help
show_help() {
    echo -e "${YELLOW}Opzioni disponibili:${NC}"
    echo "  install   - Installa e abilita servizio WebUI"
    echo "  start     - Avvia servizio WebUI"
    echo "  stop      - Ferma servizio WebUI"
    echo "  restart   - Riavvia servizio WebUI"
    echo "  status    - Stato servizio WebUI"
    echo "  enable    - Abilita avvio automatico"
    echo "  disable   - Disabilita avvio automatico"
    echo "  logs      - Visualizza log WebUI in tempo reale"
    echo "  uninstall - Rimuove servizio WebUI"
    echo
    echo -e "${YELLOW}Esempi:${NC}"
    echo "  sudo bash scripts/setup_webui_service.sh install"
    echo "  sudo bash scripts/setup_webui_service.sh status"
    echo "  sudo bash scripts/setup_webui_service.sh logs"
}

# Funzione per installare servizio WebUI
install_webui_service() {
    echo -e "${YELLOW}🌐 Installazione servizio Web UI...${NC}"
    
    # Verifica che esista directory webui
    if [ ! -d "$PROJECT_DIR/webui" ]; then
        echo -e "${RED}❌ Directory webui non trovata in $PROJECT_DIR${NC}"
        exit 1
    fi
    
    # Verifica che esista app_demo.py
    if [ ! -f "$PROJECT_DIR/webui/app_demo.py" ]; then
        echo -e "${RED}❌ File app_demo.py non trovato${NC}"
        exit 1
    fi
    
    # Rileva se c'è Nginx installato per scegliere configurazione produzione
    if command -v nginx >/dev/null 2>&1 && systemctl is-enabled nginx >/dev/null 2>&1; then
        PRODUCTION_MODE=true
        WEBUI_COMMAND="${PROJECT_DIR}/venv/bin/gunicorn -c ${PROJECT_DIR}/webui/gunicorn.conf.py webui.app_demo:app"
        echo -e "${YELLOW}🔧 Configurazione produzione con Gunicorn${NC}"
    else
        PRODUCTION_MODE=false
        WEBUI_COMMAND="${PROJECT_DIR}/venv/bin/python webui/app_demo.py"
        echo -e "${YELLOW}🧪 Configurazione sviluppo con Uvicorn${NC}" 
    fi

    # Crea file systemd service
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=RFID Gate Web UI Server
After=network.target
Wants=network.target
$([ "$PRODUCTION_MODE" = true ] && echo "After=nginx.service")

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${PROJECT_DIR}/venv/bin
ExecStart=${WEBUI_COMMAND}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# Limiti risorse
MemoryLimit=512M
CPUQuota=50%

# Sicurezza
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${PROJECT_DIR}/logs ${PROJECT_DIR}/backups
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
RestrictRealtime=yes

[Install]
WantedBy=multi-user.target
EOF

    # Ricarica systemd
    systemctl daemon-reload
    
    echo -e "${GREEN}✅ Servizio Web UI installato${NC}"
    
    # Abilita servizio
    systemctl enable ${SERVICE_NAME}
    echo -e "${GREEN}✅ Avvio automatico abilitato${NC}"
    
    # Crea directory backup se non esiste
    mkdir -p "${PROJECT_DIR}/backups/config"
    chown -R ${SERVICE_USER}:${SERVICE_USER} "${PROJECT_DIR}/backups"
    
    # Mostra stato
    show_webui_status
}

# Funzione per mostrare stato WebUI
show_webui_status() {
    echo -e "${YELLOW}📊 Stato servizio Web UI:${NC}"
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "${GREEN}🟢 Stato: ATTIVO${NC}"
        echo -e "${GREEN}🌐 URL: http://localhost:${WEBUI_PORT}${NC}"
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

# Funzione per test WebUI
test_webui() {
    echo -e "${YELLOW}🧪 Test Web UI...${NC}"
    
    if [ ! -f "$PROJECT_DIR/webui/config_manager.py" ]; then
        echo -e "${RED}❌ ConfigManager non trovato${NC}"
        return 1
    fi
    
    # Test import moduli WebUI
    cd "$PROJECT_DIR"
    if sudo -u "$SERVICE_USER" ./venv/bin/python -c "
import sys
sys.path.insert(0, 'webui')
try:
    from config_manager import ConfigManager
    cm = ConfigManager()
    config = cm.load_env_config()
    print('✅ ConfigManager funzionante')
    print(f'   Parametri caricati: {len(config)}')
    
    # Test dipendenze FastAPI
    import fastapi
    import uvicorn
    print('✅ FastAPI disponibile')
    print(f'   FastAPI versione: {fastapi.__version__}')
    
except Exception as e:
    print(f'❌ Errore: {e}')
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}✅ Test Web UI superato${NC}"
        return 0
    else
        echo -e "${RED}❌ Test Web UI fallito${NC}"
        return 1
    fi
}

# Funzione per installare dipendenze WebUI
install_webui_dependencies() {
    echo -e "${YELLOW}📦 Installazione dipendenze Web UI...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Installa dipendenze WebUI specifiche
    echo -e "${YELLOW}📦 FastAPI e dipendenze...${NC}"
    sudo -u "$SERVICE_USER" ./venv/bin/pip install fastapi uvicorn[standard] python-multipart jinja2
    
    echo -e "${YELLOW}📦 Sicurezza e autenticazione...${NC}"
    sudo -u "$SERVICE_USER" ./venv/bin/pip install python-jose[cryptography] passlib[bcrypt]
    
    echo -e "${YELLOW}📦 Utility aggiuntive...${NC}"
    sudo -u "$SERVICE_USER" ./venv/bin/pip install aiofiles
    
    echo -e "${GREEN}✅ Dipendenze Web UI installate${NC}"
}

# Funzione per rimuovere servizio
uninstall_webui_service() {
    echo -e "${YELLOW}🗑️ Rimozione servizio Web UI...${NC}"
    
    # Ferma servizio se attivo
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        systemctl stop ${SERVICE_NAME}
        echo -e "${GREEN}✅ Servizio fermato${NC}"
    fi
    
    # Disabilita servizio se abilitato
    if systemctl is-enabled --quiet ${SERVICE_NAME}; then
        systemctl disable ${SERVICE_NAME}
        echo -e "${GREEN}✅ Avvio automatico disabilitato${NC}"
    fi
    
    # Rimuovi file servizio
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        rm /etc/systemd/system/${SERVICE_NAME}.service
        systemctl daemon-reload
        echo -e "${GREEN}✅ File servizio rimosso${NC}"
    fi
}

# Main logic
case "${1:-help}" in
    install)
        install_webui_dependencies
        install_webui_service
        test_webui
        echo -e "${GREEN}🎉 Web UI installata e configurata!${NC}"
        echo -e "${BLUE}🌐 Accedi a: http://localhost:${WEBUI_PORT}${NC}"
        ;;
    start)
        systemctl start ${SERVICE_NAME}
        echo -e "${GREEN}✅ Servizio Web UI avviato${NC}"
        show_webui_status
        ;;
    stop)
        systemctl stop ${SERVICE_NAME}
        echo -e "${GREEN}✅ Servizio Web UI fermato${NC}"
        ;;
    restart)
        systemctl restart ${SERVICE_NAME}
        echo -e "${GREEN}✅ Servizio Web UI riavviato${NC}"
        show_webui_status
        ;;
    status)
        show_webui_status
        ;;
    enable)
        systemctl enable ${SERVICE_NAME}
        echo -e "${GREEN}✅ Avvio automatico abilitato${NC}"
        ;;
    disable)
        systemctl disable ${SERVICE_NAME}
        echo -e "${YELLOW}⏸️ Avvio automatico disabilitato${NC}"
        ;;
    logs)
        echo -e "${YELLOW}📋 Log Web UI (Ctrl+C per uscire):${NC}"
        journalctl -u ${SERVICE_NAME} -f
        ;;
    test)
        test_webui
        ;;
    uninstall)
        uninstall_webui_service
        echo -e "${GREEN}✅ Servizio Web UI rimosso${NC}"
        ;;
    help|*)
        show_help
        ;;
esac