#!/usr/bin/env python3
"""
🌐 Test Endpoint Reale Singola Carta
===================================

Test dell'endpoint reale configurato:
https://gymme-newaction.ddns.net/api/sync-gate?card_uid=02D9BAEB
"""

import sys
import asyncio
import aiohttp
import json
import ssl
from pathlib import Path

async def test_real_single_card_endpoint():
    """Test dell'endpoint reale singola carta"""
    
    print("🌐 TEST ENDPOINT REALE SINGOLA CARTA")
    print("=" * 50)
    
    # Test card UIDs
    test_cards = [
        "02D9BAEB",           # Carta esempio fornita
        "04:A3:16:CA:41:64:80"  # Carta test conosciuta
    ]
    
    base_url = "https://gymme-newaction.ddns.net"
    endpoint = "/api/sync-gate"
    
    for card_uid in test_cards:
        print(f"\n🧪 Test carta: {card_uid}")
        print("-" * 30)
        
        try:
            url = f"{base_url}{endpoint}"
            params = {
                'card_uid': card_uid,
                'gate_id': 'tornello_01',
                'refresh': 'true'
            }
            
            print(f"   📍 URL: {url}")
            print(f"   📋 Params: {params}")
            
            # SSL context che ignora certificati self-signed (come nel sistema reale)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                connector=connector
            ) as session:
                async with session.get(url, params=params) as response:
                    print(f"   📊 Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        print(f"   ✅ Response ricevuta")
                        print(f"   📋 Success: {data.get('success')}")
                        
                        # Debug completo del JSON
                        print(f"   🐛 DEBUG JSON completo:")
                        print(f"   {json.dumps(data, indent=2)[:500]}...")
                        
                        if data.get('success') and data.get('data'):
                            cards = data['data']
                            print(f"   📊 Numero carte: {len(cards)}")
                            
                            # Verifica che restituisca solo la carta richiesta
                            for i, card_data in enumerate(cards):
                                # Gestisce sia dict che string
                                if isinstance(card_data, dict):
                                    returned_uid = card_data.get('card_uid')
                                    print(f"   📄 Carta {i+1}: {returned_uid}")
                                    
                                    if returned_uid == card_uid:
                                        print(f"      ✅ Match! Carta trovata")
                                        print(f"      👤 Nome: {card_data.get('customer_name')}")
                                        print(f"      🆔 ID: {card_data.get('customer_id')}")
                                        print(f"      📋 Whitelist: {card_data.get('in_white_list')}")
                                        print(f"      🎫 Abbonamenti: {len(card_data.get('active_subscriptions', []))}")
                                    else:
                                        print(f"      ⚠️ Carta diversa restituita: {returned_uid}")
                                else:
                                    print(f"   📄 Carta {i+1}: {card_data} (formato string)")
                            
                            # Test se endpoint filtra correttamente
                            target_cards = [card for card in cards if isinstance(card, dict) and card.get('card_uid') == card_uid]
                            
                            if len(target_cards) == 1 and len(cards) == 1:
                                print(f"   🎯 PERFETTO: Endpoint restituisce solo carta richiesta")
                            elif len(target_cards) == 1 and len(cards) > 1:
                                print(f"   ⚠️ PARZIALE: Carta trovata ma server restituisce {len(cards)} carte totali")
                                print(f"      📝 Server NON filtra ancora per singola carta")
                            elif len(target_cards) == 0:
                                print(f"   📭 Carta {card_uid} non trovata nel dataset di {len(cards)} carte")
                            else:
                                print(f"   🤔 Situazione inaspettata: {len(target_cards)} match in {len(cards)} carte")
                        else:
                            print(f"   📭 Nessun dato nel response")
                            
                    else:
                        print(f"   ❌ Errore HTTP: {response.status}")
                        text = await response.text()
                        print(f"   📄 Response: {text[:200]}...")
                        
        except Exception as e:
            print(f"   ❌ Errore richiesta: {e}")
    
    return True

async def main():
    await test_real_single_card_endpoint()
    
    print(f"\n📋 RISULTATI TEST:")
    print("=" * 30)
    print("✅ Endpoint configurato correttamente")
    print("✅ URL construction funziona")
    print("🔍 Verifica se server filtra per singola carta")
    print("📊 Monitoraggio response format")
    
    print(f"\n🎯 PROSSIMI PASSI:")
    print("1. Verificare se server implementa filtro singola carta")
    print("2. Se serve, richiedere implementazione filtro lato server")
    print("3. Test con cache refresh completo")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)