# 🌐 Guida Sistema Offline - Fallback Internet

## 📖 Panoramica

Il sistema di fallback offline garantisce la continuità operativa del controllo accessi anche in caso di interruzione della connessione internet. Gli accessi vengono autorizzati localmente e sincronizzati automaticamente quando la connessione viene ripristinata.

## 🔧 Configurazione

### File `.env`
```bash
# Configurazione Fallback Offline
OFFLINE_MODE_ENABLED=True          # Abilita sistema offline
OFFLINE_ALLOW_ACCESS=True          # Consenti accessi in modalità offline
OFFLINE_SYNC_ENABLED=True          # Abilita sincronizzazione automatica
OFFLINE_STORAGE_FILE=offline_queue.json  # File per persistenza coda
OFFLINE_MAX_QUEUE_SIZE=1000        # Massimo elementi in coda
CONNECTION_CHECK_INTERVAL=30       # Secondi tra controlli connessione
CONNECTION_RETRY_ATTEMPTS=3        # Tentativi max per sync elemento
```

## 🚀 Funzionamento

### 📡 Modalità Online (Normale)
1. **Card rilevata** → Invia richiesta MQTT al server
2. **Server risponde** → Autorizza/Nega accesso
3. **Se autorizzato** → Attiva relè
4. **Logging** → Registra accesso nei log

### 🔴 Modalità Offline (Fallback)
1. **Card rilevata** → Sistema offline rilevato
2. **Accesso locale** → Autorizza automaticamente (se configurato)
3. **Attiva relè** → Consente passaggio
4. **Coda sync** → Salva dati per sincronizzazione futura
5. **Logging** → Registra accesso offline

### 🔄 Sincronizzazione Automatica
1. **Connessione ripristinata** → Sistema rileva connessione
2. **Sync automatica** → Invia dati in coda al server
3. **Conferma ricezione** → Rimuove dati dalla coda
4. **Retry intelligente** → Riprova elementi falliti

## 📊 Monitoraggio

### Status Sistema
```bash
# Mostra stato sistema offline
python3 offline_utils.py --status

# Test connessione
python3 offline_utils.py --test-connection
```

### Gestione Coda
```bash
# Visualizza coda elementi offline
python3 offline_utils.py --queue

# Forza sincronizzazione immediata
python3 offline_utils.py --sync

# Statistiche dettagliate
python3 offline_utils.py --stats
```

## 🛠️ Utilità di Gestione

### 📤 Export Dati
```bash
# Esporta coda in file JSON
python3 offline_utils.py --export backup_offline.json
```

### 🧹 Pulizia Sistema
```bash
# ATTENZIONE: Cancella tutti i dati in coda!
python3 offline_utils.py --clear
```

## 📋 Scenari d'Uso

### 🔌 Interruzione Internet
1. **Rilevamento automatico** → Sistema passa in modalità offline
2. **Notifica utente** → "🔴 Modalità Offline Attiva"
3. **Accessi continuano** → Tornello funziona normalmente
4. **Dati salvati** → Accumulati per sync futura

### 🌐 Ripristino Connessione
1. **Rilevamento automatico** → "🟢 Connessione Ripristinata"
2. **Sync automatica** → Dati inviati al server
3. **Modalità normale** → Sistema torna online

### 💾 Persistenza Dati
- **File JSON** → Coda salvata su disco
- **Sopravvive riavvii** → Dati non persi
- **Dimensione controllata** → Max elementi configurabile
- **Rotazione automatica** → Elementi più vecchi rimossi se coda piena

## ⚠️ Considerazioni di Sicurezza

### 🔒 Modalità Offline
- **Accessi autorizzati localmente** → Nessuna verifica server
- **Configurabile** → Può essere disabilitata per sicurezza massima
- **Tracciabilità** → Tutti gli accessi offline sono loggati
- **Sync obbligatoria** → Dati devono essere sincronizzati

### 🛡️ Raccomandazioni
1. **Monitoraggio attivo** → Controllare regolarmente status sistema
2. **Backup coda** → Esportare periodicamente dati offline
3. **Connessione ridondante** → Considerare backup internet (4G/5G)
4. **Notifiche** → Implementare alert per disconnessioni prolungate

## 🔍 Risoluzione Problemi

### 🔴 Sistema sempre offline
```bash
# Test connessione specifica
python3 offline_utils.py --test-connection

# Verifica configurazioni
python3 -c "from config import Config; Config.print_config()"
```

### 📤 Sync non funziona
1. **Verifica connessione MQTT**
2. **Controlla credenziali** 
3. **Verifica certificati TLS**
4. **Log errori** → Controllare `logs/system.log`

### 💾 Coda troppo grande
```bash
# Statistiche dettagliate
python3 offline_utils.py --stats

# Export e pulizia selettiva
python3 offline_utils.py --export backup.json
python3 offline_utils.py --clear  # Dopo backup
```

### 🔄 Elementi bloccati in coda
- **Tentativi multipli** → Ogni elemento riprova fino a `CONNECTION_RETRY_ATTEMPTS`
- **Scadenza** → Elementi con troppi tentativi vengono scartati
- **Manuale** → Forzare sync con `--sync`

## 📈 Metriche e KPI

### 📊 Metriche Sistema
- **Uptime connessione** → % tempo online/offline
- **Elementi in coda** → Numero accessi da sincronizzare
- **Tasso sync** → % successo sincronizzazione
- **Tempo ripristino** → Tempo per sync completa dopo reconnect

### 🎯 Obiettivi Raccomandati
- **Uptime** → >99% (massimo 1% tempo offline)
- **Coda** → <50 elementi in condizioni normali
- **Sync rate** → >95% successo
- **Recovery time** → <5 minuti per sync completa

## 🚨 Alert e Notifiche

Il sistema registra eventi importanti nei log:

```bash
# Monitoraggio eventi critici
tail -f logs/system.log | grep -E "(connection_lost|offline_sync|queue_full)"
```

### Eventi da Monitorare:
- `connection_lost` → Connessione internet persa
- `connection_restored` → Connessione ripristinata
- `offline_sync_completed` → Sincronizzazione completata
- `offline_queue_full` → Coda offline al limite

## 🎛️ Tuning Prestazioni

### ⚡ Configurazioni Ottimali

**Per ambienti stabili:**
```bash
CONNECTION_CHECK_INTERVAL=60      # Check meno frequenti
OFFLINE_MAX_QUEUE_SIZE=500       # Coda più piccola
```

**Per ambienti instabili:**
```bash
CONNECTION_CHECK_INTERVAL=15     # Check più frequenti
OFFLINE_MAX_QUEUE_SIZE=2000      # Coda più grande
CONNECTION_RETRY_ATTEMPTS=5      # Più tentativi
```

**Per sicurezza massima:**
```bash
OFFLINE_ALLOW_ACCESS=False       # No accessi offline
OFFLINE_SYNC_ENABLED=True        # Solo sync dati esistenti
```

Il sistema offline garantisce la continuità operativa mantenendo la tracciabilità e sincronizzazione di tutti gli accessi! 🎯
