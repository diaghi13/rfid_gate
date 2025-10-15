# 🔄 Endpoint Backend per Sistema di Sincronizzazione RFID Gate

## Panoramica

Il sistema RFID Gate implementa un'architettura **offline-first** che richiede i seguenti endpoint sul backend per la sincronizzazione.

## Endpoint Richiesti

### 1. 📥 Sincronizzazione Completa Carte

**Endpoint:** `GET /api/sync`

**Descrizione:** Restituisce tutte le carte attive con abbonamenti validi per la sincronizzazione giornaliera.

**Response Schema:**

```json
[
  {
    "card_uid": "E298C6EB",
    "customer_id": 1281,
    "customer_name": "GABRIELE TOSO",
    "in_white_list": false,
    "active_subscriptions": [
      {
        "type": "time_based",
        "expiry_date": "2026-05-21",
        "remaining_entrances": null,
        "is_active": true
      }
    ]
  },
  {
    "card_uid": "632D3903",
    "customer_id": 1671,
    "customer_name": "DAVIDE DONGHI",
    "in_white_list": false,
    "active_subscriptions": [
      {
        "type": "single_entrance",
        "expiry_date": null,
        "remaining_entrances": 10,
        "is_active": true
      }
    ]
  },
  {
    "card_uid": "ABC12345",
    "customer_id": null,
    "customer_name": "STAFF MEMBER",
    "in_white_list": true,
    "active_subscriptions": []
  },
  {
    "card_uid": "EMERGENCY001",
    "customer_id": null,
    "customer_name": "VIGILI DEL FUOCO",
    "in_white_list": true,
    "active_subscriptions": []
  }
]
```

### 2. 📤 SYNC LOG (ogni 5 minuti)

├─ 12. Invia log accessi: POST /api/logs/bulk
└─ 13. Marca log come sincronizzati

⚠️ GESTIONE GAP TEMPORALI
├─ 14. Carta sconosciuta → Real-time check
├─ 15. Se trovata → Cache immediata + autorizza
├─ 16. Se non trovata → MQTT fallback
└─ 17. Sync adattiva se troppe carte sconosciute

````

## ⚠️ Gestione Gap Temporali (15 minuti)

**Request Schema:**
```json
{
    "logs": [
        {
            "timestamp": "2025-10-15T14:30:00.000Z",
            "card_uid": "E298C6EB",
            "customer_id": "CUST123456",
            "tornello_id": "tornello_01",
            "direction": "in",
            "result": "authorized",
            "reason": "Accesso autorizzato (modalità offline)",
            "customer_name": "GABRIELE TOSO",
            "reader_type": "mfrc522",
            "metadata": {
                "raw_uid": "E298C6EB00",
                "reader_id": "in",
                "mode": "offline"
            }
        }
    ]
}
````

**Response:**

```json
{
  "success": true,
  "processed": 1,
  "message": "Log ricevuti correttamente"
}
```

> **📊 Nota sui Log Analytics**: Il campo `customer_id` è stato aggiunto per migliorare l'analisi dei dati di accesso. Viene automaticamente incluso quando disponibile, oppure viene impostato a `null` per le carte in whitelist o quando non disponibile.

### 3. 🔄 Aggiornamenti Incrementali

**Endpoint:** `GET /api/cards/updates`

**Query Parameters:**

- `since` (optional): Timestamp ISO per aggiornamenti dopo una data specifica

**Descrizione:** Restituisce solo le carte modificate/aggiunte/rimosse dall'ultima sincronizzazione.

#### 🔍 **Come Funziona il Parametro `since`**

```bash
# Prima chiamata (sync completa) - nessun parametro
GET /api/cards/updates

# Chiamate successive - con timestamp ultima sync
GET /api/cards/updates?since=2025-10-15T14:30:00.000Z
```

#### 📊 **Logica Server Required**

Il server deve tenere traccia di quando ogni carta è stata **creata/modificata**:

```sql
-- Esempio schema database server
CREATE TABLE cards (
    id INTEGER PRIMARY KEY,
    card_uid TEXT UNIQUE,
    customer_id INTEGER,
    customer_name TEXT,
    in_white_list BOOLEAN,
    active_subscriptions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- ← Chiave per updates
);

-- Trigger per aggiornare updated_at
CREATE TRIGGER update_cards_timestamp
    BEFORE UPDATE ON cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 🔄 **Query di Esempio**

```sql
-- Tutte le carte modificate/create dopo timestamp
SELECT
    card_uid, customer_id, customer_name,
    in_white_list, active_subscriptions,
    created_at, updated_at
FROM cards
WHERE updated_at > $1  -- $1 = parametro 'since'
   OR created_at > $1   -- Include anche carte nuove
ORDER BY updated_at ASC;

-- Carte cancellate (se hai soft-delete)
SELECT card_uid, deleted_at
FROM cards
WHERE deleted_at > $1
  AND deleted_at IS NOT NULL;
```

**Response Schema:**

```json
[
  {
    "action": "update",
    "card_data": {
      "card_uid": "NEW12345",
      "customer_id": 1500,
      "customer_name": "NUOVO CLIENTE",
      "in_white_list": false,
      "active_subscriptions": [
        {
          "type": "time_based",
          "expiry_date": "2026-01-01",
          "remaining_entrances": null,
          "is_active": true
        }
      ]
    }
  },
  {
    "action": "delete",
    "card_uid": "OLD98765"
  }
]
```

### 4. ❤️ Health Check

**Endpoint:** `GET /api/health`

**Descrizione:** Endpoint per verificare la connettività e lo stato del server.

**Response:**

```json
{
  "status": "ok",
  "timestamp": "2025-10-15T14:30:00.000Z",
  "version": "1.0.0"
}
```

### Struttura Dati Carta

Ogni carta ha i seguenti campi:

- **`card_uid`**: UID univoco della carta (string, obbligatorio)
- **`customer_id`**: ID del cliente nel sistema (integer, **può essere null per carte whitelist**)
- **`customer_name`**: Nome del cliente o descrizione carta (string, obbligatorio)
- **`in_white_list`**: Flag whitelist per accesso sempre autorizzato (boolean, obbligatorio)
- **`active_subscriptions`**: Array degli abbonamenti attivi (array, obbligatorio)

#### Customer ID Null

Il campo `customer_id` può essere `null` per:

- 🔑 **Carte whitelist di servizio** (staff, manutenzione, emergenza)
- 👮 **Carte non associate a clienti specifici**
- 🚨 **Accessi temporanei o speciali**

```json
// Esempi customer_id null
{
  "card_uid": "EMERGENCY001",
  "customer_id": null, // ← NULL per carte di servizio
  "customer_name": "VIGILI DEL FUOCO",
  "in_white_list": true,
  "active_subscriptions": []
}
```

#### Logica Whitelist

Se `in_white_list` è `true`:

- ✅ **Accesso sempre autorizzato** indipendentemente dagli abbonamenti
- ✅ **Nessun decremento** di ingressi rimanenti
- ✅ **Nessun controllo** di scadenza abbonamenti
- 📝 **Log comunque registrato** con motivo "whitelist"

Tipico per:

- 👮 Staff e personale autorizzato
- 🔧 Carte di servizio e manutenzione
- 🚨 Accessi di emergenza
- 🔑 Carte master

## Flusso di Sincronizzazione Completo

### 🚀 **Prima Installazione/Reset**

```bash
# 1. Sistema RFID chiama sync completa (senza 'since')
GET /api/cards/updates
# → Server ritorna TUTTE le carte attive

# 2. Sistema salva timestamp sync
last_sync = "2025-10-15T06:00:00.000Z"
```

### 🔄 **Sincronizzazione Incrementale**

```bash
# 3. Check periodico (ogni 15 minuti)
GET /api/cards/updates?since=2025-10-15T06:00:00.000Z
# → Server ritorna solo modifiche dopo quel timestamp

# 4. Aggiorna timestamp
last_sync = "2025-10-15T06:15:00.000Z"
```

### 📝 **Esempi Pratici**

#### Scenario: Nuova Carta Registrata

```javascript
// 1. Utente registra nuova carta alle 14:30
INSERT INTO cards (card_uid, customer_name, ..., created_at)
VALUES ('NEW123', 'Mario Rossi', ..., '2025-10-15T14:30:00Z');

// 2. Sistema RFID chiama updates alle 14:45
GET /api/cards/updates?since=2025-10-15T14:15:00Z

// 3. Server risponde con carta nuova
[
    {
        "action": "update",
        "card_data": {
            "card_uid": "NEW123",
            "customer_name": "Mario Rossi",
            // ... altri campi
        }
    }
]

// 4. Sistema RFID aggiorna cache locale
```

#### Scenario: Modifica Abbonamento Esistente

```javascript
// 1. Cliente rinnova abbonamento alle 15:20
UPDATE cards
SET active_subscriptions = '[{"type":"time_based","expiry_date":"2026-01-01",...}]',
    updated_at = '2025-10-15T15:20:00Z'
WHERE card_uid = 'EXISTING001';

// 2. Sistema RFID check alle 15:30
GET /api/cards/updates?since=2025-10-15T15:15:00Z

// 3. Server rileva modifica e risponde
[
    {
        "action": "update",
        "card_data": {
            "card_uid": "EXISTING001",
            "active_subscriptions": [
                {"type": "time_based", "expiry_date": "2026-01-01", ...}
            ]
        }
    }
]
```

#### Scenario: Cancellazione Carta

```javascript
// 1. Admin disabilita carta alle 16:10
UPDATE cards
SET deleted_at = '2025-10-15T16:10:00Z'
WHERE card_uid = 'OLD123';

// 2. Sistema RFID check alle 16:15
GET /api/cards/updates?since=2025-10-15T16:05:00Z

// 3. Server risponde con cancellazione
[
    {
        "action": "delete",
        "card_uid": "OLD123"
    }
]

// 4. Sistema RFID rimuove dalla cache locale
```

### ⚡ **Ottimizzazioni Server**

#### 1. **Indicizzazione Database**

```sql
-- Index per performance query updates
CREATE INDEX idx_cards_updated_at ON cards(updated_at);
CREATE INDEX idx_cards_created_at ON cards(created_at);
CREATE INDEX idx_cards_deleted_at ON cards(deleted_at)
    WHERE deleted_at IS NOT NULL;
```

#### 2. **Paginazione per Grandi Dataset**

```javascript
// Se hai migliaia di carte modificate
app.get("/api/cards/updates", async (req, res) => {
  const { since, limit = 100, offset = 0 } = req.query;

  const updates = await db.query(
    `
        SELECT * FROM cards 
        WHERE updated_at > $1 
        ORDER BY updated_at ASC
        LIMIT $2 OFFSET $3
    `,
    [since, limit, offset]
  );

  res.json({
    updates,
    has_more: updates.length === limit,
    next_offset: offset + limit,
  });
});
```

#### 3. **Caching Redis**

```javascript
// Cache per evitare query ripetute
const cacheKey = `updates:${since}`;
let updates = await redis.get(cacheKey);

if (!updates) {
  updates = await db.getUpdates(since);
  await redis.setex(cacheKey, 300, JSON.stringify(updates)); // 5 min
}
```

## Specifiche Tecniche

### Tipi di Abbonamento

#### time_based

```json
{
  "type": "time_based",
  "expiry_date": "2026-05-21", // Formato: YYYY-MM-DD
  "remaining_entrances": null,
  "is_active": true
}
```

#### single_entrance

```json
{
  "type": "single_entrance",
  "expiry_date": null,
  "remaining_entrances": 10, // Numero ingressi rimanenti
  "is_active": true
}
```

### Risultati Log

- `"authorized"`: Accesso autorizzato
- `"denied"`: Accesso negato
- `"manual"`: Apertura manuale

### Direzioni

- `"in"`: Ingresso
- `"out"`: Uscita

### Gestione Errori

Tutti gli endpoint devono gestire:

- **200**: Successo
- **400**: Bad Request (dati malformati)
- **401**: Unauthorized (se auth richiesta)
- **500**: Internal Server Error
- **503**: Service Unavailable (manutenzione)

### Autenticazione

Il sistema supporta:

- **API Key**: Header `X-API-Key`
- **Bearer Token**: Header `Authorization: Bearer <token>`
- **Basic Auth**: Per compatibilità legacy

## Configurazione Client

Nel file `.env` del client:

```bash
# Server configuration
SYNC_SERVER_URL=https://your-api-server.com
SYNC_ENDPOINT=/api/sync
SYNC_LOGS_ENDPOINT=/api/logs/bulk
SYNC_HEALTH_ENDPOINT=/api/health
SYNC_UPDATES_ENDPOINT=/api/cards/updates

# Autenticazione (scegli uno)
API_KEY=your-api-key
# oppure
AUTH_TOKEN=your-bearer-token
```

## Flusso di Sincronizzazione

1. **Avvio Sistema**: Sync completa di tutte le carte (`/api/sync`)
2. **Operazione Normale**:
   - Validazione locale con cache SQLite
   - Log accessi in coda locale
3. **Sync Periodica**:
   - Ogni 5 minuti: invio log (`/api/logs/bulk`)
   - Ogni 15 minuti: check aggiornamenti (`/api/cards/updates`)
   - Ogni giorno alle 6:00: sync completa (`/api/sync`)
4. **Resilienza**: Retry automatici e accumulo offline

## Note di Implementazione

### Lato Server

- Implementare paginazione per endpoint con molti dati
- Considerare rate limiting per protezione
- Log tutte le operazioni per audit
- Backup regolari del database

### Lato Client

- Il sistema mantiene compatibilità con MQTT esistente
- La cache locale ha priorità sulla validazione MQTT
- I log vengono sempre salvati localmente e sincronizzati
- Fallback graceful in caso di problemi di rete

## Esempi di Implementazione

### Node.js/Express

```javascript
// GET /api/cards/updates
app.get("/api/cards/updates", async (req, res) => {
  try {
    const { since } = req.query;
    let updates = [];

    if (since) {
      // Updates incrementali
      const sinceDate = new Date(since);

      // Carte modificate/nuove
      const modifiedCards = await db.query(
        `
                SELECT card_uid, customer_id, customer_name, 
                       in_white_list, active_subscriptions, updated_at
                FROM cards 
                WHERE updated_at > $1 OR created_at > $1
                ORDER BY updated_at ASC
            `,
        [sinceDate]
      );

      modifiedCards.forEach((card) => {
        updates.push({
          action: "update",
          card_data: {
            card_uid: card.card_uid,
            customer_id: card.customer_id,
            customer_name: card.customer_name,
            in_white_list: card.in_white_list,
            active_subscriptions: card.active_subscriptions,
          },
        });
      });

      // Carte cancellate (se hai soft-delete)
      const deletedCards = await db.query(
        `
                SELECT card_uid FROM cards 
                WHERE deleted_at > $1 AND deleted_at IS NOT NULL
            `,
        [sinceDate]
      );

      deletedCards.forEach((card) => {
        updates.push({
          action: "delete",
          card_uid: card.card_uid,
        });
      });
    } else {
      // Prima chiamata - ritorna tutte le carte attive
      const allCards = await db.getActiveCardsWithSubscriptions();
      allCards.forEach((card) => {
        updates.push({
          action: "update",
          card_data: card,
        });
      });
    }

    res.json(updates);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### Python/FastAPI

```python
from datetime import datetime
from fastapi import FastAPI, Query
from typing import Optional

@app.get("/api/cards/updates")
async def get_card_updates(since: Optional[str] = Query(None)):
    updates = []

    if since:
        # Parse timestamp
        since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))

        # Query carte modificate
        modified_cards = await db.execute("""
            SELECT card_uid, customer_id, customer_name,
                   in_white_list, active_subscriptions
            FROM cards
            WHERE updated_at > :since OR created_at > :since
            ORDER BY updated_at ASC
        """, {"since": since_date})

        for card in modified_cards:
            updates.append({
                "action": "update",
                "card_data": {
                    "card_uid": card.card_uid,
                    "customer_id": card.customer_id,
                    "customer_name": card.customer_name,
                    "in_white_list": card.in_white_list,
                    "active_subscriptions": card.active_subscriptions
                }
            })

        # Query carte cancellate
        deleted_cards = await db.execute("""
            SELECT card_uid FROM cards
            WHERE deleted_at > :since AND deleted_at IS NOT NULL
        """, {"since": since_date})

        for card in deleted_cards:
            updates.append({
                "action": "delete",
                "card_uid": card.card_uid
            })
    else:
        # Prima chiamata - tutte le carte
        all_cards = await get_all_active_cards()
        for card in all_cards:
            updates.append({
                "action": "update",
                "card_data": card
            })

    return updates
```

## Implementazione Lato Client RFID

### 🔄 **SyncManager - Check Updates**

```python
async def check_for_updates(self) -> bool:
    """Controlla aggiornamenti carte dal server"""
    try:
        params = {}
        if self.last_sync:
            # Usa timestamp ultima sync come parametro 'since'
            params['since'] = self.last_sync.isoformat()

        url = f"{self.config.server_url}/api/cards/updates"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    updates = await response.json()
                    if updates:
                        self.logger.info(f"📥 Ricevuti {len(updates)} aggiornamenti")
                        self._apply_updates(updates)

                        # Aggiorna timestamp ultima sync
                        self.last_sync = datetime.now()
                    return True
                else:
                    return False
    except Exception as e:
        self.logger.error(f"Errore check updates: {e}")
        return False
```

### 🔄 **Applicazione Updates**

```python
def _apply_updates(self, updates: List[Dict[str, Any]]):
    """Applica aggiornamenti incrementali delle carte"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    try:
        for update in updates:
            action = update.get('action', 'update')

            if action == 'update':
                # Carta nuova o modificata
                card_data = update['card_data']
                cursor.execute('''
                    INSERT OR REPLACE INTO synced_cards
                    (card_uid, customer_id, customer_name, in_white_list,
                     active_subscriptions, last_sync, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (
                    card_data['card_uid'],
                    card_data.get('customer_id'),
                    card_data['customer_name'],
                    card_data.get('in_white_list', False),
                    json.dumps(card_data['active_subscriptions']),
                    datetime.now()
                ))

            elif action == 'delete':
                # Carta cancellata - disattiva nella cache locale
                cursor.execute(
                    'UPDATE synced_cards SET is_active = 0 WHERE card_uid = ?',
                    (update['card_uid'],)
                )

        conn.commit()
        self.logger.info(f"✅ Applicati {len(updates)} aggiornamenti alla cache")

    except Exception as e:
        self.logger.error(f"Errore applicazione updates: {e}")
    finally:
        conn.close()
```

### ⏰ **Scheduling Automatico**

```python
async def _background_worker(self):
    """Worker per sincronizzazioni periodiche"""
    while True:
        try:
            now = datetime.now()

            # Check aggiornamenti ogni 15 minuti
            if (now - self.last_updates_check).total_seconds() >= 15 * 60:
                if self.is_online:
                    await self.check_for_updates()
                self.last_updates_check = now

            # Sync completa giornaliera alle 6:00
            sync_time = datetime.strptime("06:00", "%H:%M").time()
            if (now.time().hour == sync_time.hour and
                now.time().minute == sync_time.minute):
                await self.daily_sync()

            await asyncio.sleep(60)  # Check ogni minuto

        except Exception as e:
            self.logger.error(f"Errore background worker: {e}")
            await asyncio.sleep(60)
```

### 📋 **Riassunto Flusso Completo**

```
🚀 AVVIO SISTEMA
├─ 1. Sync completa: GET /api/cards/updates (senza 'since')
├─ 2. Popola cache locale con tutte le carte
└─ 3. Salva timestamp: last_sync = now()

🔄 OPERAZIONE NORMALE (ogni 15 minuti)
├─ 4. Check updates: GET /api/cards/updates?since=last_sync
├─ 5. Server risponde con modifiche dopo last_sync
├─ 6. Applica updates alla cache locale:
│    ├─ action:"update" → INSERT OR REPLACE
│    └─ action:"delete" → SET is_active = 0
└─ 7. Aggiorna last_sync = now()

📝 VALIDAZIONE ACCESSI
├─ 8. Carta letta → Valida con cache locale
├─ 9. Se in whitelist → accesso sempre autorizzato
├─ 10. Se abbonamento valido → autorizza + decrementa
└─ 11. Log sempre registrato per sync futuro

📤 SYNC LOG (ogni 5 minuti)
├─ 12. Invia log accessi: POST /api/logs/bulk
└─ 13. Marca log come sincronizzati
```

## Best Practices Customer ID

### ✅ **Quando Usare customer_id NULL**

```json
// Carte di servizio/staff
{
    "card_uid": "STAFF001",
    "customer_id": null,                    // NULL - non è un cliente
    "customer_name": "Guardia Notturna",
    "in_white_list": true,
    "active_subscriptions": []
}

// Carte emergenza/speciali
{
    "card_uid": "EMERGENCY001",
    "customer_id": null,                    // NULL - accesso speciale
    "customer_name": "Vigili del Fuoco",
    "in_white_list": true,
    "active_subscriptions": []
}

// Carte manutenzione
{
    "card_uid": "MAINT999",
    "customer_id": null,                    // NULL - carta di servizio
    "customer_name": "Tecnico Ascensori",
    "in_white_list": true,
    "active_subscriptions": []
}
```

### ✅ **Quando Mantenere customer_id**

```json
// Clienti normali (sempre con customer_id)
{
    "card_uid": "CLIENT001",
    "customer_id": 1234,                   // ID del cliente nel database
    "customer_name": "Mario Rossi",
    "in_white_list": false,
    "active_subscriptions": [...]
}

// Manager/VIP (possono avere customer_id + whitelist)
{
    "card_uid": "VIP001",
    "customer_id": 9999,                   // ID del manager
    "customer_name": "Direttore Generale",
    "in_white_list": true,                 // Accesso privilegiato
    "active_subscriptions": []
}
```

### 🎯 **Vantaggi customer_id NULL**

- 🔧 **Separazione logica**: carte di servizio vs clienti
- 📊 **Analytics pulite**: report clienti senza "rumore" da carte staff
- 🔒 **Sicurezza**: carte speciali facilmente identificabili
- 💾 **Database efficiente**: no FK inutili per carte non-clienti

## Test degli Endpoint

Usa i seguenti comandi curl per testare:

```bash
# Test sync completa
curl -X GET "https://your-api.com/api/sync" \
     -H "X-API-Key: your-key"

# Test invio log
curl -X POST "https://your-api.com/api/logs/bulk" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-key" \
     -d '{"logs":[{"timestamp":"2025-10-15T14:30:00.000Z","card_uid":"TEST123","customer_id":"CUST789","tornello_id":"tornello_01","direction":"in","result":"authorized","reason":"Test"}]}'

# Test health
curl -X GET "https://your-api.com/api/health"
```

## ⚠️ Gestione Gap Temporali (15 minuti)

### 🚨 **Problema: Nuova Registrazione nell'Intervallo**

**Scenario**: Cliente registra carta alle 10:45, ma ultima sync era alle 10:30 e prossima alle 10:45.

#### **Strategia 1: Fallback MQTT Real-time** ⚡

```python
async def validate_card_offline(self, card_uid: str) -> AccessResult:
    """Validazione offline-first con fallback real-time"""

    # 1. Prima prova cache locale
    local_result = self._check_local_cache(card_uid)
    if local_result.is_valid:
        return local_result

    # 2. Se carta non in cache E sistema online → Check real-time
    if not local_result.is_valid and self.is_online:
        realtime_result = await self._check_realtime_fallback(card_uid)

        if realtime_result.is_valid:
            # Carta nuova trovata! Aggiorna cache immediatamente
            self._cache_new_card(realtime_result.card_data)
            return realtime_result

    # 3. Ultima risorsa: MQTT fallback
    return await self._mqtt_fallback(card_uid)

async def _check_realtime_fallback(self, card_uid: str) -> AccessResult:
    """Check singola carta in real-time"""
    try:
        url = f"{self.config.server_url}/api/cards/validate/{card_uid}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3) as response:
                if response.status == 200:
                    card_data = await response.json()
                    self.logger.info(f"🔥 Carta {card_uid} trovata via real-time!")
                    return self._create_access_result(card_data)

        return AccessResult(is_valid=False, reason="Carta non trovata")

    except asyncio.TimeoutError:
        self.logger.warning("⏱️ Timeout real-time check, uso MQTT")
        return AccessResult(is_valid=False, reason="Timeout")
```

#### **Strategia 2: Sync Trigger su Carta Sconosciuta** 🔄

```python
async def validate_card_offline(self, card_uid: str) -> AccessResult:
    """Validazione con sync immediata se carta non trovata"""

    # Prova cache locale
    result = self._check_local_cache(card_uid)
    if result.is_valid:
        return result

    # Carta non trovata → Trigger sync immediata
    if self.is_online and not self._is_syncing:
        self.logger.info(f"🔍 Carta {card_uid} non in cache, sync immediata...")

        # Sync rapida per questa carta specifica
        if await self._quick_sync_single_card(card_uid):
            # Riprova dopo sync
            return self._check_local_cache(card_uid)

    # Fallback MQTT
    return await self._mqtt_fallback(card_uid)

async def _quick_sync_single_card(self, card_uid: str) -> bool:
    """Sync rapida per carta singola"""
    try:
        url = f"{self.config.server_url}/api/cards/find/{card_uid}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    card_data = await response.json()
                    self._cache_new_card(card_data)
                    return True
        return False
    except Exception as e:
        self.logger.error(f"Errore quick sync: {e}")
        return False
```

#### **Strategia 3: Sync Adattiva (Raccomandato)** 🎯

```python
class SyncManager:
    def __init__(self):
        self.unknown_cards_buffer = []  # Buffer carte sconosciute
        self.adaptive_sync_interval = 15 * 60  # Parte da 15 minuti
        self.min_sync_interval = 2 * 60        # Minimo 2 minuti

async def validate_card_offline(self, card_uid: str) -> AccessResult:
    """Validazione con sync adattiva"""

    result = self._check_local_cache(card_uid)
    if result.is_valid:
        return result

    # Carta sconosciuta → aggiungi al buffer
    if card_uid not in self.unknown_cards_buffer:
        self.unknown_cards_buffer.append(card_uid)

        # Se troppe carte sconosciute → accelera sync
        if len(self.unknown_cards_buffer) >= 3:
            self._accelerate_sync()

    # Prova real-time per carta critica
    if self.is_online:
        realtime_result = await self._check_realtime_fallback(card_uid)
        if realtime_result.is_valid:
            self._cache_new_card(realtime_result.card_data)
            self.unknown_cards_buffer.remove(card_uid)
            return realtime_result

    return await self._mqtt_fallback(card_uid)

def _accelerate_sync(self):
    """Accelera frequenza sync quando troppe carte sconosciute"""
    old_interval = self.adaptive_sync_interval
    self.adaptive_sync_interval = max(
        self.min_sync_interval,
        self.adaptive_sync_interval // 2
    )

    self.logger.warning(
        f"⚡ Accelerando sync: {old_interval//60}min → {self.adaptive_sync_interval//60}min"
    )

async def check_for_updates(self) -> bool:
    """Check updates con reset intervallo dopo sync successo"""
    success = await self._do_sync_updates()

    if success and self.unknown_cards_buffer:
        # Reset buffer e rallenta sync
        cleared = len(self.unknown_cards_buffer)
        self.unknown_cards_buffer.clear()
        self.adaptive_sync_interval = 15 * 60  # Reset a 15 minuti

        self.logger.info(f"✅ Sync completata, {cleared} carte risolte")

    return success
```

### 📊 **Endpoint Server per Real-time**

```javascript
// Endpoint dedicato per validazione real-time singola carta
app.get("/api/cards/validate/:card_uid", async (req, res) => {
  try {
    const { card_uid } = req.params;

    const card = await db.query(
      `
            SELECT c.*, 
                   cu.customer_id, cu.customer_name,
                   (CASE WHEN w.card_uid IS NOT NULL THEN true ELSE false END) as in_white_list,
                   array_agg(
                       json_build_object(
                           'subscription_type', s.subscription_type,
                           'remaining_entries', s.remaining_entries,
                           'expiry_date', s.expiry_date
                       )
                   ) FILTER (WHERE s.id IS NOT NULL) as active_subscriptions
            FROM cards c
            LEFT JOIN customers cu ON c.customer_id = cu.id
            LEFT JOIN whitelist w ON c.card_uid = w.card_uid
            LEFT JOIN subscriptions s ON cu.id = s.customer_id 
                AND s.remaining_entries > 0 
                AND s.expiry_date > NOW()
            WHERE c.card_uid = $1
            GROUP BY c.id, cu.id, w.card_uid
        `,
      [card_uid]
    );

    if (card.rows.length === 0) {
      return res.status(404).json({ error: "Carta non trovata" });
    }

    res.json(card.rows[0]);
  } catch (error) {
    console.error("Errore validazione real-time:", error);
    res.status(500).json({ error: "Errore server" });
  }
});

// Endpoint per sync singola carta
app.get("/api/cards/find/:card_uid", async (req, res) => {
  // Stessa logica ma con log diverso per tracking
  // ...
});
```

### 🎯 **Flusso Completo Aggiornato**

```
🚀 AVVIO SISTEMA
├─ 1. Sync completa: GET /api/cards/updates (senza 'since')
├─ 2. Popola cache locale con tutte le carte
└─ 3. Salva timestamp: last_sync = now()

🔄 OPERAZIONE NORMALE (ogni 15 minuti)
├─ 4. Check updates: GET /api/cards/updates?since=last_sync
├─ 5. Server risponde con modifiche dopo last_sync
├─ 6. Applica updates alla cache locale:
│    ├─ action:"update" → INSERT OR REPLACE
│    └─ action:"delete" → SET is_active = 0
└─ 7. Aggiorna last_sync = now()

📝 VALIDAZIONE ACCESSI
├─ 8. Carta letta → Valida con cache locale
├─ 9. Se in whitelist → accesso sempre autorizzato
├─ 10. Se abbonamento valido → autorizza + decrementa
└─ 11. Log sempre registrato per sync futuro

📤 SYNC LOG (ogni 5 minuti)
├─ 12. Invia log accessi: POST /api/logs/bulk
└─ 13. Marca log come sincronizzati

⚠️ GESTIONE GAP TEMPORALI
├─ 14. Carta sconosciuta → Real-time check
├─ 15. Se trovata → Cache immediata + autorizza
├─ 16. Se non trovata → MQTT fallback
└─ 17. Sync adattiva se troppe carte sconosciute
```

### 🛡️ **Strategie di Resilienza**

1. **Triple Fallback**: Cache → Real-time → MQTT
2. **Sync Adattiva**: Accelera quando necessario
3. **Buffer Intelligente**: Traccia carte problematiche
4. **Timeout Ottimizzati**: 3s real-time, 5s sync specifica
5. **Retry Logic**: Exponential backoff per fallback

## 🗄️ Setup Database Locale

### **SQLite - Nessuna Installazione Richiesta** ✅

Il sistema utilizza **SQLite** che è **incluso di default** in Python - **non serve installare nulla!**

```python
import sqlite3  # ✅ Già disponibile in Python standard library
```

### **Creazione Automatica del Database** 🔧

Il database viene creato **automaticamente** al primo avvio del `SyncManager`:

```python
# rfid_gate/network/sync_manager.py
class SyncManager:
    def __init__(self, config: SyncConfig, tornello_id: str):
        # ...
        self.cache_dir = Path(config.cache_db_path).parent
        self.cache_dir.mkdir(parents=True, exist_ok=True)  # ✅ Crea directory se non esiste

        self.db_path = config.cache_db_path  # Default: "cache/local_cache.db"

        # ✅ Inizializza database automaticamente
        self._init_database()
```

### **Schema Database Completo** 📋

```sql
-- 🃏 Tabella cache carte (offline-first)
CREATE TABLE IF NOT EXISTS synced_cards (
    card_uid TEXT PRIMARY KEY,                    -- UID carta RFID
    customer_id INTEGER,                          -- FK cliente (può essere NULL)
    customer_name TEXT,                           -- Nome leggibile
    in_white_list BOOLEAN DEFAULT 0,              -- Flag whitelist
    active_subscriptions TEXT,                    -- JSON abbonamenti attivi
    last_sync TIMESTAMP,                          -- Ultima sincronizzazione
    is_active BOOLEAN DEFAULT 1                   -- Carta attiva
);

-- 📝 Tabella log pending (queue offline)
CREATE TABLE IF NOT EXISTS pending_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,                               -- ISO timestamp accesso
    card_uid TEXT,                               -- UID carta utilizzata
    tornello_id TEXT,                            -- ID tornello
    direction TEXT,                              -- "in" | "out"
    result TEXT,                                 -- "authorized" | "denied"
    reason TEXT,                                 -- Motivo dettagliato
    customer_name TEXT,                          -- Nome cliente
    reader_type TEXT,                            -- "MFRC522" | "PN532"
    metadata TEXT,                               -- JSON metadata extra
    synced BOOLEAN DEFAULT 0,                    -- Flag sincronizzato
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ⚙️ Tabella stato sync
CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY,
    last_full_sync TIMESTAMP,                    -- Ultima sync completa
    last_log_sync TIMESTAMP,                     -- Ultimo invio log
    last_updates_check TIMESTAMP,                -- Ultimo check updates
    sync_errors INTEGER DEFAULT 0                -- Contatore errori
);
```

### **Configurazione Path Database** 📁

Nel file `.env`:

```bash
# 🗄️ Database Configuration
SYNC_CACHE_DB_PATH=cache/local_cache.db

# Esempi percorsi alternativi:
# SYNC_CACHE_DB_PATH=/var/lib/rfid_gate/cache.db     # Linux system-wide
# SYNC_CACHE_DB_PATH=data/cache/rfid_cache.db        # Cartella dati
# SYNC_CACHE_DB_PATH=/tmp/rfid_cache.db              # Temporaneo (testing)
```

### **Struttura Directory Auto-generata** 📂

```
rfid_gate/
├─ cache/                           # ✅ Creata automaticamente
│  ├─ local_cache.db               # ✅ Database SQLite
│  └─ backup/                      # ✅ Backup automatici (opzionale)
├─ logs/
│  ├─ system.log
│  └─ access_log.json
└─ ...
```

### **Verifiche Setup Database** 🔍

Il sistema include controlli automatici:

```python
def _verify_database_setup(self):
    """Verifica integrità database al startup"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ✅ Verifica esistenza tabelle
        tables_check = cursor.execute('''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('synced_cards', 'pending_logs', 'sync_status')
        ''').fetchall()

        if len(tables_check) != 3:
            self.logger.warning("🔧 Ricreazione tabelle database...")
            self._init_database()

        # ✅ Verifica permissions
        cursor.execute("INSERT OR IGNORE INTO sync_status (id) VALUES (1)")
        conn.commit()

        self.logger.info("✅ Database verificato e funzionante")

    except Exception as e:
        self.logger.error(f"❌ Errore setup database: {e}")
        raise
    finally:
        conn.close()
```

### **Manutenzione Database** 🧹

```python
# Script manutenzione automatica
async def _database_maintenance(self):
    """Manutenzione periodica database"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 🧹 Pulisci log vecchi (>30 giorni)
        cursor.execute('''
            DELETE FROM pending_logs
            WHERE synced = 1 AND created_at < datetime('now', '-30 days')
        ''')

        # 🧹 Vacuum database (ottimizza spazio)
        cursor.execute("VACUUM")

        # 📊 Statistiche
        stats = cursor.execute('''
            SELECT
                (SELECT COUNT(*) FROM synced_cards) as cards_count,
                (SELECT COUNT(*) FROM pending_logs WHERE synced = 0) as pending_logs,
                (SELECT COUNT(*) FROM pending_logs WHERE synced = 1) as synced_logs
        ''').fetchone()

        self.logger.info(f"🗄️ DB Stats: {stats[0]} cards, {stats[1]} pending logs, {stats[2]} synced logs")

    except Exception as e:
        self.logger.error(f"Errore manutenzione DB: {e}")
```

### **Backup Automatico** 💾

```python
def _create_backup(self):
    """Crea backup del database"""
    try:
        backup_dir = self.cache_dir / "backup"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"cache_backup_{timestamp}.db"

        # SQLite backup
        source = sqlite3.connect(self.db_path)
        backup = sqlite3.connect(str(backup_path))
        source.backup(backup)
        backup.close()
        source.close()

        self.logger.info(f"💾 Backup creato: {backup_path}")

        # Mantieni solo ultimi 7 backup
        self._cleanup_old_backups(backup_dir, keep=7)

    except Exception as e:
        self.logger.error(f"Errore backup: {e}")
```

### **Riassunto: Zero Setup Required!** 🎯

✅ **SQLite**: Incluso in Python  
✅ **Database**: Creazione automatica  
✅ **Directory**: Auto-generate  
✅ **Schema**: Setup automatico  
✅ **Verifiche**: Controlli integrità  
✅ **Manutenzione**: Pulizia automatica  
✅ **Backup**: Opzionale ma integrato

**Il sistema è completamente plug-and-play!** 🚀

### **Requirements Python** 📦

Il sistema utilizza **solo librerie standard** per il database:

```txt
# requirements.txt - Sezione Database
# ✅ SQLite è GIÀ incluso in Python - nessun requirement!

# 📡 Networking per sync (già presenti)
aiohttp>=3.8.0          # HTTP async client
requests>=2.28.0        # HTTP fallback
paho-mqtt>=1.6.1        # MQTT fallback

# 🔧 Utilities (già presenti)
python-dotenv>=1.0.0    # Configurazione .env
```

**Nessuna dipendenza aggiuntiva per il database!** ✅

### **Installazione e Primo Avvio** 🚀

```bash
# 1. ✅ Installa dipendenze (già fatto)
pip install -r requirements.txt

# 2. ✅ Configura .env
cp .env.example .env
# Modifica SYNC_SERVER_URL e altre config

# 3. ✅ Avvia sistema
python main.py

# 4. ✅ Database creato automaticamente!
# Log: "📁 Database cache inizializzato: cache/local_cache.db"
```

### **Controllo Setup Database** 🔍

```bash
# Verifica che il database sia stato creato
ls -la cache/
# Dovrebbe mostrare: local_cache.db

# Ispezione database (opzionale)
sqlite3 cache/local_cache.db ".tables"
# Output: synced_cards  pending_logs  sync_status

# Controllo schema
sqlite3 cache/local_cache.db ".schema synced_cards"
```

### **Gestione Errori Database** ⚠️

Il sistema gestisce automaticamente gli errori più comuni:

```python
# 🔧 Auto-riparazione in caso di corruzione
if database_corrupted:
    self.logger.warning("🔧 Database corrotto, ricreazione...")
    os.remove(self.db_path)  # Rimuovi file corrotto
    self._init_database()     # Ricrea da zero
    await self.daily_sync()   # Risincronizza tutto

# 🔒 Gestione permessi
if permission_denied:
    self.logger.error("❌ Permessi insufficienti per database")
    # Suggerisce fix: sudo chown user:group cache/

# 💾 Gestione spazio insufficiente
if disk_full:
    self.logger.warning("⚠️ Spazio insufficiente, pulizia automatica...")
    self._database_maintenance()  # Pulizia log vecchi
```
