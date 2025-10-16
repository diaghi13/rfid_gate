#!/usr/bin/env python3
"""
🧪 Test MQTT Reale - Connessione Broker Vera
============================================
Test che si connette al broker MQTT reale e invia messaggi
che puoi vedere in MQTT Explorer.
"""

import asyncio
import time
import sys
import json
from pathlib import Path
from datetime import datetime

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

async def test_real_mqtt_connection():
    """Test connessione MQTT reale"""
    print("🧪 Test MQTT Reale - Connessione Broker")
    print("=" * 60)
    
    try:
        # Import configurazione reale
        from rfid_gate.config.settings import Config
        from rfid_gate.network.mqtt import AsyncMQTTClient, CardReadMessage
        
        print("📋 Configurazione MQTT:")
        print(f"   Broker: {Config.MQTT_BROKER}")
        print(f"   Port: {Config.MQTT_PORT}")
        print(f"   Username: {Config.MQTT_USERNAME}")
        print(f"   TLS: {Config.MQTT_USE_TLS}")
        print(f"   Card Read Topic: {Config.get_mqtt_topic('badge')}")
        print()
        
        # Crea config MQTT corretto
        mqtt_config = type('MQTTConfig', (), {
            'broker': Config.MQTT_BROKER,
            'port': Config.MQTT_PORT,
            'username': Config.MQTT_USERNAME,
            'password': Config.MQTT_PASSWORD,
            'use_tls': Config.MQTT_USE_TLS,
            'keep_alive': 60,
            'card_read_topic': Config.get_mqtt_topic('badge'),
            'auth_response_topic': Config.get_auth_response_topic()
        })()
        
        # Crea client MQTT reale
        print("🔌 Creazione client MQTT...")
        mqtt_client = AsyncMQTTClient(mqtt_config)
        
        # Inizializza client
        print("⚙️ Inizializzazione client MQTT...")
        initialized = await mqtt_client.initialize()
        if not initialized:
            print("❌ Inizializzazione fallita!")
            return False
        
        # Connetti al broker
        print("🔗 Connessione al broker MQTT...")
        connected = await mqtt_client.connect()
        
        if not connected:
            print("❌ Connessione fallita!")
            return False
            
        print("✅ Connesso al broker MQTT!")
        print()
        
        # Test invio messaggi reali
        test_cards = [
            "632D3903",
            "ABCD1234", 
            "12345678"
        ]
        
        for i, card_uid in enumerate(test_cards, 1):
            print(f"📤 Test {i}/{len(test_cards)} - Card: {card_uid}")
            
            # Crea messaggio card read reale
            message = CardReadMessage(
                card_uid=card_uid,
                identificativo_tornello=Config.TORNELLO_ID,
                timestamp=datetime.now().isoformat(),
                direzione="in",
                raw_id=card_uid,
                reader_id="pn532",
                auth_required=True
            )
            
            print(f"   Invio a topic: {Config.get_mqtt_topic('badge')}")
            
            # Invia messaggio reale
            success = await mqtt_client.send_card_read(message)
            
            if success:
                print(f"   ✅ Messaggio inviato con successo!")
                print(f"   📡 Controlla MQTT Explorer su topic: {Config.get_mqtt_topic('badge')}")
            else:
                print(f"   ❌ Invio fallito!")
            
            print()
            
            # Pausa tra invii
            await asyncio.sleep(2)
        
        # Disconnect
        print("🔌 Disconnessione...")
        await mqtt_client.disconnect()
        print("✅ Disconnesso dal broker")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test MQTT reale: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mqtt_payload_inspection():
    """Test per ispezionare payload MQTT"""
    print("\n🔍 Test Payload MQTT - Ispezione Dettagliata")
    print("=" * 60)
    
    try:
        from rfid_gate.config.settings import Config
        from rfid_gate.network.mqtt import CardReadMessage
        from datetime import datetime
        
        # Crea messaggio di test
        card_uid = "TEST123456"
        message = CardReadMessage(
            card_uid=card_uid,
            identificativo_tornello=Config.TORNELLO_ID,
            timestamp=datetime.now(),
            direzione="in",
            raw_id=card_uid,
            reader_id="pn532",
            auth_required=True
        )
        
        print("📋 Dettagli Messaggio MQTT:")
        print(f"   Card UID: {message.card_uid}")
        print(f"   Tornello ID: {message.identificativo_tornello}")
        print(f"   Timestamp: {message.timestamp}")
        print(f"   Direction: {message.direzione}")
        print(f"   Reader Type: {message.reader_id}")
        print(f"   Auth Required: {message.auth_required}")
        print()
        
        # Converti in payload JSON (come fa il client)
        payload = {
            "card_uid": message.card_uid,
            "identificativo_tornello": message.identificativo_tornello,
            "timestamp": message.timestamp.isoformat(),
            "direzione": message.direzione,
            "reader_id": message.reader_id,
            "auth_required": message.auth_required
        }
        
        print("📦 Payload JSON che verrà inviato:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print()
        
        print(f"📍 Topic di destinazione: {Config.get_mqtt_topic('badge')}")
        print()
        
        return payload
        
    except Exception as e:
        print(f"❌ Errore ispezione payload: {e}")
        return None

async def test_manual_mqtt_send():
    """Test invio MQTT manuale con paho-mqtt"""
    print("\n📡 Test MQTT Manuale - Paho Client")
    print("=" * 60)
    
    try:
        import paho.mqtt.client as mqtt
        import ssl
        from rfid_gate.config.settings import Config
        
        # Setup client paho
        client = mqtt.Client()
        
        # Configurazione TLS se necessario (senza verifica certificato per test)
        if Config.MQTT_USE_TLS:
            client.tls_set(ca_certs=None, certfile=None, keyfile=None, 
                          cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLS,
                          ciphers=None)
            client.tls_insecure_set(True)  # Disabilita verifica hostname
        
        # Credenziali
        if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
            client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)
        
        # Callback connessione
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✅ Connesso con paho-mqtt!")
            else:
                print(f"❌ Connessione fallita: {rc}")
        
        def on_publish(client, userdata, mid):
            print(f"✅ Messaggio pubblicato (mid: {mid})")
        
        client.on_connect = on_connect
        client.on_publish = on_publish
        
        # Connetti
        print(f"🔗 Connessione a {Config.MQTT_BROKER}:{Config.MQTT_PORT}...")
        client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
        
        # Start loop
        client.loop_start()
        
        # Aspetta connessione
        await asyncio.sleep(2)
        
        # Crea payload test
        test_payload = {
            "card_uid": "REAL_TEST_123",
            "identificativo_tornello": Config.TORNELLO_ID,
            "timestamp": datetime.now().isoformat(),
            "direzione": "in",
            "reader_type": "pn532_test",
            "auth_required": True,
            "test_source": "manual_mqtt_test"
        }
        
        topic = Config.get_mqtt_topic('badge')
        payload_json = json.dumps(test_payload)
        
        print(f"📤 Invio a topic: {topic}")
        print(f"📦 Payload: {payload_json}")
        
        # Pubblica messaggio
        result = client.publish(topic, payload_json, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ Pubblicazione avviata!")
            print("🔍 Controlla MQTT Explorer per vedere il messaggio!")
        else:
            print(f"❌ Errore pubblicazione: {result.rc}")
        
        # Aspetta pubblicazione
        await asyncio.sleep(3)
        
        # Disconnect
        client.loop_stop()
        client.disconnect()
        print("🔌 Disconnesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore MQTT manuale: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mqtt_explorer_guide():
    """Guida per MQTT Explorer"""
    print("\n📱 Guida MQTT Explorer")
    print("=" * 60)
    
    from rfid_gate.config.settings import Config
    
    print("🔧 Configurazione MQTT Explorer:")
    print(f"   Host: {Config.MQTT_BROKER}")
    print(f"   Port: {Config.MQTT_PORT}")
    print(f"   Username: {Config.MQTT_USERNAME}")
    print(f"   Password: {Config.MQTT_PASSWORD}")
    print(f"   Protocol: {'MQTT over TLS' if Config.MQTT_USE_TLS else 'MQTT'}")
    print()
    
    print("👀 Topic da monitorare:")
    print(f"   📍 {Config.get_mqtt_topic('badge')}")
    print(f"   📍 {Config.get_auth_response_topic()}")
    print(f"   📍 {Config.get_manual_open_topic()}")
    print()
    
    print("🎯 Cosa vedrai nei messaggi:")
    print("   • card_uid: ID della card")
    print("   • identificativo_tornello: tornello_01")
    print("   • timestamp: quando è stata letta")
    print("   • direzione: in/out")
    print("   • reader_type: pn532")
    print("   • auth_required: true/false")

async def main():
    """Test principale"""
    print("🧪 Test Suite MQTT Reale")
    print("=" * 60)
    print("Test di connessione e invio MQTT reale al broker")
    print("Messaggi visibili in MQTT Explorer!")
    print()
    
    # Guida MQTT Explorer
    await test_mqtt_explorer_guide()
    
    # Test payload inspection
    payload = await test_mqtt_payload_inspection()
    
    # Test connessione reale
    print("🚀 Avvio test connessione MQTT reale...")
    print("📱 Apri MQTT Explorer e connettiti al broker!")
    print()
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"⏳ Invio messaggi reali tra {i} secondi...")
        await asyncio.sleep(1)
    
    print()
    
    # Test connessione sistema
    success1 = await test_real_mqtt_connection()
    
    # Test manuale paho
    success2 = await test_manual_mqtt_send()
    
    print("\n" + "=" * 60)
    print("🎯 RISULTATI TEST MQTT REALE")
    print("=" * 60)
    
    if success1:
        print("✅ Test AsyncMQTTClient: SUCCESSO")
    else:
        print("❌ Test AsyncMQTTClient: FALLITO")
    
    if success2:
        print("✅ Test Paho Manual: SUCCESSO")
    else:
        print("❌ Test Paho Manual: FALLITO")
    
    if success1 or success2:
        print("\n🎉 MESSAGGI MQTT INVIATI!")
        print("📱 Controlla MQTT Explorer per vedere i messaggi reali!")
        from rfid_gate.config.settings import Config
        print(f"📍 Topic: {Config.get_mqtt_topic('badge')}")
    else:
        print("\n❌ Nessun messaggio inviato")
        print("🔧 Controlla configurazione broker MQTT")

if __name__ == "__main__":
    asyncio.run(main())