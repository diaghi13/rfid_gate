# ========================================
# 📄 scripts/start.sh - Avvio Manuale Sistema
# ========================================
#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"
SERVICE_USER="rfid"

echo -e "${BLUE}🚀 AVVIO MANUALE RFID GATE${NC}"
echo "=========================="

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    exit 1
fi

# Controllo se servizio è attivo
if systemctl is-active --quiet rfid-gate; then
    echo -e "${YELLOW}⚠️ Servizio systemd già attivo${NC}"
    echo "   Per fermare: sudo systemctl stop rfid-gate"
    exit 1
fi

# Verifica installazione
if [ ! -d "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ Sistema non installato correttamente${NC}"
    echo "💡 Eseguire: sudo bash scripts/install.sh"
    exit 1
fi

echo -e "${YELLOW}📋 Avvio sistema...${NC}"
cd "$PROJECT_DIR"

# Avvia come utente rfid
sudo -u "$SERVICE_USER" ./venv/bin/python main.py

# ========================================
# 📄 scripts/stop.sh - Stop Sistema
# ========================================
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 STOP RFID GATE SYSTEM${NC}"
echo "======================="

# Stop servizio se attivo
if systemctl is-active --quiet rfid-gate 2>/dev/null; then
    echo -e "${YELLOW}🛑 Fermata servizio systemd...${NC}"
    sudo systemctl stop rfid-gate
fi

# Trova processi Python del sistema
PIDS=$(pgrep -f "python.*main.py" 2>/dev/null || true)

if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}🛑 Fermata processi manuali...${NC}"
    for PID in $PIDS; do
        echo "   Fermando PID $PID"
        kill -INT "$PID" 2>/dev/null || kill -TERM "$PID" 2>/dev/null || true
    done
    
    # Aspetta terminazione
    sleep 2
    
    # Force kill se necessario
    REMAINING=$(pgrep -f "python.*main.py" 2>/dev/null || true)
    if [ -n "$REMAINING" ]; then
        echo -e "${YELLOW}⚡ Force kill processi rimanenti...${NC}"
        pkill -9 -f "python.*main.py" 2>/dev/null || true
    fi
fi

# Emergency stop relè
if [ -f "/opt/rfid-gate/tools/emergency_stop.py" ]; then
    echo -e "${YELLOW}🚨 Emergency stop relè...${NC}"
    cd /opt/rfid-gate
    sudo ./venv/bin/python tools/emergency_stop.py all 2>/dev/null || true
fi

echo -e "${GREEN}✅ Sistema fermato${NC}"

# ========================================
# 📄 scripts/update.sh - Aggiornamento Sistema
# ========================================
#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"
SERVICE_USER="rfid"
BACKUP_DIR="/opt/rfid-gate-backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}🔄 AGGIORNAMENTO RFID GATE SYSTEM${NC}"
echo "================================"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    exit 1
fi

# Backup configurazione
echo -e "${YELLOW}💾 Backup configurazione...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    cp -r "$PROJECT_DIR" "$BACKUP_DIR/"
    echo -e "${GREEN}✅ Backup salvato in: $BACKUP_DIR${NC}"
fi

# Ferma servizio
echo -e "${YELLOW}🛑 Fermata servizio...${NC}"
systemctl stop rfid-gate 2>/dev/null || true

# Aggiorna codice (assumendo che sia in directory corrente)
echo -e "${YELLOW}📦 Aggiornamento file sistema...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Backup e aggiorna src
if [ -d "$SCRIPT_DIR/src" ]; then
    cp -r "$SCRIPT_DIR/src" "$PROJECT_DIR/"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/src"
    echo -e "${GREEN}✅ Codice sorgente aggiornato${NC}"
fi

# Aggiorna tools
if [ -d \"$SCRIPT_DIR/tools\" ]; then
    mkdir -p \"$PROJECT_DIR/tools\"
    cp -r \"$SCRIPT_DIR/tools\"/* \"$PROJECT_DIR/tools/\" 2>/dev/null || true
    chown -R \"$SERVICE_USER:$SERVICE_USER\" \"$PROJECT_DIR/tools\"
    chmod +x \"$PROJECT_DIR/tools\"/*.py
    echo -e "${GREEN}✅ Tools aggiornati${NC}"
fi

# Aggiorna dipendenze se necessario
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo -e "${YELLOW}📦 Aggiornamento dipendenze Python...${NC}"
    cp "$SCRIPT_DIR/requirements.txt" "$PROJECT_DIR/"
    cd "$PROJECT_DIR"
    sudo -u "$SERVICE_USER" ./venv/bin/pip install -r requirements.txt --upgrade
    echo -e "${GREEN}✅ Dipendenze aggiornate${NC}"
fi

# Mantieni configurazione esistente
if [ -f "$BACKUP_DIR/opt/rfid-gate/.env" ] && [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$BACKUP_DIR/opt/rfid-gate/.env" "$PROJECT_DIR/"
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
    echo -e "${GREEN}✅ Configurazione ripristinata${NC}"
fi

# Test configurazione
echo -e "${YELLOW}🧪 Test configurazione...${NC}"
cd "$PROJECT_DIR"
if sudo -u "$SERVICE_USER" ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
from config import Config
print('✅ Configurazione OK')
"; then
    echo -e "${GREEN}✅ Test configurazione superato${NC}"
else
    echo -e "${RED}❌ Errore configurazione${NC}"
    echo -e "${YELLOW}💡 Ripristinando backup...${NC}"
    rm -rf "$PROJECT_DIR"
    mv "$BACKUP_DIR/opt/rfid-gate" "$PROJECT_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    exit 1
fi

# Riavvia servizio
echo -e "${YELLOW}🚀 Riavvio servizio...${NC}"
systemctl daemon-reload
systemctl start rfid-gate

# Verifica stato
sleep 3
if systemctl is-active --quiet rfid-gate; then
    echo -e "${GREEN}✅ Servizio riavviato correttamente${NC}"
else
    echo -e "${RED}❌ Errore riavvio servizio${NC}"
    systemctl status rfid-gate --no-pager
    exit 1
fi

echo -e "${GREEN}🎉 AGGIORNAMENTO COMPLETATO!${NC}"
echo -e "${YELLOW}💾 Backup disponibile in: $BACKUP_DIR${NC}"

# ========================================
# 📄 scripts/backup.sh - Backup Sistema
# ========================================
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"
BACKUP_BASE_DIR="/opt/rfid-gate-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="$BACKUP_BASE_DIR/backup-$TIMESTAMP"

echo -e "${BLUE}💾 BACKUP RFID GATE SYSTEM${NC}"
echo "========================="

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Eseguire come root${NC}"
    exit 1
fi

# Crea directory backup
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📦 Creazione backup...${NC}"

# Backup configurazione
if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$BACKUP_DIR/"
    echo "✅ Configurazione salvata"
fi

# Backup log
if [ -d "$PROJECT_DIR/logs" ]; then
    cp -r "$PROJECT_DIR/logs" "$BACKUP_DIR/"
    echo "✅ Log salvati"
fi

# Backup configurazioni personalizzate
if [ -d "$PROJECT_DIR/config" ]; then
    cp -r "$PROJECT_DIR/config" "$BACKUP_DIR/"
    echo "✅ Configurazioni personalizzate salvate"
fi

# Comprimi backup
cd "$BACKUP_BASE_DIR"
tar -czf "backup-$TIMESTAMP.tar.gz" "backup-$TIMESTAMP/"
rm -rf "backup-$TIMESTAMP"

echo -e "${GREEN}✅ Backup completato: $BACKUP_BASE_DIR/backup-$TIMESTAMP.tar.gz${NC}"

# Pulizia backup vecchi (mantieni ultimi 10)
echo -e "${YELLOW}🧹 Pulizia backup vecchi...${NC}"
cd "$BACKUP_BASE_DIR"
ls -t backup-*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
echo "✅ Cleanup completato"

# ========================================
# 📄 scripts/monitor.sh - Monitor Sistema
# ========================================
#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="/opt/rfid-gate"

echo -e "${BLUE}👁️ MONITOR RFID GATE SYSTEM${NC}"
echo "=========================="

show_system_status() {
    echo -e "${YELLOW}📊 Stato Sistema:${NC}"
    
    # Stato servizio
    if systemctl is-active --quiet rfid-gate; then
        echo -e "   🟢 Servizio: ATTIVO"
    else
        echo -e "   🔴 Servizio: INATTIVO"
    fi
    
    # Uptime servizio
    if systemctl is-active --quiet rfid-gate; then
        UPTIME=$(systemctl show rfid-gate --property=ActiveEnterTimestamp | cut -d= -f2)
        echo -e "   ⏱️ Avviato: $UPTIME"
    fi
    
    # Memoria
    if pgrep -f "python.*main.py" > /dev/null; then
        PID=$(pgrep -f "python.*main.py")
        MEMORY=$(ps -p "$PID" -o rss= 2>/dev/null | awk '{print int($1/1024)"MB"}' || echo "N/A")
        echo -e "   💾 Memoria: $MEMORY"
    fi
    
    # Spazio disco log
    if [ -d "$PROJECT_DIR/logs" ]; then
        LOG_SIZE=$(du -sh "$PROJECT_DIR/logs" 2>/dev/null | cut -f1 || echo "N/A")
        echo -e "   📊 Log size: $LOG_SIZE"
    fi
    
    echo
}

# Mostra stato iniziale
show_system_status

# Monitor continuo
if [ "${1:-}" = "--continuous" ] || [ "${1:-}" = "-c" ]; then
    echo -e "${YELLOW}🔄 Monitoring continuo (Ctrl+C per uscire)...${NC}"
    echo
    
    while true; do
        clear
        echo -e "${BLUE}👁️ MONITOR RFID GATE SYSTEM${NC}"
        echo "=========================="
        echo -e "${YELLOW}$(date)${NC}"
        echo
        
        show_system_status
        
        # Ultimi log
        echo -e "${YELLOW}📋 Ultimi eventi:${NC}"
        if [ -f "$PROJECT_DIR/logs/system.log" ]; then
            tail -n 5 "$PROJECT_DIR/logs/system.log" | while read line; do
                echo "   $line"
            done
        else
            journalctl -u rfid-gate --no-pager -n 5 | tail -n +2
        fi
        
        sleep 5
    done
else
    echo -e "${YELLOW}💡 Per monitoring continuo: sudo bash scripts/monitor.sh --continuous${NC}"
fi