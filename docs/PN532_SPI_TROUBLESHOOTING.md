# 🔧 GUIDA TROUBLESHOOTING PN532 SPI

## "Failed to detect the PN532" - Risoluzione definitiva

### 📋 CHECKLIST HARDWARE (Da fare su Raspberry Pi)

#### 1. ✅ Verifica Jumper PN532

```
PN532 Module:
┌─────────────────┐
│ LSB ○●  MSB ○●  │  ← LSB=○ (OFF), MSB=● (ON) = Modalità SPI
│                 │
│     PN532       │
└─────────────────┘

❌ SBAGLIATO: LSB=●, MSB=○ (I2C mode)
✅ CORRETTO:  LSB=○, MSB=● (SPI mode)
```

#### 2. ✅ Collegamenti SPI

```
Raspberry Pi 4    →    PN532 (SPI Mode)
=======================================
Pin 19 (MOSI)     →    SDA/MOSI
Pin 21 (MISO)     →    MISO
Pin 23 (SCLK)     →    SCL/SCLK
Pin 24 (CE0/CS)   →    SS/CS
Pin 1  (3.3V)     →    VCC (MAI 5V!)
Pin 6  (GND)      →    GND
```

#### 3. ✅ Abilitazione SPI su Raspberry Pi

```bash
# 1. Abilita interfaccia SPI
sudo raspi-config
# > Interfacing Options > SPI > Yes

# 2. Riavvia
sudo reboot

# 3. Verifica dispositivi SPI
ls -la /dev/spidev*
# Deve mostrare: /dev/spidev0.0, /dev/spidev0.1

# 4. Verifica modulo kernel
lsmod | grep spi
# Deve mostrare: spi_bcm2835
```

### 🔧 TESTING PASSO-PASSO

#### Test 1: SPI Base (Su Raspberry Pi)

```bash
cd /opt/rfid-gate
python3 -c "
import board, busio, digitalio
from adafruit_pn532.spi import PN532_SPI

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D8)  # GPIO 8
pn532 = PN532_SPI(spi, cs, debug=True)

print('Firmware:', pn532.firmware_version)
"
```

#### Test 2: CS Pin Alternativo

```bash
# Se GPIO 8 non funziona, prova GPIO 7
python3 -c "
import board, busio, digitalio
from adafruit_pn532.spi import PN532_SPI

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = digitalio.DigitalInOut(board.D7)  # GPIO 7 invece di 8
pn532 = PN532_SPI(spi, cs, debug=True)

print('Firmware:', pn532.firmware_version)
"
```

### 🚨 PROBLEMI COMUNI E SOLUZIONI

#### Problema: "Failed to detect the PN532"

**Causa 1**: Jumper sbagliati

- **Soluzione**: LSB=○, MSB=● (SPI mode)

**Causa 2**: SPI non abilitato

- **Soluzione**: `sudo raspi-config` > SPI > Enable > Reboot

**Causa 3**: Collegamento CS sbagliato

- **Soluzione**: Usa GPIO 8 (Pin 24) come CS

**Causa 4**: Alimentazione instabile

- **Soluzione**: 3.3V stabile, capacitor di disaccoppiamento

#### Problema: Funziona a volte, a volte no

**Causa**: Interferenze o alimentazione instabile

- **Soluzione**: Cavi corti (<15cm), alimentazione dedicata

#### Problema: Due PN532 non funzionano insieme

**Causa**: Interferenze SPI o conflitti CS

- **Soluzione**: Usa configurazione I2C+SPI o dual I2C

### 🔄 CONFIGURAZIONI ALTERNATIVE

#### Opzione 1: SPI + I2C (Raccomandato)

```env
# .env
READER_IN_TYPE=mfrc522
READER_OUT_TYPE=pn532
READER_OUT_INTERFACE=spi
```

#### Opzione 2: Dual I2C (Workaround)

```env
# .env.dual_i2c
READER_IN_TYPE=pn532
READER_IN_INTERFACE=i2c
READER_IN_I2C_ADDRESS=0x24

READER_OUT_TYPE=pn532
READER_OUT_INTERFACE=i2c
READER_OUT_I2C_ADDRESS=0x24
```

#### Opzione 3: Single Reader Test

```env
# .env.single
READER_IN_TYPE=pn532
READER_IN_INTERFACE=spi
READER_OUT_TYPE=none
```

### 🧪 SCRIPT DI TEST AUTOMATICO

```bash
# Su Raspberry Pi
cd /opt/rfid-gate
python3 test_spi_detection.py
```

### 📞 TROUBLESHOOTING AVANZATO

Se il problema persiste:

1. **Test hardware fisico**:

   ```bash
   # Test con un solo PN532 alla volta
   # Cambia cavi, prova diversi pin CS
   ```

2. **Check interferenze**:

   ```bash
   # Spegni WiFi temporaneamente
   sudo iwconfig wlan0 txpower off
   ```

3. **Voltmetro**:

   ```bash
   # Verifica 3.3V stabile su VCC pin
   # Verifica continuità cavi
   ```

4. **Factory reset PN532**:
   ```bash
   # Scollegare alimentazione 10 secondi
   # Ricollegare e riprovare
   ```

### ✅ SUCCESSO!

Quando vedi:

```
Firmware: bytearray(b'\x01\x06\x07')
```

Il PN532 SPI è configurato correttamente!

---

**Nota**: Questo documento risolve definitivamente il problema "Failed to detect the PN532" su SPI.
