# 📝 Sistema di Logging Duale - Documentazione Tecnica

**Data aggiornamento:** 15 ottobre 2025  
**Versione:** v2.6 - Dual Logging Architecture

## 🎯 OVERVIEW SISTEMA LOGGING

Il sistema RFID Gate implementa un **doppio flusso di logging** per massimizzare sia l'efficienza che l'affidabilità:

### 📋 **Due Flussi Distinti:**

1. **📝 Log Locali** → Sempre salvati per backup/download
2. **📡 Sync al Server** → Solo quando necessario (MQTT fallisce)

---

## 🏗️ ARCHITETTURA TECNICA

### 📊 **Flusso Completo:**

```
Card Detection → MQTT Parallelo (non-bloccante)
                ↓
                Authentication Local (immediata)
                ↓
                ┌─ 📝 Log LOCALE (sempre salvato)
                │   ├─ File: logs/access_log.json
                │   ├─ DB: cache/local_cache.db (pending_logs)
                │   └─ Scopo: Backup, download, audit
                │
                └─ 📡 Sync SERVER (condizionale)
                    ├─ Se MQTT OK → sync saltato
                    ├─ Se MQTT FAIL → sync immediato
                    └─ Se offline → queue per retry
```

### 🔧 **Componenti Coinvolti:**

#### 1. **AccessControlSystem** (`rfid_gate/core/access_control.py`)

- Gestisce i due flussi di logging
- Decide quando sincronizzare al server
- Mantiene log locali sempre attivi

#### 2. **SyncManager** (`rfid_gate/network/sync_manager.py`)

- Salva log in SQLite locale (`pending_logs`)
- Gestisce queue retry per server offline
- Background sync automatico

#### 3. **MQTTConfig** (`rfid_gate/config/settings.py`)

- Controlla comportamento dual logging
- Configurazioni separate per i due flussi

---

## ⚙️ CONFIGURAZIONE

### 📄 **Variabili .env:**

```bash
# ✨ Configurazioni MQTT Parallelo e Logging
MQTT_PARALLEL_AUTH=True                    # MQTT parallelo, non-bloccante
MQTT_SYNC_LOGS_ONLY_ON_FAILURE=True      # Sync server solo se MQTT fallisce
MQTT_ALWAYS_LOG_LOCALLY=True              # Log locali sempre salvati
MQTT_ENABLE_RETRY_QUEUE=True              # Queue retry per connessioni perse
MQTT_MAX_RETRY_QUEUE_SIZE=1000            # Dimensione max queue retry
MQTT_RETRY_INTERVAL=30                    # Intervallo retry in secondi
```

### 🎛️ **Modalità Operative:**

| Configurazione                         | Comportamento                                      |
| -------------------------------------- | -------------------------------------------------- |
| `MQTT_ALWAYS_LOG_LOCALLY=True`         | **Log locali SEMPRE salvati** (raccomandato)       |
| `MQTT_SYNC_LOGS_ONLY_ON_FAILURE=True`  | **Sync server solo se MQTT fallisce** (efficiente) |
| `MQTT_SYNC_LOGS_ONLY_ON_FAILURE=False` | **Sync server sempre** (ridondante ma sicuro)      |

---

## 📊 FLUSSI OPERATIVI

### ✅ **Scenario 1: MQTT Funzionante**

```
1. Card detected → MQTT parallelo ✅ INVIATO
2. Auth locale → ✅ AUTORIZZATO
3. Log locale → ✅ SALVATO (access_log.json + DB)
4. Sync server → ⏭️ SALTATO (server riceve via MQTT)
```

**Risultato:** Log locale per backup, server aggiornato via MQTT

### ⚠️ **Scenario 2: MQTT Fallito**

```
1. Card detected → MQTT parallelo ❌ FALLITO
2. Auth locale → ✅ AUTORIZZATO
3. Log locale → ✅ SALVATO (access_log.json + DB)
4. Sync server → ✅ FORZATO (compensazione MQTT)
```

**Risultato:** Log locale + sync compensativo al server

### 📴 **Scenario 3: Sistema Offline**

```
1. Card detected → MQTT ❌ NON DISPONIBILE
2. Auth locale → ✅ AUTORIZZATO (cache)
3. Log locale → ✅ SALVATO (pending_logs queue)
4. Sync server → 📦 IN CODA (retry quando online)
```

**Risultato:** Log locale + queue per sync futuro

---

## 🗃️ STORAGE E PERSISTENZA

### 📁 **File di Log:**

#### 1. **access_log.json** (`logs/access_log.json`)

```json
{
  "timestamp": "2025-10-15T14:30:15.123Z",
  "card_uid": "A1B2C3D4",
  "direction": "IN",
  "result": "authorized",
  "reason": "Card trovata in cache | Local",
  "customer_id": 12345,
  "customer_name": "Mario Rossi"
}
```

#### 2. **SQLite Cache** (`cache/local_cache.db`)

```sql
-- Tabella pending_logs per sync al server
CREATE TABLE pending_logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    card_uid TEXT,
    result TEXT,
    customer_id INTEGER,
    synced BOOLEAN DEFAULT 0  -- 0 = pending, 1 = synced
);
```

### 🔄 **Ciclo di Vita Log:**

1. **Creazione** → Salvato in access_log.json + pending_logs
2. **Sync tentativo** → Se server disponibile e MQTT fallito
3. **Marcatura** → pending_logs.synced = 1 se riuscito
4. **Cleanup** → Rimozione log sincronizzati vecchi

---

## 🎛️ CONTROLLO AVANZATO

### 📊 **Monitoring Status:**

```python
from rfid_gate.network.sync_manager import SyncManager

# Controlla stato queue
status = sync_manager.get_sync_status()
print(f"Pending logs: {status['pending_logs']}")
print(f"Online: {status['is_online']}")
```

### 🛠️ **Operazioni Manuali:**

```bash
# Forza sync manuale
python3 -c "
import asyncio
from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import RFIDGateConfig

async def force_sync():
    config = RFIDGateConfig.from_env()
    sm = SyncManager(config, 'tornello_01')
    await sm._sync_logs()

asyncio.run(force_sync())
"
```

### 📥 **Download Log Locali:**

I log locali sono sempre disponibili per download in:

- `logs/access_log.json` - Formato JSON
- `logs/access_log.csv` - Formato CSV (se configurato)

---

## 🎯 VANTAGGI ARCHITETTURA

### ⚡ **Performance:**

- **Zero latenza** per autenticazione utente
- **MQTT parallelo** non blocca il flusso
- **Sync condizionale** riduce carico rete

### 🛡️ **Affidabilità:**

- **Log sempre salvati** localmente per audit
- **Queue resiliente** per server offline
- **Compensazione automatica** per MQTT falliti

### 📊 **Efficienza:**

- **Nessuna duplicazione** quando MQTT funziona
- **Retry automatico** per connessioni instabili
- **Background sync** trasparente

### 💾 **Gestione Dati:**

- **Backup locale sempre disponibile**
- **Download su richiesta** senza dipendenze server
- **Audit trail completo** per compliance

---

## 🚨 TROUBLESHOOTING

### ❓ **Problemi Comuni:**

**Q: Log duplicati nel server?**  
A: Verifica `MQTT_SYNC_LOGS_ONLY_ON_FAILURE=True`

**Q: Log mancanti localmente?**  
A: Controlla `MQTT_ALWAYS_LOG_LOCALLY=True`

**Q: Queue troppo grande?**  
A: Aumenta `MQTT_MAX_RETRY_QUEUE_SIZE` o diminuisci `MQTT_RETRY_INTERVAL`

### 📊 **Log Patterns:**

```bash
# Funzionamento normale
"📝 Log LOCALE salvato: [CARD_UID]"
"🚀 Log sync saltato - MQTT OK per: [CARD_UID]"

# MQTT fallito
"📡 MQTT parallelo ⚠️ accodato/retry: [CARD_UID]"
"📤 Log sync forzato al server per: [CARD_UID]"

# Sistema offline
"📦 Log accodato per sync futuro: [CARD_UID]"
"🔄 Processing retry queue: N messaggi"
```

---

## 🎉 CONCLUSIONI

L'architettura dual logging garantisce:

✅ **Log locali sempre disponibili** per download/backup  
✅ **Server sempre aggiornato** via MQTT o sync compensativo  
✅ **Performance ottimale** con zero latenza  
✅ **Resilienza totale** a problemi di connettività

**Sistema pronto per produzione con massima affidabilità!**
