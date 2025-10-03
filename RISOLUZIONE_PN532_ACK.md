# Risoluzione Errore "Did not receive expected ACK from PN532!"

## Problema

Stai riscontrando l'errore:

```
Did not receive expected ACK from PN532!
```

## Soluzioni Passo-Passo

### 1. Verifica Connessioni Hardware

```bash
# Verifica che i2c sia abilitato
sudo raspi-config
# Vai a "Interfacing Options" > "I2C" > "Yes"

# Riavvia dopo aver abilitato I2C
sudo reboot
```

### 2. Verifica Dispositivo PN532

```bash
# Controlla se PN532 è visibile su I2C
sudo i2cdetect -y 1

# Dovresti vedere 0x24 nella griglia
#     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- 24 -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

### 3. Verifica Connessioni Fisiche

**Waveshare PN532:**

- VCC → Pin 1 (3.3V) ⚡ **NON 5V!**
- GND → Pin 6 (GND)
- SDA → Pin 3 (GPIO 2)
- SCL → Pin 5 (GPIO 3)

**Jumper Waveshare:**

- LSB: **ON** (per I2C)
- MSB: **OFF** (per I2C)

### 4. Test Hardware Base

```bash
# Esegui diagnostica hardware
./scripts/diagnose_pn532.sh

# Se vedi errori, verifica alimentazione
# PN532 richiede alimentazione stabile a 3.3V
```

### 5. Test Configurazione Semplificata

```bash
# Usa configurazione single reader per test
python test_pn532_single.py

# Oppure usa il sistema principale con config semplificata
cp config/examples/.env.pn532_single .env
python src/main.py
```

### 6. Risoluzione Avanzata

**Se dispositivo non appare in i2cdetect:**

```bash
# Controlla gpio
gpio readall

# Verifica i2c kernel modules
lsmod | grep i2c
# Dovresti vedere: i2c_bcm2835

# Se mancano, carica manualmente
sudo modprobe i2c-bcm2835
sudo modprobe i2c-dev
```

**Se dispositivo appare ma ACK fallisce:**

```bash
# Test comunicazione diretta
python3 -c "
import board
import busio

try:
    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        pass
    print('I2C devices:', [hex(addr) for addr in i2c.scan()])
    i2c.unlock()
except Exception as e:
    print('Errore I2C:', e)
"
```

### 7. Verifica Librerie

```bash
# Controlla installazione librerie
python3 -c "
try:
    from adafruit_pn532.i2c import PN532_I2C
    print('✅ adafruit_pn532 OK')
except ImportError as e:
    print('❌ adafruit_pn532 mancante:', e)

try:
    import board, busio
    print('✅ board/busio OK')
except ImportError as e:
    print('❌ board/busio mancante:', e)
"

# Se mancanti, reinstalla
pip install --upgrade adafruit-circuitpython-pn532 adafruit-blinka
```

### 8. Reset Hardware

```bash
# Spegni sistema
sudo shutdown -h now

# Scollega alimentazione per 10 secondi
# Riconnetti e riavvia

# Test dopo riavvio
python test_pn532_single.py
```

## Checklist Rapida

- [ ] I2C abilitato in raspi-config
- [ ] PN532 visibile con `sudo i2cdetect -y 1` su 0x24
- [ ] Jumper: LSB=ON, MSB=OFF
- [ ] VCC a 3.3V (NON 5V)
- [ ] Cavi saldamente connessi
- [ ] Librerie installate correttamente
- [ ] Test con configurazione semplificata

## Se Nulla Funziona

1. Testa con MFRC522 per verificare che il resto del sistema funzioni
2. Verifica PN532 su Arduino o altro dispositivo
3. Considera problemi hardware del modulo PN532
4. Contatta supporto Waveshare
