# 🔧 Esempi di Configurazioni

## 📝 Configurazione 1: Solo Ingresso (Unidirezionale)
```bash
# Sistema con un solo lettore RFID e un relè per l'ingresso
BIDIRECTIONAL_MODE=False
ENABLE_IN_READER=True
ENABLE_OUT_READER=False

# RFID Reader IN
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# RFID Reader OUT (disabilitato)
RFID_OUT_ENABLE=False

# Relè IN
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=False
RELAY_IN_INITIAL_STATE=LOW
RELAY_IN_ENABLE=True

# Relè OUT (disabilitato)
RELAY_OUT_ENABLE=False
```

## 🔄 Configurazione 2: Sistema Bidirezionale Completo
```bash
# Sistema con due lettori RFID e relè a due canali
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=True

# RFID Reader IN
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# RFID Reader OUT
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=True

# Relè IN
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=False
RELAY_IN_INITIAL_STATE=LOW
RELAY_IN_ENABLE=True

# Relè OUT
RELAY_OUT_PIN=19
RELAY_OUT_ACTIVE_TIME=2
RELAY_OUT_ACTIVE_LOW=False
RELAY_OUT_INITIAL_STATE=LOW
RELAY_OUT_ENABLE=True
```

## ↩️ Configurazione 3: Solo Uscita
```bash
# Sistema con solo lettore e relè per l'uscita
BIDIRECTIONAL_MODE=False
ENABLE_IN_READER=False
ENABLE_OUT_READER=True

# RFID Reader IN (disabilitato)
RFID_IN_ENABLE=False

# RFID Reader OUT
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=True

# Relè IN (disabilitato)
RELAY_IN_ENABLE=False

# Relè OUT
RELAY_OUT_PIN=19
RELAY_OUT_ACTIVE_TIME=3
RELAY_OUT_ACTIVE_LOW=False
RELAY_OUT_INITIAL_STATE=LOW
RELAY_OUT_ENABLE=True
```

## 🎛️ Configurazione 4: Due Lettori, Un Solo Relè
```bash
# Due lettori RFID che controllano lo stesso relè
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=True

# RFID Reader IN
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True

# RFID Reader OUT
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=True

# Solo Relè IN attivo (condiviso)
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=False
RELAY_IN_INITIAL_STATE=LOW
RELAY_IN_ENABLE=True

# Relè OUT disabilitato
RELAY_OUT_ENABLE=False
```

## 🔧 Configurazione 5: Relè Attivi LOW (per alcuni moduli)
```bash
# Per relè che si attivano con segnale LOW
BIDIRECTIONAL_MODE=True
ENABLE_IN_READER=True
ENABLE_OUT_READER=True

# RFID standard
RFID_IN_RST_PIN=22
RFID_IN_SDA_PIN=8
RFID_IN_ENABLE=True
RFID_OUT_RST_PIN=25
RFID_OUT_SDA_PIN=7
RFID_OUT_ENABLE=True

# Relè con logica invertita
RELAY_IN_PIN=18
RELAY_IN_ACTIVE_TIME=2
RELAY_IN_ACTIVE_LOW=True     # Attivo con LOW
RELAY_IN_INITIAL_STATE=HIGH  # Parte HIGH (relè spento)
RELAY_IN_ENABLE=True

RELAY_OUT_PIN=19
RELAY_OUT_ACTIVE_TIME=2
RELAY_OUT_ACTIVE_LOW=True    # Attivo con LOW
RELAY_OUT_INITIAL_STATE=HIGH # Parte HIGH (relè spento)
RELAY_OUT_ENABLE=True
```

## 📋 Pin Mapping Raccomandati

### 🔌 RFID RC522
```
Modulo IN:  RST=22, SDA=8  (SPI0)
Modulo OUT: RST=25, SDA=7  (SPI1)
```

### ⚡ Relè
```
Relè IN:  GPIO 18
Relè OUT: GPIO 19
```

### 🔄 GPIO Liberi Disponibili
```
GPIO disponibili: 2, 3, 4, 5, 6, 12, 13, 16, 17, 20, 21, 23, 24, 26, 27
```

## 🚀 Test delle Configurazioni

Dopo aver modificato il file `.env`, testa sempre:

```bash
# Test configurazione
sudo python3 -c "from config import Config; Config.print_config()"

# Test completo
sudo python3 main.py
```

## ⚠️ Note Importanti

1. **Pin SDA/SS**: Ogni lettore RFID deve avere un pin SDA diverso
2. **Pin Relè**: Ogni relè deve avere un GPIO diverso  
3. **Alimentazione**: Ogni modulo RFID ha bisogno di 3.3V
4. **GND Comune**: Tutti i dispositivi condividono lo stesso GND
5. **SPI**: Deve essere abilitato con `sudo raspi-config`
