#!/bin/bash
# 🔄 Script di Aggiornamento RFID Gate System
# Aggiorna un'installazione esistente preservando le configurazioni

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"

echo -e "${BLUE}🔄 AGGIORNAMENTO RFID GATE SYSTEM${NC}"
echo "=================================="

# Verifica root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root: sudo bash scripts/update.sh${NC}"
    exit 1
fi

# Verifica installazione esistente
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Installazione non trovata in $PROJECT_DIR${NC}"
    echo "💡 Esegui prima: sudo bash scripts/install.sh"
    exit 1
fi

echo -e "${YELLOW}📋 Controllo installazione esistente...${NC}"

# Backup configurazione
echo -e "${YELLOW}💾 Backup configurazioni...${NC}"
BACKUP_DIR="/tmp/rfid-gate-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$BACKUP_DIR/"
    echo -e "${GREEN}✅ Backup .env creato${NC}"
fi

if [ -f "$PROJECT_DIR/offline_queue.json" ]; then
    cp "$PROJECT_DIR/offline_queue.json" "$BACKUP_DIR/"
    echo -e "${GREEN}✅ Backup dati offline creato${NC}"
fi

if [ -d "$PROJECT_DIR/logs" ]; then
    cp -r "$PROJECT_DIR/logs" "$BACKUP_DIR/"
    echo -e "${GREEN}✅ Backup logs creato${NC}"
fi

echo "📁 Backup salvato in: $BACKUP_DIR"

# Ferma servizio se attivo
if systemctl is-active --quiet rfid-gate 2>/dev/null; then
    echo -e "${YELLOW}🛑 Fermata servizio...${NC}"
    systemctl stop rfid-gate
    SERVICE_WAS_RUNNING=true
else
    SERVICE_WAS_RUNNING=false
fi

# Aggiorna file sorgente - ARCHITETTURA REFACTORIZZATA
echo -e "${YELLOW}📋 Aggiornamento architettura modulare...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Aggiorna rfid_gate/ (nuova architettura modulare)
if [ -d "$SCRIPT_DIR/rfid_gate" ]; then
    if [ -d "$PROJECT_DIR/rfid_gate" ]; then
        rm -rf "$PROJECT_DIR/rfid_gate"
    fi
    cp -r "$SCRIPT_DIR/rfid_gate" "$PROJECT_DIR/"
    echo -e "${GREEN}✅ Modulo rfid_gate aggiornato${NC}"
fi

# Aggiorna main.py (nuovo entry point)
if [ -f "$SCRIPT_DIR/main.py" ]; then
    cp "$SCRIPT_DIR/main.py" "$PROJECT_DIR/"
    echo -e "${GREEN}✅ Main entry point aggiornato${NC}"
fi

# Rimuovi src/ obsoleto se esiste
if [ -d "$PROJECT_DIR/src" ]; then
    echo -e "${YELLOW}🗑️ Rimozione directory src/ obsoleta...${NC}"
    rm -rf "$PROJECT_DIR/src"
    echo -e "${GREEN}✅ Directory obsoleta rimossa${NC}"
fi

# Aggiorna tools/
if [ -d "$SCRIPT_DIR/tools" ]; then
    cp -r "$SCRIPT_DIR/tools"/* "$PROJECT_DIR/tools/" 2>/dev/null || true
fi

# Copia file mancanti da src/ a tools/
TOOL_FILES=(
    "src/offline_utils.py"
    "src/manual_open_tool.py"
    "src/log_viewer.py"
    "src/emergency_stop.py"
)

for tool_file in "${TOOL_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$tool_file" ]; then
        cp "$SCRIPT_DIR/$tool_file" "$PROJECT_DIR/tools/"
    fi
done

echo -e "${GREEN}✅ Tool aggiornati${NC}"

# Aggiorna scripts/
if [ -d "$SCRIPT_DIR/scripts" ]; then
    cp -r "$SCRIPT_DIR/scripts"/* "$PROJECT_DIR/scripts/" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/scripts"/*.sh 2>/dev/null || true
    echo -e "${GREEN}✅ Script aggiornati${NC}"
fi

# Crea directory mancanti
mkdir -p "$PROJECT_DIR/config/examples"
mkdir -p "$PROJECT_DIR/docs"

# Aggiorna file configurazione esempio
CONFIG_FILES=(
    "config/examples/bidirezionale.env"
    "config/examples/unidirezionale.env"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$config_file" ]; then
        target_dir="$PROJECT_DIR/$(dirname "$config_file")"
        mkdir -p "$target_dir"
        cp "$SCRIPT_DIR/$config_file" "$target_dir/"
        echo -e "${GREEN}✅ Aggiornato $config_file${NC}"
    fi
done

# Aggiorna documentazione
DOC_FILES=(
    "docs/CONFIGURATION_EXAMPLES.md"
    "docs/MANUAL_CONTROL.md"
    "docs/OFFLINE_SYSTEM.md"
    "README.md"
    "readme_complete.md"
)

for doc_file in "${DOC_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$doc_file" ]; then
        target_dir="$PROJECT_DIR/$(dirname "$doc_file")"
        mkdir -p "$target_dir"
        cp "$SCRIPT_DIR/$doc_file" "$target_dir/"
        echo -e "${GREEN}✅ Aggiornato $doc_file${NC}"
    fi
done

# Aggiorna requirements.txt se necessario
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    if ! cmp -s "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/requirements.txt" 2>/dev/null; then
        cp "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"
        echo -e "${YELLOW}📦 Aggiornamento dipendenze Python...${NC}"
        cd "$PROJECT_DIR"
        sudo -u rfid ./venv/bin/pip install -r requirements.txt
        echo -e "${GREEN}✅ Dipendenze aggiornate${NC}"
    fi
fi

# Ripristina configurazione
echo -e "${YELLOW}⚙️ Ripristino configurazioni...${NC}"
if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" "$PROJECT_DIR/"
    echo -e "${GREEN}✅ Configurazione ripristinata${NC}"
fi

if [ -f "$BACKUP_DIR/offline_queue.json" ]; then
    cp "$BACKUP_DIR/offline_queue.json" "$PROJECT_DIR/"
    echo -e "${GREEN}✅ Dati offline ripristinati${NC}"
fi

# Imposta permessi
chown -R rfid:rfid "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/scripts"/*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/tools"/*.py 2>/dev/null || true

# Ricarica servizio systemd
systemctl daemon-reload

# Riavvia servizio se era attivo
if [ "$SERVICE_WAS_RUNNING" = true ]; then
    echo -e "${YELLOW}🚀 Riavvio servizio...${NC}"
    systemctl start rfid-gate
    
    # Verifica avvio
    sleep 3
    if systemctl is-active --quiet rfid-gate; then
        echo -e "${GREEN}✅ Servizio riavviato correttamente${NC}"
    else
        echo -e "${RED}❌ Errore riavvio servizio${NC}"
        echo "🔍 Controlla: sudo journalctl -fu rfid-gate"
    fi
fi

# Test rapido configurazione - ARCHITETTURA REFACTORIZZATA
echo -e "${YELLOW}🧪 Test configurazione...${NC}"
cd "$PROJECT_DIR"
if sudo -u rfid ./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
try:
    from rfid_gate.config.settings import RFIDGateConfig
    config = RFIDGateConfig()
    print('✅ Configurazione OK')
except Exception as e:
    print(f'❌ Errore: {e}')
    exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✅ Test configurazione OK${NC}"
else
    echo -e "${YELLOW}⚠️ Possibili problemi configurazione - Verifica manuale richiesta${NC}"
fi

echo -e "${GREEN}🎉 AGGIORNAMENTO COMPLETATO!${NC}"
echo "============================"
echo
echo -e "${BLUE}📁 Directory progetto:${NC} $PROJECT_DIR"
echo -e "${BLUE}💾 Backup salvato in:${NC} $BACKUP_DIR"
echo
echo -e "${YELLOW}🔧 Comandi utili:${NC}"
echo "• Stato servizio: sudo systemctl status rfid-gate"
echo "• Log in tempo reale: sudo journalctl -fu rfid-gate"
echo "• Test manuale: cd $PROJECT_DIR && sudo ./venv/bin/python src/main.py"
echo "• Configurazione: sudo nano $PROJECT_DIR/.env"