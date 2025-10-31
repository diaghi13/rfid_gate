#!/bin/bash
"""
🔍 Analizzatore Log RFID Gate
============================

Script per raccogliere e analizzare i log completi del sistema
per identificare la causa dei crash.

Uso:
    bash debug_logs.sh
"""

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=============================================="
echo "🔍 Debug Log RFID Gate"
echo "=============================================="
echo -e "${NC}"

SERVICE_NAME="rfid-gate"
LOG_FILE="/tmp/rfid-gate-debug.log"

echo -e "${YELLOW}📋 Raccolta log completi...${NC}"

# Ferma servizio per analisi pulita
echo -e "🛑 Fermo servizio per analisi..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
sleep 2

# Raccoglie log recenti
echo -e "📄 Raccolta ultimi 200 log..."
sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 200 > "$LOG_FILE"

echo -e "🔍 Analisi errori..."

# Cerca errori specifici
echo -e "\n${RED}=== ERRORI CRITICI ===${NC}"
grep -i "error\|exception\|traceback\|failed" "$LOG_FILE" | tail -20

echo -e "\n${RED}=== RUNTIME WARNINGS ===${NC}"
grep -i "runtimewarning\|never awaited" "$LOG_FILE" | tail -10

echo -e "\n${RED}=== ERRORI MQTT ===${NC}"
grep -i "mqtt.*error\|connection.*refused\|reconnect.*fail" "$LOG_FILE" | tail -10

echo -e "\n${RED}=== ERRORI IMPORT/MODULE ===${NC}"
grep -i "import.*error\|modulenotfound\|no module named" "$LOG_FILE" | tail -10

echo -e "\n${RED}=== EXIT CODES ===${NC}"
grep -i "exit.*code\|status.*failure" "$LOG_FILE" | tail -10

echo -e "\n${YELLOW}=== SEQUENZA ULTIMA ESECUZIONE ===${NC}"
echo -e "Ultimi 30 log prima del crash:"
tail -30 "$LOG_FILE"

echo -e "\n${BLUE}=== INFORMAZIONI SISTEMA ===${NC}"
echo -e "📊 Stato attuale servizio:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -15

echo -e "\n📁 Verifica file critici:"
PROD_DIR="/opt/rfid-gate"

if [ -f "$PROD_DIR/main.py" ]; then
    echo -e "  ✅ main.py presente"
else
    echo -e "  ❌ main.py MANCANTE"
fi

if [ -f "$PROD_DIR/rfid_gate/__init__.py" ]; then
    version=$(grep "__version__" "$PROD_DIR/rfid_gate/__init__.py" 2>/dev/null | cut -d'"' -f2 || echo "unknown")
    echo -e "  ✅ rfid_gate modulo presente (v$version)"
else
    echo -e "  ❌ rfid_gate modulo MANCANTE"
fi

if [ -f "$PROD_DIR/.env" ]; then
    echo -e "  ✅ Configurazione presente"
else
    echo -e "  ❌ Configurazione MANCANTE"
fi

echo -e "\n📁 Permessi:"
ls -la "$PROD_DIR/" | head -5

echo -e "\n🐍 Test Python environment:"
cd "$PROD_DIR"
if sudo -u rfid bash -c "source venv/bin/activate && python --version" 2>/dev/null; then
    echo -e "  ✅ Python environment OK"
else
    echo -e "  ❌ Python environment PROBLEM"
fi

echo -e "\n🧪 Test import base:"
if sudo -u rfid bash -c "source venv/bin/activate && cd $PROD_DIR && python -c 'import sys; print(sys.path)'" 2>/dev/null; then
    echo -e "  ✅ Python path OK"
else
    echo -e "  ❌ Python path PROBLEM"
fi

# Test manuale
echo -e "\n${YELLOW}🧪 TEST MANUALE${NC}"
echo -e "Per testare manualmente:"
echo -e "  cd $PROD_DIR"
echo -e "  sudo -u rfid bash -c 'source venv/bin/activate && python main.py'"

echo -e "\n${GREEN}📄 Log completi salvati in: $LOG_FILE${NC}"
echo -e "Per vedere: cat $LOG_FILE"

echo -e "\n${BLUE}=============================================="
echo "🏁 Analisi completata"
echo "=============================================="
echo -e "${NC}"