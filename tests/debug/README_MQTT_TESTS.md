# 🧪 Test Debug - MQTT Connection & Reconnection

Questa cartella contiene i test per la diagnosi e verifica del sistema MQTT, in particolare per i problemi di riconnessione dopo riavvio del broker.

## 📋 Test MQTT Recenti

### `test_mqtt_real.py`

**Scopo**: Test completo della connessione MQTT reale al broker

- ✅ Verifica connessione TLS a `mqbrk.ddns.net:8883`
- ✅ Test autenticazione con credenziali dal `.env`
- ✅ Invio e ricezione messaggi bidirezionali
- ✅ Sottoscrizione a tutti i topics necessari
- ✅ Statistiche di connessione e performance

**Utilizzo**:

```bash
cd /path/to/rfid_gate
python3 tests/debug/test_mqtt_real.py
```

### `test_reconnection_mqtt.py`

**Scopo**: Test specifico per la riconnessione automatica MQTT

- 🔄 Monitora riconnessioni automatiche
- ⏱️ Test continuo per 2 minuti con messaggi ogni 10s
- 📊 Statistiche dettagliate su connessioni/disconnessioni
- 🔔 Permette di testare riavvio broker durante esecuzione
- ♻️ Verifica tentativi di riconnessione e resilienza

**Utilizzo**:

```bash
cd /path/to/rfid_gate
python3 tests/debug/test_reconnection_mqtt.py
```

### `test_mqtt_patch.py`

**Scopo**: Verifica che la patch di resilienza sia stata applicata

- ✅ Conferma max_retries aumentato da 3 a 10
- ✅ Conferma reconnect_delay ridotto da 5s a 2s
- ✅ Verifica reset automatico tentativi ogni 5 minuti
- ✅ Test inizializzazione e connessione con patch

**Utilizzo**:

```bash
cd /path/to/rfid_gate
python3 tests/debug/test_mqtt_patch.py
```

## 🔧 Patch Applicata

La patch per la resilienza MQTT è stata applicata al file:

- `rfid_gate/network/mqtt.py`

**Miglioramenti**:

1. **Max retries**: `3` → `10` tentativi
2. **Reconnect delay**: `5.0s` → `2.0s`
3. **Reset automatico**: Ogni 5 minuti resetta i tentativi
4. **Resilienza infinita**: Non si blocca mai in stato ERROR

## 📊 Risultati Attesi

### Test Connessione (`test_mqtt_real.py`)

```
✅ MQTT COMPLETAMENTE OPERATIVO!
   - Connessione broker: OK
   - Autenticazione: OK
   - Invio messaggi: OK
   - Sottoscrizione topics: OK
```

### Test Riconnessione (`test_reconnection_mqtt.py`)

```
🎉 RICONNESSIONE AUTOMATICA FUNZIONA!
📊 Connessioni totali: X
🔄 Disconnessioni totali: Y
♻️ Tentativi riconnessione: Z
📤 Messaggi inviati: N
✅ Stato finale: CONNESSO
```

### Test Patch (`test_mqtt_patch.py`)

```
✅ PATCH APPLICATA CORRETTAMENTE!
• Max retries aumentato a 10
• Delay ridotto a 2 secondi
• Reset automatico tentativi ogni 5 minuti
• Miglior resilienza dopo riavvio broker
```

## 🐛 Problema Risolto

**Sintomo**: Dopo riavvio del broker MQTT, il sistema non si riconnetteva più e non si vedevano più le chiamate MQTT.

**Causa**: Il sistema aveva un limite di soli 3 tentativi di riconnessione, dopo i quali andava in stato ERROR e smetteva di tentare.

**Soluzione**: Patch applicata per aumentare i tentativi, ridurre i delay e implementare reset automatico dei tentativi.

## 🚀 Utilizzo in Produzione

Per applicare la patch a un sistema in produzione:

1. **Ferma il sistema**:

   ```bash
   sudo systemctl stop rfid_gate
   # oppure
   pkill -f main.py
   ```

2. **Riavvia con patch**:

   ```bash
   cd /path/to/rfid_gate
   python3 main.py
   ```

3. **Verifica funzionamento**:
   ```bash
   python3 tests/debug/test_mqtt_patch.py
   ```

Il sistema ora si riconnetterà automaticamente anche dopo riavvii del broker entro 20 secondi.
