# 🔧 GUIDA RAPIDA: INTEGRAZIONE PN532

## ✅ INSTALLAZIONE (1 minuto)

```bash
# 1. Installa dipendenze PN532
pip install -r requirements_pn532.txt

# 2. Test del sistema
python test_multi_rfid_system.py
```

## 🔀 SWITCH TRA LETTORI

### Per usare PN532:

```bash
# Nel file .env, cambia:
RFID_IN_READER_TYPE=pn532
RFID_OUT_READER_TYPE=pn532

# Configurazione I2C (default)
RFID_IN_PN532_INTERFACE=i2c
RFID_IN_PN532_I2C_ADDRESS=0x24
RFID_OUT_PN532_I2C_ADDRESS=0x25
```

### Per tornare a MFRC522:

```bash
# Nel file .env, cambia:
RFID_IN_READER_TYPE=mfrc522
RFID_OUT_READER_TYPE=mfrc522
```

## 📱 CONFIGURAZIONI HARDWARE

### PN532 I2C (Raccomandato per doppio lettore):

- **IN**: Address 0x24
- **OUT**: Address 0x25
- Connessioni: VCC, GND, SDA, SCL

### PN532 SPI (Alternativa):

```bash
RFID_IN_PN532_INTERFACE=spi
RFID_IN_PN532_SPI_BUS=0
RFID_OUT_PN532_SPI_BUS=1
```

### PN532 UART (Per singolo lettore):

```bash
RFID_IN_PN532_INTERFACE=uart
RFID_IN_PN532_UART_PORT=/dev/serial0
```

## 🚀 FUNZIONAMENTO

1. **Compatibilità Totale**: Il codice esistente funziona senza modifiche
2. **Switch Automatico**: Cambia solo il file .env e riavvia
3. **Fallback Robusto**: Se PN532 non funziona, torna automaticamente a MFRC522
4. **Debug Integrato**: Log dettagliati per troubleshooting

## 🔧 TROUBLESHOOTING

### Errore "Libreria PN532 non trovata":

```bash
pip install adafruit-circuitpython-pn532 adafruit-blinka
```

### Errore I2C Address:

- Verifica che i due lettori abbiano indirizzi diversi (0x24, 0x25)
- Controlla i jumper sull'hardware PN532

### Errore SPI:

- Verifica che `spidev` sia installato: `pip install spidev`
- Abilita SPI in raspi-config

## 📊 VANTAGGI PN532

✅ **Migliore per doppio lettore**: Supporto I2C con indirizzi diversi  
✅ **Più stabile**: Meno interferenze nelle letture multiple  
✅ **Veloce**: Tempo di risposta migliorato  
✅ **Versatile**: Supporta più interfacce (I2C, SPI, UART)

## 🔄 ESEMPI CONFIGURAZIONI

### Solo entrata con PN532:

```bash
RFID_IN_READER_TYPE=pn532
RFID_OUT_READER_TYPE=mfrc522
ENABLE_OUT_READER=False
```

### Doppio PN532 per tornello bidirezionale:

```bash
RFID_IN_READER_TYPE=pn532
RFID_OUT_READER_TYPE=pn532
BIDIRECTIONAL_MODE=True
```

**⚡ PRONTO ALL'USO - Cambia solo .env e riavvia!**
