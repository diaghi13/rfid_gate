# 🔓 Guida Apertura Manuale Tornello

## 📖 Panoramica

Il sistema di apertura manuale permette di controllare il tornello da remoto tramite app/server o localmente senza bisogno di card RFID. Supporta autenticazione e logging completo.

## 🚀 Modalità di Controllo

### 📡 Controllo Remoto (MQTT)

- **App/Server → MQTT → Tornello**
- Richiede connessione internet
- Supporta autenticazione token
- Risposta di conferma automatica

### 🔧 Controllo Locale

- **Direttamente sul Raspberry Pi**
- Funziona sempre (anche offline)
- Per manutenzione e test
- Tramite script o comando

## ⚙️ Configurazione

### File `.env`

```bash
# Configurazione Apertura Manuale
MANUAL_OPEN_ENABLED=True                    # Abilita apertura manuale
MANUAL_OPEN_TOPIC_SUFFIX=manual_open        # Topic comandi MQTT
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response  # Topic risposte
MANUAL_OPEN_TIMEOUT=10                      # Timeout operazione (secondi)
MANUAL_OPEN_AUTH_REQUIRED=True              # Richiedi autenticazione
```

## 📡 Protocollo MQTT

### 📤 Topic Comandi (App → Tornello)

**Topic**: `gate/tornello_01/manual_open`

**Payload**:

```json
{
  "command_id": "cmd_1703123456",
  "direction": "in",
  "duration": 3,
  "user_id": "admin",
  "auth_token": "your_secure_token",
  "timestamp": "2024-12-20T10:30:00.000Z",
  "source": "mobile_app"
}
```

### 📥 Topic Risposte (Tornello → App)

**Topic**: `gate/tornello_01/manual_response`

**Payload**:

```json
{
  "command_id": "cmd_1703123456",
  "success": true,
  "message": "Apertura eseguita con successo",
  "user_id": "admin",
  "timestamp": "2024-12-20T10:30:05.000Z",
  "tornello_id": "tornello_01"
}
```

## 🛠️ Utilizzo Pratico

### 📱 Da App Mobile/Web

1. **Invia comando MQTT** con payload JSON
2. **Attendi risposta** sul topic response
3. **Mostra risultato** all'utente

### 🔧 Da Script Locale

```bash
# Apertura locale immediata
python3 manual_open_tool.py --local --direction in --duration 3

# Comando remoto via MQTT
python3 manual_open_tool.py --remote --direction in --user admin --token mytoken123
```

### 💻 Da Terminale Sistema

```bash
# Test rapido
python3 manual_open_tool.py --test

# Monitor risposte in tempo reale
python3 manual_open_tool.py --monitor
```

## 🔒 Sicurezza e Autenticazione

### 🔑 Token di Autenticazione

- **Minimo 8 caratteri**
- **Validazione server-side**
- **Timeout automatico**
- **Log di tutti i tentativi**

### 🛡️ Best Practices

```bash
# Token sicuri (esempi)
auth_token: "MySecureToken2024!"
auth_token: "App_Admin_987654321"
auth_token: "Mobile_User_ABC123XYZ"

# Evitare
auth_token: "123"          # Troppo corto
auth_token: "password"     # Troppo semplice
auth_token: ""             # Vuoto
```

### 🚨 Controlli di Sicurezza

- **Rate limiting**: Previene spam comandi
- **Token validation**: Verifica autenticità
- **User tracking**: Traccia chi apre cosa
- **Audit logging**: Log completo accessi

## 📊 Esempi di Integrazione

### 🌐 API REST Server

```python
@app.route('/api/open-gate', methods=['POST'])
def open_gate():
    data = request.json

    # Valida richiesta
    if not validate_user_token(data['user_id'], data['token']):
        return {'error': 'Unauthorized'}, 401

    # Invia comando MQTT
    command = {
        'command_id': generate_uuid(),
        'direction': data.get('direction', 'in'),
        'duration': data.get('duration', 2),
        'user_id': data['user_id'],
        'auth_token': data['token'],
        'timestamp': datetime.now().isoformat(),
        'source': 'api_server'
    }

    mqtt_client.publish('gate/tornello_01/manual_open', json.dumps(command))
    return {'status': 'command_sent', 'command_id': command['command_id']}
```

### 📱 App Mobile (React Native)

```javascript
const openGate = async (direction = "in", duration = 2) => {
  const command = {
    command_id: `mobile_${Date.now()}`,
    direction: direction,
    duration: duration,
    user_id: getCurrentUserId(),
    auth_token: await getAuthToken(),
    timestamp: new Date().toISOString(),
    source: "mobile_app",
  };

  // Invia via MQTT
  await mqttClient.publish(
    "gate/tornello_01/manual_open",
    JSON.stringify(command)
  );

  // Ascolta risposta
  mqttClient.subscribe("gate/tornello_01/manual_response");

  showLoading("Apertura in corso...");
};
```

### 🖥️ Dashboard Web

```html
<!-- Pulsante apertura -->
<button onclick="openGate('in')" class="btn-open">🔓 Apri Ingresso</button>

<script>
  function openGate(direction) {
    const payload = {
      command_id: "web_" + Date.now(),
      direction: direction,
      duration: 3,
      user_id: "web_admin",
      auth_token: "web_secure_token_123",
      timestamp: new Date().toISOString(),
      source: "web_dashboard",
    };

    // Invia tramite WebSocket o HTTP API
    sendMQTTCommand("gate/tornello_01/manual_open", payload);
  }
</script>
```

## 🔍 Debug e Monitoraggio

### 📋 Controllo Status

```bash
# Status sistema completo
python3 src/main.py --status

# Status specifico apertura manuale
python3 manual_open_tool.py --test
```

### 📊 Log e Statistiche

```bash
# Monitor log in tempo reale
tail -f logs/system.log | grep manual

# Statistiche aperture manuali
python3 -c "
from src.manual_control import ManualControl
from src.logger import AccessLogger
logger = AccessLogger('logs')
mc = ManualControl(None, None, logger)
print(mc.get_stats())
"
```

## 🔍 Debug e Monitoraggio

### 📋 Controllo Status

```bash
# Status sistema completo
python3 src/main.py --status

# Status specifico apertura manuale
python3 manual_open_tool.py --test
```

### 📊 Log e Statistiche

```bash
# Monitor log in tempo reale
tail -f logs/system.log | grep manual

# Statistiche aperture manuali
python3 -c "
from src.manual_control import ManualControl
from src.logger import AccessLogger
logger = AccessLogger('logs')
mc = ManualControl(None, None, logger)
print(mc.get_stats())
"
```

### 🧪 Test di Funzionamento

```bash
# Test completo sistema
python3 manual_open_tool.py --test

# Output atteso:
# ✅ MANUAL_OPEN_ENABLED: True
# ✅ MQTT disponibile per comandi remoti
# ✅ Relay Manager OK - Relè disponibili: ['in']
# ✅ Manual Control - Status: {...}
```

## ⚡ Scenari d'Uso

### 🏃‍♂️ Emergenza - Apertura Rapida

```bash
# Apertura immediata locale (sempre funziona)
sudo python3 manual_open_tool.py --local --duration 10
```

### 👥 Accesso Multiplo - Gruppo

```bash
# Apertura prolungata per gruppo
sudo python3 manual_open_tool.py --local --duration 30 --user "gruppo_visitatori"
```

### 🔧 Manutenzione - Test Relè

```bash
# Test di tutti i relè
for direction in in out; do
    echo "Test relè $direction..."
    sudo python3 manual_open_tool.py --local --direction $direction --duration 1
    sleep 2
done
```

### 📱 App Integration - Gestione Utenti

```python
# Esempio gestione utenti nell'app
class GateController:
    def __init__(self):
        self.mqtt_client = mqtt.Client()
        self.user_permissions = self.load_user_permissions()

    async def request_gate_open(self, user_id, gate_direction):
        # Verifica permessi utente
        if not self.check_user_permission(user_id, gate_direction):
            raise PermissionError(f"User {user_id} not allowed for {gate_direction}")

        # Genera comando
        command = {
            'command_id': f"app_{user_id}_{int(time.time())}",
            'direction': gate_direction,
            'duration': self.get_user_max_duration(user_id),
            'user_id': user_id,
            'auth_token': self.generate_user_token(user_id),
            'timestamp': datetime.now().isoformat(),
            'source': 'mobile_app_v2'
        }

        # Invia e aspetta conferma
        return await self.send_and_wait_response(command)
```

## 🎯 Configurazioni Avanzate

### 🔐 Sicurezza Massima

```bash
# Per ambienti ad alta sicurezza
MANUAL_OPEN_ENABLED=True
MANUAL_OPEN_AUTH_REQUIRED=True
MANUAL_OPEN_TIMEOUT=5               # Timeout ridotto
AUTH_ENABLED=True                   # Auth anche per RFID
OFFLINE_ALLOW_ACCESS=False          # No accessi offline
```

### 🏢 Ambiente Aziendale

```bash
# Per uffici e aziende
MANUAL_OPEN_ENABLED=True
MANUAL_OPEN_AUTH_REQUIRED=True
MANUAL_OPEN_TIMEOUT=10
BIDIRECTIONAL_MODE=True             # Ingresso e uscita
RELAY_IN_ACTIVE_TIME=3              # Più tempo per passaggio
RELAY_OUT_ACTIVE_TIME=3
```

### 🏠 Uso Residenziale

```bash
# Per case e condomini
MANUAL_OPEN_ENABLED=True
MANUAL_OPEN_AUTH_REQUIRED=False     # Auth semplificata
MANUAL_OPEN_TIMEOUT=15              # Timeout generoso
OFFLINE_ALLOW_ACCESS=True           # Sempre funzionante
```

## 🔄 Workflow Tipici

### 📋 Flusso App Mobile

1. **Utente apre app** → Login/autenticazione
2. **Preme "Apri Cancello"** → App genera comando
3. **Invia via MQTT** → Comando raggiunge tornello
4. **Tornello valida** → Controlla token e permessi
5. **Attiva relè** → Cancello si apre
6. **Invia conferma** → App riceve notifica successo
7. **Log evento** → Registra accesso nel sistema

### 🖥️ Flusso Dashboard Admin

1. **Admin accede dashboard** → Visualizza stato tornelli
2. **Vede richiesta accesso** → Notifica utente in attesa
3. **Clicca "Autorizza"** → Invia comando apertura
4. **Monitor real-time** → Vede relè che si attiva
5. **Conferma operazione** → Log e notifica utente

### 🚨 Flusso Emergenza

1. **Allarme/emergenza** → Sistema rileva situazione
2. **Apertura automatica** → Script attiva tutti i relè
3. **Notifica security** → Avvisa personale di sicurezza
4. **Log eventi** → Registra tutto per audit

## 📈 Monitoraggio e Analytics

### 📊 Metriche Importanti

- **Aperture manuali/giorno**: Traccia utilizzo
- **Utenti più attivi**: Identifica pattern
- **Orari di picco**: Ottimizza sistema
- **Tasso successo**: Monitora affidabilità
- **Tempo risposta**: Performance sistema

### 🎯 Dashboard Metriche

```python
def get_manual_open_analytics():
    return {
        'daily_manual_opens': count_today_manual_opens(),
        'top_users': get_top_manual_users(limit=10),
        'peak_hours': get_peak_manual_hours(),
        'success_rate': calculate_success_rate(),
        'avg_response_time': get_avg_response_time(),
        'failed_attempts': count_failed_attempts()
    }
```

## 🛠️ Risoluzione Problemi

### ❌ Comando Non Funziona

```bash
# 1. Verifica configurazione
python3 manual_open_tool.py --test

# 2. Controlla connessione MQTT
python3 src/offline_utils.py --test-connection

# 3. Test locale
sudo python3 manual_open_tool.py --local

# 4. Monitor log
tail -f logs/system.log | grep -E "(manual|error)"
```

### 🔴 Relè Non Scatta

```bash
# 1. Verifica relè disponibili
python3 -c "
from src.relay_manager import RelayManager
rm = RelayManager()
rm.initialize()
print('Relè attivi:', rm.get_active_relays())
rm.cleanup()
"

# 2. Test relè diretto
sudo python3 -c "
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)  # Cambia pin se necessario
GPIO.output(18, GPIO.HIGH)
time.sleep(2)
GPIO.output(18, GPIO.LOW)
GPIO.cleanup()
print('Test relè completato')
"
```

### 📡 MQTT Non Risponde

```bash
# 1. Test connessione broker
mosquitto_pub -h mqbrk.ddns.net -p 8883 -u palestraUser -P "28dade03$" \
    --capath /etc/ssl/certs -t "test/topic" -m "test_message"

# 2. Monitor topic
mosquitto_sub -h mqbrk.ddns.net -p 8883 -u palestraUser -P "28dade03$" \
    --capath /etc/ssl/certs -t "gate/tornello_01/manual_open"
```

### 🔒 Autenticazione Fallisce

```bash
# Verifica token nell'invio
echo "Token deve essere minimo 8 caratteri e non vuoto"

# Test con token valido
python3 manual_open_tool.py --remote --token "ValidToken123" --user "testuser"
```

## 🎉 Esempi Pratici Completi

### 📱 App React Native - Componente Completo

````jsx
import React, { useState, useEffect } from 'react';
import { View, Button, Alert, Text } from 'react-native';
import mqtt from 'react-native-mqtt';

const GateControl = ({ tornelloId = 'tornello_01' }) => {
  const [isOpening, setIsOpening] = useState(false);
  const [mqttClient, setMqttClient] = useState(null);

  useEffect(() => {
    // Inizializza MQTT
    const client = mqtt.createClient({
      host: 'mqbrk.ddns.net',
      port: 8883,
      protocol: 'mqtts',
      username: 'palestraUser',
      password: '28dade03# 🔓 Guida Apertura Manuale Tornello

## 📖 Panoramica

Il sistema di apertura manuale permette di controllare il tornello da remoto tramite app/server o localmente senza bisogno di card RFID. Supporta autenticazione e logging completo.

## 🚀 Modalità di Controllo

### 📡 Controllo Remoto (MQTT)
- **App/Server → MQTT → Tornello**
- Richiede connessione internet
- Supporta autenticazione token
- Risposta di conferma automatica

### 🔧 Controllo Locale
- **Direttamente sul Raspberry Pi**
- Funziona sempre (anche offline)
- Per manutenzione e test
- Tramite script o comando

## ⚙️ Configurazione

### File `.env`
```bash
# Configurazione Apertura Manuale
MANUAL_OPEN_ENABLED=True                    # Abilita apertura manuale
MANUAL_OPEN_TOPIC_SUFFIX=manual_open        # Topic comandi MQTT
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response  # Topic risposte
MANUAL_OPEN_TIMEOUT=10                      # Timeout operazione (secondi)
MANUAL_OPEN_AUTH_REQUIRED=True              # Richiedi autenticazione
````

## 📡 Protocollo MQTT

### 📤 Topic Comandi (App → Tornello)

**Topic**: `gate/tornello_01/manual_open`

**Payload**:

```json
{
  "command_id": "cmd_1703123456",
  "direction": "in",
  "duration": 3,
  "user_id": "admin",
  "auth_token": "your_secure_token",
  "timestamp": "2024-12-20T10:30:00.000Z",
  "source": "mobile_app"
}
```

### 📥 Topic Risposte (Tornello → App)

**Topic**: `gate/tornello_01/manual_response`

**Payload**:

```json
{
  "command_id": "cmd_1703123456",
  "success": true,
  "message": "Apertura eseguita con successo",
  "user_id": "admin",
  "timestamp": "2024-12-20T10:30:05.000Z",
  "tornello_id": "tornello_01"
}
```

## 🛠️ Utilizzo Pratico

### 📱 Da App Mobile/Web

1. **Invia comando MQTT** con payload JSON
2. **Attendi risposta** sul topic response
3. **Mostra risultato** all'utente

### 🔧 Da Script Locale

```bash
# Apertura locale immediata
python3 manual_open_tool.py --local --direction in --duration 3

# Comando remoto via MQTT
python3 manual_open_tool.py --remote --direction in --user admin --token mytoken123
```

### 💻 Da Terminale Sistema

```bash
# Test rapido
python3 manual_open_tool.py --test

# Monitor risposte in tempo reale
python3 manual_open_tool.py --monitor
```

## 🔒 Sicurezza e Autenticazione

### 🔑 Token di Autenticazione

- **Minimo 8 caratteri**
- **Validazione server-side**
- **Timeout automatico**
- **Log di tutti i tentativi**

### 🛡️ Best Practices

```bash
# Token sicuri (esempi)
auth_token: "MySecureToken2024!"
auth_token: "App_Admin_987654321"
auth_token: "Mobile_User_ABC123XYZ"

# Evitare
auth_token: "123"          # Troppo corto
auth_token: "password"     # Troppo semplice
auth_token: ""             # Vuoto
```

### 🚨 Controlli di Sicurezza

- **Rate limiting**: Previene spam comandi
- **Token validation**: Verifica autenticità
- **User tracking**: Traccia chi apre cosa
- **Audit logging**: Log completo accessi

## 📊 Esempi di Integrazione

### 🌐 API REST Server

```python
@app.route('/api/open-gate', methods=['POST'])
def open_gate():
    data = request.json

    # Valida richiesta
    if not validate_user_token(data['user_id'], data['token']):
        return {'error': 'Unauthorized'}, 401

    # Invia comando MQTT
    command = {
        'command_id': generate_uuid(),
        'direction': data.get('direction', 'in'),
        'duration': data.get('duration', 2),
        'user_id': data['user_id'],
        'auth_token': data['token'],
        'timestamp': datetime.now().isoformat(),
        'source': 'api_server'
    }

    mqtt_client.publish('gate/tornello_01/manual_open', json.dumps(command))
    return {'status': 'command_sent', 'command_id': command['command_id']}
```

### 📱 App Mobile (React Native)

```javascript
const openGate = async (direction = "in", duration = 2) => {
  const command = {
    command_id: `mobile_${Date.now()}`,
    direction: direction,
    duration: duration,
    user_id: getCurrentUserId(),
    auth_token: await getAuthToken(),
    timestamp: new Date().toISOString(),
    source: "mobile_app",
  };

  // Invia via MQTT
  await mqttClient.publish(
    "gate/tornello_01/manual_open",
    JSON.stringify(command)
  );

  // Ascolta risposta
  mqttClient.subscribe("gate/tornello_01/manual_response");

  showLoading("Apertura in corso...");
};
```

### 🖥️ Dashboard Web

```html
<!-- Pulsante apertura -->
<button onclick="openGate('in')" class="btn-open">🔓 Apri Ingresso</button>

<script>
  function openGate(direction) {
    const payload = {
      command_id: "web_" + Date.now(),
      direction: direction,
      duration: 3,
      user_id: "web_admin",
      auth_token: "web_secure_token_123",
      timestamp: new Date().toISOString(),
      source: "web_dashboard",
    };

    // Invia tramite WebSocket o HTTP API
    sendMQTTCommand("gate/tornello_01/manual_open", payload);
  }
</script>
```

## 🔍 Debug e Monitoraggio

### 📋 Controllo Status

```bash
# Status sistema completo
python3 src/main.py --status

# Status specifico apertura manuale
python3 manual_open_tool.py --test
```

### 📊 Log e Statistiche

```bash
# Monitor log in tempo reale
tail -f logs/system.log | grep manual

# Statistiche aperture manuali
python3 -c "
from src.manual_control import ManualControl
from src.logger import AccessLogger
logger = AccessLogger('logs')
mc = ManualControl(None, None, logger)
print(mc.get_stats())
"
```

    });

    client.on('connect', () => {
      client.subscribe(`gate/${tornelloId}/manual_response`);
    });

    client.on('message', (topic, message) => {
      if (topic === `gate/${tornelloId}/manual_response`) {
        const response = JSON.parse(message.toString());
        handleOpenResponse(response);
      }
    });

    setMqttClient(client);

    return () => client?.disconnect();

}, [tornelloId]);

const openGate = async (direction = 'in') => {
if (!mqttClient || isOpening) return;

    setIsOpening(true);

    const command = {
      command_id: `mobile_${Date.now()}`,
      direction,
      duration: 3,
      user_id: await getCurrentUserId(),
      auth_token: await getStoredAuthToken(),
      timestamp: new Date().toISOString(),
      source: 'react_native_app'
    };

    try {
      mqttClient.publish(
        `gate/${tornelloId}/manual_open`,
        JSON.stringify(command),
        { qos: 1 }
      );

      // Auto-timeout dopo 10 secondi
      setTimeout(() => {
        if (isOpening) {
          setIsOpening(false);
          Alert.alert('Timeout', 'Nessuna risposta dal tornello');
        }
      }, 10000);

    } catch (error) {
      setIsOpening(false);
      Alert.alert('Errore', 'Impossibile inviare comando');
    }

};

const handleOpenResponse = (response) => {
setIsOpening(false);

    if (response.success) {
      Alert.alert('Successo', response.message || 'Tornello aperto');
    } else {
      Alert.alert('Errore', response.message || 'Comando fallito');
    }

};

return (
<View style={{ padding: 20 }}>
<Button
title={isOpening ? "Apertura in corso..." : "🔓 Apri Cancello"}
onPress={() => openGate('in')}
disabled={isOpening}
/>

      <Text style={{ marginTop: 10, textAlign: 'center', color: '#666' }}>
        Tornello: {tornelloId}
      </Text>
    </View>

);
};

export default GateControl;

````

Il sistema di apertura manuale è ora completo e ready per l'integrazione con qualsiasi app o sistema! 🎯

**Vantaggi chiave:**
- ✅ **Controllo remoto** via MQTT
- ✅ **Backup locale** sempre funzionante
- ✅ **Autenticazione sicura** con token
- ✅ **Logging completo** di tutti gli eventi
- ✅ **API standardizzata** JSON su MQTT
- ✅ **Monitoraggio real-time** con feedback
- ✅ **Integrazione semplice** con app esistenti# 🔓 Guida Apertura Manuale Tornello

## 📖 Panoramica

Il sistema di apertura manuale permette di controllare il tornello da remoto tramite app/server o localmente senza bisogno di card RFID. Supporta autenticazione e logging completo.

## 🚀 Modalità di Controllo

### 📡 Controllo Remoto (MQTT)
- **App/Server → MQTT → Tornello**
- Richiede connessione internet
- Supporta autenticazione token
- Risposta di conferma automatica

### 🔧 Controllo Locale
- **Direttamente sul Raspberry Pi**
- Funziona sempre (anche offline)
- Per manutenzione e test
- Tramite script o comando

## ⚙️ Configurazione

### File `.env`
```bash
# Configurazione Apertura Manuale
MANUAL_OPEN_ENABLED=True                    # Abilita apertura manuale
MANUAL_OPEN_TOPIC_SUFFIX=manual_open        # Topic comandi MQTT
MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX=manual_response  # Topic risposte
MANUAL_OPEN_TIMEOUT=10                      # Timeout operazione (secondi)
MANUAL_OPEN_AUTH_REQUIRED=True              # Richiedi autenticazione
````

## 📡 Protocollo MQTT

### 📤 Topic Comandi (App → Tornello)

**Topic**: `gate/tornello_01/manual_open`

**Payload**:

```json
{
  "command_id": "cmd_1703123456",
  "direction": "in",
  "duration": 3,
  "user_id": "admin",
  "auth_token": "your_secure_token",
  "timestamp": "2024-12-20T10:30:00.000Z",
  "source": "mobile_app"
}
```

### 📥 Topic Risposte (Tornello → App)

**Topic**: `gate/tornello_01/manual_response`

**Payload**:

```json
{
  "command_id": "cmd_1703123456",
  "success": true,
  "message": "Apertura eseguita con successo",
  "user_id": "admin",
  "timestamp": "2024-12-20T10:30:05.000Z",
  "tornello_id": "tornello_01"
}
```

## 🛠️ Utilizzo Pratico

### 📱 Da App Mobile/Web

1. **Invia comando MQTT** con payload JSON
2. **Attendi risposta** sul topic response
3. **Mostra risultato** all'utente

### 🔧 Da Script Locale

```bash
# Apertura locale immediata
python3 manual_open_tool.py --local --direction in --duration 3

# Comando remoto via MQTT
python3 manual_open_tool.py --remote --direction in --user admin --token mytoken123
```

### 💻 Da Terminale Sistema

```bash
# Test rapido
python3 manual_open_tool.py --test

# Monitor risposte in tempo reale
python3 manual_open_tool.py --monitor
```

## 🔒 Sicurezza e Autenticazione

### 🔑 Token di Autenticazione

- **Minimo 8 caratteri**
- **Validazione server-side**
- **Timeout automatico**
- **Log di tutti i tentativi**

### 🛡️ Best Practices

```bash
# Token sicuri (esempi)
auth_token: "MySecureToken2024!"
auth_token: "App_Admin_987654321"
auth_token: "Mobile_User_ABC123XYZ"

# Evitare
auth_token: "123"          # Troppo corto
auth_token: "password"     # Troppo semplice
auth_token: ""             # Vuoto
```

### 🚨 Controlli di Sicurezza

- **Rate limiting**: Previene spam comandi
- **Token validation**: Verifica autenticità
- **User tracking**: Traccia chi apre cosa
- **Audit logging**: Log completo accessi

## 📊 Esempi di Integrazione

### 🌐 API REST Server

```python
@app.route('/api/open-gate', methods=['POST'])
def open_gate():
    data = request.json

    # Valida richiesta
    if not validate_user_token(data['user_id'], data['token']):
        return {'error': 'Unauthorized'}, 401

    # Invia comando MQTT
    command = {
        'command_id': generate_uuid(),
        'direction': data.get('direction', 'in'),
        'duration': data.get('duration', 2),
        'user_id': data['user_id'],
        'auth_token': data['token'],
        'timestamp': datetime.now().isoformat(),
        'source': 'api_server'
    }

    mqtt_client.publish('gate/tornello_01/manual_open', json.dumps(command))
    return {'status': 'command_sent', 'command_id': command['command_id']}
```

### 📱 App Mobile (React Native)

```javascript
const openGate = async (direction = "in", duration = 2) => {
  const command = {
    command_id: `mobile_${Date.now()}`,
    direction: direction,
    duration: duration,
    user_id: getCurrentUserId(),
    auth_token: await getAuthToken(),
    timestamp: new Date().toISOString(),
    source: "mobile_app",
  };

  // Invia via MQTT
  await mqttClient.publish(
    "gate/tornello_01/manual_open",
    JSON.stringify(command)
  );

  // Ascolta risposta
  mqttClient.subscribe("gate/tornello_01/manual_response");

  showLoading("Apertura in corso...");
};
```

### 🖥️ Dashboard Web

```html
<!-- Pulsante apertura -->
<button onclick="openGate('in')" class="btn-open">🔓 Apri Ingresso</button>

<script>
  function openGate(direction) {
    const payload = {
      command_id: "web_" + Date.now(),
      direction: direction,
      duration: 3,
      user_id: "web_admin",
      auth_token: "web_secure_token_123",
      timestamp: new Date().toISOString(),
      source: "web_dashboard",
    };

    // Invia tramite WebSocket o HTTP API
    sendMQTTCommand("gate/tornello_01/manual_open", payload);
  }
</script>
```

## 🔍 Debug e Monitoraggio

### 📋 Controllo Status

```bash
# Status sistema completo
python3 src/main.py --status

# Status specifico apertura manuale
python3 manual_open_tool.py --test
```

### 📊 Log e Statistiche

```bash
# Monitor log in tempo reale
tail -f logs/system.log | grep manual

# Statistiche aperture manuali
python3 -c "
from src.manual_control import ManualControl
from src.logger import AccessLogger
logger = AccessLogger('logs')
mc = ManualControl(None, None, logger)
print(mc.get_stats())
"
```
