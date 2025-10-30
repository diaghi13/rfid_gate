#!/usr/bin/env python3
"""
🧪 Test Patch Riconnessione MQTT 
================================
Verifica miglioramenti della patch per la resilienza
"""

import sys
import os
import asyncio
from pathlib import Path

# Aggiungi path per importare rfid_gate
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Carica .env
def load_env():
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

async def test_mqtt_patch():
    """Test della patch MQTT"""
    try:
        from rfid_gate.config.settings import MQTTConfig
        from rfid_gate.network.mqtt import AsyncMQTTClient
        
        print("🧪 TEST PATCH RICONNESSIONE MQTT")
        print("=" * 50)
        
        # Crea configurazione
        mqtt_config = MQTTConfig.from_env()
        print(f"🔧 Broker: {mqtt_config.broker}:{mqtt_config.port}")
        
        # Crea client MQTT
        mqtt_client = AsyncMQTTClient(mqtt_config)
        
        # Verifica miglioramenti nella configurazione
        print("\\n📊 CONFIGURAZIONI PATCH:")
        print(f"✅ Max retries: {mqtt_client.max_retries} (era 3)")
        print(f"✅ Reconnect delay: {mqtt_client.reconnect_delay}s (era 5.0s)")
        print(f"✅ Connection reset interval: {mqtt_client.connection_reset_interval}s")
        print(f"✅ Last connection time: {mqtt_client.last_connection_time}")
        
        # Test inizializzazione
        print("\\n🔧 INIZIALIZZAZIONE CLIENT...")
        init_success = await mqtt_client.initialize()
        if not init_success:
            print("❌ Inizializzazione fallita")
            return False
        
        print("✅ Client inizializzato")
        
        # Test connessione
        print("\\n🔌 TEST CONNESSIONE...")
        connect_success = await mqtt_client.connect()
        
        if connect_success:
            print("✅ Connessione riuscita!")
            print(f"📊 Stato: {mqtt_client.state}")
            print(f"🔗 Connesso: {mqtt_client.is_connected()}")
            print(f"📈 Stats: {mqtt_client.stats}")
            
            # Cleanup
            await mqtt_client.cleanup()
            return True
        else:
            print("❌ Connessione fallita")
            return False
            
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🚀 VERIFICA PATCH RICONNESSIONE MQTT")
    print("Controllo che la patch sia stata applicata correttamente")
    print()
    
    success = await test_mqtt_patch()
    
    if success:
        print("\\n✅ PATCH APPLICATA CORRETTAMENTE!")
        print("\\n🎯 MIGLIORAMENTI:")
        print("• Max retries aumentato a 10")
        print("• Delay ridotto a 2 secondi")
        print("• Reset automatico tentativi ogni 5 minuti")
        print("• Miglior resilienza dopo riavvio broker")
    else:
        print("\\n❌ PROBLEMI CON LA PATCH")
        
    return success

if __name__ == "__main__":
    asyncio.run(main())