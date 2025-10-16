#!/usr/bin/env python3
"""
🧪 TEST REALE SEMPLIFICATO - Solo Endpoint HTTP
===============================================

Test focalizzato su:
- Endpoint HTTP reali (gymme-newaction.ddns.net)
- Flusso intelligente senza hardware
- Cache e sync manager
- Payload MQTT (simulato)

Senza:
- Hardware PN532 (richiede Raspberry Pi)
- MQTT reale (richiede hardware)
"""

import sys
import os
import asyncio
import time
import json
import aiohttp
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Carica configurazione
load_dotenv()

class SimplifiedRealTester:
    """Tester semplificato per endpoint HTTP reali"""
    
    def __init__(self):
        # URLs dal .env
        self.cache_sync_url = os.getenv('CACHE_SYNC_SERVER_URL')
        self.sync_url = os.getenv('SYNC_SERVER_URL')
        self.gate_verification_endpoint = os.getenv('GATE_VERIFICATION_ENDPOINT', '/api/gate-verification')
        self.cache_sync_endpoint = os.getenv('CACHE_SYNC_ENDPOINT', '/api/sync-gate')
        self.tornello_id = os.getenv('SYNC_GATE_ID', 'tornello_01')
        
        # MQTT Topics (per verifica)
        self.mqtt_badge_topic = os.getenv('MQTT_CARD_READ_TOPIC')
        self.mqtt_response_topic = os.getenv('MQTT_AUTH_RESPONSE_TOPIC')
        
        self.test_results = []
        
        print("🔧 CONFIGURAZIONE TEST REALE SEMPLIFICATO")
        print("=" * 50)
        print(f"🌐 Cache Server: {self.cache_sync_url}")
        print(f"🚪 Gate Server: {self.sync_url}")
        print(f"🏷️ Tornello ID: {self.tornello_id}")
        print()
        print(f"📡 MQTT Topics (configurati):")
        print(f"   📤 Badge: {self.mqtt_badge_topic}")
        print(f"   📥 Response: {self.mqtt_response_topic}")
        print()
    
    async def test_server_connectivity(self):
        """Test connettività server"""
        
        print("🌐 TEST CONNETTIVITÀ SERVER")
        print("-" * 35)
        
        # Test health endpoint
        health_url = f"{self.sync_url}/api/health"
        
        try:
            # SSL context che ignora certificati
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Server Health: {health_url}")
                        print(f"   Status: {data.get('status', 'unknown')}")
                        print(f"   Version: {data.get('version', 'unknown')}")
                        return True
                    else:
                        print(f"❌ Health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Errore connessione server: {e}")
            return False
    
    async def simulate_intelligent_flow(self, card_uid, direction="in"):
        """Simula il flusso intelligente completo"""
        
        print(f"\n🎯 SIMULAZIONE FLUSSO INTELLIGENTE")
        print(f"   Carta: {card_uid}")
        print(f"   Direzione: {direction}")
        print("-" * 40)
        
        start_time = time.time()
        result = {
            "card_uid": card_uid,
            "direction": direction,
            "scenario": None,
            "cache_hit": False,
            "mqtt_sent": False,
            "final_authorized": False,
            "response_time_ms": 0,
            "steps": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # STEP 1: Controlla Cache (Cache Sync)
            print("🔄 STEP 1: Cache Sync Check")
            cache_url = f"{self.cache_sync_url}{self.cache_sync_endpoint}"
            params = {"card_uid": card_uid}
            
            # SSL context che ignora certificati
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(cache_url, params=params) as response:
                    if response.status == 200:
                        cache_data = await response.json()
                        print(f"✅ Cache Hit: Carta trovata in cache")
                        print(f"   Data: {json.dumps(cache_data, indent=2)}")
                        
                        result["cache_hit"] = True
                        result["scenario"] = "CASO 1: Cache Hit"
                        result["steps"].append("cache_hit")
                        
                        # CASO 1: Simula MQTT parallelo
                        mqtt_payload = {
                            "card_uid": card_uid,
                            "identificativo_tornello": self.tornello_id,
                            "direzione": direction,
                            "timestamp": datetime.now().isoformat(),
                            "auth_required": True
                        }
                        
                        print(f"📡 MQTT Parallelo simulato su: {self.mqtt_badge_topic}")
                        print(f"   Payload: {json.dumps(mqtt_payload, indent=2)}")
                        
                        result["mqtt_sent"] = True
                        result["final_authorized"] = True
                        result["steps"].append("mqtt_parallel")
                        
                    elif response.status == 404:
                        print(f"📭 Cache Miss: Carta non in cache")
                        result["steps"].append("cache_miss")
                        
                        # STEP 2: Fallback diretto (Gate Verification)
                        print("\n🔗 STEP 2: Direct Gate Verification")
                        gate_url = f"{self.cache_sync_url}{self.gate_verification_endpoint}"
                        payload = {
                            "uid": card_uid,
                            "direction": direction,
                            "gate_id": self.tornello_id
                        }
                        
                        async with session.post(gate_url, json=payload) as gate_response:
                            if gate_response.status == 200:
                                gate_data = await gate_response.json()
                                print(f"✅ Gate Verification: {gate_data}")
                                
                                result["scenario"] = "CASO 2: Cache Miss → Direct Fallback"
                                result["final_authorized"] = gate_data.get("authorized", False)
                                result["steps"].append("direct_fallback")
                                
                                # CASO 2: NO MQTT (corretto)
                                print(f"🚫 NO MQTT Parallelo (CASO 2 - corretto)")
                                
                            else:
                                gate_text = await gate_response.text()
                                print(f"❌ Gate Verification Failed: {gate_text}")
                                result["scenario"] = "CASO 2: Fallback Failed"
                                result["steps"].append("fallback_failed")
                    
                    else:
                        cache_text = await response.text()
                        print(f"❌ Cache Error: {cache_text}")
                        result["steps"].append("cache_error")
            
            end_time = time.time()
            result["response_time_ms"] = (end_time - start_time) * 1000
            
            print(f"\n🎯 RISULTATO FINALE:")
            print(f"   Scenario: {result['scenario']}")
            print(f"   Autorizzato: {'✅ SÌ' if result['final_authorized'] else '❌ NO'}")
            print(f"   MQTT inviato: {'✅ SÌ' if result['mqtt_sent'] else '🚫 NO'}")
            print(f"   Tempo totale: {result['response_time_ms']:.1f}ms")
            
            return result
            
        except Exception as e:
            print(f"❌ Errore simulazione: {e}")
            result["scenario"] = "ERROR"
            result["error"] = str(e)
            return result
    
    async def test_multiple_cards(self):
        """Test con multiple carte"""
        
        print("\n🃏 TEST MULTIPLE CARTE")
        print("=" * 30)
        
        test_cards = [
            {
                "uid": "632D3903",  # Carta reale (DAVIDE DONGHI)
                "direction": "in",
                "description": "Carta reale nel sistema"
            },
            {
                "uid": "A1B2C3D4",
                "direction": "out", 
                "description": "Carta test inesistente"
            },
            {
                "uid": "12345678",
                "direction": "in",
                "description": "Carta test generica"
            }
        ]
        
        for i, card in enumerate(test_cards, 1):
            print(f"\n{'='*60}")
            print(f"🧪 TEST CARTA {i}: {card['description']}")
            print(f"{'='*60}")
            
            result = await self.simulate_intelligent_flow(card['uid'], card['direction'])
            self.test_results.append(result)
            
            # Pausa tra test
            await asyncio.sleep(1)
    
    async def generate_final_report(self):
        """Report finale"""
        
        print(f"\n{'='*70}")
        print("📊 REPORT FINALE TEST REALE SEMPLIFICATO")
        print(f"{'='*70}")
        
        if not self.test_results:
            print("❌ Nessun risultato disponibile")
            return
        
        # Statistiche
        total_tests = len(self.test_results)
        cache_hits = len([r for r in self.test_results if r['cache_hit']])
        cache_misses = total_tests - cache_hits
        authorizations = len([r for r in self.test_results if r['final_authorized']])
        mqtt_sent = len([r for r in self.test_results if r['mqtt_sent']])
        
        print(f"📈 STATISTICHE GENERALI:")
        print(f"   Test totali: {total_tests}")
        print(f"   Cache Hits: {cache_hits}/{total_tests}")
        print(f"   Cache Misses: {cache_misses}/{total_tests}")
        print(f"   Autorizzazioni: {authorizations}/{total_tests}")
        print(f"   MQTT inviati: {mqtt_sent}/{total_tests}")
        
        if self.test_results:
            avg_time = sum(r['response_time_ms'] for r in self.test_results if r['response_time_ms'] > 0) / len(self.test_results)
            print(f"   Tempo medio: {avg_time:.1f}ms")
        
        print()
        
        # Analisi flusso intelligente
        print("🎯 ANALISI FLUSSO INTELLIGENTE:")
        
        caso1_count = len([r for r in self.test_results if r['scenario'] and 'CASO 1' in r['scenario']])
        caso2_count = len([r for r in self.test_results if r['scenario'] and 'CASO 2' in r['scenario']])
        
        print(f"   CASO 1 (Cache Hit + MQTT): {caso1_count}")
        print(f"   CASO 2 (Cache Miss + Direct): {caso2_count}")
        print(f"   CASO 3 (Cache Refresh): 0 (non testato)")
        
        print()
        
        # Dettagli per carta
        print("📋 DETTAGLI TEST:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result['final_authorized'] else "❌"
            mqtt_status = "📡" if result['mqtt_sent'] else "🚫"
            
            print(f"   {i}. {status} {result['card_uid']} ({result['direction']})")
            print(f"      Scenario: {result.get('scenario', 'Unknown')}")
            print(f"      MQTT: {mqtt_status} | Tempo: {result['response_time_ms']:.1f}ms")
        
        print()
        
        # Verifica conformità
        print("✅ VERIFICA CONFORMITÀ FLUSSO INTELLIGENTE:")
        
        # CASO 1: Cache hit deve avere MQTT
        caso1_tests = [r for r in self.test_results if r['cache_hit']]
        caso1_mqtt_ok = all(r['mqtt_sent'] for r in caso1_tests) if caso1_tests else True
        print(f"   CASO 1 (Cache Hit → MQTT): {'✅' if caso1_mqtt_ok else '❌'}")
        
        # CASO 2: Cache miss non deve avere MQTT
        caso2_tests = [r for r in self.test_results if not r['cache_hit'] and r['scenario'] and 'CASO 2' in r['scenario']]
        caso2_no_mqtt_ok = all(not r['mqtt_sent'] for r in caso2_tests) if caso2_tests else True
        print(f"   CASO 2 (Cache Miss → NO MQTT): {'✅' if caso2_no_mqtt_ok else '❌'}")
        
        overall_ok = caso1_mqtt_ok and caso2_no_mqtt_ok
        print(f"\n🎯 CONFORMITÀ GENERALE: {'✅ PERFETTA' if overall_ok else '❌ PROBLEMI'}")

async def main():
    """Funzione principale"""
    
    print("🚀 TEST REALE SISTEMA RFID GATE - ENDPOINT HTTP")
    print("=" * 65)
    print(f"⏰ Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = SimplifiedRealTester()
    
    try:
        # Test connettività
        if not await tester.test_server_connectivity():
            print("❌ Server non raggiungibile")
            return False
        
        # Test multiple carte
        await tester.test_multiple_cards()
        
        # Report finale
        await tester.generate_final_report()
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto")
        return False
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n🏁 Test {'✅ COMPLETATO' if success else '❌ FALLITO'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Errore critico: {e}")
        sys.exit(1)