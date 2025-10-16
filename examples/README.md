# 📋 RFID Gate - Esempi Configurazione

# ====================================

Questa directory contiene esempi di configurazione per diversi scenari di deployment.

## 📁 File Disponibili

### Configurazioni Base

- `basic-single-reader.env` - Setup base con singolo lettore
- `dual-reader-bidirectional.env` - Setup bidirezionale con due lettori
- `whitelist-only.env` - Configurazione solo whitelist

### Configurazioni Avanzate

- `enterprise-mqtt.env` - Setup enterprise con MQTT TLS
- `offline-primary.env` - Modalità principalmente offline
- `high-security.env` - Configurazione alta sicurezza

### Configurazioni Hardware

- `raspberry-pi4.env` - Ottimizzato per RPi 4
- `raspberry-pi-zero.env` - Ottimizzato per RPi Zero
- `dual-pn532.env` - Configurazione dual PN532

### Update Manager

- `update-config-production.json` - Config update produzione
- `update-config-development.json` - Config update sviluppo

## 🚀 Utilizzo

1. **Copia il file esempio appropriato**:

   ```bash
   cp examples/basic-single-reader.env .env
   ```

2. **Modifica con i tuoi valori**:

   ```bash
   nano .env
   ```

3. **Testa la configurazione**:
   ```bash
   python main.py --validate-config
   ```

## ⚡ Quick Start

Per iniziare rapidamente con setup standard:

```bash
# Setup base singolo lettore
cp examples/basic-single-reader.env .env

# Setup bidirezionale
cp examples/dual-reader-bidirectional.env .env

# Setup enterprise
cp examples/enterprise-mqtt.env .env
```

## 📞 Supporto

Per domande sui file di configurazione, consulta:

- `docs/CONFIGURATION_EXAMPLES.md` - Guida dettagliata
- `docs/deployment/` - Guide deployment
- GitHub Issues per problemi specifici
