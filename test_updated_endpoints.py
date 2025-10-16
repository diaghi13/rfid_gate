#!/usr/bin/env python3
"""
🧪 Test API Aggiornate - Selezione Singola + Gate Verification
==============================================================

Test di:
1. Endpoint sync con selezione singola (aggiornato)
2. Endpoint gate-verification con payload corretto
"""

import asyncio
import aiohttp
import json
import time
import ssl
from datetime import datetime


async def test_updated_endpoints():
    """Test degli endpoint aggiornati"""
    print("🧪 TEST ENDPOINT AGGIORNATI")
    print("="*60)
    
    # SSL context per testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=connector
        ) as session:
            
            # TEST 1: Selezione singola carta (sync endpoint aggiornato)
            print("📋 TEST 1: Selezione Singola Carta")
            print("-"*50)
            
            # Prima recupera una carta reale
            print("🔍 Recupero carta reale per test...")
            sync_url = "https://gymme-newaction.ddns.net/api/sync-gate"
            
            async with session.get(sync_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data') and len(data['data']) > 0:
                        test_card = data['data'][0]
                        test_card_uid = test_card.get('card_uid')
                        
                        print(f"✅ Carta test: {test_card_uid}")
                        print(f"   Cliente: {test_card.get('customer_name')}")
                        print(f"   Subscriptions: {len(test_card.get('active_subscriptions', []))}")
                        
                        # TEST selezione singola
                        print(f"\n🎯 Test selezione singola per: {test_card_uid}")
                        
                        params = {
                            'card_uid': test_card_uid,
                            'gate_id': 'tornello_01',
                            'refresh': 'true'
                        }
                        
                        start_time = time.time()
                        
                        async with session.get(sync_url, params=params) as response:
                            end_time = time.time()
                            latency = (end_time - start_time) * 1000
                            
                            print(f"📊 Status: {response.status}")
                            print(f"⏱️ Latency: {latency:.2f}ms")
                            
                            if response.status == 200:
                                single_data = await response.json()
                                
                                if single_data.get('data'):
                                    returned_cards = single_data['data']
                                    print(f"📦 Carte restituite: {len(returned_cards)}")
                                    
                                    if len(returned_cards) == 1:
                                        returned_card = returned_cards[0]
                                        if returned_card.get('card_uid') == test_card_uid:
                                            print("✅ SELEZIONE SINGOLA FUNZIONA!")
                                            print(f"   Card UID: {returned_card.get('card_uid')}")
                                            print(f"   Customer: {returned_card.get('customer_name')}")
                                            print(f"   Subscriptions: {len(returned_card.get('active_subscriptions', []))}")
                                            
                                            # Verifica autorizzazione
                                            subscriptions = returned_card.get('active_subscriptions', [])
                                            is_authorized = (
                                                returned_card.get('in_white_list', False) or
                                                (isinstance(subscriptions, list) and 
                                                 len(subscriptions) > 0 and 
                                                 any(sub.get('is_active', False) for sub in subscriptions))
                                            )
                                            
                                            print(f"   🔐 Autorizzata: {'✅ SI' if is_authorized else '❌ NO'}")
                                        else:
                                            print(f"❌ ERRORE: Carta restituita diversa!")
                                            print(f"   Richiesta: {test_card_uid}")
                                            print(f"   Ricevuta: {returned_card.get('card_uid')}")
                                    else:
                                        print(f"⚠️ PROBLEMA: {len(returned_cards)} carte restituite (dovrebbe essere 1)")
                                        print("   Selezione singola NON implementata correttamente")
                                else:
                                    print("❌ Response senza dati")
                            else:
                                text = await response.text()
                                print(f"❌ Errore HTTP: {text[:200]}...")
            
            # TEST 2: Gate Verification endpoint
            print(f"\n📋 TEST 2: Gate Verification Endpoint")
            print("-"*50)
            
            gate_verification_url = "https://gymme-newaction.ddns.net/api/gate-verification"
            
            # Test con carta reale
            if 'test_card_uid' in locals():
                payload = {
                    "uid": test_card_uid,
                    "direction": "in",  # Cambio a "in" per test
                    "gate_id": "tornello_01"
                }
                
                print(f"🎯 Test gate verification per: {test_card_uid}")
                print(f"📦 Payload: {json.dumps(payload, indent=2)}")
                
                start_time = time.time()
                
                # Prova POST con JSON payload
                async with session.post(gate_verification_url, json=payload) as response:
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000
                    
                    print(f"📊 Status: {response.status}")
                    print(f"⏱️ Latency: {latency:.2f}ms")
                    
                    if response.status == 200:
                        verification_data = await response.json()
                        print(f"✅ GATE VERIFICATION FUNZIONA!")
                        print(f"📦 Response: {json.dumps(verification_data, indent=2, ensure_ascii=False)}")
                        
                        # Analizza response
                        if 'authorized' in verification_data:
                            authorized = verification_data.get('authorized', False)
                            print(f"🔐 Autorizzazione: {'✅ GRANTED' if authorized else '❌ DENIED'}")
                        
                        if 'customer_name' in verification_data:
                            print(f"👤 Cliente: {verification_data.get('customer_name')}")
                            
                    elif response.status == 404:
                        print("📭 Carta non trovata (404) - comportamento normale per carte inesistenti")
                    else:
                        text = await response.text()
                        print(f"❌ Errore: {text[:200]}...")
                
                # Test anche con carta inesistente
                print(f"\n🧪 Test carta inesistente...")
                fake_payload = {
                    "uid": "FAKE_CARD_123",
                    "direction": "in",
                    "gate_id": "tornello_01"
                }
                
                async with session.post(gate_verification_url, json=fake_payload) as response:
                    print(f"📊 Status carta fake: {response.status}")
                    
                    if response.status == 404:
                        print("✅ Comportamento corretto: 404 per carta inesistente")
                    else:
                        text = await response.text()
                        print(f"Response: {text[:100]}...")
            
            # TEST 3: Confronto performance
            print(f"\n📋 TEST 3: Confronto Performance")
            print("-"*50)
            
            if 'test_card_uid' in locals():
                print("⏱️ Performance comparison:")
                
                # Sync con selezione singola
                start = time.time()
                params = {'card_uid': test_card_uid, 'gate_id': 'tornello_01'}
                async with session.get(sync_url, params=params) as response:
                    if response.status == 200:
                        await response.json()
                sync_time = (time.time() - start) * 1000
                
                # Gate verification  
                start = time.time()
                payload = {"uid": test_card_uid, "direction": "in", "gate_id": "tornello_01"}
                async with session.post(gate_verification_url, json=payload) as response:
                    if response.status == 200:
                        await response.json()
                gate_time = (time.time() - start) * 1000
                
                print(f"📊 Sync singola:       {sync_time:.2f}ms")
                print(f"📊 Gate verification:  {gate_time:.2f}ms")
                
                if gate_time < sync_time:
                    print("🚀 Gate verification è più veloce!")
                else:
                    print("🚀 Sync singola è più veloce!")
    
    except Exception as e:
        print(f"❌ Errore generale: {e}")


async def update_cache_refresh_strategy():
    """Aggiorna la strategia per usare il migliore endpoint"""
    print(f"\n🔄 AGGIORNAMENTO STRATEGIA CACHE REFRESH")
    print("="*60)
    
    print("""
📝 STRATEGIA AGGIORNATA:

OPZIONE 1: Sync con selezione singola
- URL: /api/sync-gate?card_uid=AA:BB:CC:DD
- Metodo: GET
- Vantaggi: Usa endpoint esistente, dati completi
- Svantaggi: Possibile latenza maggiore

OPZIONE 2: Gate verification dedicato  
- URL: /api/gate-verification
- Metodo: POST
- Payload: {"uid": "AA:BB:CC:DD", "direction": "in", "gate_id": "tornello_01"}
- Vantaggi: Endpoint dedicato, response ottimizzata
- Svantaggi: Serve implementazione se non esiste

RACCOMANDAZIONE:
Usa gate-verification se disponibile (più veloce e specifico),
fallback su sync singola se gate-verification non risponde.
""")


if __name__ == "__main__":
    asyncio.run(test_updated_endpoints())
    asyncio.run(update_cache_refresh_strategy())