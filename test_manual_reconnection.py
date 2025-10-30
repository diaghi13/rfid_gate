#!/usr/bin/env python3
"""
🧪 Test MQTT Reconnection Manual
================================
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient


async def test_manual_reconnection():
    """Test manuale della riconnessione"""
    print("🧪 Test Riconnessione MQTT Manuale")
    print("=" * 40)
    
    # Carica config
    config = RFIDGateConfig.from_env()
    mqtt_client = AsyncMQTTClient(config.mqtt)
    
    try:
        # Inizializza e connetti
        print("🔌 Connessione iniziale...")
        await mqtt_client.initialize()
        connected = await mqtt_client.connect()
        
        if not connected:
            print("❌ Connessione iniziale fallita")
            return
        
        print("✅ Connessione iniziale OK!")
        
        # Aspetta un po'
        print("⏱️ Attendo 10 secondi...")
        await asyncio.sleep(10)
        
        # Forza disconnessione per simulare problemi di rete
        print("🔌 Forzo disconnessione...")
        if mqtt_client.client:
            mqtt_client.client.disconnect()
        
        # Aspetta che il callback venga chiamato
        await asyncio.sleep(2)
        
        print(f"📊 Stato dopo disconnessione: {mqtt_client.state.value}")
        print(f"📊 Connesso: {mqtt_client.is_connected()}")
        print(f"📊 Task riconnessione attivo: {mqtt_client._reconnect_task is not None}")
        
        # Ora testa riconnessione manuale
        print("\n🔄 Test riconnessione manuale...")
        for attempt in range(3):
            print(f"   Tentativo #{attempt + 1}")
            success = await mqtt_client.connect()
            
            if success:
                print(f"   ✅ Riconnesso!")
                break
            else:
                print(f"   ❌ Fallito")
                await asyncio.sleep(2)
        
        if mqtt_client.is_connected():
            print("✅ Riconnessione manuale riuscita!")
            
            # Testa heartbeat dopo riconnessione
            print("💓 Test heartbeat post-riconnessione...")
            await asyncio.sleep(35)  # Aspetta un ping
            
            if mqtt_client.last_ping_time > 0:
                print("✅ Heartbeat funziona dopo riconnessione")
            else:
                print("❌ Heartbeat non funziona dopo riconnessione")
        else:
            print("❌ Riconnessione manuale fallita")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mqtt_client.cleanup()


if __name__ == "__main__":
    asyncio.run(test_manual_reconnection())