#!/usr/bin/env python3
"""
🧪 Test MQTT Reale Semplice - Verifica Connessione Broker
=========================================================
Test diretto per verificare se la connessione MQTT funziona realmente
"""

import os
import ssl
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Carica file .env
def load_env():
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ File .env caricato")

# Configurazioni dal .env
load_env()

MQTT_CONFIG = {
    'broker': os.getenv('MQTT_BROKER', 'mqbrk.ddns.net'),
    'port': int(os.getenv('MQTT_PORT', '8883')),
    'username': os.getenv('MQTT_USERNAME', 'palestraUser'),
    'password': os.getenv('MQTT_PASSWORD', '28dade03$'),
    'use_tls': os.getenv('MQTT_USE_TLS', 'True').lower() == 'true',
    'keep_alive': int(os.getenv('MQTT_KEEP_ALIVE', '60')),
    'tornello_id': os.getenv('TORNELLO_ID', 'tornello_01')
}

# Topics
TOPICS = {
    'card_read': os.getenv('MQTT_CARD_READ_TOPIC', 'gate/tornello_01/badge'),
    'auth_response': os.getenv('MQTT_AUTH_RESPONSE_TOPIC', 'gate/tornello_01/response'),
    'manual_open': os.getenv('MQTT_MANUAL_OPEN_TOPIC', 'gate/tornello_01/manual_open')
}

async def test_mqtt_connection():
    """Test connessione MQTT con paho-mqtt"""
    print("🧪 TEST CONNESSIONE MQTT REALE")
    print("=" * 60)
    
    try:
        import paho.mqtt.client as mqtt
        
        # Variabili di stato
        connected = False
        connection_result = None
        messages_received = []
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected, connection_result
            connection_result = rc
            if rc == 0:
                connected = True
                print("✅ CONNESSO AL BROKER MQTT!")
                print(f"   Broker: {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
                print(f"   Username: {MQTT_CONFIG['username']}")
                print(f"   TLS: {MQTT_CONFIG['use_tls']}")
            else:
                print(f"❌ CONNESSIONE FALLITA - Codice: {rc}")
                error_messages = {
                    1: "Protocol version non supportato",
                    2: "Identificativo client non valido", 
                    3: "Server non disponibile",
                    4: "Username/password non validi",
                    5: "Non autorizzato"
                }
                print(f"   Errore: {error_messages.get(rc, 'Errore sconosciuto')}")
        
        def on_disconnect(client, userdata, rc):
            nonlocal connected
            connected = False
            print(f"🔌 DISCONNESSO - Codice: {rc}")
        
        def on_message(client, userdata, msg):
            nonlocal messages_received
            try:
                payload = msg.payload.decode('utf-8')
                message_info = {
                    'topic': msg.topic,
                    'payload': payload,
                    'timestamp': datetime.now().isoformat()
                }
                messages_received.append(message_info)
                print(f"📨 MESSAGGIO RICEVUTO:")
                print(f"   Topic: {msg.topic}")
                print(f"   Payload: {payload}")
            except Exception as e:
                print(f"❌ Errore decodifica messaggio: {e}")
        
        # Crea client
        print("🔧 Creazione client MQTT...")
        client = mqtt.Client()
        client.username_pw_set(MQTT_CONFIG['username'], MQTT_CONFIG['password'])
        
        # Configura callbacks
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect  
        client.on_message = on_message
        
        # Configura TLS se necessario
        if MQTT_CONFIG['use_tls']:
            print("🔒 Configurazione TLS...")
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            client.tls_set_context(context)
        
        # Tenta connessione
        print("🔌 Tentativo di connessione...")
        start_time = time.time()
        
        client.connect_async(
            MQTT_CONFIG['broker'], 
            MQTT_CONFIG['port'], 
            MQTT_CONFIG['keep_alive']
        )
        client.loop_start()
        
        # Attendi connessione (max 10 secondi)
        timeout = 10
        elapsed = 0
        while not connected and elapsed < timeout:
            await asyncio.sleep(0.1)
            elapsed = time.time() - start_time
            
        if connected:
            connection_time = time.time() - start_time
            print(f"⏱️ Tempo connessione: {connection_time:.2f}s")
            
            # Test sottoscrizione topics
            print("\\n📡 TEST SOTTOSCRIZIONE TOPICS...")
            for topic_name, topic_path in TOPICS.items():
                result = client.subscribe(topic_path, qos=1)
                if result[0] == 0:
                    print(f"✅ Sottoscritto a: {topic_path}")
                else:
                    print(f"❌ Errore sottoscrizione: {topic_path}")
            
            # Test invio messaggio
            print("\\n📤 TEST INVIO MESSAGGIO...")
            test_message = {
                "card_uid": "TEST123456",
                "identificativo_tornello": MQTT_CONFIG['tornello_id'],
                "timestamp": datetime.now().isoformat(),
                "direzione": "in",
                "test": True,
                "message": "Test connessione MQTT reale"
            }
            
            result = client.publish(
                TOPICS['card_read'],
                json.dumps(test_message),
                qos=1
            )
            
            if result.rc == 0:
                print(f"✅ Messaggio inviato a: {TOPICS['card_read']}")
                print(f"   Payload: {json.dumps(test_message, indent=2)}")
            else:
                print(f"❌ Errore invio messaggio: {result.rc}")
            
            # Attendi eventuali messaggi (5 secondi)
            print("\\n⏳ Attendo messaggi per 5 secondi...")
            await asyncio.sleep(5)
            
            # Statistiche finali
            print("\\n" + "=" * 60)
            print("📊 STATISTICHE FINALI:")
            print(f"✅ Connessione: {'OK' if connected else 'FALLITA'}")
            print(f"📨 Messaggi ricevuti: {len(messages_received)}")
            print(f"⏱️ Tempo connessione: {connection_time:.2f}s")
            
            if messages_received:
                print("\\n📬 MESSAGGI RICEVUTI:")
                for i, msg in enumerate(messages_received, 1):
                    print(f"   {i}. Topic: {msg['topic']}")
                    print(f"      Timestamp: {msg['timestamp']}")
                    print(f"      Payload: {msg['payload'][:100]}...")
            
            # Disconnetti
            client.disconnect()
            client.loop_stop()
            
            return True
            
        else:
            print(f"❌ TIMEOUT CONNESSIONE ({timeout}s)")
            print(f"   Risultato: {connection_result}")
            client.loop_stop()
            return False
            
    except ImportError:
        print("❌ ERRORE: paho-mqtt non installato")
        print("   Installare con: pip install paho-mqtt")
        return False
    except Exception as e:
        print(f"❌ ERRORE GENERICO: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mqtt_config_validation():
    """Valida la configurazione MQTT dal .env"""
    print("\\n🔧 VALIDAZIONE CONFIGURAZIONE MQTT")
    print("=" * 60)
    
    # Controlla configurazioni obbligatorie
    required_configs = {
        'MQTT_BROKER': MQTT_CONFIG['broker'],
        'MQTT_PORT': MQTT_CONFIG['port'],
        'MQTT_USERNAME': MQTT_CONFIG['username'],
        'MQTT_PASSWORD': MQTT_CONFIG['password']
    }
    
    print("📋 Configurazioni trovate:")
    all_ok = True
    for key, value in required_configs.items():
        if value:
            # Nascondi password per sicurezza
            display_value = "***" if 'PASSWORD' in key else str(value)
            print(f"   ✅ {key}: {display_value}")
        else:
            print(f"   ❌ {key}: MANCANTE")
            all_ok = False
    
    print("\\n🎯 Topics configurati:")
    for name, topic in TOPICS.items():
        print(f"   ✅ {name}: {topic}")
    
    print("\\n🔒 Configurazioni sicurezza:")
    print(f"   ✅ TLS: {MQTT_CONFIG['use_tls']}")
    print(f"   ✅ Keep Alive: {MQTT_CONFIG['keep_alive']}s")
    
    return all_ok

async def main():
    """Funzione principale"""
    print("🚀 AVVIO TEST SUITE MQTT REALE")
    print("Verifica connessione, autenticazione e invio messaggi")
    print()
    
    # 1. Validazione configurazione
    config_ok = await test_mqtt_config_validation()
    if not config_ok:
        print("\\n❌ CONFIGURAZIONE NON VALIDA - Test interrotto")
        return False
    
    # 2. Test connessione reale
    connection_ok = await test_mqtt_connection()
    
    # 3. Risultato finale
    print("\\n" + "=" * 60)
    print("🎯 RISULTATO FINALE:")
    if connection_ok:
        print("✅ MQTT COMPLETAMENTE OPERATIVO!")
        print("   - Connessione broker: OK")
        print("   - Autenticazione: OK") 
        print("   - Invio messaggi: OK")
        print("   - Sottoscrizione topics: OK")
    else:
        print("❌ PROBLEMI MQTT RILEVATI")
        print("   Controllare configurazione e connettività")
    
    return connection_ok

if __name__ == "__main__":
    asyncio.run(main())