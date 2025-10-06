# 📁 Archive - Sistema RFID Gate Legacy

Questa directory contiene tutti i file del sistema precedente al refactor, mantenuti per:

- Riferimento storico
- Backup di sicurezza
- Debugging eventuali problemi
- Documentazione del processo di sviluppo

## 📂 Struttura Archive

```
archive/
├── old_system/           # Sistema precedente completo
│   ├── src/             # Codice sorgente originale
│   └── config_legacy/   # Configurazioni vecchie
├── old_tests/           # Test del sistema legacy
│   ├── legacy_tests/    # Directory tests/ originale
│   └── test_*.py        # File di test individuali
├── debug_tools/         # Tool di debug e diagnostica
│   ├── debug_*.py       # Script di debug
│   ├── analyze_*.py     # Tool di analisi
│   ├── minimal_*.py     # Implementazioni minime
│   ├── demo_*.py        # Demo e esempi
│   └── *.sh            # Script shell di diagnostica
├── documentation/       # Documentazione sviluppo
│   ├── *.md            # File markdown di documentazione
│   └── README_*.md     # Guide e manuali
└── config_backup/      # Backup configurazioni
    ├── .env.*          # File ambiente backup
    └── requirements_*.txt # Dipendenze alternative
```

## 🔄 Sistema Refactored (Attivo)

Il nuovo sistema si trova in:

- `rfid_gate/` - Codice refactored modulare
- `main_refactored.py` - Entry point principale
- `tests/` - Test del nuovo sistema

## 🚀 Per Utilizzare il Sistema Nuovo

```bash
# Avvia il sistema refactored
python3 main_refactored.py

# Esegui test
python3 tests/test_refactored_system.py
```

## 📋 File Archiviati

### Sistema Legacy

- ✅ `src/` → `archive/old_system/src/`
- ✅ `config/` → `archive/old_system/config_legacy/`

### Test Legacy

- ✅ `tests/` → `archive/old_tests/legacy_tests/`
- ✅ `test_*.py` → `archive/old_tests/`

### Tool Debug

- ✅ `debug_*.py` → `archive/debug_tools/`
- ✅ `analyze_*.py` → `archive/debug_tools/`
- ✅ `minimal_*.py` → `archive/debug_tools/`
- ✅ `demo_*.py` → `archive/debug_tools/`
- ✅ `start_system.py` → `archive/debug_tools/`
- ✅ `*.sh` → `archive/debug_tools/`

### Documentazione

- ✅ `*.md` → `archive/documentation/`

### Configurazioni Backup

- ✅ `.env.dual_spi` → `archive/config_backup/`
- ✅ `.env.optimal` → `archive/config_backup/`
- ✅ `requirements_pn532.txt` → `archive/config_backup/`

## ⚠️ Importante

**NON eliminare questa directory!** Contiene:

- Storia completa dello sviluppo
- Backup del sistema funzionante precedente
- Tool di diagnostica utili per debug futuro
- Documentazione del processo di integrazione PN532

## 🔮 Futuro

Questa archive può essere compressa/esternalizzata quando:

- Sistema refactored testato in produzione per > 6 mesi
- Nessun bug critico trovato
- Team confidenza completa nel nuovo sistema

---

_Archiviato il: $(date)_
_Refactor completato con successo: 100% test passed_
