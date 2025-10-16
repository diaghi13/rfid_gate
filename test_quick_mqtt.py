#!/usr/bin/env python3
"""
🔧 Test Quick MQTT - Verifica problemi specifici
=================================================
"""

import sys
from pathlib import Path
from datetime import datetime

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

def test_cardreadmessage_creation():
    """Test creazione CardReadMessage"""
    try:
        from rfid_gate.network.mqtt import CardReadMessage
        from rfid_gate.config.settings import Config
        
        print("🧪 Test creazione CardReadMessage")
        print("=" * 50)
        
        # Test creazione corretta
        message = CardReadMessage(
            card_uid="TEST123456",
            identificativo_tornello=Config.TORNELLO_ID,
            timestamp=datetime.now().isoformat(),
            direzione="in",
            raw_id="TEST123456",
            reader_id="pn532"
        )
        
        print("✅ Messaggio creato con successo!")
        print(f"   Card UID: {message.card_uid}")
        print(f"   Tornello: {message.identificativo_tornello}")
        print(f"   Direzione: {message.direzione}")
        print(f"   Reader ID: {message.reader_id}")
        print(f"   Raw ID: {message.raw_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore creazione CardReadMessage: {e}")
        return False

def test_mqtt_config():
    """Test configurazione MQTT"""
    try:
        from rfid_gate.config.settings import Config
        
        print("\n🧪 Test configurazione MQTT")
        print("=" * 50)
        
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
        
        print("✅ Config MQTT creato con successo!")
        print(f"   Broker: {mqtt_config.broker}")
        print(f"   Port: {mqtt_config.port}")
        print(f"   Card Topic: {mqtt_config.card_read_topic}")
        print(f"   Auth Topic: {mqtt_config.auth_response_topic}")
        
        return mqtt_config
        
    except Exception as e:
        print(f"❌ Errore configurazione MQTT: {e}")
        return None

async def test_mqtt_client_init():
    """Test inizializzazione client MQTT"""
    try:
        from rfid_gate.network.mqtt import AsyncMQTTClient
        
        print("\n🧪 Test inizializzazione AsyncMQTTClient")
        print("=" * 50)
        
        # Usa config creato dal test precedente
        mqtt_config = test_mqtt_config()
        if not mqtt_config:
            return False
        
        # Crea client
        client = AsyncMQTTClient(mqtt_config)
        print("✅ Client MQTT creato!")
        
        # Tenta inizializzazione
        initialized = await client.initialize()
        if initialized:
            print("✅ Client MQTT inizializzato!")
        else:
            print("❌ Inizializzazione client fallita")
            
        return initialized
        
    except Exception as e:
        print(f"❌ Errore inizializzazione client: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Test Quick MQTT - Verifica problemi")
    print("=" * 60)
    
    # Test 1: CardReadMessage
    success1 = test_cardreadmessage_creation()
    
    # Test 2: Config MQTT
    success2 = test_mqtt_config() is not None
    
    # Test 3: Client MQTT (async)
    import asyncio
    success3 = asyncio.run(test_mqtt_client_init())
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI:")
    print(f"   CardReadMessage: {'✅ OK' if success1 else '❌ FAIL'}")
    print(f"   MQTT Config: {'✅ OK' if success2 else '❌ FAIL'}")
    print(f"   MQTT Client Init: {'✅ OK' if success3 else '❌ FAIL'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 Tutti i test passati!")
        exit(0)
    else:
        print("\n❌ Alcuni test falliti")
        exit(1)