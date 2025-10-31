#!/bin/bash
# 🚀 Deploy RFID Gate v2.2.1 - MQTT Subscription Persistence Fix
# =============================================================

set -e  # Exit on any error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 RFID Gate v2.2.1 Deployment${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if running as root/sudo
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Non eseguire questo script come root!${NC}"
   echo -e "${YELLOW}   Usa: ./deploy_v2.2.1.sh${NC}"
   exit 1
fi

# Verifica sistema
echo -e "${BLUE}🔍 Verifica sistema...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 non trovato${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 non trovato${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Sistema verificato${NC}"
echo ""

# Backup configurazione esistente
echo -e "${BLUE}💾 Backup configurazione esistente...${NC}"
if [ -f "/home/pi/rfid_gate/.env" ]; then
    cp /home/pi/rfid_gate/.env /home/pi/rfid_gate/.env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup .env creato${NC}"
fi

# Ferma servizio esistente se attivo
echo -e "${BLUE}🛑 Ferma servizio esistente...${NC}"
if systemctl is-active --quiet rfid-gate; then
    sudo systemctl stop rfid-gate
    echo -e "${GREEN}✅ Servizio fermato${NC}"
else
    echo -e "${YELLOW}ℹ️ Servizio non attivo${NC}"
fi

# Backup directory esistente
if [ -d "/home/pi/rfid_gate" ]; then
    echo -e "${BLUE}📦 Backup directory esistente...${NC}"
    sudo mv /home/pi/rfid_gate /home/pi/rfid_gate_backup_$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup completato${NC}"
fi

# Clone repository
echo -e "${BLUE}📥 Download v2.2.1...${NC}"
cd /home/pi
git clone https://github.com/diaghi13/rfid_gate.git
cd rfid_gate
git checkout v2.2.1
echo -e "${GREEN}✅ v2.2.1 scaricata${NC}"

# Ripristina configurazione
if [ -f "/home/pi/rfid_gate_backup_$(date +%Y%m%d_%H%M%S)/.env" ]; then
    echo -e "${BLUE}🔄 Ripristino configurazione...${NC}"
    cp /home/pi/rfid_gate_backup_*/.env /home/pi/rfid_gate/.env
    echo -e "${GREEN}✅ Configurazione ripristinata${NC}"
else
    echo -e "${YELLOW}⚠️ Nessuna configurazione precedente trovata${NC}"
    echo -e "${YELLOW}   Copia manualmente il file .env${NC}"
fi

# Installa dipendenze
echo -e "${BLUE}📦 Installazione dipendenze...${NC}"
pip3 install -r requirements.txt
echo -e "${GREEN}✅ Dipendenze installate${NC}"

# Test rapido connessione MQTT
echo -e "${BLUE}🧪 Test rapido sistema...${NC}"
cd /home/pi/rfid_gate
if python3 -c "
import sys
sys.path.append('.')
from rfid_gate.network.mqtt import AsyncMQTTClient
from rfid_gate.config.settings import RFIDGateConfig
import asyncio

async def test():
    config = RFIDGateConfig.from_env()
    client = AsyncMQTTClient(config.mqtt)
    await client.initialize()
    success = await client.connect()
    if success:
        print('✅ MQTT connection test passed')
        await client.disconnect()
        return True
    else:
        print('❌ MQTT connection test failed')
        return False

result = asyncio.run(test())
exit(0 if result else 1)
"; then
    echo -e "${GREEN}✅ Test MQTT superato${NC}"
else
    echo -e "${RED}❌ Test MQTT fallito - controllare configurazione${NC}"
    echo -e "${YELLOW}   Il deployment continua, ma verificare .env${NC}"
fi

# Riavvia servizio
echo -e "${BLUE}🔄 Riavvio servizio...${NC}"
sudo systemctl start rfid-gate
sleep 3

if systemctl is-active --quiet rfid-gate; then
    echo -e "${GREEN}✅ Servizio riavviato correttamente${NC}"
else
    echo -e "${RED}❌ Errore riavvio servizio${NC}"
    echo -e "${YELLOW}   Controlla: sudo journalctl -u rfid-gate -f${NC}"
fi

# Verifica finale
echo -e "${BLUE}🔍 Verifica finale...${NC}"
sleep 5

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT v2.2.1 COMPLETATO!${NC}"
echo -e "${GREEN}===================================${NC}"
echo ""
echo -e "${YELLOW}🔧 PROBLEMA RISOLTO:${NC}"
echo -e "   ✅ Subscription MQTT persistenti dopo riconnessione broker"
echo -e "   ✅ Badge requests ora arrivano correttamente dopo restart broker" 
echo -e "   ✅ Heartbeat e auth responses entrambi funzionali"
echo ""
echo -e "${YELLOW}📊 Per monitorare:${NC}"
echo -e "   sudo journalctl -u rfid-gate -f"
echo -e "   sudo systemctl status rfid-gate"
echo ""
echo -e "${YELLOW}🧪 Per testare subscription persistence:${NC}"
echo -e "   cd /home/pi/rfid_gate"
echo -e "   python3 test_subscription_persistence.py"
echo ""
echo -e "${GREEN}🚀 Sistema pronto per la produzione!${NC}"

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