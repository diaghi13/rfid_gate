# 🔧 Tools & Scripts - RFID Gate System

Questa directory contiene strumenti organizzati e script per la gestione del sistema RFID Gate refactorizzato.

## 📁 Struttura Organizzata

### 🛠️ **Tools (`tools/`)**

Strumenti Python avanzati per gestione sistema:

- **`update_manager.py`** 🔄  
  Manager moderno per aggiornamenti con GitHub integration, backup/rollback automatico

  ```bash
  python3 tools/update_manager.py --diagnostic    # Diagnostica sistema
  python3 tools/update_manager.py --check         # Controlla aggiornamenti
  python3 tools/update_manager.py --auto          # Aggiornamento automatico
  ```

- **`rfid_diagnostic.py`** 🔍  
  Diagnostica specifica per lettori RFID (MFRC522, PN532)

- **`manual_open_tool.py`** 🔓  
  Strumento per apertura manuale cancello (emergenze)

- **`log_viewer.py`** 📄  
  Visualizzatore logs con filtri e analisi

- **`offline_diagnostics.py`** 📡  
  Diagnostica modalità offline e coda messaggi

### 📜 **Scripts (`scripts/`)**

Script bash per automazione e setup:

#### 🔄 **Aggiornamenti**

- **`modern_update.sh`** - Wrapper moderno per aggiornamenti
- **`update.sh`** - Script legacy aggiornato per nuova architettura

#### 🔍 **Diagnostica**

- **`system_diagnostic.sh`** - Script unificato per diagnostica completa
- **`diagnose_pn532.sh`** - Diagnostica specifica PN532 _(da consolidare)_
- **`verify_dual_spi.sh`** - Verifica configurazione dual SPI _(da consolidare)_

#### ⚙️ **Setup & Management**

- **`install.sh`** - Installazione automatica sistema
- **`setup_service.sh`** - Configurazione servizio systemd
- **`management.sh`** - Gestione servizio (start/stop/status)
- **`cleanup.sh`** - Pulizia logs e file temporanei

#### 🧪 **Testing & Verification**

- **`test_readers.sh`** - Test lettori RFID
- **`verify_refactor.sh`** - Verifica refactoring completato

## 🚀 **Quick Start**

### 1. **Diagnostica Sistema Completa**

```bash
# Script unificato (raccomandato)
./scripts/system_diagnostic.sh

# Tool Python avanzato
python3 tools/update_manager.py --diagnostic
```

### 2. **Aggiornamento Sistema**

```bash
# Modalità moderna (raccomandato)
./scripts/modern_update.sh --check          # Controlla aggiornamenti
./scripts/modern_update.sh --interactive    # Aggiornamento guidato
sudo ./scripts/modern_update.sh --auto      # Aggiornamento automatico

# Modalità legacy (compatibilità)
./scripts/update.sh
```

### 3. **Gestione Servizio**

```bash
./scripts/management.sh status    # Stato servizio
./scripts/management.sh start     # Avvia servizio
./scripts/management.sh stop      # Ferma servizio
./scripts/management.sh restart   # Riavvia servizio
```

### 4. **Diagnostica Hardware**

```bash
# Diagnostica completa
./scripts/system_diagnostic.sh

# Test specifici
./scripts/system_diagnostic.sh --hardware     # Solo hardware
./scripts/system_diagnostic.sh --dependencies # Solo dipendenze Python
./scripts/test_readers.sh                     # Test lettori RFID
```

## 📋 **Checklist Refactoring**

### ✅ **Completato:**

- [x] Update Manager moderno con GitHub integration
- [x] Script diagnostico unificato
- [x] Requirements.txt pulito (rimossi duplicati)
- [x] Architettura modulare `rfid_gate/` funzionale
- [x] Script legacy aggiornati per nuova struttura
- [x] Sistema backup/rollback automatico
- [x] Fallback per dipendenze mancanti

### 🔄 **Da Consolidare:**

- [ ] Unificare `diagnose_pn532.sh` e `verify_dual_spi.sh` nel nuovo `system_diagnostic.sh`
- [ ] Rimuovere script ridondanti dopo verifica
- [ ] Aggiornare documentazione in `docs/`

### 🎯 **Raccomandazioni:**

1. **Usa sempre il sistema moderno:**

   ```bash
   ./scripts/modern_update.sh --diagnostic  # Prima diagnostica
   ./scripts/modern_update.sh --check       # Poi controlla aggiornamenti
   ```

2. **Per troubleshooting:**

   ```bash
   ./scripts/system_diagnostic.sh           # Diagnostica completa
   python3 tools/rfid_diagnostic.py         # Diagnostica RFID specifica
   ```

3. **Per aggiornamenti:**
   ```bash
   sudo ./scripts/modern_update.sh --auto   # Automatico con backup
   ```

## 🔗 **File Correlati**

- `requirements.txt` - Dipendenze Python (pulite dai duplicati)
- `update_config.json` - Configurazione sistema aggiornamenti
- `.env` - Configurazione ambiente (preservata durante aggiornamenti)

---

**Nota:** Questo sistema sostituisce i vecchi script sparsi con un approccio organizzato e modulare, mantenendo compatibilità con il sistema legacy dove necessario.
