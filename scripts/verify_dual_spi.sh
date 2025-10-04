#!/bin/bash
# Verifica configurazione dual PN532 SPI

echo "🔧 VERIFICA DUAL PN532 SPI"
echo "========================="

# Verifica SPI abilitato
echo "🔍 Verifica SPI..."
if lsmod | grep -q spi_bcm2835; then
    echo "✅ Modulo SPI caricato"
else
    echo "❌ SPI non abilitato"
    echo "💡 Abilita con: sudo raspi-config → Interface → SPI → Yes"
fi

# Verifica device SPI
echo ""
echo "🔍 Device SPI disponibili:"
ls -la /dev/spidev* 2>/dev/null || echo "❌ Nessun device SPI trovato"

# Verifica jumper setup
echo ""
echo "🔧 SETUP JUMPER PN532 per SPI:"
echo "   Entrambi i PN532 devono avere:"
echo "   LSB = ○ (vuoto)"  
echo "   MSB = ● (jumper)"
echo "   → Questo configura interfaccia SPI"

# Test GPIO CS pins
echo ""
echo "🔍 Test GPIO CS pins..."
echo "📍 CS0 (GPIO 8) → PN532 IN"
echo "📍 CS1 (GPIO 7) → PN532 OUT"

# Test lettura GPIO
if command -v gpio >/dev/null 2>&1; then
    echo "GPIO 8 (CS0): $(gpio read 8)"
    echo "GPIO 7 (CS1): $(gpio read 7)"
else
    echo "💡 Installa wiringpi per test GPIO: sudo apt install wiringpi"
fi

echo ""
echo "🔌 SCHEMA COLLEGAMENTO:"
echo "PN532 IN  → /dev/spidev0.0 (CS0 = GPIO 8)"
echo "PN532 OUT → /dev/spidev0.1 (CS1 = GPIO 7)"
echo ""
echo "Bus SPI condiviso:"
echo "MOSI → GPIO 10 (Pin 19)"
echo "MISO → GPIO 9  (Pin 21)" 
echo "SCK  → GPIO 11 (Pin 23)"