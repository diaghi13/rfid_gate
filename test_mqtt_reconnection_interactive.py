#!/usr/bin/env python3
"""
🧪 Test MQTT Reconnection Interattivo
====================================

Test che richiede intervento manuale per verificare la riconnessione automatica.
"""

import asyncio
import time
import sys
from pathlib import Path

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient


async def test_interactive_reconnection():
    """Test interattivo della riconnessione"""
    print("🧪 Test MQTT Reconnection INTERATTIVO")
    print("=" * 50)
    
    # Carica config
    config = RFIDGateConfig.from_env()
    mqtt_client = AsyncMQTTClient(config.mqtt)
    
    try:
        # FASE 1: Connessione iniziale
        print("\n📝 FASE 1: Connessione Iniziale")
        print("-" * 30)
        
        await mqtt_client.initialize()
        connected = await mqtt_client.connect()
        
        if not connected:
            print("❌ Connessione iniziale fallita - Test terminato")
            return
        
        print("✅ Connessione iniziale OK!")
        print(f"   Broker: {config.mqtt.broker}:{config.mqtt.port}")
        print(f"   Stato: {mqtt_client.state.value}")
        print(f"   Heartbeat: ogni {mqtt_client.heartbeat_interval}s")
        
        # FASE 2: Verifica heartbeat funzionante
        print("\n📝 FASE 2: Verifica Heartbeat (60 secondi)")
        print("-" * 40)
        print("⏱️ Monitoring heartbeat... (aspetta 2 ping)")
        
        ping_count = 0
        start_time = time.time()
        last_ping = mqtt_client.last_ping_time
        
        while ping_count < 2 and (time.time() - start_time) < 80:
            await asyncio.sleep(5)
            
            # Check nuovo ping
            if mqtt_client.last_ping_time > last_ping:
                ping_count += 1
                ping_time = time.strftime("%H:%M:%S", time.localtime(mqtt_client.last_ping_time))
                print(f"💓 Ping #{ping_count}/2 alle {ping_time}")
                last_ping = mqtt_client.last_ping_time
            
            # Check connessione
            if not mqtt_client.is_connected():
                print("❌ Connessione persa durante heartbeat test")
                break
        
        if ping_count >= 2:
            print("✅ Heartbeat funziona correttamente!")
        else:
            print("⚠️ Heartbeat non completo, ma procediamo...")
        
        # FASE 3: Test disconnessione manuale
        print("\n📝 FASE 3: Test Disconnessione Manuale del Broker")
        print("-" * 50)
        print("")
        print("🚨 AZIONE RICHIESTA:")
        print("   1. Vai sul tuo server/computer dove gira il broker MQTT")
        print("   2. Ferma il servizio broker MQTT")
        print("   3. Torna qui e premi INVIO per continuare il monitoring")
        print("")
        input("👆 Premi INVIO quando hai FERMATO il broker MQTT...")
        
        # FASE 4: Monitoring disconnessione
        print("\n📝 FASE 4: Monitoring Disconnessione")
        print("-" * 35)
        print("⏱️ Monitoring per max 3 minuti... (aspetto che rilevi disconnessione)")
        
        disconnect_detected = False
        start_monitor = time.time()
        
        while (time.time() - start_monitor) < 180:  # 3 minuti max
            current_state = mqtt_client.state.value
            is_connected = mqtt_client.is_connected()
            missed_pings = mqtt_client.missed_pings
            reconnect_active = mqtt_client._reconnect_task is not None and not mqtt_client._reconnect_task.done()
            
            # Report status ogni 10 secondi
            elapsed = int(time.time() - start_monitor)
            if elapsed % 10 == 0:
                print(f"📊 t+{elapsed:3d}s | Stato: {current_state:12} | Ping mancati: {missed_pings}/3 | Reconnect: {'🔄' if reconnect_active else '❌'}")
            
            # Rileva disconnessione
            if not is_connected and not disconnect_detected:
                disconnect_detected = True
                disconnect_time = time.strftime("%H:%M:%S")
                print(f"🔌 DISCONNESSIONE RILEVATA alle {disconnect_time}!")
                print(f"   📊 Missed pings: {missed_pings}")
                print(f"   📊 Reconnect task attivo: {reconnect_active}")
                break
            
            await asyncio.sleep(1)
        
        if not disconnect_detected:
            print("⚠️ Disconnessione non rilevata in 3 minuti")
            print("   Forse il broker è ancora attivo?")
            return
        
        # FASE 5: Test riconnessione
        print("\n📝 FASE 5: Test Riconnessione Automatica")
        print("-" * 40)
        print("")
        print("🚨 AZIONE RICHIESTA:")
        print("   1. Riavvia il broker MQTT")
        print("   2. Torna qui e premi INVIO per monitorare la riconnessione")
        print("")
        input("👆 Premi INVIO quando hai RIAVVIATO il broker MQTT...")
        
        # FASE 6: Monitoring riconnessione
        print("\n📝 FASE 6: Monitoring Riconnessione")
        print("-" * 35)
        print("⏱️ Monitoring per max 5 minuti... (aspetto riconnessione automatica)")
        
        reconnect_detected = False
        start_reconnect = time.time()
        
        while (time.time() - start_reconnect) < 300:  # 5 minuti max
            current_state = mqtt_client.state.value
            is_connected = mqtt_client.is_connected()
            connection_attempts = mqtt_client.connection_attempts
            reconnect_active = mqtt_client._reconnect_task is not None and not mqtt_client._reconnect_task.done()
            
            # Report status ogni 5 secondi
            elapsed = int(time.time() - start_reconnect)
            if elapsed % 5 == 0:
                print(f"📊 t+{elapsed:3d}s | Stato: {current_state:12} | Connesso: {'✅' if is_connected else '❌'} | Tentativi: {connection_attempts} | Reconnect: {'🔄' if reconnect_active else '❌'}")
            
            # Rileva riconnessione
            if is_connected and not reconnect_detected:
                reconnect_detected = True
                reconnect_time = time.strftime("%H:%M:%S")
                print(f"🔌 RICONNESSIONE RIUSCITA alle {reconnect_time}!")
                break
            
            await asyncio.sleep(1)
        
        # FASE 7: Risultati finali
        print("\n📝 FASE 7: Risultati Finali")
        print("-" * 30)
        
        if reconnect_detected:
            print("🎉 TEST RICONNESSIONE: SUCCESSO!")
            print("   ✅ Disconnessione rilevata automaticamente")
            print("   ✅ Riconnessione automatica funzionante")
            
            # Test heartbeat post-riconnessione
            print("\n💓 Test heartbeat post-riconnessione...")
            await asyncio.sleep(35)  # Aspetta un ping
            
            if mqtt_client.last_ping_time > start_reconnect:
                print("✅ Heartbeat riavviato correttamente")
            else:
                print("⚠️ Heartbeat non riavviato")
        else:
            print("❌ TEST RICONNESSIONE: FALLITO!")
            print("   ❌ Riconnessione automatica non funziona")
        
        # Statistiche finali
        stats = mqtt_client.get_stats()
        print(f"\n📊 Statistiche finali:")
        print(f"   🔄 Riconnessioni: {stats.get('reconnections', 0)}")
        print(f"   📤 Messaggi inviati: {stats.get('messages_sent', 0)}")
        print(f"   📥 Messaggi ricevuti: {stats.get('messages_received', 0)}")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleanup...")
        await mqtt_client.cleanup()
        print("✅ Test terminato")


if __name__ == "__main__":
    print("🚀 Avvio test interattivo MQTT reconnection...")
    print("   Questo test richiede che TU fermi e riavvii manualmente il broker MQTT")
    print("   per verificare se la riconnessione automatica funziona davvero.")
    print("")
    
    try:
        asyncio.run(test_interactive_reconnection())
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto")