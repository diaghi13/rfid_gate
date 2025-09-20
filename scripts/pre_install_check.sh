#!/bin/bash
# 🔍 Script di Verifica Pre-Installazione RFID Gate System
# Diagnostica problemi comuni prima dell'installazione

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 VERIFICA PRE-INSTALLAZIONE RFID GATE SYSTEM${NC}"
echo "=================================================="

ERRORS=0
WARNINGS=0

# Verifica privilegi root
echo -e "${YELLOW}👤 Controllo privilegi...${NC}"
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Script deve essere eseguito come root${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ Privilegi root OK${NC}"
fi

# Verifica sistema
echo -e "\n${YELLOW}🖥️  Controllo sistema...${NC}"
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${GREEN}✅ Sistema Raspberry Pi rilevato${NC}"
    RPI_MODEL=$(grep "Model" /proc/cpuinfo | cut -d: -f2 | xargs)
    echo "   Modello: $RPI_MODEL"
else
    echo -e "${YELLOW}⚠️ Sistema non rilevato come Raspberry Pi${NC}"
    ((WARNINGS++))
fi

# Verifica connessione internet
echo -e "\n${YELLOW}🌐 Controllo connessione internet...${NC}"
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Connessione internet OK${NC}"
else
    echo -e "${RED}❌ Nessuna connessione internet${NC}"
    ((ERRORS++))
fi

# Verifica spazio disco
echo -e "\n${YELLOW}💾 Controllo spazio disco...${NC}"
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
REQUIRED_SPACE=1048576  # 1GB in KB
if [ "$AVAILABLE_SPACE" -gt "$REQUIRED_SPACE" ]; then
    echo -e "${GREEN}✅ Spazio disco sufficiente ($(($AVAILABLE_SPACE/1024/1024))GB disponibili)${NC}"
else
    echo -e "${RED}❌ Spazio disco insufficiente ($(($AVAILABLE_SPACE/1024/1024))GB disponibili, richiesto 1GB)${NC}"
    ((ERRORS++))
fi

# Verifica Python 3
echo -e "\n${YELLOW}🐍 Controllo Python...${NC}"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python3 trovato (versione $PYTHON_VERSION)${NC}"
    
    # Verifica versione minima
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        echo -e "${GREEN}✅ Versione Python OK (>= 3.7)${NC}"
    else
        echo -e "${RED}❌ Versione Python troppo vecchia (richiesta >= 3.7)${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${RED}❌ Python3 non trovato${NC}"
    ((ERRORS++))
fi

# Verifica pip
if command -v pip3 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ pip3 trovato${NC}"
else
    echo -e "${YELLOW}⚠️ pip3 non trovato (verrà installato)${NC}"
    ((WARNINGS++))
fi

# Verifica GPIO
echo -e "\n${YELLOW}🔌 Controllo GPIO...${NC}"
if [ -d "/sys/class/gpio" ]; then
    echo -e "${GREEN}✅ Sistema GPIO disponibile${NC}"
else
    echo -e "${RED}❌ Sistema GPIO non disponibile${NC}"
    ((ERRORS++))
fi

# Verifica SPI
echo -e "\n${YELLOW}📡 Controllo SPI...${NC}"
if [ -e "/dev/spidev0.0" ] || [ -e "/dev/spidev0.1" ]; then
    echo -e "${GREEN}✅ SPI già abilitato${NC}"
elif grep -q "dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    echo -e "${YELLOW}⚠️ SPI configurato ma richiede riavvio${NC}"
    ((WARNINGS++))
else
    echo -e "${YELLOW}⚠️ SPI non abilitato (verrà configurato)${NC}"
    ((WARNINGS++))
fi

# Verifica I2C (opzionale ma utile)
echo -e "\n${YELLOW}🔗 Controllo I2C...${NC}"
if [ -e "/dev/i2c-1" ]; then
    echo -e "${GREEN}✅ I2C abilitato${NC}"
else
    echo -e "${YELLOW}⚠️ I2C non abilitato (opzionale)${NC}"
fi

# Verifica file progetto esistenti
echo -e "\n${YELLOW}📁 Controllo file progetto...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# File essenziali
REQUIRED_FILES=(
    "src/main.py"
    "src/config.py"
    "src/rfid_manager.py"
    "src/relay_controller.py"
    "src/mqtt_client.py"
    "requirements.txt"
)

ALL_FILES_OK=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file mancante${NC}"
        ((ERRORS++))
        ALL_FILES_OK=false
    fi
done

# Verifica directory
REQUIRED_DIRS=(
    "src"
    "scripts"
    "config/examples"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$SCRIPT_DIR/$dir" ]; then
        echo -e "${GREEN}✅ Directory $dir${NC}"
    else
        echo -e "${RED}❌ Directory $dir mancante${NC}"
        ((ERRORS++))
    fi
done

# Verifica file di configurazione
echo -e "\n${YELLOW}⚙️ Controllo configurazioni...${NC}"
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${GREEN}✅ File .env trovato${NC}"
    
    # Verifica configurazioni critiche
    if grep -q "MQTT_BROKER=" "$SCRIPT_DIR/.env"; then
        echo -e "${GREEN}✅ Configurazione MQTT presente${NC}"
    else
        echo -e "${YELLOW}⚠️ Configurazione MQTT mancante${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠️ File .env non trovato (verrà creato)${NC}"
    ((WARNINGS++))
fi

# Verifica esempi configurazione
if [ -f "$SCRIPT_DIR/config/examples/unidirezionale.env" ]; then
    echo -e "${GREEN}✅ Esempio configurazione unidirezionale${NC}"
else
    echo -e "${YELLOW}⚠️ Esempio unidirezionale mancante${NC}"
    ((WARNINGS++))
fi

if [ -f "$SCRIPT_DIR/config/examples/bidirezionale.env" ]; then
    echo -e "${GREEN}✅ Esempio configurazione bidirezionale${NC}"
else
    echo -e "${YELLOW}⚠️ Esempio bidirezionale mancante${NC}"
    ((WARNINGS++))
fi

# Verifica installazioni esistenti
echo -e "\n${YELLOW}🔍 Controllo installazioni esistenti...${NC}"
if [ -d "/opt/rfid-gate" ]; then
    echo -e "${YELLOW}⚠️ Installazione esistente trovata in /opt/rfid-gate${NC}"
    echo "   Sarà aggiornata durante l'installazione"
    ((WARNINGS++))
else
    echo -e "${GREEN}✅ Nessuna installazione esistente${NC}"
fi

if systemctl list-unit-files | grep -q "rfid-gate.service"; then
    echo -e "${YELLOW}⚠️ Servizio rfid-gate già configurato${NC}"
    if systemctl is-active --quiet rfid-gate; then
        echo -e "${YELLOW}⚠️ Servizio attualmente in esecuzione${NC}"
    fi
    ((WARNINGS++))
fi

# Verifica hardware (se su Raspberry Pi)
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "\n${YELLOW}🔧 Controllo hardware Raspberry Pi...${NC}"
    
    # Verifica pin GPIO utilizzati
    USED_PINS=(18 19 22 25 8 7)
    for pin in "${USED_PINS[@]}"; do
        if [ -d "/sys/class/gpio/gpio$pin" ]; then
            echo -e "${YELLOW}⚠️ GPIO $pin già in uso${NC}"
            ((WARNINGS++))
        else
            echo -e "${GREEN}✅ GPIO $pin libero${NC}"
        fi
    done
fi

# Sommario risultati
echo -e "\n${BLUE}📊 SOMMARIO VERIFICA${NC}"
echo "===================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 Sistema pronto per l'installazione!${NC}"
    echo -e "${GREEN}✅ Nessun errore o warning rilevato${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️ Sistema compatibile con $WARNINGS warning${NC}"
    echo -e "${YELLOW}💡 L'installazione può procedere ma controlla i warning${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS errori critici rilevati${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️ $WARNINGS warning aggiuntivi${NC}"
    fi
    echo
    echo -e "${YELLOW}🔧 Azioni consigliate:${NC}"
    
    if [ $ERRORS -gt 0 ]; then
        echo "1. Risolvi gli errori critici evidenziati"
        echo "2. Esegui nuovamente questa verifica"
        echo "3. Procedi con l'installazione"
    fi
    
    echo
    echo -e "${RED}⚠️ NON procedere con l'installazione fino alla risoluzione degli errori${NC}"
    exit 1
fi