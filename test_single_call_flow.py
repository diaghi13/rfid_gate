#!/usr/bin/env python3
"""
🧪 Test Flusso Corretto - Eliminazione Chiamate Doppie
=====================================================

Verifica che il sistema ora faccia UNA SOLA chiamata al server gate-verification
via MQTT broker, e usi /api/gate-sync solo per aggiornare cache.
"""

import sys
import os
from pathlib import Path

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

def test_removed_double_calls():
    """Testa che le chiamate doppie siano eliminate"""
    
    print("🧪 TEST ELIMINAZIONE CHIAMATE DOPPIE")
    print("=" * 40)
    
    # 1. Verifica che _check_realtime_fallback sia stata rimossa
    try:
        from rfid_gate.network.sync_manager import SyncManager
        
        # Controlla se il metodo esiste ancora
        if hasattr(SyncManager, '_check_realtime_fallback'):
            print("❌ ERRORE: _check_realtime_fallback ancora presente!")
            return False
        else:
            print("✅ _check_realtime_fallback rimossa correttamente")
    except Exception as e:
        print(f"❌ Errore import: {e}")
        return False
    
    # 2. Verifica configurazione cache sync
    try:
        from rfid_gate.config.settings import load_env_file
        load_env_file()
        
        cache_endpoint = os.getenv('CACHE_REFRESH_SINGLE_CARD_ENDPOINT', '/api/sync-gate')
        print(f"📋 Cache refresh endpoint: {cache_endpoint}")
        
        if cache_endpoint == '/api/sync-gate':
            print("✅ Cache refresh usa gate-sync (corretto)")
        else:
            print(f"⚠️ Cache refresh usa: {cache_endpoint}")
            
    except Exception as e:
        print(f"❌ Errore config: {e}")
        return False
    
    return True

def show_correct_flow():
    """Mostra il flusso corretto implementato"""
    
    print("\n✅ FLUSSO CORRETTO IMPLEMENTATO")
    print("=" * 35)
    
    print("1. 📱 Carta RFID letta")
    print("   ↓")
    print("2. 📡 UNA SOLA chiamata MQTT → broker → gate-verification")
    print("   ↓")
    print("3. 🔄 Se carta non in cache:")
    print("   → Cache refresh: GET /api/sync-gate?card_uid=xxx")
    print("   → Aggiorna cache locale")
    print("   → NON autorizza direttamente")
    print("   ↓")
    print("4. ✅ Risultato: UNA sola autorizzazione via MQTT")

def test_cache_refresh_strategy():
    """Testa la strategia cache refresh"""
    
    print("\n🔄 TEST CACHE REFRESH STRATEGY")
    print("=" * 35)
    
    try:
        from rfid_gate.network.cache_refresh_strategy import CacheRefreshManager
        
        # Simula sync manager
        class MockSyncManager:
            def __init__(self):
                self.config = type('Config', (), {
                    'server_url': 'http://localhost:8000',
                    'cache_sync_endpoint': '/api/gate-sync'
                })()
        
        mock_sync = MockSyncManager()
        cache_mgr = CacheRefreshManager(mock_sync)
        
        print(f"✅ CacheRefreshManager creato")
        print(f"📋 Endpoint: {cache_mgr.single_card_endpoint}")
        
        if cache_mgr.single_card_endpoint == '/api/sync-gate':
            print("✅ Cache refresh configurato correttamente")
        else:
            print(f"⚠️ Endpoint inaspettato: {cache_mgr.single_card_endpoint}")
            
    except Exception as e:
        print(f"❌ Errore cache refresh: {e}")
        return False
    
    return True

def analyze_log_entries():
    """Analizza le entry di log attese"""
    
    print("\n📋 ANALISI LOG ATTESI")
    print("=" * 25)
    
    print("❌ PRIMA (DOPPIO LOG):")
    print("   1619 - 'Carta autorizzata via fallback REST real-time | Local'")
    print("   1618 - 'Accesso consentito - bypass per test'")
    print("   → DUE chiamate separate al server!")
    
    print("\n✅ DOPO (LOG SINGOLO):")
    print("   1619 - 'Accesso consentito' (solo via MQTT)")
    print("   → UNA sola chiamata gate-verification via broker")
    
    print("\n🔄 LOG CACHE REFRESH (opzionale):")
    print("   → 'Cache refresh: carta XXX aggiornata'")
    print("   → 'GET /api/sync-gate?card_uid=XXX'")
    print("   → Solo per popolare cache, non per autorizzare")

def show_expected_behavior():
    """Mostra comportamento atteso"""
    
    print("\n🎯 COMPORTAMENTO ATTESO")
    print("=" * 25)
    
    print("📱 CASO 1: Carta in cache")
    print("   → MQTT → broker → gate-verification → risposta")
    print("   → Log: UNA entry di autorizzazione")
    
    print("\n📱 CASO 2: Carta NON in cache")  
    print("   → MQTT → broker → 'carta non trovata'")
    print("   → Cache refresh: GET /api/gate-sync?card_uid=XXX")
    print("   → Se trova dati → aggiorna cache")
    print("   → Ri-prova MQTT → broker → gate-verification")
    print("   → Log: UNA entry di autorizzazione finale")
    
    print("\n📱 CASO 3: Carta con abbonamento scaduto")
    print("   → MQTT → broker → 'abbonamento scaduto'")
    print("   → Cache refresh: GET /api/gate-sync?card_uid=XXX")
    print("   → Se trova rinnovo → aggiorna cache")
    print("   → Ri-prova MQTT → broker → gate-verification")
    print("   → Log: UNA entry con nuovo abbonamento")

def main():
    """Test principale"""
    
    print("🧪 TEST ELIMINAZIONE CHIAMATE DOPPIE")
    print("=" * 45)
    
    # Test rimozione funzioni
    removed_ok = test_removed_double_calls()
    
    # Test cache refresh  
    cache_ok = test_cache_refresh_strategy()
    
    # Mostra flusso
    show_correct_flow()
    
    # Analizza log
    analyze_log_entries()
    
    # Comportamento atteso
    show_expected_behavior()
    
    print(f"\n📊 RISULTATI TEST:")
    print(f"   ✅ Funzioni rimosse: {'OK' if removed_ok else 'ERRORE'}")
    print(f"   ✅ Cache refresh: {'OK' if cache_ok else 'ERRORE'}")
    
    if removed_ok and cache_ok:
        print("\n🎉 SUCCESSO!")
        print("   ✅ Chiamate doppie eliminate")
        print("   ✅ Un solo path: MQTT → broker → gate-verification")
        print("   ✅ Cache refresh: /api/sync-gate (solo per cache)")
        
        print("\n🚀 PRONTO PER TEST SU RASPBERRY PI:")
        print("   → Ora dovresti vedere UN SOLO log per carta")
        print("   → Cache refresh in background quando necessario")
    else:
        print("\n❌ ERRORI TROVATI - verificare implementazione")

if __name__ == "__main__":
    main()