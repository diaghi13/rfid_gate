#!/usr/bin/env python3
"""
Test del workflow corretto di cache refresh
Verifica che la cache refresh NON bypassi il flusso MQTT normale
"""

import sys
import asyncio
import json
from pathlib import Path

# Add il modulo principale al path
sys.path.append(str(Path(__file__).parent))

from cache_refresh_strategy import CacheRefreshManager
from rfid_gate.config.settings import Config
from rfid_gate.network.sync_manager import SyncManager

async def test_corrected_workflow():
    """
    Test del workflow corretto:
    1. Cache refresh SOLO aggiorna cache locale
    2. NON chiama gate-verification direttamente  
    3. Restituisce success/failure dell'update cache
    4. Il sistema poi procede con normale workflow MQTT se cache OK
    """
    
    print("🧪 TEST WORKFLOW CORRETTO CACHE REFRESH")
    print("=" * 60)
    
    try:
        # Setup
        config = Config()  # Usa config default
        sync_manager = SyncManager(config, "tornello_01")
        refresh_mgr = CacheRefreshManager(sync_manager)
        
        # Test 1: Cache refresh con carta esistente
        print("\n1️⃣ TEST: Cache refresh carta esistente")
        print("-" * 40)
        
        test_card_uid = "04:A3:16:CA:41:64:80"  # Carta test conosciuta
        
        # Simula carta negata da cache che ha bisogno di refresh
        print(f"🔄 Simulando cache refresh per carta negata: {test_card_uid}")
        
        # Chiama il metodo corretto (che NON deve chiamare gate-verification)
        cache_updated = await refresh_mgr.handle_denied_card_refresh(test_card_uid)
        
        print(f"📊 Risultato cache refresh: {cache_updated}")
        
        if cache_updated:
            print("✅ Cache refresh SUCCESS - cache aggiornata con dati server")
            print("📡 Workflow continua: cache check → MQTT send → broker → gate-verification")
        else:
            print("❌ Cache refresh FAILED - carta non trovata su server o errore")
            print("🚫 Workflow: accesso negato")
        
        print("\n2️⃣ TEST: Verifica che non sia stata chiamata gate-verification")
        print("-" * 40)
        
        # Verifica che il metodo refresh NON contenga più chiamate a gate-verification
        import inspect
        source = inspect.getsource(refresh_mgr.handle_denied_card_refresh)
        
        if "gate_verification" in source or "_try_gate_verification" in source:
            print("❌ ERRORE: Cache refresh ancora contiene chiamate a gate-verification!")
            print("⚠️  Workflow NON corretto - bypass del broker MQTT")
            return False
        else:
            print("✅ CORRETTO: Cache refresh NON chiama gate-verification")
            print("✅ Workflow corretto: cache refresh → MQTT → broker → gate-verification")
        
        print("\n3️⃣ TEST: Verifica che usi solo sync endpoint")
        print("-" * 40)
        
        if "_try_sync_endpoint" in source:
            print("✅ CORRETTO: Cache refresh usa solo sync endpoint per dati")
            print("💾 Separazione delle responsabilità: refresh = aggiorna cache")
        else:
            print("❌ ERRORE: Cache refresh non usa sync endpoint")
            return False
        
        print("\n🎯 RIASSUNTO WORKFLOW CORRETTO:")
        print("-" * 40)
        print("1. Carta negata da cache locale")
        print("2. Cache refresh → scarica dati server → aggiorna cache")
        print("3. Sistema ricontrolla cache aggiornata")
        print("4. Se cache OK → MQTT send → broker chiama gate-verification")
        print("5. Broker restituisce decisione finale di autorizzazione")
        print("\n✅ Flusso autorizzazione SEMPRE passa per broker MQTT")
        print("✅ Cache refresh = solo update dati, NON autorizzazione")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        return False

async def main():
    success = await test_corrected_workflow()
    
    if success:
        print(f"\n🎉 TEST COMPLETATO CON SUCCESSO")
        print("✅ Workflow cache refresh corretto e sicuro")
    else:
        print(f"\n❌ TEST FALLITO")
        print("⚠️  Necessarie correzioni al workflow")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)