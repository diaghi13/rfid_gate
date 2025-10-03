#!/bin/bash
# Script di diagnosi hardware PN532

echo "🔍 DIAGNOSI CONNESSIONI PN532"
echo "=============================="

# Test I2C bus
echo "📡 Test bus I2C:"
if command -v i2cdetect >/dev/null 2>&1; then
    echo "Scansione dispositivi I2C..."
    sudo i2cdetect -y 1
else
    echo "❌ i2cdetect non installato. Installa con: sudo apt install i2c-tools"
fi

echo ""
echo "🔧 Verifica interfacce abilitate:"

# Verifica I2C abilitato
if lsmod | grep -q i2c_bcm2835; then
    echo "✅ I2C abilitato"
else
    echo "❌ I2C non abilitato - Esegui: sudo raspi-config → Interface Options → I2C → Yes"
fi

# Verifica SPI abilitato
if lsmod | grep -q spi_bcm2835; then
    echo "✅ SPI abilitato"
else
    echo "❌ SPI non abilitato - Esegui: sudo raspi-config → Interface Options → SPI → Yes"
fi

echo ""
echo "⚡ Verifica alimentazione:"
echo "Tensione 3.3V dovrebbe essere stabile tra 3.2V e 3.4V"

echo ""
echo "📋 Checklist connessioni PN532:"
echo "□ VCC collegato a Pin 1 (3.3V) - NON Pin 2 (5V)!"
echo "□ GND collegato a Pin 6"
echo "□ SDA(P31) collegato a Pin 3 (GPIO 2)"
echo "□ SCL(P35) collegato a Pin 5 (GPIO 3)"
echo "□ Jumper PN532: LSB=ON, MSB=OFF per I2C"
echo "□ Cavi lunghi max 20cm"
echo "□ Nessun corto circuito"

echo ""
echo "🧪 Test GPIO:"
gpio readall 2>/dev/null | grep -E "(GPIO\. 2|GPIO\. 3)" || echo "Installa wiringpi per test GPIO"