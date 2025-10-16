#!/usr/bin/env python3
"""
🧪 TEST REALE MQTT - Invio Effettivo
===================================

Test che invia REALMENTE i payload MQTT:
- Connessione al broker MQTT reale (mqbrk.ddns.net:8883)
- Invio payload su gate/tornello_01/badge
- Ascolto risposte su gate/tornello_01/response
- Payload visibili su MQTT Explorer

Questo test invia DAVVERO i messaggi MQTT!
"""

import sys
import os
import asyncio
import time
import json
import ssl
from datetime import datetime
from dotenv import load_dotenv

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ Installo paho-mqtt...")
    os.system("pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org paho-mqtt")
    import paho.mqtt.client as mqtt

# Carica configurazione
load_dotenv()

class RealMQTTTester:
    """Tester che invia realmente i messaggi MQTT"""
    
    def __init__(self):
        # Configurazione MQTT dal .env
        self.mqtt_host = os.getenv('MQTT_HOST', 'mqbrk.ddns.net')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '8883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME')
        self.mqtt_password = os.getenv('MQTT_PASSWORD')
        self.mqtt_use_tls = os.getenv('MQTT_USE_TLS', 'true').lower() == 'true'
        
        # Topics
        self.badge_topic = os.getenv('MQTT_CARD_READ_TOPIC', 'gate/tornello_01/badge')
        self.response_topic = os.getenv('MQTT_AUTH_RESPONSE_TOPIC', 'gate/tornello_01/response')
        self.manual_open_topic = os.getenv('MQTT_MANUAL_OPEN_TOPIC', 'gate/tornello_01/manual_open')
        
        # Tornello ID
        self.tornello_id = os.getenv('SYNC_GATE_ID', 'tornello_01')
        
        # Client MQTT
        self.mqtt_client = None
        self.connected = False
        self.messages_received = []
        
        print("🔧 CONFIGURAZIONE MQTT REALE")
        print("=" * 40)
        print(f"🌐 Broker: {self.mqtt_host}:{self.mqtt_port}")
        print(f"🔐 TLS: {'✅ Sì' if self.mqtt_use_tls else '❌ No'}")
        print(f"👤 Username: {self.mqtt_username}")
        print(f"🏷️ Tornello: {self.tornello_id}")
        print()
        print(f"📡 TOPICS:")
        print(f"   📤 Badge: {self.badge_topic}")
        print(f"   📥 Response: {self.response_topic}")
        print(f"   🚪 Manual Open: {self.manual_open_topic}")
        print()
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback connessione MQTT"""
        if rc == 0:
            print("✅ Connesso al broker MQTT!")
            self.connected = True
            
            # Sottoscrivi ai topic di risposta
            print(f"🔔 Sottoscrizione a: {self.response_topic}")
            client.subscribe(self.response_topic)
            
            print(f"🔔 Sottoscrizione a: {self.manual_open_topic}")
            client.subscribe(self.manual_open_topic)
            
        else:
            print(f"❌ Connessione fallita: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback disconnessione"""
        print(f"🔌 Disconnesso dal broker MQTT (rc: {rc})")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback ricezione messaggi"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        timestamp = datetime.now().isoformat()
        
        print(f"\n📩 MESSAGGIO RICEVUTO:")
        print(f"   Topic: {topic}")
        print(f"   Payload: {payload}")
        print(f"   Timestamp: {timestamp}")
        
        # Salva messaggio
        self.messages_received.append({
            'topic': topic,
            'payload': payload,
            'timestamp': timestamp
        })
        
        try:
            payload_json = json.loads(payload)
            print(f"   JSON: {json.dumps(payload_json, indent=2)}")
        except:
            print(f"   (Non JSON)")
        
        print()
    
    async def connect_mqtt(self):
        """Connetti al broker MQTT"""
        
        print("🔌 CONNESSIONE AL BROKER MQTT")
        print("-" * 35)
        
        try:
            # Crea client
            self.mqtt_client = mqtt.Client()
            
            # Callback
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.on_message = self.on_message
            
            # Credenziali
            if self.mqtt_username and self.mqtt_password:
                self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
                print(f"🔑 Credenziali impostate")
            
            # TLS
            if self.mqtt_use_tls:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.mqtt_client.tls_set_context(context)
                print(f"🔒 TLS abilitato (senza verifica certificato)")
            
            # Connetti
            print(f"⏳ Connessione a {self.mqtt_host}:{self.mqtt_port}...")
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # Avvia loop in background
            self.mqtt_client.loop_start()
            
            # Aspetta connessione
            for i in range(10):
                if self.connected:
                    break
                await asyncio.sleep(0.5)
            
            if not self.connected:
                print("❌ Timeout connessione MQTT")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Errore connessione MQTT: {e}")
            return False
    
    async def send_card_badge(self, card_uid, direction="in"):
        """Invia payload badge card (REALE)"""
        
        if not self.connected:
            print("❌ MQTT non connesso")
            return False
        
        timestamp = datetime.now().isoformat()
        
        payload = {
            "card_uid": card_uid,
            "identificativo_tornello": self.tornello_id,
            "direzione": direction,
            "timestamp": timestamp,
            "auth_required": True
        }
        
        payload_json = json.dumps(payload)
        
        print(f"📤 INVIO REALE MQTT:")
        print(f"   Topic: {self.badge_topic}")
        print(f"   Payload: {payload_json}")
        
        try:
            result = self.mqtt_client.publish(self.badge_topic, payload_json, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Messaggio inviato con successo!")
                return True
            else:
                print(f"❌ Errore invio: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Errore invio MQTT: {e}")
            return False
    
    async def send_manual_open(self, direction="in"):
        """Invia comando manual open (REALE)"""
        
        if not self.connected:
            print("❌ MQTT non connesso")
            return False
        
        timestamp = datetime.now().isoformat()
        
        payload = {
            "identificativo_tornello": self.tornello_id,
            "direzione": direction,
            "timestamp": timestamp
        }
        
        payload_json = json.dumps(payload)
        
        print(f"🚪 INVIO MANUAL OPEN REALE:")
        print(f"   Topic: {self.manual_open_topic}")
        print(f"   Payload: {payload_json}")
        
        try:
            result = self.mqtt_client.publish(self.manual_open_topic, payload_json, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Manual open inviato!")
                return True
            else:
                print(f"❌ Errore invio: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Errore invio manual open: {e}")
            return False
    
    async def test_multiple_cards(self):
        """Test con multiple carte REALI"""
        
        print("\n🃏 TEST INVIO CARTE REALI")
        print("=" * 35)
        
        test_cards = [
            {
                "uid": "632D3903",  # Carta reale DAVIDE DONGHI
                "direction": "in",
                "description": "🆔 DAVIDE DONGHI (carta reale)"
            },
            {
                "uid": "A1B2C3D4",
                "direction": "out", 
                "description": "🧪 Carta test inesistente"
            },
            {
                "uid": "12345678",
                "direction": "in",
                "description": "🧪 Carta test generica"
            }
        ]
        
        for i, card in enumerate(test_cards, 1):
            print(f"\n{'='*60}")
            print(f"📤 INVIO CARTA {i}: {card['description']}")
            print(f"{'='*60}")
            
            success = await self.send_card_badge(card['uid'], card['direction'])
            
            if success:
                print(f"⏳ Aspetto risposta per 3 secondi...")
                await asyncio.sleep(3)
            
            print()
    
    async def test_manual_open(self):
        """Test manual open"""
        
        print(f"\n{'='*60}")
        print("🚪 TEST MANUAL OPEN")
        print(f"{'='*60}")
        
        await self.send_manual_open("in")
        print(f"⏳ Aspetto risposta per 3 secondi...")
        await asyncio.sleep(3)
    
    def disconnect(self):
        """Disconnetti MQTT"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        print("🔌 Disconnesso da MQTT")
    
    def generate_report(self):
        """Report finale"""
        
        print(f"\n{'='*70}")
        print("📊 REPORT FINALE MQTT REALE")
        print(f"{'='*70}")
        
        print(f"📈 STATISTICHE:")
        print(f"   Messaggi ricevuti: {len(self.messages_received)}")
        print(f"   Connessione MQTT: {'✅ OK' if self.connected else '❌ Fallita'}")
        
        if self.messages_received:
            print(f"\n📩 MESSAGGI RICEVUTI:")
            for i, msg in enumerate(self.messages_received, 1):
                print(f"   {i}. {msg['topic']}")
                print(f"      Timestamp: {msg['timestamp']}")
                print(f"      Payload: {msg['payload']}")
                print()
        else:
            print(f"\n📭 Nessun messaggio ricevuto")
        
        print(f"🎯 VERIFICA MQTT EXPLORER:")
        print(f"   Broker: {self.mqtt_host}:{self.mqtt_port}")
        print(f"   Controlla topics:")
        print(f"   - {self.badge_topic}")
        print(f"   - {self.response_topic}")
        print(f"   - {self.manual_open_topic}")

async def main():
    """Funzione principale"""
    
    print("🚀 TEST REALE MQTT - INVIO EFFETTIVO")
    print("=" * 50)
    print(f"⏰ Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⚠️  QUESTO TEST INVIA REALMENTE I MESSAGGI MQTT!")
    print("   Saranno visibili su MQTT Explorer")
    print()
    
    tester = RealMQTTTester()
    
    try:
        # Connetti MQTT
        if not await tester.connect_mqtt():
            print("❌ Impossibile connettersi a MQTT")
            return False
        
        # Aspetta un po' per stabilizzare
        await asyncio.sleep(2)
        
        # Test carte
        await tester.test_multiple_cards()
        
        # Test manual open
        await tester.test_manual_open()
        
        # Aspetta eventuali ultimi messaggi
        print("⏳ Aspetto eventuali ultimi messaggi...")
        await asyncio.sleep(5)
        
        # Report
        tester.generate_report()
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto")
        return False
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        return False
    finally:
        tester.disconnect()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n🏁 Test {'✅ COMPLETATO' if success else '❌ FALLITO'}")
        print(f"\n💡 Ora controlla MQTT Explorer su mqbrk.ddns.net:8883")
        print(f"   Topics da monitorare:")
        print(f"   - gate/tornello_01/badge")
        print(f"   - gate/tornello_01/response") 
        print(f"   - gate/tornello_01/manual_open")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Errore critico: {e}")
        sys.exit(1)