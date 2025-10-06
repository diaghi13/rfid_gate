#!/bin/bash
# 🚀 Script di installazione rapida per PN532 compatibile

echo "🔧 INSTALLAZIONE PN532 COMPATIBILE"
echo "==================================="

# Verifica se siamo su Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️ Non siamo su Raspberry Pi - installazione limitata"
    INSTALL_MODE="limited"
else
    echo "✅ Raspberry Pi rilevato"
    INSTALL_MODE="full"
fi

# Aggiorna pip
echo "📦 Aggiornamento pip..."
python3 -m pip install --upgrade pip

# Installa dipendenze base sempre
echo "📚 Installazione dipendenze base..."
pip3 install paho-mqtt python-dotenv requests

if [[ "$INSTALL_MODE" == "full" ]]; then
    # Solo su Raspberry Pi
    echo "🔧 Installazione librerie hardware..."
    
    # Aggiorna sistema
    sudo apt update
    sudo apt install -y python3-pip python3-dev i2c-tools
    
    # Installa librerie RFID
    pip3 install RPi.GPIO spidev mfrc522
    
    # Installa PN532 con versioni compatibili
    pip3 install adafruit-circuitpython-pn532==2.4.5
    pip3 install adafruit-blinka==8.20.0
    pip3 install adafruit-circuitpython-busdevice==5.2.0
    
    # Abilita I2C
    echo "🔌 Abilitazione I2C..."
    sudo raspi-config nonint do_i2c 0
    
    echo ""
    echo "✅ INSTALLAZIONE COMPLETA!"
    echo ""
    echo "🔧 VERIFICA HARDWARE:"
    echo "sudo i2cdetect -y 1"
    echo ""
    echo "🧪 TEST PN532:"
    echo "python3 test_pn532_compatible.py"
    
else
    # Su macOS/Windows - solo dipendenze Python
    echo "📚 Installazione dipendenze Python (senza hardware)..."
    pip3 install adafruit-circuitpython-pn532 adafruit-blinka
    
    echo ""
    echo "✅ INSTALLAZIONE LIMITATA COMPLETATA"
    echo "⚠️ Test hardware non disponibile su questo sistema"
fi

echo ""
echo "📋 PROSSIMI PASSI:"
echo "1. Connetti hardware PN532 (se su Raspberry Pi)"
echo "2. cp config/examples/.env.pn532_single .env"
echo "3. python3 src/main.py"