#!/bin/bash
# ===========================================
# 🔄 RFID Gate - Ripristino Manuale Sistema
# ===========================================
#
# Script per ripristino manuale da backup specifico
# Uso: ./restore_backup.sh /path/to/backup/directory
#
# Autore: Sistema RFID Gate v2.0.0
# Data: 16 ottobre 2025

set -e

# Configurazione
PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"
SERVICE_USER="rfid"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verifica parametri
if [[ $# -ne 1 ]]; then
    echo -e "${RED}❌ Uso: $0 /path/to/backup/directory${NC}"
    echo -e "${YELLOW}💡 Esempio: $0 /opt/rfid-gate/backups/production_update_20251016_123456${NC}"
    exit 1
fi

BACKUP_DIR="$1"

# Banner
echo -e "${BLUE}"
echo "=================================================="
echo "🔄 RFID Gate - Ripristino Manuale Sistema"
echo "=================================================="
echo -e "${NC}"

# Verifica backup directory
if [[ ! -d "$BACKUP_DIR" ]]; then
    echo -e "${RED}❌ Directory backup non trovata: $BACKUP_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Directory backup: $BACKUP_DIR${NC}"
echo -e "${YELLOW}🎯 Destinazione: $PROD_DIR${NC}"
echo ""

# Mostra contenuto backup
echo -e "${BLUE}📦 Contenuto backup:${NC}"
ls -la "$BACKUP_DIR"
echo ""

# Conferma
read -p "🚨 ATTENZIONE: Questo ripristinerà TUTTO il sistema. Continuare? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚫 Ripristino annullato${NC}"
    exit 0
fi

# Stop servizio
echo -e "${YELLOW}⏹️ Fermo il servizio...${NC}"
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Ripristina codice sorgente
echo -e "${BLUE}🔧 Ripristino codice sorgente...${NC}"

if [[ -d "$BACKUP_DIR/rfid_gate" ]]; then
    sudo rm -rf "$PROD_DIR/rfid_gate" 2>/dev/null || true
    sudo cp -r "$BACKUP_DIR/rfid_gate" "$PROD_DIR/"
    echo "  ✅ Ripristinato rfid_gate/"
fi

if [[ -f "$BACKUP_DIR/main.py" ]]; then
    sudo cp "$BACKUP_DIR/main.py" "$PROD_DIR/"
    echo "  ✅ Ripristinato main.py"
fi

if [[ -d "$BACKUP_DIR/webui" ]]; then
    # Preserva uploads attuali se esistono
    if [[ -d "$PROD_DIR/webui/uploads" ]]; then
        sudo mv "$PROD_DIR/webui/uploads" "/tmp/current_uploads_backup" 2>/dev/null || true
    fi
    
    sudo rm -rf "$PROD_DIR/webui" 2>/dev/null || true
    sudo cp -r "$BACKUP_DIR/webui" "$PROD_DIR/"
    
    # Ripristina uploads attuali
    if [[ -d "/tmp/current_uploads_backup" ]]; then
        sudo rm -rf "$PROD_DIR/webui/uploads" 2>/dev/null || true
        sudo mv "/tmp/current_uploads_backup" "$PROD_DIR/webui/uploads"
    fi
    echo "  ✅ Ripristinato webui/ (uploads preservati)"
fi

if [[ -d "$BACKUP_DIR/tools" ]]; then
    sudo rm -rf "$PROD_DIR/tools" 2>/dev/null || true
    sudo cp -r "$BACKUP_DIR/tools" "$PROD_DIR/"
    echo "  ✅ Ripristinato tools/"
fi

# Ripristina configurazioni e dati
echo -e "${BLUE}🗂️ Ripristino configurazioni e dati...${NC}"

if [[ -f "$BACKUP_DIR/.env" ]]; then
    sudo cp "$BACKUP_DIR/.env" "$PROD_DIR/" 2>/dev/null || true
    echo "  ✅ Ripristinato .env"
fi

if [[ -d "$BACKUP_DIR/logs" ]]; then
    sudo rm -rf "$PROD_DIR/logs" 2>/dev/null || true
    sudo cp -r "$BACKUP_DIR/logs" "$PROD_DIR/" 2>/dev/null || true
    echo "  ✅ Ripristinati logs"
fi

if [[ -d "$BACKUP_DIR/cache" ]]; then
    sudo rm -rf "$PROD_DIR/cache" 2>/dev/null || true
    sudo cp -r "$BACKUP_DIR/cache" "$PROD_DIR/" 2>/dev/null || true
    echo "  ✅ Ripristinata cache"
fi

if [[ -d "$BACKUP_DIR/config" ]]; then
    sudo rm -rf "$PROD_DIR/config" 2>/dev/null || true
    sudo cp -r "$BACKUP_DIR/config" "$PROD_DIR/" 2>/dev/null || true
    echo "  ✅ Ripristinate configurazioni"
fi

# Ripristina permessi
echo -e "${YELLOW}🔐 Ripristino permessi...${NC}"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROD_DIR"
sudo chmod +x "$PROD_DIR/scripts"/*.sh 2>/dev/null || true
sudo chmod +x "$PROD_DIR/tools"/*.py 2>/dev/null || true

# Riavvia servizio
echo -e "${GREEN}🚀 Riavvio servizio...${NC}"
sudo systemctl start "$SERVICE_NAME"
sleep 2

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Servizio riavviato con successo${NC}"
    
    # Mostra stato
    echo -e "${BLUE}📊 Stato servizio:${NC}"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
else
    echo -e "${RED}❌ ERRORE: Servizio non si avvia!${NC}"
    echo -e "${YELLOW}📋 Log errori:${NC}"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 20
fi

echo ""
echo -e "${GREEN}"
echo "=================================================="
echo "✅ RIPRISTINO COMPLETATO"
echo "=================================================="
echo -e "${NC}"
echo -e "${BLUE}📋 Sistema ripristinato da: $BACKUP_DIR${NC}"
echo -e "${YELLOW}🔗 Comandi utili:${NC}"
echo "  📊 Stato: sudo systemctl status $SERVICE_NAME"
echo "  📋 Log: sudo journalctl -u $SERVICE_NAME -f"
echo "  🌐 WebUI: http://$(hostname -I | awk '{print $1}'):8080"