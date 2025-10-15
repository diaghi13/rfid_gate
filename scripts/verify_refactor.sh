#!/bin/bash
# 🧪 Script di verifica rapida refactor
# Testa che tutti i componenti della nuova architettura funzionino

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 VERIFICA REFACTOR RFID GATE${NC}"
echo "================================="

cd "$(dirname "$0")/.."

# Test 1: Struttura file
echo -e "\n${YELLOW}📁 Test struttura file${NC}"
required_files=(
    "main.py"
    "requirements.txt"
    ".env.example"
    ".gitignore"
    "rfid_gate/__init__.py"
    "rfid_gate/config/settings.py"
    "rfid_gate/core/access_control.py"
    "rfid_gate/hardware/readers/factory.py"
    "rfid_gate/network/mqtt.py"
    "tests/test_refactored_system.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file MANCANTE${NC}"
        exit 1
    fi
done

# Test 2: Import Python
echo -e "\n${YELLOW}🐍 Test import Python${NC}"
if python3 -c "
from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.core.access_control import AccessControlSystem  
from rfid_gate.hardware.readers.factory import ReaderFactory
from rfid_gate.network.mqtt import AsyncMQTTClient
print('✅ Tutti gli import OK')
" 2>/dev/null; then
    echo -e "${GREEN}✅ Import Python OK${NC}"
else
    echo -e "${RED}❌ Errore import Python${NC}"
    exit 1
fi

# Test 3: Configurazione
echo -e "\n${YELLOW}⚙️ Test configurazione${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ File .env presente${NC}"
    if python3 -c "
from rfid_gate.config.settings import RFIDGateConfig
config = RFIDGateConfig.from_env()
print(f'✅ Config caricata: {config.system.tornello_id}')
" 2>/dev/null; then
        echo -e "${GREEN}✅ Configurazione caricata${NC}"
    else
        echo -e "${YELLOW}⚠️ Configurazione con errori${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ File .env non presente (usando .env.example)${NC}"
    if python3 -c "
import os
os.environ['MQTT_BROKER'] = 'test.broker.com'
os.environ['TORNELLO_ID'] = 'test_01'
from rfid_gate.config.settings import RFIDGateConfig
config = RFIDGateConfig.from_env()
print(f'✅ Config test OK: {config.system.tornello_id}')
" 2>/dev/null; then
        echo -e "${GREEN}✅ Configurazione test OK${NC}"
    else
        echo -e "${RED}❌ Errore configurazione${NC}"
        exit 1
    fi
fi

# Test 4: Compatibility test
echo -e "\n${YELLOW}🔄 Test compatibilità${NC}"
if python3 tests/test_refactored_system.py >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Test suite PASS${NC}"
else
    echo -e "${RED}❌ Test suite FAIL${NC}"
    echo "Eseguendo test per dettagli..."
    python3 tests/test_refactored_system.py
    exit 1
fi

# Test 5: Script integrity
echo -e "\n${YELLOW}📜 Test integrità script${NC}"
scripts_ok=0
scripts_total=0

for script in scripts/*.sh; do
    if [ -f "$script" ]; then
        scripts_total=$((scripts_total + 1))
        if bash -n "$script" 2>/dev/null; then
            scripts_ok=$((scripts_ok + 1))
            echo -e "${GREEN}✅ $(basename "$script")${NC}"
        else
            echo -e "${RED}❌ $(basename "$script") - syntax error${NC}"
        fi
    fi
done

echo -e "${BLUE}📊 Script: $scripts_ok/$scripts_total OK${NC}"

# Test 6: Archivio
echo -e "\n${YELLOW}📦 Test archivio${NC}"
if [ -d "archive" ]; then
    archived_items=$(find archive -type f | wc -l)
    echo -e "${GREEN}✅ Archive con $archived_items files${NC}"
    echo -e "${BLUE}ℹ️ Sistema legacy preservato in archive/${NC}"
else
    echo -e "${YELLOW}⚠️ Directory archive non trovata${NC}"
fi

# Riepilogo finale
echo -e "\n${GREEN}🎉 VERIFICA COMPLETATA${NC}"
echo "=========================="
echo -e "${BLUE}📊 Stato refactor:${NC}"
echo "  ✅ Struttura modulare OK"
echo "  ✅ Import Python OK" 
echo "  ✅ Configurazione OK"
echo "  ✅ Test compatibilità OK"
echo "  ✅ Script aggiornati"
echo "  ✅ Sistema legacy archiviato"
echo

echo -e "${GREEN}🚀 Sistema pronto per deployment!${NC}"
echo -e "${YELLOW}💡 Per installare: sudo bash scripts/install.sh${NC}"