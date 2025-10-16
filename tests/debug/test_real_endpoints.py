#!/usr/bin/env python3
"""
Test reale semplificato con endpoint produzione
"""

import os
import sys
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
from datetime import datetime

# Carica configurazione
load_dotenv()

async def test_real_endpoints():
    """Test reale degli endpoint"""
    
    # Configurazione dal .env
    cache_sync_url = os.getenv('CACHE_SYNC_SERVER_URL')
    sync_url = os.getenv('SYNC_SERVER_URL')
    gate_verification_endpoint = os.getenv('GATE_VERIFICATION_ENDPOINT', '/api/gate-verification')
    cache_sync_endpoint = os.getenv('CACHE_SYNC_ENDPOINT', '/api/sync-gate')
    
    print("🔍 CONFIGURAZIONE ATTUALE:")
    print(f"CACHE_SYNC_SERVER_URL: {cache_sync_url}")
    print(f"SYNC_SERVER_URL: {sync_url}")
    print(f"GATE_VERIFICATION_ENDPOINT: {gate_verification_endpoint}")
    print(f"CACHE_SYNC_ENDPOINT: {cache_sync_endpoint}")
    print()
    
    if "localhost" in str(cache_sync_url) or "localhost" in str(sync_url):
        print("⚠️  ATTENZIONE: Rilevato localhost in configurazione!")
        print("   Il sistema dovrebbe usare URL di produzione")
        print()
    
    # Test connettività base
    print("🌐 TEST CONNETTIVITÀ")
    print("-" * 30)
    
    health_url = f"{sync_url}/api/health"
    print(f"💚 Test Health: {health_url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(health_url) as response:
                print(f"📥 Status Code: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"✅ Health Response: {json.dumps(data, indent=2)}")
                        connectivity_ok = True
                    except:
                        text = await response.text()
                        print(f"✅ Health Response (text): {text}")
                        connectivity_ok = True
                else:
                    text = await response.text()
                    print(f"❌ Health Failed: {text}")
                    connectivity_ok = False
                    
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        connectivity_ok = False
    
    if not connectivity_ok:
        print("❌ Server non raggiungibile!")
        return False
    
    print()
    print("✅ Server raggiungibile! Procedo con test endpoint...")
    print()
    
    # Test carte
    test_cards = [
        {
            "uid": "1A2B3C4D",
            "description": "Carta test cache hit",
            "scenario": "CASO 1"
        },
        {
            "uid": "9Z8Y7X6W", 
            "description": "Carta test cache miss",
            "scenario": "CASO 2"
        },
        {
            "uid": "5E6F7G8H",
            "description": "Carta test refresh",
            "scenario": "CASO 3"
        }
    ]
    
    for i, card in enumerate(test_cards, 1):
        print(f"🃏 TEST CARTA {i}: {card['scenario']}")
        print(f"   UID: {card['uid']}")
        print(f"   Descrizione: {card['description']}")
        print("-" * 40)
        
        # Test cache sync
        cache_url = f"{cache_sync_url}{cache_sync_endpoint}"
        params = {"card_uid": card['uid']}
        
        print(f"🔄 Cache Sync: {cache_url}")
        print(f"📤 Params: {params}")
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(cache_url, params=params) as response:
                    print(f"📥 Cache Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Cache Response: {json.dumps(data, indent=2)}")
                        cache_success = True
                    else:
                        text = await response.text()
                        print(f"❌ Cache Error: {text}")
                        cache_success = False
                        
        except Exception as e:
            print(f"❌ Cache Exception: {e}")
            cache_success = False
        
        print()
        
        # Test gate verification se cache fallisce
        if not cache_success:
            gate_url = f"{cache_sync_url}{gate_verification_endpoint}"
            payload = {
                "uid": card['uid'],
                "direction": "in",
                "gate_id": "tornello_01"
            }
            
            print(f"🔗 Gate Verification: {gate_url}")
            print(f"📤 Payload: {json.dumps(payload, indent=2)}")
            
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(gate_url, json=payload) as response:
                        print(f"📥 Gate Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ Gate Response: {json.dumps(data, indent=2)}")
                        else:
                            text = await response.text()
                            print(f"❌ Gate Error: {text}")
                            
            except Exception as e:
                print(f"❌ Gate Exception: {e}")
        
        print("=" * 50)
        print()
    
    return True

async def main():
    print("🚀 TEST REALE ENDPOINT PRODUZIONE")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = await test_real_endpoints()
    
    if success:
        print("🎉 Test completato!")
    else:
        print("❌ Test fallito!")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrotto")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        sys.exit(1)