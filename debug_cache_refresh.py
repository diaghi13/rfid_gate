#!/usr/bin/env python3
"""
🔍 Debug Cache Refresh Workflow
==============================
Verifica perché la cache refresh non viene attivata quando serve.
"""

import sys
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

def debug_cache_refresh_conditions():
    """Debug condizioni per cache refresh"""
    
    print("🔍 Debug Cache Refresh Workflow")
    print("=" * 50)
    
    print("📋 CONDIZIONI PER CACHE REFRESH:")
    print("1. sync_result['authorized'] = False (carta negata da cache)")
    print("2. self.mode == SystemMode.ONLINE (sistema online)")
    print("3. CACHE_REFRESH_ENABLED=true (configurazione)")
    print()
    
    print("🔧 VERIFICA CONFIGURAZIONE:")
    
    # Controlla configurazione cache refresh
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        cache_enabled = os.getenv('CACHE_REFRESH_ENABLED', 'false').lower() == 'true'
        offline_allow = os.getenv('OFFLINE_ALLOW_ACCESS', 'true').lower() == 'true'
        auth_enabled = os.getenv('AUTH_ENABLED', 'true').lower() == 'true'
        
        print(f"   CACHE_REFRESH_ENABLED: {cache_enabled}")
        print(f"   OFFLINE_ALLOW_ACCESS: {offline_allow}")
        print(f"   AUTH_ENABLED: {auth_enabled}")
        print()
        
        print("🔍 POSSIBILI PROBLEMI:")
        
        if not cache_enabled:
            print("❌ CACHE_REFRESH_ENABLED=false - Cache refresh disabilitata!")
        else:
            print("✅ CACHE_REFRESH_ENABLED=true - OK")
            
        if offline_allow:
            print("⚠️  OFFLINE_ALLOW_ACCESS=true - Potrebbe bypassare la cache")
            print("   Questo significa che se MQTT fallisce, il sistema da accesso")
            print("   senza controllare la cache, quindi cache refresh non viene mai chiamata")
        else:
            print("✅ OFFLINE_ALLOW_ACCESS=false - Cache sarà controllata")
            
        if not auth_enabled:
            print("❌ AUTH_ENABLED=false - Nessuna autenticazione, cache refresh inutile")
        else:
            print("✅ AUTH_ENABLED=true - OK")
            
        print()
        print("🎯 SCENARI CACHE REFRESH:")
        print("1. Sistema ONLINE + Carta in cache NEGATA → Cache refresh SI")
        print("2. Sistema OFFLINE + OFFLINE_ALLOW_ACCESS=true → Cache refresh NO (bypass)")
        print("3. Sistema OFFLINE + OFFLINE_ALLOW_ACCESS=false → Cache refresh NO (offline)")
        print("4. AUTH_ENABLED=false → Cache refresh NO (no auth)")
        print()
        
        print("🔧 PER FORZARE CACHE REFRESH TEST:")
        print("Temporaneamente imposta:")
        print("   OFFLINE_ALLOW_ACCESS=false")
        print("   AUTH_ENABLED=true")
        print("   CACHE_REFRESH_ENABLED=true")
        print("E testa con una carta che sai essere scaduta/rinnovata")
        
    except Exception as e:
        print(f"❌ Errore verifica config: {e}")

def test_scenario_description():
    """Descrivi lo scenario del problema"""
    
    print("\n📝 SCENARIO DEL PROBLEMA:")
    print("=" * 50)
    print("1. Abbonamento scade → Carta negata (corretto)")
    print("2. Abbonamento rinnovato → Server ha dati aggiornati")
    print("3. Sistema ha vecchi dati in cache → Carta ancora negata")
    print("4. Cache refresh DOVREBBE aggiornare cache → Carta autorizzata")
    print()
    print("❓ DOMANDA: Nei log vedi questa riga?")
    print("   '🔄 Carta XXXXXXXX negata dalla cache - tentativo refresh server...'")
    print()
    print("Se NON vedi questa riga, significa che:")
    print("- Il sistema non sta controllando la cache")
    print("- O il sistema è in modalità offline con bypass")
    print("- O l'autenticazione è disabilitata")

if __name__ == "__main__":
    debug_cache_refresh_conditions()
    test_scenario_description()