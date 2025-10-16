# 📡 Documentazione Endpoint Sistema RFID Gate

## 🌐 Endpoint Server Utilizzati dal Sistema

### **Server Base:** `https://gymme-newaction.ddns.net`

---

## 🔄 **1. SYNC ENDPOINT (Cache Refresh)**

### **URL:** `/api/sync-gate`

**Utilizzo:** Cache refresh per singola carta  
**Chiamato da:** `cache_refresh_strategy.py`  
**Scopo:** Scaricare dati aggiornati carta per refresh cache locale

#### **Request GET:**

```url
https://gymme-newaction.ddns.net/api/sync-gate?card_uid=02D9BAEB&gate_id=tornello_01&refresh=true
```

#### **Parametri:**

- `card_uid`: UID della carta da verificare
- `gate_id`: ID del tornello (es: "tornello_01")
- `refresh`: "true" per forzare refresh

#### **Response (Success 200):**

```json
{
  "success": true,
  "data": {
    "card_uid": "02D9BAEB",
    "customer_id": 1670,
    "customer_name": "LORENZO RAMUNNO",
    "active_subscriptions": [
      {
        "type": "time_based",
        "expiry_date": "2026-10-13",
        "remaining_entrances": null,
        "is_active": true
      }
    ],
    "in_white_list": false,
    "created_at": "2025-10-13 15:18:54",
    "updated_at": "2025-10-13 15:19:40"
  }
}
```

#### **Response (Not Found 404):**

```json
{
  "success": false,
  "message": "Card non trovata"
}
```

#### **Performance Testata:** ~229ms

#### **Configurazione .env:**

```properties
CACHE_REFRESH_SINGLE_CARD_ENDPOINT=/api/sync-gate
CACHE_REFRESH_TIMEOUT=5000
```

---

## 🔐 **2. GATE VERIFICATION ENDPOINT**

### **URL:** `/api/gate-verification`

**Utilizzo:** Autorizzazione finale carta  
**Chiamato da:** Broker MQTT (NON direttamente dal sistema RFID)  
**Scopo:** Decisione finale di autorizzazione accesso

#### **Request POST:**

```url
https://gymme-newaction.ddns.net/api/gate-verification
```

#### **Payload JSON:**

```json
{
  "uid": "02D9BAEB",
  "direction": "in",
  "gate_id": "tornello_01"
}
```

#### **Parametri:**

- `uid`: UID della carta
- `direction`: "in" o "out" (campo corretto per broker)
- `gate_id`: ID del tornello

#### **Response (Success 200):**

```json
{
  "authorized": true,
  "customer_name": "LORENZO RAMUNNO",
  "customer_id": 1670,
  "message": "Customer unlocked successfully"
}
```

#### **Response (Denied 200):**

```json
{
  "authorized": false,
  "message": "Access denied - No active subscription"
}
```

#### **Performance Testata:** ~295ms

#### **Nota:** ⚠️ Attualmente in modalità test - autorizza sempre

#### **Configurazione .env:**

```properties
SYNC_FALLBACK_ENDPOINT=/api/gate-verification
SYNC_FALLBACK_TIMEOUT=3
```

---

## 📊 **3. SYNC LOGS ENDPOINT**

### **URL:** `/api/sync-gate/logs`

**Utilizzo:** Sincronizzazione log accessi  
**Chiamato da:** `sync_manager.py`  
**Scopo:** Upload log locali al server

#### **Request POST:**

```url
https://gymme-newaction.ddns.net/api/sync-gate/logs
```

#### **Payload JSON:**

```json
{
  "logs": [
    {
      "card_uid": "02D9BAEB",
      "direction": "in",
      "result": "authorized",
      "timestamp": "2025-10-16T03:10:00",
      "customer_id": 1670,
      "customer_name": "LORENZO RAMUNNO",
      "gate_id": "tornello_01"
    }
  ]
}
```

#### **Configurazione .env:**

```properties
SYNC_LOGS_ENDPOINT=/api/sync-gate/logs
SYNC_LOGS_INTERVAL=5
```

---

## 🔍 **4. HEALTH CHECK ENDPOINT**

### **URL:** `/api/health`

**Utilizzo:** Controllo stato server  
**Chiamato da:** `sync_manager.py`  
**Scopo:** Verificare connettività server

#### **Request GET:**

```url
https://gymme-newaction.ddns.net/api/health
```

#### **Response:**

```json
{
  "status": "ok",
  "timestamp": "2025-10-16T03:10:00"
}
```

#### **Configurazione .env:**

```properties
SYNC_HEALTH_ENDPOINT=/api/health
CONNECTION_CHECK_INTERVAL=30
```

---

## 🔄 **5. UPDATES ENDPOINT**

### **URL:** `/api/sync-gate/updates`

**Utilizzo:** Sincronizzazione aggiornamenti  
**Chiamato da:** `sync_manager.py`  
**Scopo:** Download aggiornamenti carte

#### **Request GET:**

```url
https://gymme-newaction.ddns.net/api/sync-gate/updates
```

#### **Configurazione .env:**

```properties
SYNC_UPDATES_ENDPOINT=/api/sync-gate/updates
SYNC_UPDATES_INTERVAL=15
```

---

## 📡 **MQTT BROKER**

### **Broker:** `mqbrk.ddns.net:8883`

**Utilizzo:** Comunicazione real-time  
**Chiamato da:** `mqtt_client.py`  
**Scopo:** Invio eventi carte e ricezione autorizzazioni

#### **Topic Pubblicazione:**

```
gate/tornello_01/badge
```

#### **Payload MQTT:**

```json
{
  "uid": "02D9BAEB",
  "direzione": "in",
  "tornello_id": "tornello_01",
  "timestamp": "2025-10-16T03:10:00",
  "reader_type": "PN532"
}
```

#### **Topic Ricezione:**

```
gate/tornello_01/auth_response
```

#### **Configurazione .env:**

```properties
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_CARD_READ_TOPIC=gate/tornello_01/badge
MQTT_AUTH_RESPONSE_TOPIC=gate/tornello_01/auth_response
```

---

## 🔧 **SSL/TLS Configuration**

**Tutti gli endpoint HTTPS utilizzano:**

```python
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

**Motivo:** Server con certificati self-signed

---

## 📈 **Performance Rilevate (Test Reali)**

| Endpoint                 | Tempo Medio | Utilizzo       |
| ------------------------ | ----------- | -------------- |
| `/api/sync-gate`         | ~229ms      | Cache refresh  |
| `/api/gate-verification` | ~295ms      | Autorizzazione |
| `/api/sync-gate/logs`    | ~100ms      | Sync log       |
| `/api/health`            | ~50ms       | Health check   |

---

## 🎯 **Workflow Endpoint nel Sistema**

### **Scenario Normale:**

1. **Carta letta** → Cache check locale
2. **Se cache OK** → MQTT → Broker → `/api/gate-verification` → Decisione
3. **Log locale** → `/api/sync-gate/logs` (periodico)

### **Scenario Cache Refresh:**

1. **Carta letta** → Cache nega (dati vecchi)
2. **Cache refresh** → `/api/sync-gate?card_uid=XXX` → Aggiorna cache
3. **Ricontrollo cache** → Se OK: workflow normale MQTT
4. **MQTT** → Broker → `/api/gate-verification` → Decisione finale

### **Scenario Sync Periodico:**

1. **Timer sync** → `/api/sync-gate` → Download tutte le carte
2. **Health check** → `/api/health` → Verifica server
3. **Log sync** → `/api/sync-gate/logs` → Upload log accessi

---

## 🔒 **Sicurezza e Separazione Responsabilità**

- **✅ Cache Refresh** = Solo `/api/sync-gate` (dati)
- **✅ Autorizzazione** = Solo `/api/gate-verification` (via broker)
- **✅ Nessun bypass** = Sempre workflow MQTT → broker → endpoint
- **✅ Singolo punto** = Broker decide chiamando gate-verification

**Il sistema RFID NON chiama mai direttamente `/api/gate-verification`**
