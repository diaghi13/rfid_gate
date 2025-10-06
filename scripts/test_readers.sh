#!/bin/bash
# ===========================================
# 🧪 Script Test Rapido Lettori RFID
# ===========================================
# Testa rapidamente la configurazione e i lettori

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Test configurazione
test_config() {
    print_header "📄 TEST CONFIGURAZIONE"
    
    if [ ! -f ".env" ]; then
        print_error "File .env non trovato!"
        print_info "Crea una configurazione con: cp config/.env.example .env"
        return 1
    fi
    
    print_success "File .env trovato"
    
    # Leggi tipo lettori configurati
    IN_TYPE=$(grep "RFID_IN_READER_TYPE" .env 2>/dev/null | cut -d'=' -f2)
    OUT_TYPE=$(grep "RFID_OUT_READER_TYPE" .env 2>/dev/null | cut -d'=' -f2)
    
    echo "📱 Lettori configurati:"
    echo "   IN:  ${IN_TYPE:-'non definito'}"
    echo "   OUT: ${OUT_TYPE:-'non definito'}"
    
    return 0
}

# Test I2C (per PN532)
test_i2c() {
    print_header "🔌 TEST BUS I2C"
    
    if ! command -v i2cdetect >/dev/null 2>&1; then
        print_warning "i2cdetect non installato"
        print_info "Installa con: sudo apt install i2c-tools"
        return 1
    fi
    
    print_info "Scansione dispositivi I2C..."
    i2c_result=$(sudo i2cdetect -y 1 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "$i2c_result"
        
        # Controlla indirizzi PN532 comuni
        if echo "$i2c_result" | grep -q "24"; then
            print_success "Dispositivo rilevato a 0x24 (possibile PN532 IN)"
        fi
        
        if echo "$i2c_result" | grep -q "25"; then
            print_success "Dispositivo rilevato a 0x25 (possibile PN532 OUT)"
        fi
        
        if ! echo "$i2c_result" | grep -q "[0-9a-f][0-9a-f]"; then
            print_warning "Nessun dispositivo I2C rilevato"
        fi
        
        return 0
    else
        print_error "Errore accesso bus I2C"
        print_info "Verifica che I2C sia abilitato: sudo raspi-config"
        return 1
    fi
}

# Test SPI (per MFRC522)
test_spi() {
    print_header "🔌 TEST BUS SPI"
    
    if [ -e "/dev/spidev0.0" ]; then
        print_success "SPI0 disponibile (/dev/spidev0.0)"
    else
        print_warning "SPI0 non disponibile"
    fi
    
    if [ -e "/dev/spidev0.1" ]; then
        print_success "SPI0.1 disponibile (/dev/spidev0.1)"
    else
        print_info "SPI0.1 non disponibile (normale)"
    fi
    
    if [ -e "/dev/spidev1.0" ]; then
        print_success "SPI1 disponibile (/dev/spidev1.0)"
    else
        print_info "SPI1 non disponibile (normale per singolo lettore)"
    fi
    
    # Controlla se SPI è abilitato
    if lsmod | grep -q spi_; then
        print_success "Moduli SPI caricati"
    else
        print_warning "Moduli SPI non caricati"
        print_info "Abilita SPI con: sudo raspi-config"
    fi
}

# Test GPIO
test_gpio() {
    print_header "📍 TEST GPIO"
    
    # Leggi pin dai file .env se esiste
    if [ -f ".env" ]; then
        RFID_IN_RST=$(grep "RFID_IN_RST_PIN" .env 2>/dev/null | cut -d'=' -f2)
        RFID_IN_SDA=$(grep "RFID_IN_SDA_PIN" .env 2>/dev/null | cut -d'=' -f2)
        RELAY_IN=$(grep "RELAY_IN_PIN" .env 2>/dev/null | cut -d'=' -f2)
        
        echo "📌 PIN configurati (.env):"
        echo "   RFID IN RST: ${RFID_IN_RST:-'non definito'}"
        echo "   RFID IN SDA: ${RFID_IN_SDA:-'non definito'}"  
        echo "   RELAY IN:    ${RELAY_IN:-'non definito'}"
    fi
    
    # Controlla /sys/class/gpio
    if [ -d "/sys/class/gpio" ]; then
        print_success "Interfaccia GPIO disponibile"
        
        # Conta GPIO esportati
        gpio_count=$(ls /sys/class/gpio/ | grep -c "gpio" || echo "0")
        print_info "$gpio_count GPIO attualmente esportati"
    else
        print_error "Interfaccia GPIO non disponibile"
    fi
}

# Test dipendenze Python
test_python_deps() {
    print_header "🐍 TEST DIPENDENZE PYTHON"
    
    # Test import base
    if python3 -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
        print_success "Python3 disponibile"
    else
        print_error "Python3 non disponibile"
        return 1
    fi
    
    # Test dipendenze MFRC522
    if python3 -c "import mfrc522" 2>/dev/null; then
        print_success "Libreria mfrc522 installata"
    else
        print_warning "Libreria mfrc522 non installata"
    fi
    
    if python3 -c "import RPi.GPIO" 2>/dev/null; then
        print_success "RPi.GPIO installata"
    else
        print_warning "RPi.GPIO non installata (normale su non-RPi)"
    fi
    
    # Test dipendenze PN532
    if python3 -c "import adafruit_pn532" 2>/dev/null; then
        print_success "Libreria adafruit_pn532 installata"
    else
        print_warning "Libreria adafruit_pn532 non installata"
    fi
    
    if python3 -c "import board" 2>/dev/null; then
        print_success "Libreria board installata"
    else
        print_warning "Libreria board non installata"
    fi
    
    # Test progetto\n    if [ -f \"main.py\" ]; then\n        print_success \"Progetto RFID Gate trovato\"\n        \n        # Test import configurazione\n        if python3 -c \"from rfid_gate.config.settings import RFIDGateConfig; config = RFIDGateConfig.load_from_env(); print('Config OK')\" 2>/dev/null; then\n            print_success \"Configurazione Python valida\"\n        else\n            print_error \"Errore nella configurazione Python\"\n        fi\n    else\n        print_error \"File main.py non trovato\"\n        return 1\n    fi
}

# Test lettori RFID
test_rfid_readers() {
    print_header "📱 TEST LETTORI RFID"
    
    if [ ! -f "test_multi_rfid_system.py" ]; then
        print_warning "Script test non trovato, creo test semplice..."
        
        # Test semplificato inline
        python3 << 'EOF'
import sys
import os
sys.path.insert(0, 'src')

try:
    from config import Config
    print(f"✅ Configurazione caricata")
    print(f"   IN Type:  {getattr(Config, 'RFID_IN_READER_TYPE', 'non definito')}")
    print(f"   OUT Type: {getattr(Config, 'RFID_OUT_READER_TYPE', 'non definito')}")
    
    from rfid_reader import RFIDReader
    print("✅ Modulo RFIDReader importato")
    
    # Test creazione reader
    reader = RFIDReader("test")
    print(f"✅ Reader creato: {reader.reader_type}")
    
except ImportError as e:
    print(f"❌ Errore import: {e}")
except Exception as e:
    print(f"⚠️  Errore: {e}")
EOF
    else
        print_info "Esecuzione test completo..."
        python3 test_multi_rfid_system.py
    fi
}

# Test sistema completo
test_system_status() {
    print_header "🔍 STATUS SISTEMA COMPLETO"
    
    # Info sistema
    echo "🖥️ Sistema:"
    if [ -f "/proc/cpuinfo" ]; then
        if grep -q "Raspberry Pi" /proc/cpuinfo; then
            print_success "Raspberry Pi rilevato"
        else
            print_info "Sistema non-RPi"
        fi
    fi
    
    # Info risorse
    echo "💾 Risorse:"
    if command -v free >/dev/null; then
        free -h | head -2
    fi
    
    echo "💽 Spazio disco:"
    df -h . | tail -1
    
    # Info processo (se in esecuzione)
    echo "🏃 Processi RFID Gate:"
    if pgrep -f "main.py" >/dev/null; then
        print_success "Processo RFID Gate in esecuzione"
        pgrep -f "main.py" | while read pid; do
            echo "   PID: $pid"
        done
    else
        print_info "Nessun processo RFID Gate in esecuzione"
    fi
}

# Menu principale
show_menu() {
    print_header "🧪 TEST LETTORI RFID - MENU"
    echo "Seleziona test da eseguire:"
    echo ""
    echo "1) Test completo (tutti i test)"
    echo "2) Test configurazione (.env)"
    echo "3) Test hardware (I2C/SPI/GPIO)"
    echo "4) Test dipendenze Python"  
    echo "5) Test lettori RFID"
    echo "6) Status sistema"
    echo "7) Test I2C (solo PN532)"
    echo "8) Test SPI (solo MFRC522)"
    echo "0) Esci"
    echo ""
}

# Test completo
run_full_test() {
    print_header "🚀 TEST COMPLETO SISTEMA RFID"
    
    echo "Esecuzione di tutti i test..."
    echo ""
    
    test_config && echo ""
    test_python_deps && echo ""
    test_i2c && echo ""
    test_spi && echo ""
    test_gpio && echo ""
    test_rfid_readers && echo ""
    test_system_status
    
    echo ""
    print_header "📊 RIEPILOGO TEST COMPLETATO"
    print_info "Verifica i risultati sopra per eventuali problemi"
}

# Menu interattivo
interactive_menu() {
    while true; do
        show_menu
        read -p "Scelta: " choice
        
        case $choice in
            1) run_full_test ;;
            2) test_config ;;
            3) 
                test_i2c
                echo ""
                test_spi  
                echo ""
                test_gpio
                ;;
            4) test_python_deps ;;
            5) test_rfid_readers ;;
            6) test_system_status ;;
            7) test_i2c ;;
            8) test_spi ;;
            0) 
                print_info "Uscita..."
                exit 0 
                ;;
            *) 
                print_warning "Scelta non valida" 
                ;;
        esac
        
        echo ""
        read -p "Premi INVIO per continuare..."
        echo ""
    done
}

# Aiuto
show_help() {
    echo "🧪 Script Test Rapido Lettori RFID"
    echo ""
    echo "Uso:"
    echo "  $0              # Menu interattivo"
    echo "  $0 full         # Test completo"
    echo "  $0 config       # Test configurazione"
    echo "  $0 i2c          # Test I2C"
    echo "  $0 spi          # Test SPI" 
    echo "  $0 gpio         # Test GPIO"
    echo "  $0 python       # Test dipendenze Python"
    echo "  $0 readers      # Test lettori RFID"
    echo "  $0 status       # Status sistema"
    echo ""
}

# Main
case $1 in
    "full") run_full_test ;;
    "config") test_config ;;
    "i2c") test_i2c ;;
    "spi") test_spi ;;
    "gpio") test_gpio ;;
    "python") test_python_deps ;;
    "readers") test_rfid_readers ;;
    "status") test_system_status ;;
    "--help"|"-h") show_help ;;
    "") interactive_menu ;;
    *) 
        echo "Comando non riconosciuto. Usa --help per aiuto."
        exit 1
        ;;
esac