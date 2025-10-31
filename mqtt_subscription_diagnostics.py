#!/usr/bin/env python3
"""
🔍 MQTT Subscription Diagnostics
===============================

Tool per diagnosticare problemi con le subscription MQTT dopo riconnessione.
"""

import asyncio
import time
import sys
import json
from pathlib import Path

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient


class MQTTSubscriptionDiagnostics:
    """Diagnostica subscription MQTT"""
    
    def __init__(self):
        self.config = RFIDGateConfig.from_env()
        self.mqtt_client = None
        self.received_messages = []
        
    async def run_diagnostics(self):
        """Esegue diagnostica completa"""
        print("🔍 MQTT Subscription Diagnostics")
        print("=" * 50)
        
        try:
            # Setup client
            self.mqtt_client = AsyncMQTTClient(self.config.mqtt)
            
            # Hook per catturare messaggi
            original_on_message = self.mqtt_client.on_message
            self.mqtt_client.on_message = self._message_interceptor
            
            # Test connessione e subscription
            await self._test_initial_connection()
            await self._test_subscription_topics()
            await self._test_message_reception()
            await self._test_forced_reconnection()
            
        except Exception as e:
            print(f"❌ Errore diagnostica: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.mqtt_client:
                await self.mqtt_client.cleanup()
    
    def _message_interceptor(self, topic: str, payload: dict):
        """Intercetta messaggi ricevuti"""
        timestamp = time.strftime("%H:%M:%S")
        self.received_messages.append({
            'timestamp': timestamp,
            'topic': topic,
            'payload': payload
        })
        print(f"📨 [{timestamp}] RICEVUTO: {topic}")
        print(f"    Payload: {json.dumps(payload, indent=2)}")
    
    async def _test_initial_connection(self):
        """Test connessione iniziale"""
        print("\n🔌 TEST: Connessione Iniziale")
        print("-" * 30)
        
        await self.mqtt_client.initialize()
        connected = await self.mqtt_client.connect()
        
        if connected:
            print("✅ Connessione riuscita")
            print(f"   Stato: {self.mqtt_client.state.value}")
        else:
            print("❌ Connessione fallita")
            return False
            
        return True
    
    async def _test_subscription_topics(self):
        """Test topic subscription"""
        print("\n📧 TEST: Topic Subscription")
        print("-" * 30)
        
        if not self.mqtt_client.is_connected():
            print("❌ Client non connesso")
            return
        
        # Verifica topic configurati
        print("📋 Topic configurati:")
        print(f"   Auth response: {self.config.mqtt.auth_response_topic}")
        print(f"   Card read: {self.config.mqtt.card_read_topic}")
        print(f"   Auth request: {self.config.mqtt.auth_request_topic}")
        
        # Verifica subscription attuali (dal client paho)
        if hasattr(self.mqtt_client.client, '_subscriptions'):
            subs = self.mqtt_client.client._subscriptions
            print(f"📡 Subscription attive nel client: {len(subs) if subs else 0}")
            if subs:
                for topic, qos in subs.items():
                    print(f"   - {topic} (QoS: {qos})")
        
        # Test manuale subscription
        print("\n🧪 Test subscription manuale...")
        test_topic = "gate/test/debug"
        
        result = self.mqtt_client.client.subscribe(test_topic)
        print(f"   Subscribe result: {result}")
        
        # Aspetta un po' per la subscription
        await asyncio.sleep(2)
    
    async def _test_message_reception(self):
        """Test ricezione messaggi"""
        print("\n📨 TEST: Ricezione Messaggi")
        print("-" * 30)
        
        if not self.mqtt_client.is_connected():
            print("❌ Client non connesso")
            return
        
        print("⏱️ Monitoring messaggi per 30 secondi...")
        print("   (invia qualche messaggio sui topic configurati)")
        
        initial_count = len(self.received_messages)
        start_time = time.time()
        
        while (time.time() - start_time) < 30:
            current_count = len(self.received_messages)
            if current_count > initial_count:
                new_messages = current_count - initial_count
                print(f"📈 {new_messages} nuovi messaggi ricevuti")
                break
            
            await asyncio.sleep(1)
        
        final_count = len(self.received_messages)
        print(f"📊 Totale messaggi ricevuti: {final_count}")
    
    async def _test_forced_reconnection(self):
        """Test riconnessione forzata"""
        print("\n🔄 TEST: Riconnessione e Re-subscription")
        print("-" * 40)
        
        if not self.mqtt_client.is_connected():
            print("❌ Client non connesso")
            return
        
        print("🔌 Forzo disconnessione...")
        
        # Cattura subscription prima della disconnessione
        pre_subs = None
        if hasattr(self.mqtt_client.client, '_subscriptions'):
            pre_subs = dict(self.mqtt_client.client._subscriptions or {})
        
        print(f"📡 Subscription pre-disconnessione: {len(pre_subs) if pre_subs else 0}")
        
        # Forza disconnessione
        self.mqtt_client.client.disconnect()
        
        # Aspetta disconnessione
        await asyncio.sleep(3)
        print(f"   Stato post-disconnect: {self.mqtt_client.state.value}")
        
        # Aspetta riconnessione automatica
        print("⏱️ Aspetto riconnessione automatica...")
        
        reconnect_timeout = 60  # 1 minuto
        start_wait = time.time()
        
        while (time.time() - start_wait) < reconnect_timeout:
            if self.mqtt_client.is_connected():
                print("✅ Riconnessione rilevata!")
                break
            await asyncio.sleep(1)
        
        if not self.mqtt_client.is_connected():
            print("❌ Riconnessione non avvenuta entro 60 secondi")
            return
        
        # Verifica subscription post-riconnessione
        await asyncio.sleep(2)  # Aspetta subscription
        
        post_subs = None
        if hasattr(self.mqtt_client.client, '_subscriptions'):
            post_subs = dict(self.mqtt_client.client._subscriptions or {})
        
        print(f"📡 Subscription post-riconnessione: {len(post_subs) if post_subs else 0}")
        
        # Confronta subscription
        if pre_subs and post_subs:
            if pre_subs == post_subs:
                print("✅ Subscription ripristinate correttamente")
            else:
                print("⚠️ Subscription cambiate:")
                print(f"   Pre:  {list(pre_subs.keys())}")
                print(f"   Post: {list(post_subs.keys())}")
        elif not post_subs:
            print("❌ PROBLEMA: Nessuna subscription dopo riconnessione!")
        
        # Test invio messaggio post-riconnessione
        print("\n📤 Test invio messaggio post-riconnessione...")
        test_payload = {"test": "post_reconnect", "timestamp": time.time()}
        
        success = await self.mqtt_client._send_message({
            "topic": "gate/test/post_reconnect",
            "payload": test_payload,
            "qos": 1
        })
        
        print(f"   Invio riuscito: {'✅' if success else '❌'}")
    
    def print_summary(self):
        """Stampa riassunto"""
        print("\n" + "=" * 50)
        print("📋 RIASSUNTO DIAGNOSTICA")
        print("=" * 50)
        
        print(f"📨 Messaggi ricevuti totali: {len(self.received_messages)}")
        
        if self.received_messages:
            print("\n📋 Dettaglio messaggi:")
            for i, msg in enumerate(self.received_messages[-5:], 1):  # Ultimi 5
                print(f"   {i}. [{msg['timestamp']}] {msg['topic']}")


async def main():
    """Main diagnostics"""
    diagnostics = MQTTSubscriptionDiagnostics()
    
    try:
        await diagnostics.run_diagnostics()
    finally:
        diagnostics.print_summary()


if __name__ == "__main__":
    print("🚀 Avvio diagnostica MQTT subscription...")
    print("   Questo tool verificherà se le subscription vengono mantenute dopo riconnessione")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Diagnostica interrotta")