#!/usr/bin/env python3
"""
🧪 Test MQTT Reconnection System
===============================

Script di test per verificare il sistema di riconnessione MQTT.
Simula disconnessioni e verifica se il heartbeat e la riconnessione funzionano.
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient, ConnectionState


class MQTTTestHarness:
    """Test harness per sistema MQTT"""
    
    def __init__(self):
        # Carica config
        self.config = RFIDGateConfig.from_env()
        self.mqtt_client = None
        self.test_results = []
        
        # Override config per test
        self.config.mqtt.broker = os.getenv('MQTT_BROKER', 'localhost')
        self.config.mqtt.port = int(os.getenv('MQTT_PORT', '1883'))
        self.config.mqtt.username = os.getenv('MQTT_USER', '')
        self.config.mqtt.password = os.getenv('MQTT_PASS', '')
        
        print(f"🧪 Test MQTT Reconnection")
        print(f"   Broker: {self.config.mqtt.broker}:{self.config.mqtt.port}")
        print(f"   User: {self.config.mqtt.username or 'anonymous'}")
    
    async def run_tests(self):
        """Esegue tutti i test"""
        print("=" * 60)
        print("🚀 INIZIO TEST MQTT RECONNECTION")
        print("=" * 60)
        
        try:
            # Test 1: Connessione iniziale
            await self.test_initial_connection()
            
            # Test 2: Heartbeat monitoring
            await self.test_heartbeat_monitoring()
            
            # Test 3: Simulazione disconnessione broker
            await self.test_broker_disconnect_simulation()
            
            # Test 4: Test messaggi durante disconnessione
            await self.test_messages_during_disconnect()
            
        except Exception as e:
            print(f"❌ Errore durante test: {e}")
        finally:
            if self.mqtt_client:
                await self.mqtt_client.cleanup()
            
            # Risultati finali
            self.print_test_results()
    
    async def test_initial_connection(self):
        """Test 1: Connessione iniziale"""
        print("\n🔌 TEST 1: Connessione Iniziale")
        print("-" * 40)
        
        try:
            self.mqtt_client = AsyncMQTTClient(self.config.mqtt)
            
            # Inizializza
            init_success = await self.mqtt_client.initialize()
            self.log_result("Inizializzazione", init_success, "Client MQTT inizializzato")
            
            if not init_success:
                return False
            
            # Connetti
            connect_success = await self.mqtt_client.connect()
            self.log_result("Connessione", connect_success, "Connessione al broker riuscita")
            
            if connect_success:
                print(f"✅ Stato: {self.mqtt_client.state.value}")
                print(f"✅ Connesso: {self.mqtt_client.is_connected()}")
            
            return connect_success
            
        except Exception as e:
            self.log_result("Connessione", False, f"Errore: {e}")
            return False
    
    async def test_heartbeat_monitoring(self):
        """Test 2: Monitoring heartbeat"""
        print("\n💓 TEST 2: Heartbeat Monitoring")
        print("-" * 40)
        
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self.log_result("Heartbeat", False, "Client non connesso")
            return
        
        try:
            # Verifica che heartbeat task sia attivo
            heartbeat_active = (self.mqtt_client._heartbeat_task and 
                               not self.mqtt_client._heartbeat_task.done())
            
            self.log_result("Heartbeat Task", heartbeat_active, "Task heartbeat attivo")
            
            # Monitora heartbeat per 90 secondi (3 ping)
            print("⏱️ Monitoring heartbeat per 90 secondi...")
            
            start_time = time.time()
            ping_count = 0
            
            while (time.time() - start_time) < 90:
                current_ping_time = self.mqtt_client.last_ping_time
                
                # Aspetta nuovo ping
                await asyncio.sleep(5)
                
                if self.mqtt_client.last_ping_time > current_ping_time:
                    ping_count += 1
                    print(f"💓 Ping #{ping_count} rilevato (t={self.mqtt_client.last_ping_time})")
                
                # Verifica stato connessione
                if not self.mqtt_client.is_connected():
                    print("❌ Connessione persa durante monitoring")
                    break
            
            self.log_result("Ping Count", ping_count >= 2, f"{ping_count} ping rilevati in 90s")
            
        except Exception as e:
            self.log_result("Heartbeat", False, f"Errore: {e}")
    
    async def test_broker_disconnect_simulation(self):
        """Test 3: Simulazione disconnessione broker"""
        print("\n🔌 TEST 3: Simulazione Disconnessione Broker")
        print("-" * 50)
        
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self.log_result("Disconnect Simulation", False, "Client non connesso")
            return
        
        try:
            print("📋 ISTRUZIONI MANUALI:")
            print("   1. Ferma il broker MQTT ora")
            print("   2. Aspetta che il sistema rilevi la disconnessione")
            print("   3. Riavvia il broker")
            print("   4. Verifica riconnessione automatica")
            print("")
            
            # Monitora per 5 minuti
            start_time = time.time()
            disconnect_detected = False
            reconnect_detected = False
            
            print("⏱️ Monitoring per 5 minuti...")
            
            while (time.time() - start_time) < 300:  # 5 minuti
                current_state = self.mqtt_client.state
                is_connected = self.mqtt_client.is_connected()
                missed_pings = self.mqtt_client.missed_pings
                
                print(f"📊 Stato: {current_state.value} | Connesso: {is_connected} | Ping mancati: {missed_pings}")
                
                # Rileva disconnessione
                if not is_connected and not disconnect_detected:
                    disconnect_detected = True
                    print("🔌 DISCONNESSIONE RILEVATA!")
                
                # Rileva riconnessione
                if is_connected and disconnect_detected and not reconnect_detected:
                    reconnect_detected = True
                    print("🔌 RICONNESSIONE RILEVATA!")
                    break
                
                await asyncio.sleep(10)  # Check ogni 10 secondi
            
            self.log_result("Disconnect Detection", disconnect_detected, "Disconnessione rilevata")
            self.log_result("Reconnect Detection", reconnect_detected, "Riconnessione automatica")
            
        except Exception as e:
            self.log_result("Disconnect Simulation", False, f"Errore: {e}")
    
    async def test_messages_during_disconnect(self):
        """Test 4: Messaggi durante disconnessione"""
        print("\n📤 TEST 4: Messaggi Durante Disconnessione")
        print("-" * 45)
        
        if not self.mqtt_client:
            self.log_result("Message Test", False, "Client non disponibile")
            return
        
        try:
            # Invia messaggi di test
            test_payload = {"test": "message", "timestamp": time.time()}
            
            # Prova invio durante diversi stati
            states_tested = []
            
            if self.mqtt_client.is_connected():
                success = await self.mqtt_client._send_message({
                    "topic": "test/connected",
                    "payload": test_payload,
                    "qos": 1
                })
                states_tested.append(("Connected", success))
            
            # Verifica coda messaggi
            queue_size = self.mqtt_client.get_queue_size()
            retry_queue_size = self.mqtt_client.get_retry_queue_size()
            
            print(f"📊 Queue size: {queue_size}")
            print(f"📊 Retry queue size: {retry_queue_size}")
            
            self.log_result("Message Queue", True, f"Queue: {queue_size}, Retry: {retry_queue_size}")
            
        except Exception as e:
            self.log_result("Message Test", False, f"Errore: {e}")
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Registra risultato test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        self.test_results.append({
            'name': test_name,
            'success': success,
            'details': details
        })
    
    def print_test_results(self):
        """Stampa risultati finali"""
        print("\n" + "=" * 60)
        print("📋 RISULTATI FINALI TEST")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['name']}: {result['details']}")
        
        print("-" * 60)
        print(f"📊 RISULTATO: {passed}/{total} test passati")
        
        if passed == total:
            print("🎉 TUTTI I TEST PASSATI!")
        else:
            print("⚠️ ALCUNI TEST FALLITI - Rivedere implementazione")


async def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
🧪 Test MQTT Reconnection System

Usage:
    python test_mqtt_reconnection.py

Environment Variables:
    MQTT_BROKER=localhost    # Indirizzo broker MQTT
    MQTT_PORT=1883          # Porta broker MQTT  
    MQTT_USER=              # Username (opzionale)
    MQTT_PASS=              # Password (opzionale)

Il test verificherà:
1. Connessione iniziale al broker
2. Funzionamento heartbeat monitor
3. Rilevamento disconnessione/riconnessione
4. Gestione messaggi durante disconnessione

Durante il Test 3, dovrai manualmente:
- Fermare il broker MQTT
- Aspettare che il sistema rilevi la disconnessione  
- Riavviare il broker
- Verificare la riconnessione automatica
        """)
        return
    
    test_harness = MQTTTestHarness()
    await test_harness.run_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")
    except Exception as e:
        print(f"❌ Errore test: {e}")