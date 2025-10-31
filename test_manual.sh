#!/bin/bash
"""
🧪 Test Manuale RFID Gate
=========================

Script per testare manualmente il sistema e identificare errori.
Esegue il main.py direttamente per vedere gli errori completi.

Uso sul Raspberry Pi:
    bash test_manual.sh
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
echo "🧪 Test Manuale RFID Gate"
echo "=============================================="
echo -e "${NC}"

PROD_DIR="/opt/rfid-gate"
SERVICE_NAME="rfid-gate"

# Verifica ambiente
echo -e "${YELLOW}🔍 Verifica ambiente...${NC}"

if [ ! -d "$PROD_DIR" ]; then
    echo -e "${RED}❌ Directory produzione non trovata: $PROD_DIR${NC}"
    exit 1
fi

cd "$PROD_DIR"

if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py non trovato${NC}"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment non trovato${NC}"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ File .env non trovato${NC}"
    exit 1
fi

echo -e "  ✅ Ambiente verificato"

# Ferma servizio se attivo
echo -e "${YELLOW}🛑 Fermo servizio systemd...${NC}"
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
sleep 3

# Verifica che sia fermato
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${RED}❌ Servizio ancora attivo, forzo stop...${NC}"
    sudo systemctl kill "$SERVICE_NAME"
    sleep 2
fi

echo -e "  ✅ Servizio fermato"

# Test import base
echo -e "${YELLOW}🧪 Test import base...${NC}"
if sudo -u rfid bash -c "source venv/bin/activate && python -c 'import rfid_gate; print(\"✅ Import OK\")'" 2>&1; then
    echo -e "  ✅ Import base OK"
else
    echo -e "  ❌ Import base FALLITO"
    echo -e "  Provo import specifici..."
    
    sudo -u rfid bash -c "source venv/bin/activate && python -c 'from rfid_gate.config.settings import RFIDGateConfig; print(\"✅ Config OK\")'" || echo "❌ Config FAIL"
    sudo -u rfid bash -c "source venv/bin/activate && python -c 'from rfid_gate.network.mqtt import AsyncMQTTClient; print(\"✅ MQTT OK\")'" || echo "❌ MQTT FAIL"
    sudo -u rfid bash -c "source venv/bin/activate && python -c 'from rfid_gate.core.access_control import AccessControlSystem; print(\"✅ Core OK\")'" || echo "❌ Core FAIL"
fi

# Test configurazione
echo -e "${YELLOW}⚙️ Test configurazione...${NC}"
sudo -u rfid bash -c "source venv/bin/activate && python -c '
from rfid_gate.config.settings import RFIDGateConfig
try:
    config = RFIDGateConfig.from_env()
    print(f\"✅ Config caricata: broker={config.mqtt.broker}:{config.mqtt.port}\")
except Exception as e:
    print(f\"❌ Errore config: {e}\")
'"

# Test esecuzione con timeout
echo -e "${YELLOW}🚀 Test esecuzione main.py (timeout 30s)...${NC}"
echo -e "  📋 Output completo:"
echo -e "${BLUE}==================== INIZIO OUTPUT ====================${NC}"

# Esegui con timeout per evitare hang
timeout 30s sudo -u rfid bash -c "source venv/bin/activate && python main.py" || {
    exit_code=$?
    echo -e "${BLUE}==================== FINE OUTPUT ====================${NC}"
    echo ""
    
    if [ $exit_code -eq 124 ]; then
        echo -e "${YELLOW}⏰ Test terminato per timeout (30s) - Sistema sembra avviarsi${NC}"
    else
        echo -e "${RED}❌ Test fallito con exit code: $exit_code${NC}"
    fi
}

echo -e "\n${YELLOW}📊 Analisi post-test...${NC}"

# Controlla processo rimasti
rfid_processes=$(ps aux | grep -E "(python.*main.py|rfid)" | grep -v grep | wc -l)
if [ "$rfid_processes" -gt 0 ]; then
    echo -e "  ⚠️  Processi RFID ancora attivi:"
    ps aux | grep -E "(python.*main.py|rfid)" | grep -v grep
    echo -e "  🧹 Pulizia processi..."
    sudo pkill -f "main.py" 2>/dev/null || true
fi

# Verifica GPIO cleanup
if command -v gpio >/dev/null 2>&1; then
    echo -e "  🔧 Stato GPIO:"
    gpio readall | grep -E "(17|18|19|20)" || true
fi

echo -e "\n${GREEN}=============================================="
echo "🏁 Test manuale completato"
echo "=============================================="
echo -e "${NC}"

echo -e "${YELLOW}📋 Prossimi passi:${NC}"
echo -e "  1. Analizza l'output sopra per errori specifici"
echo -e "  2. Se il sistema si avvia ma poi crasha, controlla log con:"
echo -e "     sudo journalctl -fu $SERVICE_NAME"
echo -e "  3. Per riavviare il servizio:"
echo -e "     sudo systemctl start $SERVICE_NAME"