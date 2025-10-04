# 🔧 CONFIGURAZIONE IBRIDA: PN532 IN(I2C) + OUT(SPI)

## 📋 COLLEGAMENTI HARDWARE

### 🔵 PN532 INGRESSO - I2C (Indirizzo 0x24)

```
PN532 IN → Raspberry Pi 4
=======================
VCC     → Pin 1  (3.3V)
GND     → Pin 6  (GND)
SDA     → Pin 3  (GPIO 2 / SDA)
SCL     → Pin 5  (GPIO 3 / SCL)

⚙️ JUMPER: LSB=● (ON), MSB=○ (OFF) = I2C Mode
```

### 🟡 PN532 USCITA - SPI (CS0)

```
PN532 OUT → Raspberry Pi 4
========================
VCC      → Pin 1  (3.3V)
GND      → Pin 6  (GND)
MOSI     → Pin 19 (GPIO 10 / MOSI)
MISO     → Pin 21 (GPIO 9  / MISO)
SCK      → Pin 23 (GPIO 11 / SCLK)
SS/CS    → Pin 24 (GPIO 8  / CE0)

⚙️ JUMPER: LSB=○ (OFF), MSB=● (ON) = SPI Mode
```

### ⚡ RELÈ

```
Relè IN  → Pin 12 (GPIO 18)
Relè OUT → Pin 35 (GPIO 19)
```

## 🎯 VANTAGGI CONFIGURAZIONE IBRIDA

✅ **Nessun conflitto indirizzi** - I2C e SPI sono indipendenti  
✅ **Massima compatibilità** - Funziona anche se SPI ha problemi  
✅ **Performance ottimale** - Lettori completamente paralleli  
✅ **Facile troubleshooting** - Interfacce separate

## 🧪 TEST CONFIGURAZIONE

### Test PN532 IN (I2C)

```bash
python3 -c "
import board, busio
from adafruit_pn532.i2c import PN532_I2C
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, address=0x24)
print('IN Firmware:', pn532.firmware_version)
"
```

### Test PN532 OUT (SPI)

```bash
python3 -c "
import board, busio, digitalio
from adafruit_pn532.spi import PN532_SPI
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D8)
pn532 = PN532_SPI(spi, cs)
print('OUT Firmware:', pn532.firmware_version)
"
```

## 🔧 TROUBLESHOOTING

### Se PN532 IN (I2C) non funziona:

1. Verifica jumper: LSB=●, MSB=○
2. Test: `i2cdetect -y 1` (deve mostrare indirizzo 24)
3. Verifica alimentazione 3.3V

### Se PN532 OUT (SPI) non funziona:

1. Verifica jumper: LSB=○, MSB=●
2. Abilita SPI: `sudo raspi-config > Interface > SPI`
3. Test: `ls /dev/spidev*` (deve mostrare dispositivi)

### Fallback Emergency:

Se SPI non funziona, modifica `.env`:

```env
# Cambia OUT da SPI a I2C con indirizzo diverso
RFID_OUT_PN532_INTERFACE=i2c
RFID_OUT_PN532_I2C_ADDRESS=0x25
```

## 🚀 AVVIO SISTEMA

```bash
cd /opt/rfid-gate
python3 src/main.py
```

---

**Configurazione testata**: ✅ I2C + SPI ibrido  
**Status**: Pronto per deploy Raspberry Pi
