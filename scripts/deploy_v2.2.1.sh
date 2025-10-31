#!/bin/bash
# ===========================================
# 🚀 RFID Gate - Deploy Release v2.2.1
# ===========================================
#
# Script rapido per deployare la release v2.2.1 su Raspberry Pi
# Scarica automaticamente l'ultima release da GitHub e aggiorna
#
# Uso: 
#   sudo bash deploy_v2.2.1.sh
#   curl -fsSL https://raw.githubusercontent.com/diaghi13/rfid_gate/v2.2.1/scripts/deploy_v2.2.1.sh | sudo bash
#
# Autore: Sistema RFID Gate v2.2.1
# Data: 30 ottobre 2025

set -e

# Configurazione
VERSION="v2.2.1"
REPO_URL="https://github.com/diaghi13/rfid_gate.git"
REPO_DIR="$HOME/rfid-gate"
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=================================================="
echo "🚀 RFID Gate - Deploy Release $VERSION"
echo "=================================================="
echo -e "${NC}"

# Verifica permessi root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root: sudo bash deploy_v2.2.1.sh${NC}"
    exit 1
fi

# Funzione per clonare o aggiornare repository
setup_repository() {
    echo -e "${YELLOW}📡 Setup repository...${NC}"
    
    if [ -d "$REPO_DIR" ]; then
        echo "  🔄 Aggiorno repository esistente..."
        cd "$REPO_DIR"
        git fetch origin
        git checkout $VERSION
        git pull origin $VERSION 2>/dev/null || true
    else
        echo "  📥 Clono repository..."
        git clone "$REPO_URL" "$REPO_DIR"
        cd "$REPO_DIR"
        git checkout $VERSION
    fi
    
    echo -e "${GREEN}✅ Repository $VERSION pronta in: $REPO_DIR${NC}"
}

# Funzione per installazione nuova
fresh_install() {
    echo -e "${YELLOW}🔧 Nuova installazione...${NC}"
    
    cd "$REPO_DIR"
    if [ -f "scripts/install.sh" ]; then
        bash scripts/install.sh
        echo -e "${GREEN}✅ Installazione completata${NC}"
    else
        echo -e "${RED}❌ Script di installazione non trovato${NC}"
        exit 1
    fi
}

# Funzione per aggiornamento esistente
update_existing() {
    echo -e "${YELLOW}🔄 Aggiornamento installazione esistente...${NC}"
    
    cd "$REPO_DIR"
    if [ -f "scripts/update_production.sh" ]; then
        bash scripts/update_production.sh
        echo -e "${GREEN}✅ Aggiornamento completato${NC}"
    else
        echo -e "${RED}❌ Script di aggiornamento non trovato${NC}"
        exit 1
    fi
}

# Funzione per verifica post-deploy
verify_deployment() {
    echo -e "${YELLOW}🧪 Verifica deployment...${NC}"
    
    # Verifica servizio
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Servizio attivo${NC}"
    else
        echo -e "${YELLOW}⚠️ Servizio non attivo${NC}"
        systemctl status "$SERVICE_NAME" --no-pager
    fi
    
    # Verifica versione
    if [ -f "$PROD_DIR/rfid_gate/__init__.py" ]; then
        version=$(grep "__version__" "$PROD_DIR/rfid_gate/__init__.py" | cut -d'"' -f2)
        echo -e "${BLUE}📋 Versione installata: $version${NC}"
    fi
    
    # Verifica configurazione
    if [ -f "$PROD_DIR/.env" ]; then
        echo -e "${GREEN}✅ Configurazione presente${NC}"
    else
        echo -e "${YELLOW}⚠️ Configurazione da completare${NC}"
    fi
}

# Main
main() {
    echo -e "${BLUE}🎯 Deploy Release $VERSION in corso...${NC}"
    
    # Setup repository
    setup_repository
    
    # Verifica se è installazione nuova o aggiornamento
    if [ -d "$PROD_DIR" ]; then
        echo -e "${BLUE}📋 Installazione esistente trovata${NC}"
        update_existing
    else
        echo -e "${BLUE}📋 Nuova installazione${NC}"
        fresh_install
    fi
    
    # Verifica deployment
    verify_deployment
    
    # Riepilogo finale
    echo ""
    echo -e "${GREEN}"
    echo "=================================================="
    echo "✅ DEPLOY $VERSION COMPLETATO!"
    echo "=================================================="
    echo -e "${NC}"
    echo -e "${BLUE}📋 Informazioni:${NC}"
    echo "  🗂️ Repository: $REPO_DIR"
    echo "  🏭 Produzione: $PROD_DIR"
    echo "  🔄 Servizio: $(systemctl is-active $SERVICE_NAME 2>/dev/null || echo 'inactive')"
    echo ""
    echo -e "${YELLOW}🔗 Comandi utili:${NC}"
    echo "  📊 Stato: sudo systemctl status $SERVICE_NAME"
    echo "  📋 Log: sudo journalctl -fu $SERVICE_NAME"
    echo "  🌐 WebUI: http://$(hostname -I | awk '{print $1}'):8080"
    echo "  ⚙️ Config: sudo nano $PROD_DIR/.env"
    echo ""
    
    # Mostra note release se presente
    if [ -f "$REPO_DIR/CHANGELOG.md" ]; then
        echo -e "${BLUE}📝 Note release $VERSION:${NC}"
        echo "  - Independent Relay Patch per thread-safe operations"
        echo "  - Enhanced MQTT resilience con auto-reconnection"
        echo "  - UID normalization utility per robust card handling"
        echo "  - Hardware resilience fixes per power-cycle recovery"
        echo "  - Production-ready con enhanced error handling"
    fi
}

# Esegui deploy
main "$@"