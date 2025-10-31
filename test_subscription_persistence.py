#!/usr/bin/env python3
"""
🧪 Test Specifico: Persistenza Subscription MQTT
Verifica che le richieste badge arrivino dopo riconnessione broker
"""
import asyncio
import os
import sys
import json
import time
from datetime import datetime

# Aggiungi il percorso del progetto
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient

class SubscriptionPersistenceTest:
    def __init__(self):
        config = RFIDGateConfig.from_env()
        self.config = config.mqtt
        self.mqtt_client = None
        self.received_messages = []
        self.auth_responses = []
        self.test_start_time = None
        
    async def setup(self):
        """Setup test environment"""
        print("🚀 Setup Test Subscription Persistence")
        print("=" * 60)
        
        # Inizializza client MQTT
        self.mqtt_client = AsyncMQTTClient(self.config)
        
        # Registra callback per messaggi ricevuti
        def on_auth_response(topic, payload):
            timestamp = time.time()
            message = {
                'topic': topic,
                'payload': payload,
                'timestamp': timestamp,
                'time_str': datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            }
            self.auth_responses.append(message)
            print(f"📨 AUTH RESPONSE: {topic} -> {payload}")
        
        def on_message_received(topic, payload):
            timestamp = time.time()
            message = {
                'topic': topic,
                'payload': payload,
                'timestamp': timestamp,
                'time_str': datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            }
            self.received_messages.append(message)
            print(f"📨 MESSAGGIO: {topic} -> {payload}")
        
        # Registra callbacks
        self.mqtt_client.on_auth_response = on_auth_response
        self.mqtt_client.on_message = on_message_received
        
        # Inizializza client
        init_success = await self.mqtt_client.initialize()
        if not init_success:
            raise Exception("❌ Inizializzazione client MQTT fallita")
        
        # Connetti
        success = await self.mqtt_client.connect()
        if not success:
            raise Exception("❌ Impossibile connettersi al broker MQTT")
        
        print("✅ Setup completato - MQTT connesso")
        return True
    
    async def test_subscription_persistence(self):
        """Test principale: verifica persistenza subscription"""
        print("\n🔍 TEST: Persistenza Subscription dopo Riconnessione")
        print("-" * 50)
        
        self.test_start_time = time.time()
        
        # FASE 1: Invio richiesta simulata PRIMA della disconnessione
        print("\n📤 FASE 1: Invio richiesta badge (connessione stabile)")
        await self.send_test_badge_request("02D9BAEB", "test_pre_reconnect")
        await asyncio.sleep(2)
        
        # FASE 2: Aspetta disconnessione broker (manuale)
        print("\n⚠️ FASE 2: ISTRUZIONI MANUALI")
        print("   1. 🛑 FERMA il broker MQTT ora")
        print("   2. ⏱️ Aspetta 10 secondi")
        print("   3. 🔄 RIAVVIA il broker")
        print("   4. ⏱️ Aspetta che appaia 'RICONNESSIONE COMPLETATA'")
        
        # Monitora stato per 180 secondi
        disconnection_detected = False
        reconnection_detected = False
        
        for i in range(180):  # 3 minuti max
            await asyncio.sleep(1)
            
            if not self.mqtt_client.is_connected() and not disconnection_detected:
                print("🔌 DISCONNESSIONE RILEVATA!")
                disconnection_detected = True
            
            if disconnection_detected and self.mqtt_client.is_connected() and not reconnection_detected:
                print("✅ RICONNESSIONE COMPLETATA!")
                reconnection_detected = True
                break
                
            if i % 10 == 0:
                status = "🟢 connesso" if self.mqtt_client.is_connected() else "🔴 disconnesso"
                print(f"📊 Stato: {status} (t={i}s)")
        
        if not reconnection_detected:
            print("⚠️ Riconnessione non rilevata entro 3 minuti")
            return False
        
        # FASE 3: Verifica subscription dopo riconnessione
        print("\n📤 FASE 3: Invio richiesta badge (post-riconnessione)")
        await asyncio.sleep(3)  # Aspetta stabilizzazione
        await self.send_test_badge_request("02D9BAEB", "test_post_reconnect")
        
        # FASE 4: Aspetta risposta
        print("\n⏱️ FASE 4: Attesa risposta (20 secondi)...")
        for i in range(20):
            await asyncio.sleep(1)
            if len(self.auth_responses) > 0:
                break
        
        return True
    
    async def send_test_badge_request(self, uid, test_id):
        """Invia richiesta badge di test"""
        if not self.mqtt_client.is_connected():
            print("❌ Non connesso - impossibile inviare richiesta")
            return False
        
        # Usa il tornello_id dalla configurazione
        import os
        from rfid_gate.network.mqtt import AuthRequest
        tornello_id = os.getenv('TORNELLO_ID', 'tornello_01')
        
        # Crea AuthRequest
        auth_request = AuthRequest(
            card_uid=uid,
            identificativo_tornello=tornello_id,
            direzione="in",  # in minuscolo come richiesto dal server
            timestamp=datetime.now().isoformat(),
            auth_required=True,
            fallback_mode=False
        )
        
        print(f"📡 Invio richiesta auth: {uid}")
        print(f"   Test ID: {test_id}")
        print(f"   Tornello: {tornello_id}")
        print(f"   Timestamp: {auth_request.timestamp}")
        
        # Usa send_auth_request_parallel per non-bloccante
        success = await self.mqtt_client.send_auth_request_parallel(auth_request)
        if success:
            print("✅ Richiesta inviata")
        else:
            print("❌ Errore invio richiesta")
        
        return success
    
    def analyze_results(self):
        """Analizza risultati del test"""
        print("\n" + "=" * 60)
        print("📊 ANALISI RISULTATI")
        print("=" * 60)
        
        # Statistiche messaggi ricevuti
        print(f"📨 Messaggi totali ricevuti: {len(self.received_messages)}")
        print(f"🔐 Risposte auth ricevute: {len(self.auth_responses)}")
        
        # Lista tutti i messaggi ricevuti
        if self.received_messages:
            print("\n📋 MESSAGGI RICEVUTI:")
            for i, msg in enumerate(self.received_messages, 1):
                print(f"   {i}. [{msg['time_str']}] {msg['topic']}")
                print(f"      {msg['payload']}")
        
        # Verifica subscription persistence
        if len(self.auth_responses) > 0:
            print("\n✅ SUBSCRIPTION PERSISTENCE: FUNZIONA")
            print("   Le richieste badge arrivano dopo riconnessione!")
            
            for response in self.auth_responses:
                print(f"   📨 [{response['time_str']}] {response['topic']}")
                print(f"      {response['payload']}")
        else:
            print("\n❌ SUBSCRIPTION PERSISTENCE: PROBLEMA")
            print("   Le richieste badge NON arrivano dopo riconnessione!")
        
        # Test result
        success = len(self.auth_responses) > 0
        print(f"\n🎯 RISULTATO TEST: {'✅ PASS' if success else '❌ FAIL'}")
        
        return success
    
    async def cleanup(self):
        """Cleanup test"""
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
        print("🧹 Cleanup completato")

async def main():
    """Main test function"""
    print("🧪 Test Persistenza Subscription MQTT")
    print(f"   Broker: {os.getenv('MQTT_BROKER', 'N/A')}")
    print(f"   Gate ID: {os.getenv('GATE_ID', 'N/A')}")
    
    test = SubscriptionPersistenceTest()
    
    try:
        # Setup
        await test.setup()
        
        # Esegui test principale
        await test.test_subscription_persistence()
        
        # Analizza risultati
        success = test.analyze_results()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False
    finally:
        await test.cleanup()

if __name__ == "__main__":
    # Carica configurazione ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")
        sys.exit(130)