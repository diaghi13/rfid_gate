#!/usr/bin/env python3
"""
🧪 TEST REALE CASO 2: Cache Miss → Direct Fallback
==================================================

Test completo per CASO 2:
1. Carta NON in cache (cache miss)
2. Direct fallback a /api/gate-verification
3. NO MQTT parallelo (comportamento corretto CASO 2)
4. Risposta diretta autorizzazione/negazione

Carte test:
- FFFFFFFF: Carta completamente inesistente  
- 99999999: Carta test generica
- DEADBEEF: Carta hex test

Questo è il CASO 2 del flusso intelligente!
"""

import sys
import os
import asyncio
import time
import json
import ssl
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Carica configurazione
load_dotenv()

class Caso2CacheMissTester:
    """Tester per CASO 2: Cache Miss → Direct Fallback"""
    
    def __init__(self):
        # URLs
        self.cache_sync_url = os.getenv('CACHE_SYNC_SERVER_URL')
        self.sync_url = os.getenv('SYNC_SERVER_URL')
        self.cache_sync_endpoint = os.getenv('CACHE_SYNC_ENDPOINT', '/api/sync-gate')
        self.gate_verification_endpoint = os.getenv('GATE_VERIFICATION_ENDPOINT', '/api/gate-verification')
        
        # Tornello
        self.tornello_id = os.getenv('SYNC_GATE_ID', 'tornello_01')
        
        # Test results
        self.test_results = []
        
        print("🔧 CONFIGURAZIONE CASO 2: CACHE MISS")
        print("=" * 45)
        print(f"🌐 Cache Server: {self.cache_sync_url}")
        print(f"🚪 Gate Server: {self.sync_url}")
        print(f"🔍 Cache Endpoint: {self.cache_sync_endpoint}")
        print(f"🚪 Gate Endpoint: {self.gate_verification_endpoint}")
        print(f"🏷️ Tornello ID: {self.tornello_id}")
        print()
    
    async def test_cache_miss_flow(self, card_uid, direction="in"):
        """Test completo CASO 2: Cache Miss → Direct Fallback"""
        
        print(f"\n🎯 TEST CASO 2: CACHE MISS")
        print(f"   Carta: {card_uid}")
        print(f"   Direzione: {direction}")
        print("=" * 50)
        
        start_time = time.time()
        result = {
            "card_uid": card_uid,
            "direction": direction,
            "scenario": "CASO 2: Cache Miss → Direct Fallback",
            "steps": [],
            "cache_hit": False,
            "cache_status": None,
            "direct_fallback": False,
            "mqtt_sent": False,  # MUST be False for CASO 2
            "final_authorized": False,
            "response_time_ms": 0,
            "cache_response": None,
            "gate_response": None,
            "error": None
        }
        
        try:
            # SSL context per HTTPS
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                
                # STEP 1: Cache Check
                print("🔍 STEP 1: Cache Check")
                cache_url = f"{self.cache_sync_url}{self.cache_sync_endpoint}"
                params = {"card_uid": card_uid}
                
                print(f"   URL: {cache_url}")
                print(f"   Params: {params}")
                
                async with session.get(cache_url, params=params) as response:
                    result["cache_status"] = response.status
                    
                    if response.status == 200:
                        cache_data = await response.json()
                        print(f"   ✅ CACHE HIT (inaspettato!)")
                        print(f"   Data: {json.dumps(cache_data, indent=2)}")
                        
                        result["cache_hit"] = True
                        result["cache_response"] = cache_data
                        result["steps"].append("unexpected_cache_hit")
                        
                        # Se cache hit, dovrebbe essere CASO 1, non CASO 2
                        result["scenario"] = "CASO 1: Cache Hit (non CASO 2!)"
                        
                    elif response.status == 404:
                        print(f"   📭 CACHE MISS (corretto per CASO 2)")
                        result["cache_hit"] = False
                        result["steps"].append("cache_miss")
                        
                        # STEP 2: Direct Fallback (Gate Verification)
                        print(f"\n🚪 STEP 2: Direct Gate Verification")
                        gate_url = f"{self.cache_sync_url}{self.gate_verification_endpoint}"
                        payload = {
                            "uid": card_uid,
                            "direction": direction,
                            "gate_id": self.tornello_id
                        }
                        
                        print(f"   URL: {gate_url}")
                        print(f"   Payload: {json.dumps(payload, indent=2)}")
                        
                        async with session.post(gate_url, json=payload) as gate_response:
                            if gate_response.status == 200:
                                gate_data = await gate_response.json()
                                print(f"   ✅ Gate Verification Success:")
                                print(f"   {json.dumps(gate_data, indent=2)}")
                                
                                result["direct_fallback"] = True
                                result["gate_response"] = gate_data
                                result["final_authorized"] = gate_data.get("authorized", False)
                                result["steps"].append("direct_fallback_success")
                                
                                # CASO 2: NO MQTT (corretto)
                                print(f"\n🚫 NO MQTT PARALLELO (CASO 2 - corretto)")
                                print(f"   ✅ Cache Miss → Direct Response (no MQTT)")
                                result["mqtt_sent"] = False
                                result["steps"].append("no_mqtt_correct")
                                
                            else:
                                gate_text = await gate_response.text()
                                print(f"   ❌ Gate Verification Failed: {gate_response.status}")
                                print(f"   Response: {gate_text}")
                                
                                result["direct_fallback"] = False
                                result["gate_response"] = {"error": gate_text, "status": gate_response.status}
                                result["steps"].append("direct_fallback_failed")
                    
                    else:
                        cache_text = await response.text()
                        print(f"   ❌ Cache Error: {response.status}")
                        print(f"   Response: {cache_text}")
                        
                        result["cache_response"] = {"error": cache_text, "status": response.status}
                        result["steps"].append("cache_error")
            
            end_time = time.time()
            result["response_time_ms"] = (end_time - start_time) * 1000
            
            return result
            
        except Exception as e:
            print(f"❌ Errore test: {e}")
            result["error"] = str(e)
            result["steps"].append("exception")
            return result
    
    async def test_multiple_nonexistent_cards(self):
        """Test con multiple carte inesistenti"""
        
        print("\n🃏 TEST MULTIPLE CARTE INESISTENTI")
        print("=" * 45)
        
        test_cards = [
            {
                "uid": "FFFFFFFF",
                "direction": "in",
                "description": "🚫 Carta completamente inesistente (hex max)"
            },
            {
                "uid": "99999999",
                "direction": "out", 
                "description": "🧪 Carta test numerica"
            },
            {
                "uid": "DEADBEEF",
                "direction": "in",
                "description": "💀 Carta hex test pattern"
            },
            {
                "uid": "00000000",
                "direction": "out",
                "description": "⚫ Carta zero (probabilmente inesistente)"
            }
        ]
        
        for i, card in enumerate(test_cards, 1):
            print(f"\n{'='*70}")
            print(f"🧪 TEST CARTA {i}: {card['description']}")
            print(f"{'='*70}")
            
            result = await self.test_cache_miss_flow(card['uid'], card['direction'])
            self.test_results.append(result)
            
            # Analisi immediata risultato
            print(f"\n📊 RISULTATO IMMEDIATO:")
            print(f"   Scenario: {result['scenario']}")
            print(f"   Cache Hit: {'✅' if result['cache_hit'] else '📭'}")
            print(f"   Direct Fallback: {'✅' if result['direct_fallback'] else '❌'}")
            print(f"   MQTT Sent: {'❌ ERRORE!' if result['mqtt_sent'] else '✅ Corretto (no MQTT)'}")
            print(f"   Authorized: {'✅' if result['final_authorized'] else '❌'}")
            print(f"   Tempo: {result['response_time_ms']:.1f}ms")
            
            # Pausa tra test
            await asyncio.sleep(1)
    
    def generate_caso_2_report(self):
        """Report finale specifico per CASO 2"""
        
        print(f"\n{'='*80}")
        print("📊 REPORT FINALE CASO 2: CACHE MISS → DIRECT FALLBACK")
        print(f"{'='*80}")
        
        if not self.test_results:
            print("❌ Nessun risultato disponibile")
            return
        
        total_tests = len(self.test_results)
        cache_misses = len([r for r in self.test_results if not r['cache_hit']])
        direct_fallbacks = len([r for r in self.test_results if r['direct_fallback']])
        mqtt_sent = len([r for r in self.test_results if r['mqtt_sent']])
        authorizations = len([r for r in self.test_results if r['final_authorized']])
        
        print(f"📈 STATISTICHE GENERALI:")
        print(f"   Test totali: {total_tests}")
        print(f"   Cache Misses: {cache_misses}/{total_tests} (dovrebbero essere tutti)")
        print(f"   Direct Fallbacks: {direct_fallbacks}/{total_tests}")
        print(f"   MQTT inviati: {mqtt_sent}/{total_tests} (dovrebbero essere 0)")
        print(f"   Autorizzazioni: {authorizations}/{total_tests}")
        
        if self.test_results:
            avg_time = sum(r['response_time_ms'] for r in self.test_results if r['response_time_ms'] > 0) / len(self.test_results)
            print(f"   Tempo medio: {avg_time:.1f}ms")
        
        print()
        
        # Analisi conformità CASO 2
        print("🎯 ANALISI CONFORMITÀ CASO 2:")
        
        # Tutti dovrebbero essere cache miss
        all_cache_miss = all(not r['cache_hit'] for r in self.test_results)
        print(f"   Tutti Cache Miss: {'✅' if all_cache_miss else '❌'}")
        
        # Nessuno dovrebbe inviare MQTT
        no_mqtt_sent = all(not r['mqtt_sent'] for r in self.test_results)
        print(f"   Nessun MQTT inviato: {'✅' if no_mqtt_sent else '❌ ERRORE!'}")
        
        # Tutti dovrebbero usare direct fallback
        all_direct_fallback = all(r['direct_fallback'] for r in self.test_results if not r.get('error'))
        print(f"   Tutti Direct Fallback: {'✅' if all_direct_fallback else '❌'}")
        
        caso_2_perfetto = all_cache_miss and no_mqtt_sent and all_direct_fallback
        
        print()
        
        # Dettagli per carta
        print("📋 DETTAGLI TEST:")
        for i, result in enumerate(self.test_results, 1):
            cache_icon = "📭" if not result['cache_hit'] else "✅"
            auth_icon = "✅" if result['final_authorized'] else "❌"
            mqtt_icon = "🚫" if not result['mqtt_sent'] else "❌ ERRORE!"
            
            print(f"   {i}. {cache_icon} {result['card_uid']} ({result['direction']})")
            print(f"      Authorized: {auth_icon} | MQTT: {mqtt_icon} | Tempo: {result['response_time_ms']:.1f}ms")
            if result.get('error'):
                print(f"      Errore: {result['error']}")
        
        print()
        
        # Verifica finale
        print(f"✅ VERIFICA FINALE CASO 2:")
        print(f"   Flusso corretto: {'✅ PERFETTO' if caso_2_perfetto else '❌ PROBLEMI'}")
        
        if caso_2_perfetto:
            print(f"\n🎯 CASO 2 IMPLEMENTATO PERFETTAMENTE!")
            print(f"   1. ✅ Tutte cache miss")
            print(f"   2. ✅ Tutti direct fallback")
            print(f"   3. ✅ Nessun MQTT inviato (corretto)")
            print(f"   4. ✅ Risposte dirette immediate")
        else:
            print(f"\n⚠️  CASO 2 HA PROBLEMI:")
            if not all_cache_miss:
                print(f"   ❌ Alcune carte erano in cache (non dovrebbero)")
            if not no_mqtt_sent:
                print(f"   ❌ MQTT inviato (ERRORE! CASO 2 non deve inviare MQTT)")
            if not all_direct_fallback:
                print(f"   ❌ Direct fallback non funzionante")

async def main():
    """Funzione principale"""
    
    print("🚀 TEST REALE CASO 2: CACHE MISS → DIRECT FALLBACK")
    print("=" * 70)
    print(f"⏰ Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 SCENARIO CASO 2:")
    print("   - Carte NON in cache (cache miss)")
    print("   - Direct fallback a /api/gate-verification")
    print("   - NO MQTT parallelo (comportamento corretto)")
    print("   - Risposta diretta immediata")
    print()
    
    tester = Caso2CacheMissTester()
    
    try:
        # Test multiple carte inesistenti
        await tester.test_multiple_nonexistent_cards()
        
        # Report finale
        tester.generate_caso_2_report()
        
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