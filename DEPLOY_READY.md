# 🚀 PN532 PRONTO - DEPLOY IMMEDIATO

## ✅ SISTEMA CONFIGURATO

**Branch**: `working-version` (commit a1322a2)
**Setup**: PN532 IN(I2C 0x24) + PN532 OUT(SPI bus 0)

## 🎯 DEPLOY SU RASPBERRY PI

### 1. Clone e setup
```bash
git clone https://github.com/diaghi13/rfid_gate.git
cd rfid_gate
git checkout working-version
```

### 2. Installa dipendenze
```bash
sudo pip3 install -r requirements.txt
```

### 3. TEST hardware
```bash
PYTHONPATH=src python3 test_working_commit.py
```

### 4. AVVIO sistema
```bash
PYTHONPATH=src python3 src/main.py
```

## 🔧 CONFIGURAZIONE ATTUALE

- ✅ PN532 IN: I2C address 0x24
- ✅ PN532 OUT: SPI bus 0, device 0  
- ✅ Anti-crosstalk: Global debounce
- ✅ MQTT: mqbrk.ddns.net:8883

## 📡 WIRING PN532

**IN (I2C 0x24)**:
- VCC → 3.3V, GND → GND
- SDA → GPIO 2, SCL → GPIO 3

**OUT (SPI bus 0)**:
- VCC → 3.3V, GND → GND  
- MOSI → GPIO 10, MISO → GPIO 9
- SCK → GPIO 11, SS → GPIO 8

## 🎉 FATTO!

Il sistema è basato sul commit che **funzionava già** con PN532.
Solo configurato per il tuo setup ibrido I2C+SPI.

**"Deve funzionare al primo colpo"** ✅