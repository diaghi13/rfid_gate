#!/bin/bash
# Script diagnostico completo PN532 I2C + SPI

echo "🔧 DIAGNOSTICO PN532 COMPLETO"
echo "=============================="

# Test I2C
echo "🔍 Test I2C Bus..."
if command -v i2cdetect &> /dev/null; then
    echo "📡 Dispositivi I2C rilevati:"
    sudo i2cdetect -y 1
    
    if sudo i2cdetect -y 1 | grep -q "24"; then
        echo "✅ PN532 IN (I2C) rilevato all'indirizzo 0x24"
    else
        echo "❌ PN532 IN (I2C) NON rilevato"
        echo "🔧 Verifica:"
        echo "   - Alimentazione 3.3V (NON 5V!)"
        echo "   - Connessioni SDA→Pin3, SCL→Pin5"
        echo "   - Jumper: LSB=●, MSB=○"
    fi
else
    echo "❌ i2cdetect non installato"
    echo "💡 Installa con: sudo apt install i2c-tools"
fi

# Test SPI
echo ""
echo "🔍 Test SPI Bus..."
if ls /dev/spidev* &> /dev/null; then
    echo "✅ SPI dispositivi disponibili:"
    ls -la /dev/spidev*
else
    echo "❌ SPI NON abilitato"
    echo "🔧 Abilita con: sudo raspi-config → Interface → SPI → Yes"
fi

# Test GPIO
echo ""
echo "🔍 Test GPIO Status..."
echo "📍 GPIO 2 (SDA):  $(cat /sys/class/gpio/gpio2/direction 2>/dev/null || echo 'N/A')"
echo "📍 GPIO 3 (SCL):  $(cat /sys/class/gpio/gpio3/direction 2>/dev/null || echo 'N/A')"
echo "📍 GPIO 8 (NSS):  $(cat /sys/class/gpio/gpio8/direction 2>/dev/null || echo 'N/A')"
echo "📍 GPIO 10 (MOSI): $(cat /sys/class/gpio/gpio10/direction 2>/dev/null || echo 'N/A')"

# Test alimentazione (approssimativo)
echo ""
echo "🔍 Test Sistema..."
echo "📊 Temperatura CPU: $(vcgencmd measure_temp)"
echo "📊 Tensione Core: $(vcgencmd measure_volts core)"
echo "📊 Tensione SDRAM: $(vcgencmd measure_volts sdram_c)"

# Test moduli kernel
echo ""
echo "🔍 Test Moduli Kernel..."
if lsmod | grep -q "i2c_dev"; then
    echo "✅ Modulo i2c_dev caricato"
else
    echo "❌ Modulo i2c_dev non caricato"
    echo "💡 Carica con: sudo modprobe i2c_dev"
fi

if lsmod | grep -q "spi_bcm2835"; then
    echo "✅ Modulo SPI caricato"
else
    echo "❌ Modulo SPI non caricato"
    echo "💡 Carica con: sudo modprobe spi_bcm2835"
fi

echo ""
echo "✅ DIAGNOSTICO COMPLETATO!"
echo ""
echo "🔧 PROSSIMI PASSI:"
echo "1. Risolvi errori hardware evidenziati"
echo "2. Test singolo lettore: ENABLE_OUT_READER=False"
echo "3. Test sistema: python3 src/main.py"