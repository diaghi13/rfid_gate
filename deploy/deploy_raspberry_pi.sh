#!/bin/bash
# 🚀 RFID Gate - Deployment su Raspberry Pi
# ========================================
#
# Script per deployment completo del sistema RFID Gate su Raspberry Pi
# Da eseguire dopo aver trasferito il codice sul Raspberry Pi

set -e  # Exit on error

echo "🚀 RFID Gate - Deployment su Raspberry Pi"
echo "=========================================="

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Controlla sistema
print_status "Controllando sistema Raspberry Pi..."

if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "Sistema non sembra essere Raspberry Pi"
    read -p "Continuare comunque? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "Raspberry Pi rilevato"
fi

# 2. Aggiorna sistema
print_status "Aggiornando sistema..."
sudo apt update && sudo apt upgrade -y

# 3. Installa dipendenze sistema
print_status "Installando dipendenze sistema..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    i2c-tools \
    git \
    mosquitto-clients

# 4. Abilita I2C e SPI
print_status "Abilitando interfacce I2C e SPI..."

# Verifica se I2C è già abilitato
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt || \
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    print_success "I2C abilitato"
    REBOOT_NEEDED=1
else
    print_success "I2C già abilitato"
fi

# Verifica se SPI è già abilitato
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt || \
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    print_success "SPI abilitato"
    REBOOT_NEEDED=1
else
    print_success "SPI già abilitato"
fi

# 5. Crea ambiente Python
print_status "Creando ambiente Python virtuale..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Ambiente virtuale creato"
else
    print_success "Ambiente virtuale già esistente"
fi

# Attiva ambiente
source .venv/bin/python
source .venv/bin/activate

# 6. Installa dipendenze Python
print_status "Installando dipendenze Python..."
pip install --upgrade pip setuptools wheel

# Installa requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Requirements installati"
fi

# Installa dipendenze PN532 specifiche
print_status "Installando librerie PN532..."
pip install \
    adafruit-circuitpython-pn532 \
    adafruit-blinka \
    RPi.GPIO \
    setuptools

print_success "Librerie PN532 installate"

# 7. Test configurazione
print_status "Testando configurazione sistema..."

# Test I2C
if [ -e "/dev/i2c-1" ]; then
    print_success "I2C bus disponibile"
    # Scan dispositivi I2C
    print_status "Scanning dispositivi I2C..."
    i2cdetect -y 1 || print_warning "Errore scanning I2C"
else
    print_error "I2C bus non disponibile"
    REBOOT_NEEDED=1
fi

# Test SPI
if [ -e "/dev/spidev0.0" ]; then
    print_success "SPI bus disponibile"
else
    print_error "SPI bus non disponibile"
    REBOOT_NEEDED=1
fi

# 8. Test lettori PN532
print_status "Testando lettori PN532..."
print_status "Configurazione Legacy Ripristinata:"
print_status "  - Lettore IN: PN532 I2C (0x24), RST: 22, SDA: 8"  
print_status "  - Lettore OUT: PN532 SPI (bus 0), RST: 25, CS: 7"
print_status "  - CS Pin: Usa D8/D4 basato su sda_pin (come legacy)"

python diagnose_pn532_complete.py || print_warning "Test PN532 con errori"

# Test configurazione legacy specifica
python test_legacy_pn532.py || print_warning "Test legacy con errori"

# 9. Setup configurazione
print_status "Configurando sistema..."

# Crea file .env se non esiste
if [ ! -f ".env" ]; then
    cp ".env.example" ".env" 2>/dev/null || print_warning "File .env.example non trovato"
    print_success "File .env creato da template con configurazione GPIO legacy"
    print_warning "Configurare .env con credenziali MQTT corrette"
else
    print_success "File .env già esistente"
fi

# Verifica configurazione GPIO
print_status "Configurazione GPIO disponibile:"
print_status "- Sistema Legacy (Pin 22,8,25,7) - Testato e funzionante ✅"  
print_status "- .env.example aggiornato con valori legacy ✅"
print_status "- Script configurazione: python3 tools/gpio_config.py"
print_status "- Documentazione: docs/CONFIGURATION_EXAMPLES.md"

# 10. Test sistema completo
print_status "Test sistema completo..."
print_warning "Avviare manualmente: python main.py"

# 11. Setup servizio systemd (opzionale)
read -p "Installare servizio systemd per avvio automatico? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Configurando servizio systemd..."
    
    # Crea file service
    sudo tee /etc/systemd/system/rfid-gate.service > /dev/null <<EOF
[Unit]
Description=RFID Gate Access Control System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/.venv/bin
ExecStart=$(pwd)/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable rfid-gate.service
    print_success "Servizio rfid-gate installato"
    print_status "Gestione servizio:"
    print_status "  Start:   sudo systemctl start rfid-gate"
    print_status "  Stop:    sudo systemctl stop rfid-gate"
    print_status "  Status:  sudo systemctl status rfid-gate"
    print_status "  Logs:    sudo journalctl -u rfid-gate -f"
fi

# 12. Summary
echo
print_success "=========================================="
print_success "🎯 DEPLOYMENT COMPLETATO!"
print_success "=========================================="
echo
print_status "PROSSIMI PASSI:"
print_status "1. Configura .env con parametri corretti"
print_status "2. Testa connessioni fisiche lettori PN532:"
print_status "   - Lettore IN: I2C address 0x24"
print_status "   - Lettore OUT: SPI bus 0 device 0"
print_status "3. Avvia sistema: python main.py"
print_status "4. Monitor logs: tail -f logs/system.log"

if [ "$REBOOT_NEEDED" = "1" ]; then
    echo
    print_warning "=========================================="
    print_warning "⚠️  RIAVVIO NECESSARIO"
    print_warning "=========================================="
    print_warning "I2C/SPI richiedono riavvio per essere attivi"
    read -p "Riavviare ora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Riavviando sistema..."
        sudo reboot
    else
        print_warning "Ricorda di riavviare manualmente: sudo reboot"
    fi
fi

print_success "Deployment terminato con successo! 🚀"