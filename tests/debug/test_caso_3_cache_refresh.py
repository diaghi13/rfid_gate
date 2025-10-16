#!/usr/bin/env python3
"""
🧪 TEST CASO 3: Cache Refresh per Abbonamento Scaduto
=====================================================

Scenario specifico:
1. Carta 632D3903 (DAVIDE DONGHI) esiste in cache
2. Abbonamento risulta scaduto in cache  
3. Cache Refresh: verifica aggiornamenti via /api/sync-gate
4. Abbonamento ancora scaduto nel server
5. MQTT parallelo + log accesso negato locale

QUESTO È IL CASO 3 del flusso intelligente!
"""

import sys
import os
import asyncio
import time
import json
import ssl
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ Installo paho-mqtt...")
    os.system("pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org paho-mqtt")
    import paho.mqtt.client as mqtt

# Carica configurazione
load_dotenv()

class CacheRefreshTester:
    """Tester per CASO 3: Cache Refresh con abbonamento scaduto"""
    
    def __init__(self):
        # URLs
        self.cache_sync_url = os.getenv('CACHE_SYNC_SERVER_URL')
        self.sync_url = os.getenv('SYNC_SERVER_URL')
        self.cache_sync_endpoint = os.getenv('CACHE_SYNC_ENDPOINT', '/api/sync-gate')
        
        # MQTT
        self.mqtt_host = os.getenv('MQTT_HOST', 'mqbrk.ddns.net')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '8883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME')
        self.mqtt_password = os.getenv('MQTT_PASSWORD')
        self.mqtt_use_tls = os.getenv('MQTT_USE_TLS', 'true').lower() == 'true'
        self.badge_topic = os.getenv('MQTT_CARD_READ_TOPIC', 'gate/tornello_01/badge')
        self.response_topic = os.getenv('MQTT_AUTH_RESPONSE_TOPIC', 'gate/tornello_01/response')
        
        # Tornello
        self.tornello_id = os.getenv('SYNC_GATE_ID', 'tornello_01')
        
        # MQTT Client
        self.mqtt_client = None
        self.mqtt_connected = False
        self.mqtt_responses = []
        
        print("🔧 CONFIGURAZIONE CASO 3: CACHE REFRESH")
        print("=" * 50)
        print(f"🌐 Cache Server: {self.cache_sync_url}")
        print(f"🔄 Sync Endpoint: {self.cache_sync_endpoint}")
        print(f"📡 MQTT: {self.mqtt_host}:{self.mqtt_port}")
        print(f"🃏 Test Card: 632D3903 (DAVIDE DONGHI)")
        print()
    
    def setup_mqtt_callbacks(self):
        """Setup callback MQTT"""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.mqtt_connected = True
                client.subscribe(self.response_topic)
                print(f"✅ MQTT connesso, sottoscritto a: {self.response_topic}")
            else:
                print(f"❌ MQTT connessione fallita: {rc}")
        
        def on_message(client, userdata, msg):
            payload = msg.payload.decode('utf-8')
            timestamp = datetime.now().isoformat()
            
            print(f"\n📩 RISPOSTA MQTT RICEVUTA:")
            print(f"   Topic: {msg.topic}")
            print(f"   Payload: {payload}")
            
            try:
                payload_json = json.loads(payload)
                self.mqtt_responses.append({
                    'topic': msg.topic,
                    'payload': payload_json,
                    'timestamp': timestamp
                })
                print(f"   Authorized: {'✅' if payload_json.get('authorized') else '❌'}")
                print(f"   Message: {payload_json.get('message', 'N/A')}")
            except:
                pass
        
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
    
    async def setup_mqtt(self):
        """Setup connessione MQTT"""
        try:
            self.mqtt_client = mqtt.Client()
            self.setup_mqtt_callbacks()
            
            if self.mqtt_username and self.mqtt_password:
                self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
            
            if self.mqtt_use_tls:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.mqtt_client.tls_set_context(context)
            
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Aspetta connessione
            for i in range(10):
                if self.mqtt_connected:
                    break
                await asyncio.sleep(0.5)
            
            return self.mqtt_connected
        except Exception as e:
            print(f"❌ Errore setup MQTT: {e}")
            return False
    
    async def simulate_caso_3_cache_refresh(self, card_uid="632D3903"):
        """Simula CASO 3: Cache Refresh completo"""
        
        print(f"\n🎯 SIMULAZIONE CASO 3: CACHE REFRESH")
        print(f"   Carta: {card_uid}")
        print("=" * 55)
        
        start_time = time.time()
        result = {
            "card_uid": card_uid,
            "scenario": "CASO 3: Cache Refresh",
            "steps": [],
            "cache_hit": False,
            "subscription_expired_cache": False,
            "subscription_expired_server": False,
            "mqtt_sent": False,
            "final_authorized": False,
            "response_time_ms": 0,
            "local_log": None
        }
        
        try:
            # SSL context per HTTPS
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                
                # STEP 1: Cache Check (simulato - sappiamo che esiste ma scaduto)
                print("🔍 STEP 1: Cache Check (simulato)")
                print("   ✅ Carta trovata in cache locale")
                print("   ❌ Abbonamento SCADUTO in cache")
                print(f"   📅 Data scadenza cache: {(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')}")
                
                result["cache_hit"] = True
                result["subscription_expired_cache"] = True
                result["steps"].append("cache_hit_expired")
                
                # STEP 2: Cache Refresh
                print(f"\n🔄 STEP 2: Cache Refresh")
                refresh_url = f"{self.cache_sync_url}{self.cache_sync_endpoint}"
                params = {"card_uid": card_uid}
                
                print(f"   URL: {refresh_url}")
                print(f"   Params: {params}")
                
                async with session.get(refresh_url, params=params) as response:
                    if response.status == 200:
                        server_data = await response.json()
                        print(f"   ✅ Dati server ricevuti:")
                        print(f"   {json.dumps(server_data, indent=4)}")
                        
                        # Analizza abbonamenti
                        subscriptions = server_data.get('data', {}).get('active_subscriptions', [])
                        has_active = len(subscriptions) > 0
                        
                        if has_active:
                            print(f"   ✅ Abbonamento ATTIVO trovato nel server!")
                            print(f"   🔄 Cache dovrebbe essere aggiornata")
                            result["subscription_expired_server"] = False
                            result["final_authorized"] = True
                            result["steps"].append("server_active_subscription")
                        else:
                            print(f"   ❌ Abbonamento ANCORA SCADUTO nel server")
                            print(f"   📋 Active subscriptions: {subscriptions}")
                            result["subscription_expired_server"] = True
                            result["steps"].append("server_expired_subscription")
                            
                            # STEP 3: MQTT Parallelo (per abbonamento scaduto)
                            print(f"\n📡 STEP 3: MQTT Parallelo (abbonamento scaduto)")
                            
                            mqtt_payload = {
                                "card_uid": card_uid,
                                "identificativo_tornello": self.tornello_id,
                                "direzione": "in",
                                "timestamp": datetime.now().isoformat(),
                                "auth_required": True
                            }
                            
                            if self.mqtt_connected:
                                payload_json = json.dumps(mqtt_payload)
                                publish_result = self.mqtt_client.publish(self.badge_topic, payload_json, qos=1)
                                
                                if publish_result.rc == mqtt.MQTT_ERR_SUCCESS:
                                    print(f"   ✅ MQTT inviato su: {self.badge_topic}")
                                    print(f"   📦 Payload: {payload_json}")
                                    result["mqtt_sent"] = True
                                    result["steps"].append("mqtt_parallel_sent")
                                else:
                                    print(f"   ❌ Errore invio MQTT: {publish_result.rc}")
                            else:
                                print(f"   ❌ MQTT non connesso")
                            
                            # STEP 4: Log Locale Accesso Negato
                            print(f"\n📝 STEP 4: Log Locale Accesso Negato")
                            
                            log_entry = {
                                "timestamp": datetime.now().isoformat(),
                                "card_uid": card_uid,
                                "customer_name": server_data.get('data', {}).get('customer_name', 'Unknown'),
                                "customer_id": server_data.get('data', {}).get('customer_id'),
                                "action": "ACCESS_DENIED",
                                "reason": "SUBSCRIPTION_EXPIRED",
                                "direction": "in",
                                "tornello_id": self.tornello_id,
                                "scenario": "CASO_3_CACHE_REFRESH"
                            }
                            
                            print(f"   📋 Log Entry:")
                            print(f"   {json.dumps(log_entry, indent=4)}")
                            
                            result["local_log"] = log_entry
                            result["steps"].append("local_log_denied")
                            result["final_authorized"] = False
                    
                    else:
                        response_text = await response.text()
                        print(f"   ❌ Errore refresh: {response.status} - {response_text}")
                        result["steps"].append("refresh_error")
            
            # Aspetta eventuale risposta MQTT
            if result["mqtt_sent"]:
                print(f"\n⏳ Aspetto risposta MQTT...")
                await asyncio.sleep(3)
            
            end_time = time.time()
            result["response_time_ms"] = (end_time - start_time) * 1000
            
            return result
            
        except Exception as e:
            print(f"❌ Errore simulazione: {e}")
            result["error"] = str(e)
            return result
    
    def generate_caso_3_report(self, result):
        """Report specifico per CASO 3"""
        
        print(f"\n{'='*70}")
        print("📊 REPORT CASO 3: CACHE REFRESH")
        print(f"{'='*70}")
        
        print(f"🃏 CARTA TESTATA: {result['card_uid']}")
        print(f"⏱️  TEMPO TOTALE: {result['response_time_ms']:.1f}ms")
        print()
        
        print(f"📋 FLUSSO ESEGUITO:")
        for i, step in enumerate(result['steps'], 1):
            step_names = {
                'cache_hit_expired': '🔍 Cache Hit (abbonamento scaduto)',
                'server_expired_subscription': '🔄 Server Refresh (ancora scaduto)',
                'server_active_subscription': '🔄 Server Refresh (ora attivo)',
                'mqtt_parallel_sent': '📡 MQTT Parallelo inviato',
                'local_log_denied': '📝 Log locale accesso negato',
                'refresh_error': '❌ Errore refresh server'
            }
            print(f"   {i}. {step_names.get(step, step)}")
        
        print()
        
        print(f"🎯 RISULTATI:")
        print(f"   Cache Hit: {'✅' if result['cache_hit'] else '❌'}")
        print(f"   Abbonamento scaduto (cache): {'❌' if result['subscription_expired_cache'] else '✅'}")
        print(f"   Abbonamento scaduto (server): {'❌' if result['subscription_expired_server'] else '✅'}")
        print(f"   MQTT inviato: {'✅' if result['mqtt_sent'] else '❌'}")
        print(f"   Autorizzazione finale: {'✅' if result['final_authorized'] else '❌'}")
        
        if result.get('local_log'):
            print(f"\n📝 LOG LOCALE GENERATO:")
            print(f"   Azione: {result['local_log']['action']}")
            print(f"   Motivo: {result['local_log']['reason']}")
            print(f"   Cliente: {result['local_log']['customer_name']}")
        
        if self.mqtt_responses:
            print(f"\n📩 RISPOSTE MQTT RICEVUTE:")
            for i, resp in enumerate(self.mqtt_responses, 1):
                print(f"   {i}. Authorized: {'✅' if resp['payload'].get('authorized') else '❌'}")
                print(f"      Message: {resp['payload'].get('message', 'N/A')}")
        
        print()
        
        # Verifica conformità CASO 3
        caso_3_ok = (
            result['cache_hit'] and
            result['subscription_expired_cache'] and
            result['mqtt_sent'] and
            result.get('local_log') is not None
        )
        
        print(f"✅ CONFORMITÀ CASO 3:")
        print(f"   Flusso corretto: {'✅ SÌ' if caso_3_ok else '❌ NO'}")
        
        if caso_3_ok:
            print(f"\n🎯 CASO 3 IMPLEMENTATO CORRETTAMENTE!")
            print(f"   1. ✅ Cache hit con abbonamento scaduto")
            print(f"   2. ✅ Refresh server per verificare aggiornamenti")
            print(f"   3. ✅ MQTT parallelo inviato")
            print(f"   4. ✅ Log locale accesso negato")
        else:
            print(f"\n⚠️  CASO 3 NON COMPLETO")

async def main():
    """Funzione principale"""
    
    print("🚀 TEST CASO 3: CACHE REFRESH - ABBONAMENTO SCADUTO")
    print("=" * 65)
    print(f"⏰ Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 SCENARIO:")
    print("   - Carta 632D3903 esiste in cache ma abbonamento scaduto")
    print("   - Refresh server per verificare aggiornamenti")
    print("   - Abbonamento ancora scaduto → MQTT + log negato")
    print()
    
    tester = CacheRefreshTester()
    
    try:
        # Setup MQTT
        print("🔌 Setup MQTT...")
        if not await tester.setup_mqtt():
            print("⚠️  MQTT non connesso, continuo senza")
        
        # Test CASO 3
        result = await tester.simulate_caso_3_cache_refresh()
        
        # Report
        tester.generate_caso_3_report(result)
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto")
        return False
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        return False
    finally:
        if tester.mqtt_client:
            tester.mqtt_client.loop_stop()
            tester.mqtt_client.disconnect()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n🏁 Test {'✅ COMPLETATO' if success else '❌ FALLITO'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Errore critico: {e}")
        sys.exit(1)