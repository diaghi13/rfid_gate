# Changelog

Tutte le modifiche importanti a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.2.1] - 2025-10-31

### 🔧 Fixed

- **CRITICAL**: Fixed MQTT subscription persistence after broker reconnection
- Badge requests now properly received after broker restart
- Enhanced auth response callback handling for legacy topic formats
- Improved `_on_message` topic detection: `'response' in topic AND 'tornello' in topic`

### ✨ Added

- `_ensure_subscriptions_active()` method for post-connection verification
- Enhanced subscription restoration after automatic reconnection
- Comprehensive subscription persistence test (`test_subscription_persistence.py`)
- Better topic pattern recognition for legacy formats

### 🛠️ Improved

- More robust subscription restoration process
- Enhanced callback triggering for `gate/*/response` topics
- Added detailed logging for subscription setup and verification
- Production tested: both heartbeat and badge requests functional after broker restart

### 📦 Deployment

- Ready for immediate production deployment
- Backward compatible with existing configurations
- No breaking changes to API or configuration format

## [Unreleased - Archive]

### Added

- Sistema di riorganizzazione file progetto
- Documentazione strutturata per deployment
- Test suite organizzata per tipologia

### Changed

- Struttura directory più logica e professionale
- File di test spostati in tests/debug/
- Documentazione riorganizzata per argomenti

## [2.0.0] - 2025-10-16

### Added

- 🏗️ **Architettura modulare completa** - Refactoring da monolite a moduli
- 🔄 **Sistema controllo bidirezionale** con timeout configurabile
- 📦 **Sistema update automatico** con GitHub integration
- 🎯 **Flusso intelligente 3-casi** (cache hit, miss, refresh)
- 🌐 **WebUI moderna** con FastAPI e real-time updates
- 🔐 **Sistema whitelist** con bypass IN/OUT
- 📊 **Logging avanzato** con rotazione e analytics
- 🛠️ **Tools diagnostici** per troubleshooting
- 📱 **Supporto dual-reader** (PN532 + MFRC522)
- 🔄 **Cache refresh intelligente** per abbonamenti
- 📡 **MQTT parallelo** per logging server
- 🎛️ **Configurazione centralizzata** via .env

### Changed

- **Breaking**: Struttura directory completamente rinnovata
- **Breaking**: Entry point da `src/main.py` a `main.py`
- **Breaking**: Configurazione unificata in RFIDGateConfig
- Migliorata performance con cache locale SQLite
- Ottimizzato controllo accessi con validazione sequenziale

### Fixed

- Eliminati doppi log sistemici
- Corretti race condition nel debounce
- Risolti problemi timeout MQTT
- Fix gestione errori relay
- Corretta sincronizzazione offline

### Security

- Validazione input sanitizzata
- Controlli permessi file system
- Configurazione sicura MQTT TLS

## [1.0.0] - 2025-08-01

### Added

- Sistema base RFID Gate
- Supporto lettore MFRC522
- Controllo relay GPIO
- Comunicazione MQTT base
- Logging essenziale
- Configurazione via .env

### Features Initial Release

- Lettura carte RFID
- Controllo accessi base
- Integrazione MQTT broker
- Gestione offline semplice
- Log accessi CSV

---

## Tipi di Modifiche

- **Added** per nuove funzionalità
- **Changed** per modifiche a funzionalità esistenti
- **Deprecated** per funzionalità che saranno rimosse
- **Removed** per funzionalità rimosse
- **Fixed** per bug fix
- **Security** per vulnerabilità corrette
