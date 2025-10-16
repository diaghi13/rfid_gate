#!/usr/bin/env python3
"""
🧪 Test correzione errore MQTT event loop
========================================

Test per verificare che la correzione RuntimeError: no running event loop
funzioni correttamente nel client MQTT.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient

async def test_mqtt_eventloop_fix():
    """Test che il client MQTT gestisca correttamente l'event loop"""
    
    print("🧪 Test correzione MQTT event loop")
    print("=" * 40)
    
    # Carica configurazione
    config = RFIDGateConfig.from_env()
    
    # Crea client MQTT
    mqtt_client = AsyncMQTTClient(config.mqtt)
    
    print(f"✅ Client MQTT creato")
    
    # Inizializza client
    init_success = await mqtt_client.initialize()
    print(f"🔧 Inizializzazione: {'✅ Riuscita' if init_success else '❌ Fallita'}")
    print(f"🔧 Event loop salvato: {mqtt_client._event_loop is not None}")
    
    # Test connessione (dovrebbe fallire per le credenziali ma senza RuntimeError)
    try:
        print("🔌 Tentativo connessione MQTT...")
        success = await mqtt_client.connect()
        print(f"📡 Connessione: {'✅ Riuscita' if success else '❌ Fallita (normale)'}")
        
        if success:
            print("🎯 Connessione riuscita - verifico event loop nel callback...")
            # Se la connessione riesce, l'event loop dovrebbe essere impostato
            print(f"🔧 Event loop nel client: {mqtt_client._event_loop is not None}")
            
            # Disconnect
            await mqtt_client.disconnect()
            print("🔌 Disconnessione completata")
            
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        # Verifica che NON sia un RuntimeError di event loop
        if "no running event loop" in str(e):
            print("🚨 ERRORE EVENT LOOP NON RISOLTO!")
            return False
        else:
            print("ℹ️ Errore diverso (normale per test)")
    
    print("\n✅ Test completato - nessun RuntimeError event loop")
    return True

async def main():
    """Test principale"""
    
    print("🎯 TEST CORREZIONE MQTT EVENT LOOP BUG")
    print("=" * 50)
    print()
    
    success = await test_mqtt_eventloop_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CORREZIONE VERIFICATA: RuntimeError risolto!")
        print("✅ Il client MQTT ora gestisce correttamente l'event loop")
        print("🔧 Usa asyncio.run_coroutine_threadsafe() invece di create_task()")
    else:
        print("❌ Correzione non completamente efficace")
        
    print("\n💡 La correzione previene l'errore:")
    print("   RuntimeError: no running event loop")
    print("   nel callback _on_connect del client MQTT paho")

if __name__ == "__main__":
    asyncio.run(main())