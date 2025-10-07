#!/bin/bash
# 🔍 System Diagnostic - RFID Gate System
# ======================================
# 
# Script unificato per diagnostica sistema:
# - Hardware (GPIO, SPI, I2C) 
# - Software (Python, dipendenze)
# - Architettura refactorizzata
# - Lettori RFID (MFRC522, PN532)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}🔍 RFID Gate - System Diagnostic${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo ""
}

print_section() {
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}$(printf '%*s' ${#1} '' | tr ' ' '-')${NC}"
}

check_mark() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
}

# ===========================================
# 🏗️ ARCHITETTURA SOFTWARE
# ===========================================
test_software_architecture() {
    print_section "🏗️ Test Architettura Software"
    
    local score=0
    local total=5
    
    # Test 1: Python 3
    echo -n "Python 3 disponibile: "
    if command -v python3 >/dev/null 2>&1; then
        version=$(python3 --version | cut -d' ' -f2)
        echo -e "${GREEN}✅ v$version${NC}"
        ((score++))
    else
        echo -e "${RED}❌ Non installato${NC}"
    fi
    
    # Test 2: Directory rfid_gate/
    echo -n "Architettura refactorizzata: "
    if [ -d "$PROJECT_ROOT/rfid_gate" ]; then
        echo -e "${GREEN}✅ rfid_gate/ presente${NC}"
        ((score++))
    else
        echo -e "${RED}❌ Directory rfid_gate/ mancante${NC}"
    fi
    
    # Test 3: Moduli principali
    echo -n "Moduli principali: "
    local missing_modules=0
    for module in "__init__.py" "config/settings.py" "core/access_control.py" "hardware/readers/factory.py"; do
        if [ ! -f "$PROJECT_ROOT/rfid_gate/$module" ]; then
            ((missing_modules++))
        fi
    done
    
    if [ $missing_modules -eq 0 ]; then
        echo -e "${GREEN}✅ Tutti presenti${NC}"
        ((score++))
    else
        echo -e "${RED}❌ $missing_modules moduli mancanti${NC}"
    fi
    
    # Test 4: Sistema legacy
    echo -n "Pulizia sistema legacy: "
    if [ ! -d "$PROJECT_ROOT/src" ]; then
        echo -e "${GREEN}✅ Nessuna directory src/ obsoleta${NC}"
        ((score++))
    else
        echo -e "${YELLOW}⚠️ Directory src/ legacy rilevata${NC}"
    fi
    
    # Test 5: Update manager
    echo -n "Update manager moderno: "
    if [ -f "$PROJECT_ROOT/tools/update_manager.py" ]; then
        echo -e "${GREEN}✅ Disponibile${NC}"
        ((score++))
    else
        echo -e "${RED}❌ Non trovato${NC}"
    fi
    
    echo -e "📊 Punteggio architettura: ${BLUE}$score/$total${NC}"
    echo ""
    
    return $score
}

# ===========================================
# 🔧 HARDWARE & INTERFACCE
# ===========================================
test_hardware_interfaces() {
    print_section "🔧 Test Hardware & Interfacce"
    
    local score=0
    local total=4
    
    # Test 1: GPIO
    echo -n "GPIO disponibile: "
    if [ -d "/sys/class/gpio" ] || command -v gpio >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Sistema GPIO attivo${NC}"
        ((score++))
    else
        echo -e "${YELLOW}⚠️ GPIO non rilevato (normale su sistemi non-RPi)${NC}"
    fi
    
    # Test 2: SPI
    echo -n "Interfaccia SPI: "
    if lsmod 2>/dev/null | grep -q spi_bcm2835 || ls /dev/spidev* >/dev/null 2>&1; then
        echo -e "${GREEN}✅ SPI abilitato${NC}"
        spi_devices=$(ls /dev/spidev* 2>/dev/null | wc -l)
        echo "  📡 Device SPI: $spi_devices"
        ((score++))
    else
        echo -e "${YELLOW}⚠️ SPI non abilitato${NC}"
        echo "  💡 Abilita con: sudo raspi-config → Interface → SPI"
    fi
    
    # Test 3: I2C
    echo -n "Interfaccia I2C: "
    if lsmod 2>/dev/null | grep -q i2c_bcm2835 || ls /dev/i2c-* >/dev/null 2>&1; then
        echo -e "${GREEN}✅ I2C abilitato${NC}"
        ((score++))
        
        # Scan I2C devices if available
        if command -v i2cdetect >/dev/null 2>&1; then
            echo "  🔍 Scansione dispositivi I2C..."
            i2c_result=$(sudo i2cdetect -y 1 2>/dev/null | grep -E '[0-9a-f]{2}' | wc -l)
            echo "  📡 Dispositivi I2C rilevati: $i2c_result"
        else
            echo "  💡 Installa i2c-tools per scansione: sudo apt install i2c-tools"
        fi
    else
        echo -e "${YELLOW}⚠️ I2C non abilitato${NC}"
        echo "  💡 Abilita con: sudo raspi-config → Interface → I2C"
    fi
    
    # Test 4: UART/Serial
    echo -n "Interfaccia UART: "
    if ls /dev/ttyS* >/dev/null 2>&1 || ls /dev/ttyAMA* >/dev/null 2>&1; then
        echo -e "${GREEN}✅ UART disponibile${NC}"
        ((score++))
    else
        echo -e "${YELLOW}⚠️ UART non rilevato${NC}"
    fi
    
    echo -e "📊 Punteggio hardware: ${BLUE}$score/$total${NC}"
    echo ""
    
    return $score
}

# ===========================================
# 📦 DIPENDENZE PYTHON
# ===========================================
test_python_dependencies() {
    print_section "📦 Test Dipendenze Python"
    
    local score=0
    local total=6
    
    # Required packages list
    local packages=(
        "paho.mqtt:paho-mqtt"
        "requests:requests"
        "RPi.GPIO:RPi.GPIO"
        "spidev:spidev"
        "mfrc522:mfrc522"
        "adafruit_pn532:adafruit-circuitpython-pn532"
    )
    
    for package_info in "${packages[@]}"; do
        IFS=':' read -r import_name pip_name <<< "$package_info"
        echo -n "$pip_name: "
        
        if python3 -c "import $import_name" >/dev/null 2>&1; then
            version=$(python3 -c "import $import_name; print(getattr($import_name, '__version__', 'unknown'))" 2>/dev/null)
            echo -e "${GREEN}✅ v$version${NC}"
            ((score++))
        else
            echo -e "${RED}❌ Non installato${NC}"
            echo "  💡 Installa con: pip install $pip_name"
        fi
    done
    
    echo -e "📊 Punteggio dipendenze: ${BLUE}$score/$total${NC}"
    echo ""
    
    return $score
}

# ===========================================
# 🏃 TEST FUNZIONALI
# ===========================================
test_functional() {
    print_section "🏃 Test Funzionali"
    
    local score=0
    local total=3
    
    # Test 1: Import rfid_gate
    echo -n "Import modulo rfid_gate: "
    cd "$PROJECT_ROOT"
    if python3 -c "from rfid_gate import __version__; print(f'v{__version__}')" >/dev/null 2>&1; then
        version=$(python3 -c "from rfid_gate import __version__; print(__version__)")
        echo -e "${GREEN}✅ v$version${NC}"
        ((score++))
    else
        echo -e "${RED}❌ Errore import${NC}"
    fi
    
    # Test 2: Configurazione
    echo -n "Caricamento configurazione: "
    if python3 -c "from rfid_gate.config.settings import RFIDGateConfig; RFIDGateConfig()" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Configurazione OK${NC}"
        ((score++))
    else
        echo -e "${RED}❌ Errore configurazione${NC}"
    fi
    
    # Test 3: Factory lettori
    echo -n "Factory lettori RFID: "
    if python3 -c "from rfid_gate.hardware.readers.factory import RFIDReaderFactory; RFIDReaderFactory()" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Factory OK${NC}"
        ((score++))
    else
        echo -e "${RED}❌ Errore factory${NC}"
    fi
    
    echo -e "📊 Punteggio funzionale: ${BLUE}$score/$total${NC}"
    echo ""
    
    return $score
}

# ===========================================
# 📊 RIEPILOGO FINALE
# ===========================================
generate_report() {
    local arch_score=$1
    local hw_score=$2
    local deps_score=$3
    local func_score=$4
    
    local total_score=$((arch_score + hw_score + deps_score + func_score))
    local max_score=18
    
    print_section "📊 Riepilogo Diagnostica"
    
    echo -e "🏗️  Architettura Software: ${BLUE}$arch_score/5${NC}"
    echo -e "🔧 Hardware & Interfacce: ${BLUE}$hw_score/4${NC}"
    echo -e "📦 Dipendenze Python:     ${BLUE}$deps_score/6${NC}"
    echo -e "🏃 Test Funzionali:       ${BLUE}$func_score/3${NC}"
    echo ""
    echo -e "🎯 ${YELLOW}TOTALE: $total_score/$max_score${NC}"
    
    # Status finale
    local percentage=$((total_score * 100 / max_score))
    
    if [ $percentage -ge 90 ]; then
        echo -e "🎉 ${GREEN}SISTEMA COMPLETAMENTE FUNZIONALE${NC}"
        return 0
    elif [ $percentage -ge 70 ]; then
        echo -e "✅ ${GREEN}SISTEMA FUNZIONALE CON ALCUNE LACUNE${NC}"
        return 0
    elif [ $percentage -ge 50 ]; then
        echo -e "⚠️ ${YELLOW}SISTEMA PARZIALMENTE FUNZIONALE${NC}"
        echo -e "🔧 ${YELLOW}Richiesti alcuni aggiustamenti${NC}"
        return 1
    else
        echo -e "❌ ${RED}SISTEMA NON FUNZIONALE${NC}"
        echo -e "🚨 ${RED}Richiesti aggiustamenti significativi${NC}"
        return 2
    fi
}

# ===========================================
# 🚀 MAIN EXECUTION
# ===========================================
main() {
    print_header
    
    # Parse arguments
    case "$1" in
        --help|-h)
            echo "🔍 System Diagnostic per RFID Gate"
            echo ""
            echo "Uso: $0 [opzioni]"
            echo ""
            echo "Opzioni:"
            echo "  --architecture  Test solo architettura software"
            echo "  --hardware      Test solo hardware/interfacce"
            echo "  --dependencies  Test solo dipendenze Python"
            echo "  --functional    Test solo funzionalità"
            echo "  --help          Mostra questo aiuto"
            echo ""
            echo "Senza opzioni: esegue tutti i test"
            return 0
            ;;
        --architecture)
            test_software_architecture
            return $?
            ;;
        --hardware)
            test_hardware_interfaces
            return $?
            ;;
        --dependencies)
            test_python_dependencies
            return $?
            ;;
        --functional)
            test_functional
            return $?
            ;;
        "")
            # Esecuzione completa
            arch_score=$(test_software_architecture; echo $?)
            hw_score=$(test_hardware_interfaces; echo $?)
            deps_score=$(test_python_dependencies; echo $?)
            func_score=$(test_functional; echo $?)
            
            generate_report $arch_score $hw_score $deps_score $func_score
            return $?
            ;;
        *)
            echo -e "${RED}❌ Opzione non riconosciuta: $1${NC}"
            echo -e "${YELLOW}💡 Usa --help per vedere le opzioni disponibili${NC}"
            return 1
            ;;
    esac
}

# Execute with error handling
if ! main "$@"; then
    exit_code=$?
    echo ""
    echo -e "${YELLOW}💡 Raccomandazioni:${NC}"
    echo "- Controlla la documentazione in docs/"
    echo "- Esegui scripts/install.sh per setup automatico"
    echo "- Usa tools/update_manager.py --diagnostic per dettagli"
    
    exit $exit_code
fi