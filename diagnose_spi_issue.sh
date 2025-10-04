#!/bin/bash
# Diagnosi completa problema PN532 SPI

echo "🔍 DIAGNOSI PN532 SPI - Rilevazione Fallita"
echo "==========================================="

# 1. Verifica SPI abilitato nel sistema
echo "📋 1. Verifica SPI Sistema:"
if lsmod | grep -q spi_bcm2835; then
    echo "✅ Modulo SPI caricato"
else
    echo "❌ Modulo SPI NON caricato"
    echo "💡 Abilita SPI: sudo raspi-config → Interface → SPI → Yes"
fi

echo ""
echo "📋 2. Device SPI disponibili:"
if ls /dev/spidev* 2>/dev/null; then
    echo "✅ Device SPI trovati"
    ls -la /dev/spidev*
else
    echo "❌ Nessun device SPI trovato"
    echo "💡 Verifica: sudo raspi-config → Interface → SPI → Yes"
fi

echo ""
echo "📋 3. Configurazione boot SPI:"
if grep -q "dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    echo "✅ SPI abilitato in /boot/config.txt"
else
    echo "❌ SPI NON abilitato in /boot/config.txt"
    echo "💡 Aggiungi: dtparam=spi=on"
fi

echo ""
echo "📋 4. Permissions device SPI:"
if [ -c /dev/spidev0.0 ]; then
    ls -la /dev/spidev0.0
    echo "🔍 Groups utente corrente:"
    groups
    if groups | grep -q spi; then
        echo "✅ Utente nel gruppo 'spi'"
    else
        echo "⚠️ Utente NON nel gruppo 'spi'"
        echo "💡 Aggiungi: sudo usermod -a -G spi \$USER"
    fi
else
    echo "❌ /dev/spidev0.0 non esistente"
fi

echo ""
echo "📋 5. Test GPIO CS pins:"
echo "📍 CS0 (GPIO 8) per PN532 OUT"
echo "📍 CS1 (GPIO 7) disponibile come alternativa"

if command -v gpio >/dev/null 2>&1; then
    echo "GPIO 8 (CS0): $(gpio read 8)"
    echo "GPIO 7 (CS1): $(gpio read 7)"
else
    echo "💡 Installa wiringpi per test GPIO dettagliati"
fi

echo ""
echo "📋 6. Verifica alimentazione:"
echo "🔋 PN532 richiede alimentazione 3.3V stabile"
echo "⚠️ Verifica che entrambi i PN532 abbiano alimentazione adeguata"

echo ""
echo "📋 7. Verifica jumper PN532:"
echo "🔧 Per SPI il PN532 deve avere:"
echo "   LSB = ○ (vuoto)"
echo "   MSB = ● (jumper)"

echo ""
echo "📋 8. Schema collegamento SPI:"
echo "PN532 OUT (SPI):"
echo "   VCC → 3.3V"
echo "   GND → GND"
echo "   MOSI → GPIO 10 (Pin 19)"
echo "   MISO → GPIO 9 (Pin 21)"
echo "   SCK → GPIO 11 (Pin 23)"
echo "   NSS/CS → GPIO 8 (Pin 24)  ← CRITICO!"

echo ""
echo "🔧 SOLUZIONI IMMEDIATE:"
echo "1. Verifica jumper SPI su PN532 OUT"
echo "2. Controlla collegamento CS (NSS) a GPIO 8"
echo "3. Verifica alimentazione 3.3V stabile"
echo "4. Test con solo lettore SPI (disabilita I2C temporaneamente)"