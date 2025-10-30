#!/usr/bin/env python3
"""
🧪 Test MQTT Heartbeat Semplice
===============================
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


async def test_heartbeat():
    """Test semplice del heartbeat"""
    print("🧪 Test Heartbeat MQTT Semplice")
    print("=" * 40)
    
    # Carica config
    config = RFIDGateConfig.from_env()
    mqtt_client = AsyncMQTTClient(config.mqtt)
    
    try:
        # Inizializza e connetti
        print("🔌 Connessione...")
        await mqtt_client.initialize()
        connected = await mqtt_client.connect()
        
        if not connected:
            print("❌ Connessione fallita")
            return
        
        print("✅ Connesso!")
        print(f"   Heartbeat interval: {mqtt_client.heartbeat_interval}s")
        print(f"   Max missed pings: {mqtt_client.max_missed_pings}")
        
        # Monitora per 2 minuti
        start_time = time.time()
        last_ping_time = 0
        
        print("\n💓 Monitoring heartbeat per 2 minuti...")
        print("   (dovrebbe vedere ping ogni 30 secondi)")
        
        while (time.time() - start_time) < 120:  # 2 minuti
            # Check stato
            if not mqtt_client.is_connected():
                print("❌ Connessione persa!")
                break
            
            # Check ping
            current_ping = mqtt_client.last_ping_time
            if current_ping > last_ping_time:
                ping_time = time.strftime("%H:%M:%S", time.localtime(current_ping))
                print(f"💓 Ping rilevato alle {ping_time} (missed: {mqtt_client.missed_pings})")
                last_ping_time = current_ping
            
            # Info periodica
            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0:  # Ogni 15 secondi
                print(f"📊 t+{elapsed}s | Stato: {mqtt_client.state.value} | Missed pings: {mqtt_client.missed_pings}")
            
            await asyncio.sleep(1)
        
        print("\n✅ Test completato")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        await mqtt_client.cleanup()


if __name__ == "__main__":
    asyncio.run(test_heartbeat())