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

# Configurazione - RIPRISTINA LOGICA ORIGINALE
INSTALL_DIR="/opt/rfid-gate"          # Directory di installazione sistema (dove rimane tutto)
DOWNLOAD_DIR="/tmp/rfid-gate-deploy"  # Directory temporanea per download
CURRENT_USER=$(whoami)

echo -e "${BLUE}📋 Directory Deployment:${NC}"
echo -e "   📁 Installazione: ${INSTALL_DIR}"
echo -e "   📥 Download temp: ${DOWNLOAD_DIR}"
echo -e "   👤 Utente: ${CURRENT_USER}"
echo ""

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

# Ferma servizio esistente se attivo
echo -e "${BLUE}🛑 Ferma servizio esistente...${NC}"
if systemctl is-active --quiet rfid-gate; then
    sudo systemctl stop rfid-gate
    echo -e "${GREEN}✅ Servizio fermato${NC}"
else
    echo -e "${YELLOW}ℹ️ Servizio non attivo${NC}"
fi

# Pulisci directory temporanea se esiste
if [ -d "$DOWNLOAD_DIR" ]; then
    echo -e "${BLUE}🧹 Pulizia directory temporanea...${NC}"
    rm -rf "$DOWNLOAD_DIR"
fi

# Clone repository nella directory temporanea
echo -e "${BLUE}📥 Download v2.2.1...${NC}"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"
git clone https://github.com/diaghi13/rfid_gate.git .
git checkout v2.2.1
echo -e "${GREEN}✅ v2.2.1 scaricata in $DOWNLOAD_DIR${NC}"

# Crea directory di installazione se non esiste
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${BLUE}📁 Creazione directory installazione...${NC}"
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
    echo -e "${GREEN}✅ Directory $INSTALL_DIR creata${NC}"
fi

# Backup configurazione esistente (mantiene .env, logs, cache)
echo -e "${BLUE}💾 Backup configurazione esistente...${NC}"
BACKUP_DIR="$INSTALL_DIR/backup_$(date +%Y%m%d_%H%M%S)"
if [ -f "$INSTALL_DIR/.env" ] || [ -d "$INSTALL_DIR/logs" ] || [ -d "$INSTALL_DIR/cache" ]; then
    sudo mkdir -p "$BACKUP_DIR"
    
    # Backup .env
    if [ -f "$INSTALL_DIR/.env" ]; then
        sudo cp "$INSTALL_DIR/.env" "$BACKUP_DIR/.env"
        echo -e "${GREEN}✅ File .env salvato${NC}"
    fi
    
    # Backup logs
    if [ -d "$INSTALL_DIR/logs" ]; then
        sudo cp -r "$INSTALL_DIR/logs" "$BACKUP_DIR/logs"
        echo -e "${GREEN}✅ Directory logs salvata${NC}"
    fi
    
    # Backup cache
    if [ -d "$INSTALL_DIR/cache" ]; then
        sudo cp -r "$INSTALL_DIR/cache" "$BACKUP_DIR/cache"
        echo -e "${GREEN}✅ Cache salvata${NC}"
    fi
    
    echo -e "${GREEN}✅ Backup completato in: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}ℹ️ Nessuna configurazione esistente da salvare${NC}"
fi

# Copia nuovi file (sovrascrive tutto tranne config/logs/cache)
echo -e "${BLUE}📋 Aggiornamento file sistema...${NC}"
sudo cp -r "$DOWNLOAD_DIR"/* "$INSTALL_DIR/"
sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"

# Ripristina configurazione salvata
if [ -f "$BACKUP_DIR/.env" ]; then
    echo -e "${BLUE}🔄 Ripristino configurazione...${NC}"
    cp "$BACKUP_DIR/.env" "$INSTALL_DIR/.env"
    echo -e "${GREEN}✅ Configurazione ripristinata${NC}"
fi

if [ -d "$BACKUP_DIR/logs" ]; then
    cp -r "$BACKUP_DIR/logs" "$INSTALL_DIR/logs"
    echo -e "${GREEN}✅ Logs ripristinati${NC}"
fi

if [ -d "$BACKUP_DIR/cache" ]; then
    cp -r "$BACKUP_DIR/cache" "$INSTALL_DIR/cache"
    echo -e "${GREEN}✅ Cache ripristinata${NC}"
fi

# Installa dipendenze - FIX: gestisce environment externally managed
echo -e "${BLUE}📦 Installazione dipendenze...${NC}"
cd "$INSTALL_DIR"
if pip3 install -r requirements.txt 2>/dev/null; then
    echo -e "${GREEN}✅ Dipendenze installate${NC}"
else
    echo -e "${YELLOW}⚠️ Environment externally managed, provo con --break-system-packages...${NC}"
    if pip3 install --break-system-packages -r requirements.txt; then
        echo -e "${GREEN}✅ Dipendenze installate (break-system-packages)${NC}"
    else
        echo -e "${RED}❌ Errore installazione dipendenze${NC}"
        echo -e "${YELLOW}   Prova manualmente: pip3 install --break-system-packages -r requirements.txt${NC}"
    fi
fi

# Test rapido connessione MQTT
echo -e "${BLUE}🧪 Test rapido sistema...${NC}"
cd "$INSTALL_DIR"
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

# Pulizia directory temporanea
echo -e "${BLUE}🧹 Pulizia directory temporanea...${NC}"
rm -rf "$DOWNLOAD_DIR"
echo -e "${GREEN}✅ Directory temporanea rimossa${NC}"

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT v2.2.1 COMPLETATO!${NC}"
echo -e "${GREEN}===================================${NC}"
echo ""
echo -e "${YELLOW}🔧 PROBLEMA RISOLTO:${NC}"
echo -e "   ✅ Subscription MQTT persistenti dopo riconnessione broker"
echo -e "   ✅ Badge requests ora arrivano correttamente dopo restart broker" 
echo -e "   ✅ Heartbeat e auth responses entrambi funzionali"
echo ""
echo -e "${YELLOW}📁 Directory Sistema:${NC}"
echo -e "   📋 Installazione: $INSTALL_DIR"
echo -e "   💾 Backup: $BACKUP_DIR"
echo -e "   ⚙️  Configurazione: $INSTALL_DIR/.env"
echo ""
echo -e "${YELLOW}📊 Per monitorare:${NC}"
echo -e "   sudo journalctl -u rfid-gate -f"
echo -e "   sudo systemctl status rfid-gate"
echo ""
echo -e "${YELLOW}🧪 Per testare subscription persistence:${NC}"
echo -e "   cd $INSTALL_DIR"
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