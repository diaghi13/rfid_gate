#!/usr/bin/env python3
"""
🔧 Test MQTT Reconnection Real Scenario
======================================

Test per verificare riconnessione MQTT in scenario reale:
- Simula disconnessione di 10-15 secondi
- Monitora il comportamento di riconnessione
- Verifica subscription recovery

Usage:
    python test_real_mqtt_scenario.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Aggiungi il path del modulo
sys.path.append(str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient, AuthRequest


class RealScenarioTester:
    """Tester per scenario reale disconnessione broker"""
    
    def __init__(self):
        self.client = None
        self.config = None
        self.connection_events = []
        self.message_events = []
        
    async def setup(self):
        """Setup test environment"""
        try:
            print("🔧 Setup test environment...")
            
            # Carica configurazione REALE
            self.config = RFIDGateConfig.load_from_env()
            print(f"📋 Config caricata: broker={self.config.mqtt.broker}:{self.config.mqtt.port}")
            
            # Crea client MQTT con configurazione reale
            self.client = AsyncMQTTClient(self.config.mqtt)
            
            # Setup callbacks per monitoraggio
            self.client.on_connected = self._on_connected
            self.client.on_disconnected = self._on_disconnected  
            self.client.on_message = self._on_message
            
            # Inizializza client
            success = await self.client.initialize()
            if not success:
                raise Exception("Inizializzazione client fallita")
            
            print("✅ Setup completato")
            return True
            
        except Exception as e:
            print(f"❌ Errore setup: {e}")
            return False
    
    def _on_connected(self):
        """Callback connessione"""
        timestamp = time.time()
        event = {
            'type': 'connected',
            'timestamp': timestamp,
            'formatted_time': time.strftime('%H:%M:%S', time.localtime(timestamp))
        }
        self.connection_events.append(event)
        print(f"🔗 [{event['formatted_time']}] CONNESSO!")
        
    def _on_disconnected(self):
        """Callback disconnessione"""
        timestamp = time.time()
        event = {
            'type': 'disconnected', 
            'timestamp': timestamp,
            'formatted_time': time.strftime('%H:%M:%S', time.localtime(timestamp))
        }
        self.connection_events.append(event)
        print(f"🔌 [{event['formatted_time']}] DISCONNESSO!")
        
    def _on_message(self, topic: str, payload: dict):
        """Callback messaggio ricevuto"""
        timestamp = time.time()
        event = {
            'topic': topic,
            'payload': payload,
            'timestamp': timestamp,
            'formatted_time': time.strftime('%H:%M:%S', time.localtime(timestamp))
        }
        self.message_events.append(event)
        print(f"📨 [{event['formatted_time']}] Messaggio su {topic}")
    
    async def test_initial_connection(self):
        """Test connessione iniziale"""
        print("\n🧪 TEST: Connessione iniziale")
        print("-" * 40)
        
        start_time = time.time()
        success = await self.client.connect()
        
        if success:
            connection_time = time.time() - start_time
            print(f"✅ Connessione riuscita in {connection_time:.2f}s")
            
            # Attendi un po' per stabilizzare
            await asyncio.sleep(3)
            
            # Verifica stato
            print(f"📊 Stato client: {self.client.get_stats()}")
            return True
        else:
            print("❌ Connessione fallita")
            return False
    
    async def test_message_sending(self):
        """Test invio messaggi"""
        print("\n🧪 TEST: Invio messaggi pre-disconnessione")
        print("-" * 40)
        
        # Invia alcuni messaggi di test
        for i in range(3):
            auth_req = AuthRequest(
                card_uid=f"TEST_CARD_{i:03d}",
                identificativo_tornello=self.config.system.tornello_id,
                direzione="in",
                timestamp=time.time(),
                auth_required=True
            )
            
            success = await self.client.send_auth_request_parallel(auth_req)
            print(f"📤 Messaggio {i+1}: {'✅' if success else '❌'}")
            await asyncio.sleep(1)
        
        return True
    
    async def simulate_broker_outage(self, duration_seconds=12):
        """Simula outage broker con istruzioni manuali"""
        print(f"\n🧪 TEST: Simulazione outage broker ({duration_seconds}s)")
        print("=" * 50)
        
        print(f"🔥 AZIONE RICHIESTA:")
        print(f"   1. Ferma il broker MQTT ORA")
        print(f"   2. Attendi {duration_seconds} secondi")  
        print(f"   3. Riavvia il broker")
        print(f"")
        print(f"⏰ Monitoraggio automatico in corso...")
        print("-" * 50)
        
        # Monitora per tutta la durata + tempo recovery
        total_monitor_time = duration_seconds + 60  # +60s per recovery
        start_monitor = time.time()
        
        last_status_check = 0
        
        while (time.time() - start_monitor) < total_monitor_time:
            current_time = time.time()
            elapsed = current_time - start_monitor
            
            # Status check ogni 5 secondi
            if current_time - last_status_check >= 5:
                state = self.client.state.value if self.client.state else "unknown"
                stats = self.client.get_stats()
                attempts = stats.get('connection_attempts', 0)
                
                print(f"⏱️  {elapsed:5.1f}s - Stato: {state:12} - Tentativi: {attempts:2d}")
                last_status_check = current_time
            
            await asyncio.sleep(1)
        
        print("-" * 50)
        print("✅ Monitoraggio completato")
    
    async def test_post_recovery(self):
        """Test funzionalità post-recovery"""
        print("\n🧪 TEST: Funzionalità post-recovery")
        print("-" * 40)
        
        # Attendi un po' per assicurarsi che sia tutto stabile
        await asyncio.sleep(5)
        
        # Verifica stato finale
        if self.client.is_connected():
            print("✅ Client connesso")
        else:
            print("❌ Client non connesso")
            return False
        
        # Test invio messaggi post-recovery
        for i in range(3):
            auth_req = AuthRequest(
                card_uid=f"POST_RECOVERY_{i:03d}",
                identificativo_tornello=self.config.system.tornello_id,
                direzione="out",
                timestamp=time.time(),
                auth_required=True
            )
            
            success = await self.client.send_auth_request_parallel(auth_req)
            print(f"📤 Post-recovery msg {i+1}: {'✅' if success else '❌'}")
            await asyncio.sleep(1)
        
        return True
    
    def analyze_results(self):
        """Analizza risultati del test"""
        print("\n📊 ANALISI RISULTATI")
        print("=" * 50)
        
        # Analizza eventi connessione
        if self.connection_events:
            print("🔗 Timeline connessioni:")
            for event in self.connection_events:
                print(f"   {event['formatted_time']} - {event['type'].upper()}")
            
            # Calcola tempi di recovery
            disconnections = [e for e in self.connection_events if e['type'] == 'disconnected']
            reconnections = [e for e in self.connection_events if e['type'] == 'connected']
            
            if len(disconnections) > 0 and len(reconnections) > 1:
                # Trova ultima disconnessione e prima riconnessione dopo
                last_disconnect = disconnections[-1]['timestamp']
                recovery_reconnection = None
                
                for reconnect in reconnections:
                    if reconnect['timestamp'] > last_disconnect:
                        recovery_reconnection = reconnect
                        break
                
                if recovery_reconnection:
                    recovery_time = recovery_reconnection['timestamp'] - last_disconnect
                    print(f"⚡ Tempo recovery: {recovery_time:.1f} secondi")
                else:
                    print("❌ Recovery non completato durante il test")
        
        # Statistiche finali
        final_stats = self.client.get_stats()
        print(f"\n📈 Statistiche finali:")
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        
        # Messaggi ricevuti
        if self.message_events:
            print(f"\n📨 Messaggi ricevuti: {len(self.message_events)}")
            for msg in self.message_events[-3:]:  # Ultimi 3
                print(f"   {msg['formatted_time']} - {msg['topic']}")
    
    async def cleanup(self):
        """Cleanup test environment"""
        try:
            if self.client:
                await self.client.cleanup()
            print("🧹 Cleanup completato")
        except Exception as e:
            print(f"❌ Errore cleanup: {e}")


async def main():
    """Main test function"""
    print("🔧 TEST SCENARIO REALE MQTT RECONNECTION")
    print("=" * 60)
    
    tester = RealScenarioTester()
    
    try:
        # Setup
        success = await tester.setup()
        if not success:
            return 1
        
        # Test 1: Connessione iniziale
        await tester.test_initial_connection()
        
        # Test 2: Funzionalità pre-outage
        await tester.test_message_sending()
        
        # Test 3: Simulazione outage broker (MANUALE)
        await tester.simulate_broker_outage(duration_seconds=12)
        
        # Test 4: Verifica post-recovery
        await tester.test_post_recovery()
        
        # Analisi finale
        tester.analyze_results()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")
        return 0
    except Exception as e:
        print(f"❌ Errore inaspettato: {e}")
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)