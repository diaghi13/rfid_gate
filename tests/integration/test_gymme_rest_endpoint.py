#!/usr/bin/env python3
"""
🔥 Test del nuovo endpoint REST Gymme per fallback real-time
Endpoint: https://gymme-newaction.ddns.net/api/gate-verification
Payload: {"uid": "632D3903", "direction": "out", "gate_id": "tornello_01"}
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Aggiungi il path del progetto (ora siamo in tests/integration/)
project_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_path))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.sync_manager import SyncManager

def load_env_file():
    """Carica file .env"""
    env_path = project_path / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ File .env caricato")
    else:
        print("⚠️ File .env non trovato")

async def test_gymme_endpoint():
    """Test del vero endpoint Gymme con carte di esempio"""
    
    print("🚀 AVVIO TEST ENDPOINT GYMME")
    print("=" * 60)
    
    # Carica configurazione
    load_env_file()
    config = RFIDGateConfig.from_env()
    logger = logging.getLogger("test_gymme")
    logger.setLevel(logging.DEBUG)
    
    print(f"🔧 Server: {config.sync.fallback_server_url}")
    print(f"🔧 Endpoint: {config.sync.fallback_endpoint}")
    print(f"🔧 URL Completo: {config.sync.fallback_server_url}{config.sync.fallback_endpoint}")
    print(f"🏷️ Gate ID: {config.sync.gate_id}")
    print(f"⏰ Timeout: {config.sync.fallback_timeout}s")
    print()
    
    # Crea SyncManager per test
    sync_manager = SyncManager(config, logger)
    
    # Test con carte di esempio
    test_cards = [
        {"uid": "632D3903", "description": "Carta esempio dal messaggio"},
        {"uid": "TEST001", "description": "Carta di test 1"},
        {"uid": "ABC123", "description": "Carta di test 2"},
        {"uid": "NOTFOUND", "description": "Carta che non dovrebbe esistere"}
    ]
    
    for i, card in enumerate(test_cards, 1):
        print(f"{i}️⃣ TEST CARTA: {card['uid']} ({card['description']})")
        print(f"   Direzione: IN")
        
        try:
            # Test direzione IN
            result = await sync_manager._check_realtime_fallback(card["uid"], "in")
            
            if result:
                print(f"   ✅ AUTORIZZATA: {result}")
                print(f"   📋 Dati ricevuti: {list(result.keys())}")
            else:
                print(f"   ❌ NON AUTORIZZATA o errore")
                
        except Exception as e:
            print(f"   🚨 ERRORE: {e}")
            
        print()
        
        # Aspetta un po' tra le richieste per non sovraccaricare il server
        await asyncio.sleep(1)
    
    print("=" * 60)
    print("🏁 Test completato!")

async def test_direction_variations():
    """Test con diverse direzioni"""
    
    print("🔄 TEST DIREZIONI DIVERSE")
    print("=" * 40)
    
    load_env_file()
    config = RFIDGateConfig.from_env()
    logger = logging.getLogger("test_gymme_directions")
    logger.setLevel(logging.DEBUG)
    
    sync_manager = SyncManager(config, logger)
    
    test_uid = "632D3903"  # Carta di esempio
    
    for direction in ["in", "out"]:
        print(f"🚪 Test direzione: {direction.upper()}")
        
        try:
            result = await sync_manager._check_realtime_fallback(test_uid, direction)
            if result:
                print(f"   ✅ Successo per direzione {direction}")
            else:
                print(f"   ❌ Fallito per direzione {direction}")
        except Exception as e:
            print(f"   🚨 Errore per direzione {direction}: {e}")
            
        await asyncio.sleep(1)
    
    print()

async def main():
    """Test principale"""
    
    print("🎯 TEST ENDPOINT GYMME REST")
    print("🌐 https://gymme-newaction.ddns.net/api/gate-verification")
    print("=" * 60)
    print()
    
    # Test base endpoint
    await test_gymme_endpoint()
    
    print()
    
    # Test direzioni
    await test_direction_variations()
    
    print("🎉 Tutti i test completati!")

if __name__ == "__main__":
    asyncio.run(main())