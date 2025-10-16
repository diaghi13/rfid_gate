#!/usr/bin/env python3
"""
🔍 Test Endpoint Reale - Analisi Struttura Dati
==============================================

Controllo endpoint sync reale per verificare:
1. Struttura response per sync completo
2. Struttura response per singola carta
3. Campi disponibili per cache refresh
4. Compatibilità con sistema esistente
"""

import asyncio
import aiohttp
import json
import time
import ssl
from datetime import datetime


async def test_real_endpoint_structure():
    """Testa struttura dati endpoint reale"""
    print("🔍 ANALISI ENDPOINT REALE")
    print("="*60)
    
    # Config from .env
    server_url = "https://gymme-newaction.ddns.net"
    sync_endpoint = "/api/sync-gate"
    
    print(f"🌐 Server: {server_url}")
    print(f"📡 Endpoint: {sync_endpoint}")
    
    try:
        # SSL context per testing (bypass verificazione certificato)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=connector
        ) as session:
            
            # TEST 1: Sync completo (per capire struttura generale)
            print(f"\n📋 TEST 1: Sync Completo")
            print("-"*40)
            
            full_url = f"{server_url}{sync_endpoint}"
            print(f"URL: {full_url}")
            
            async with session.get(full_url) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"Response type: {type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"Keys: {list(data.keys())}")
                            
                            if 'data' in data and data['data']:
                                first_card = data['data'][0] if data['data'] else None
                                if first_card:
                                    print(f"\n📋 STRUTTURA CARTA TIPO:")
                                    print(json.dumps(first_card, indent=2, ensure_ascii=False))
                                    
                                    # Analizza campi disponibili
                                    print(f"\n🔍 CAMPI DISPONIBILI:")
                                    for key, value in first_card.items():
                                        print(f"   {key}: {type(value).__name__} = {str(value)[:50]}")
                                
                                print(f"\n📊 STATISTICHE:")
                                print(f"   Totale carte: {len(data['data'])}")
                                
                                # Conta carte attive
                                active_count = 0
                                for card in data['data']:
                                    if card.get('in_white_list') or (card.get('active_subscriptions') and len(card.get('active_subscriptions', [])) > 0):
                                        active_count += 1
                                
                                print(f"   Carte attive: {active_count}")
                                print(f"   Carte inattive: {len(data['data']) - active_count}")
                        
                        elif isinstance(data, list):
                            print(f"Response è array diretto con {len(data)} elementi")
                            if data:
                                print(f"Primo elemento: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                                
                    except json.JSONDecodeError as e:
                        print(f"❌ Errore JSON: {e}")
                        text = await response.text()
                        print(f"Raw response: {text[:200]}...")
                else:
                    text = await response.text()
                    print(f"❌ Error response: {text[:200]}...")
            
            # TEST 2: Singola carta (per cache refresh)
            print(f"\n📋 TEST 2: Verifica Singola Carta")
            print("-"*40)
            
            # Prova con carta inventata per vedere response
            test_card_uid = "TEST:CARD:123"
            params = {
                'card_uid': test_card_uid,
                'gate_id': 'tornello_01',
                'refresh': 'true'
            }
            
            print(f"URL: {full_url}?card_uid={test_card_uid}")
            
            async with session.get(full_url, params=params) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"Response type: {type(data)}")
                        print(f"Content: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        
                        # Verifica se supporta filtro singola carta
                        if isinstance(data, dict) and 'data' in data:
                            if len(data['data']) == 0:
                                print("✅ Server supporta filtro singola carta (response vuoto per carta inesistente)")
                            elif len(data['data']) == 1:
                                print("✅ Server supporta filtro singola carta (response con una carta)")
                            else:
                                print("⚠️ Server potrebbe non supportare filtro (troppe carte in response)")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Errore JSON: {e}")
                        text = await response.text()
                        print(f"Raw response: {text[:200]}...")
                else:
                    text = await response.text()
                    print(f"❌ Error response: {text[:200]}...")
            
            # TEST 3: Carta esistente (se ne troviamo una dal sync completo)
            print(f"\n📋 TEST 3: Verifica Carta Esistente")
            print("-"*40)
            
            # Prima recupera una carta vera dal sync completo
            async with session.get(full_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, dict) and 'data' in data and data['data']:
                        real_card = data['data'][0]
                        real_card_uid = real_card.get('card_uid')
                        
                        if real_card_uid:
                            print(f"Testando carta reale: {real_card_uid}")
                            
                            params = {
                                'card_uid': real_card_uid,
                                'gate_id': 'tornello_01', 
                                'refresh': 'true'
                            }
                            
                            async with session.get(full_url, params=params) as response:
                                print(f"Status: {response.status}")
                                
                                if response.status == 200:
                                    data = await response.json()
                                    print(f"Response type: {type(data)}")
                                    
                                    if isinstance(data, dict) and 'data' in data:
                                        if len(data['data']) == 1:
                                            returned_card = data['data'][0]
                                            print("✅ Server supporta filtro singola carta!")
                                            print(f"Carta restituita: {returned_card.get('card_uid')}")
                                            print(f"Customer: {returned_card.get('customer_name', 'N/A')}")
                                            print(f"Whitelist: {returned_card.get('in_white_list', False)}")
                                            print(f"Subscriptions: {len(returned_card.get('active_subscriptions', []))}")
                                        else:
                                            print(f"⚠️ Risposta con {len(data['data'])} carte (dovrebbe essere 1)")
                                    
                                else:
                                    text = await response.text()
                                    print(f"❌ Error: {text[:200]}...")
            
    except Exception as e:
        print(f"❌ Errore connessione: {e}")


async def test_cache_refresh_compatibility():
    """Testa compatibilità con sistema cache refresh"""
    print(f"\n🔄 TEST COMPATIBILITÀ CACHE REFRESH")
    print("="*60)
    
    server_url = "https://gymme-newaction.ddns.net"
    sync_endpoint = "/api/sync-gate"
    
    try:
        # SSL context per testing
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            connector=connector
        ) as session:
            
            # Recupera prime 3 carte per test
            full_url = f"{server_url}{sync_endpoint}"
            
            async with session.get(full_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, dict) and 'data' in data and data['data']:
                        test_cards = data['data'][:3]  # Prime 3 carte
                        
                        print(f"📊 Testando {len(test_cards)} carte per cache refresh...")
                        
                        for i, card in enumerate(test_cards, 1):
                            card_uid = card.get('card_uid')
                            if not card_uid:
                                continue
                                
                            print(f"\n🔍 Test {i}/3: {card_uid}")
                            
                            # Simula cache refresh
                            params = {
                                'card_uid': card_uid,
                                'gate_id': 'tornello_01',
                                'refresh': 'true'
                            }
                            
                            start_time = time.time()
                            
                            async with session.get(full_url, params=params) as response:
                                end_time = time.time()
                                latency = (end_time - start_time) * 1000
                                
                                print(f"   ⏱️ Latency: {latency:.2f}ms")
                                
                                if response.status == 200:
                                    refresh_data = await response.json()
                                    
                                    if isinstance(refresh_data, dict) and 'data' in refresh_data:
                                        if len(refresh_data['data']) == 1:
                                            refreshed_card = refresh_data['data'][0]
                                            
                                            # Verifica campi necessari per cache refresh
                                            required_fields = ['card_uid', 'customer_name']
                                            optional_fields = ['customer_id', 'in_white_list', 'active_subscriptions']
                                            
                                            print(f"   ✅ Singola carta restituita")
                                            
                                            missing_required = []
                                            for field in required_fields:
                                                if field not in refreshed_card:
                                                    missing_required.append(field)
                                            
                                            if missing_required:
                                                print(f"   ❌ Campi obbligatori mancanti: {missing_required}")
                                            else:
                                                print(f"   ✅ Tutti i campi obbligatori presenti")
                                            
                                            # Simula logica is_enabled
                                            is_enabled = False
                                            if refreshed_card.get('in_white_list'):
                                                is_enabled = True
                                                print(f"   🏷️ Carta in whitelist")
                                            elif refreshed_card.get('active_subscriptions'):
                                                subs = refreshed_card.get('active_subscriptions', [])
                                                if isinstance(subs, list) and len(subs) > 0:
                                                    is_enabled = True
                                                    print(f"   📅 {len(subs)} subscription(s) attive")
                                            
                                            print(f"   🔐 Cache refresh result: {'ENABLED' if is_enabled else 'DISABLED'}")
                                            
                                        else:
                                            print(f"   ⚠️ Response con {len(refresh_data['data'])} carte (dovrebbe essere 1)")
                                    else:
                                        print(f"   ❌ Response format non valido")
                                else:
                                    print(f"   ❌ HTTP {response.status}")
                            
                            # Pausa tra test
                            await asyncio.sleep(0.5)
    
    except Exception as e:
        print(f"❌ Errore test compatibilità: {e}")


async def main():
    """Test completo endpoint"""
    await test_real_endpoint_structure()
    await test_cache_refresh_compatibility()
    
    print(f"\n🎯 CONCLUSIONI")
    print("="*60)
    print("✅ Se i test sopra mostrano supporto per filtro singola carta,")
    print("   il sistema cache refresh può usare l'endpoint esistente")
    print("❌ Se non supporta filtro, serve implementazione backend")
    print("\n💡 Guarda i risultati dei test per la decisione finale!")


if __name__ == "__main__":
    asyncio.run(main())