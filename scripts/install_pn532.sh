#!/bin/bash
# ===========================================
# 🚀 Script Installazione PN532 per RFID Gate
# ===========================================
# Installa e configura supporto PN532 su Raspberry Pi

set -e  # Esce se c'è un errore

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzioni helper
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

# Verifica se siamo su Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "Non sembra essere un Raspberry Pi"
        read -p "Continuare comunque? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Aggiorna sistema
update_system() {
    print_header "🔄 AGGIORNAMENTO SISTEMA"
    
    print_info "Aggiornamento repository..."
    sudo apt update -qq
    
    print_info "Aggiornamento pacchetti..."
    sudo apt upgrade -y
    
    print_success "Sistema aggiornato"
}

# Abilita I2C e SPI
enable_interfaces() {
    print_header "🔌 ABILITAZIONE INTERFACCE"
    
    print_info "Abilitazione I2C..."
    sudo raspi-config nonint do_i2c 0
    
    print_info "Abilitazione SPI..."
    sudo raspi-config nonint do_spi 0
    
    # Verifica che i moduli siano caricati
    if ! lsmod | grep -q i2c_dev; then
        sudo modprobe i2c-dev
        echo 'i2c-dev' | sudo tee -a /etc/modules >/dev/null
    fi
    
    print_success "Interfacce abilitate"
}

# Installa dipendenze sistema
install_system_deps() {
    print_header "📚 INSTALLAZIONE DIPENDENZE SISTEMA"
    
    print_info "Installazione strumenti sviluppo..."
    sudo apt install -y \
        python3-pip \
        python3-dev \
        python3-setuptools \
        python3-venv \
        build-essential \
        git
    
    print_info "Installazione strumenti I2C/SPI..."
    sudo apt install -y \
        i2c-tools \
        python3-smbus \
        spi-tools
    
    print_success "Dipendenze sistema installate"
}

# Installa dipendenze Python
install_python_deps() {
    print_header "🐍 INSTALLAZIONE DIPENDENZE PYTHON"
    
    # Verifica che il file requirements.txt esista
    if [ ! -f "requirements.txt" ]; then
        print_error "File requirements.txt non trovato!"
        print_info "Assicurati di essere nella directory del progetto"
        exit 1
    fi
    
    print_info "Aggiornamento pip..."
    python3 -m pip install --upgrade pip
    
    print_info "Installazione dipendenze Python..."
    python3 -m pip install -r requirements.txt
    
    print_success "Dipendenze Python installate"
}

# Test I2C
test_i2c() {
    print_header "🧪 TEST BUS I2C"
    
    print_info "Scansione dispositivi I2C..."
    i2c_output=$(sudo i2cdetect -y 1)
    echo "$i2c_output"
    
    # Controlla se ci sono dispositivi
    if echo "$i2c_output" | grep -q "[0-9a-f][0-9a-f]"; then
        print_success "Dispositivi I2C rilevati"
        
        # Controlla specificamente per indirizzi PN532
        if echo "$i2c_output" | grep -q "24"; then
            print_success "PN532 rilevato all'indirizzo 0x24"
        fi
        if echo "$i2c_output" | grep -q "25"; then
            print_success "PN532 rilevato all'indirizzo 0x25"
        fi
    else
        print_warning "Nessun dispositivo I2C rilevato"
        print_info "Verifica le connessioni hardware"
    fi
}

# Configura file .env
setup_config() {
    print_header "📄 CONFIGURAZIONE SISTEMA"
    
    # Backup configurazione esistente
    if [ -f ".env" ]; then
        backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backup configurazione esistente in $backup_file"
        cp .env "$backup_file"
    fi
    
    # Copia configurazione esempio se .env non esiste
    if [ ! -f ".env" ]; then
        if [ -f "config/.env.example" ]; then
            print_info "Creazione file .env da template..."
            cp config/.env.example .env
            
            # Configura automaticamente per PN532 se rilevato
            if sudo i2cdetect -y 1 | grep -q "24\|25"; then
                print_info "PN532 rilevato, configurazione automatica..."
                sed -i 's/RFID_IN_READER_TYPE=mfrc522/RFID_IN_READER_TYPE=pn532/' .env
                sed -i 's/RFID_OUT_READER_TYPE=pn532/RFID_OUT_READER_TYPE=pn532/' .env
                print_success "Configurazione PN532 applicata automaticamente"
            fi
        else
            print_warning "File config/.env.example non trovato"
        fi
    else
        print_info "File .env già esistente, non modificato"
    fi
}

# Test lettori RFID
test_readers() {
    print_header "🔍 TEST LETTORI RFID"
    
    if [ -f "test_multi_rfid_system.py" ]; then
        print_info "Esecuzione test sistema..."
        python3 test_multi_rfid_system.py
    else
        print_warning "File di test non trovato"
        print_info "Test manuale: python3 -c \"from src.rfid_reader import RFIDReader; r=RFIDReader('test'); print('OK' if r.initialize() else 'FAIL')\""
    fi
}

# Installa servizio systemd (opzionale)
install_service() {
    print_header "🔧 INSTALLAZIONE SERVIZIO (OPZIONALE)"
    
    read -p "Installare servizio systemd per avvio automatico? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "scripts/setup_service.sh" ]; then
            print_info "Installazione servizio..."
            bash scripts/setup_service.sh
        else
            print_warning "Script setup_service.sh non trovato"
        fi
    fi
}

# Mostra riepilogo finale
show_summary() {
    print_header "📋 RIEPILOGO INSTALLAZIONE"
    
    echo -e "${GREEN}🎉 INSTALLAZIONE COMPLETATA!${NC}"
    echo ""
    echo "📱 Configurazione RFID:"
    if [ -f ".env" ]; then
        IN_TYPE=$(grep "RFID_IN_READER_TYPE" .env | cut -d'=' -f2)
        OUT_TYPE=$(grep "RFID_OUT_READER_TYPE" .env | cut -d'=' -f2)
        echo "   Lettore IN:  $IN_TYPE"
        echo "   Lettore OUT: $OUT_TYPE"
    fi
    
    echo ""
    echo "🔧 Prossimi passi:"
    echo "1. Collega i moduli PN532 secondo schema:"
    echo "   - PN532 IN:  I2C Address 0x24"
    echo "   - PN532 OUT: I2C Address 0x25"
    echo "2. Modifica .env se necessario"
    echo "3. Riavvia sistema: sudo reboot"
    echo "4. Test: python3 test_multi_rfid_system.py"
    echo ""
    echo "📋 Comandi utili:"
    echo "   - Scansione I2C: sudo i2cdetect -y 1"
    echo "   - Test sistema: python3 test_multi_rfid_system.py"
    echo "   - Avvio manuale: python3 src/main.py"
    echo ""
    echo "🌐 Documentazione: docs/PN532_QUICK_GUIDE.md"
}

# Funzione principale
main() {
    print_header "🚀 INSTALLAZIONE PN532 PER RFID GATE"
    
    # Verifica permessi
    if [[ $EUID -eq 0 ]]; then
        print_error "Non eseguire come root (sudo verrà richiesto quando necessario)"
        exit 1
    fi
    
    # Verifica directory progetto
    if [ ! -f "src/main.py" ] && [ ! -f "requirements.txt" ]; then
        print_error "Non sei nella directory del progetto RFID Gate"
        print_info "Naviga nella directory del progetto prima di eseguire questo script"
        exit 1
    fi
    
    echo "Questo script installerà il supporto PN532 per RFID Gate"
    echo "Verranno installate dipendenze e configurate le interfacce I2C/SPI"
    echo ""
    read -p "Continuare con l'installazione? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installazione annullata"
        exit 0
    fi
    
    # Esegui installazione
    check_raspberry_pi
    update_system
    enable_interfaces
    install_system_deps
    install_python_deps
    test_i2c
    setup_config
    test_readers
    install_service
    show_summary
    
    echo ""
    print_success "Installazione completata con successo!"
    print_info "Riavvia il sistema per applicare tutte le modifiche: sudo reboot"
}

# Esegui se chiamato direttamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi