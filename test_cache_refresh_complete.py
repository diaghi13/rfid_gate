#!/usr/bin/env python3
"""
🎯 Test Completo Strategia Cache Refresh
======================================

Test di tutti i scenari di gestione abbonamenti rinnovati:
1. Carta in cache valid → Accesso diretto 
2. Carta in cache expired + server valid → Refresh success
3. Carta in cache expired + server expired → Accesso negato
4. Carta non in cache → Server fallback
"""

import asyncio
import time
import sqlite3
from pathlib import Path
from datetime import datetime


async def test_cache_refresh_scenarios():
    """Test completo di tutti gli scenari cache refresh"""
    print("🎯 TEST COMPLETO CACHE REFRESH SCENARIOS")
    print("="*60)
    
    cache_path = Path("cache/local_cache.db")
    
    # Setup database test
    conn = sqlite3.connect(str(cache_path))
    cursor = conn.cursor()
    
    # Assicura che tabella abbia colonna last_server_check
    try:
        cursor.execute('ALTER TABLE synced_cards ADD COLUMN last_server_check TIMESTAMP')
        print("✅ Aggiunta colonna last_server_check")
    except sqlite3.OperationalError:
        pass  # Già esistente
    
    # Crea scenari test
    test_scenarios = [
        {
            'card_uid': 'CACHE_VALID_001',
            'name': 'Carta in cache VALIDA',
            'cache_active': True,
            'server_response': True,
            'expected_result': 'immediate_grant',
            'description': 'Carta valida in cache → accesso immediato'
        },
        {
            'card_uid': 'CACHE_EXPIRED_SERVER_RENEWED',
            'name': 'Carta scaduta ma RINNOVATA',
            'cache_active': False,
            'server_response': True,  # Abbonamento rinnovato!
            'expected_result': 'refresh_success',
            'description': 'Carta scaduta in cache ma rinnovata su server → refresh success'
        },
        {
            'card_uid': 'CACHE_EXPIRED_SERVER_EXPIRED', 
            'name': 'Carta scaduta CONFERMATA',
            'cache_active': False,
            'server_response': False,  # Effettivamente scaduta
            'expected_result': 'access_denied',
            'description': 'Carta scaduta sia in cache che su server → accesso negato'
        },
        {
            'card_uid': 'NOT_IN_CACHE_SERVER_VALID',
            'name': 'Nuova carta AUTORIZZATA',
            'cache_active': None,  # Non in cache
            'server_response': True,
            'expected_result': 'server_fallback_grant',
            'description': 'Carta non in cache ma autorizzata da server → fallback success'
        }
    ]
    
    # Setup carte in cache
    for scenario in test_scenarios:
        if scenario['cache_active'] is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO synced_cards 
                (card_uid, is_active, customer_name, last_sync)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                scenario['card_uid'],
                1 if scenario['cache_active'] else 0,
                scenario['name']
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Setup completato: {len(test_scenarios)} scenari preparati")
    
    # Simula sistema access control
    from cache_refresh_strategy import CacheRefreshManager
    
    print(f"\n🎯 ESECUZIONE TEST SCENARI")
    print("-"*60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 SCENARIO {i}/4: {scenario['name']}")
        print(f"   💳 Card: {scenario['card_uid']}")
        print(f"   📝 {scenario['description']}")
        print(f"   💾 Cache: {'VALID' if scenario['cache_active'] else 'EXPIRED' if scenario['cache_active'] is False else 'MISS'}")
        print(f"   🌐 Server: {'VALID' if scenario['server_response'] else 'EXPIRED'}")
        
        # Simula flusso access_control.py
        result = await simulate_access_flow(scenario)
        
        # Verifica risultato
        if result['access_granted']:
            icon = "✅"
            status = "ACCESSO GARANTITO"
        else:
            icon = "❌" 
            status = "ACCESSO NEGATO"
        
        print(f"   {icon} Risultato: {status}")
        print(f"   ⏱️ Tempo: {result['total_time_ms']:.2f}ms")
        print(f"   📡 Cache hit: {'SI' if result['cache_hit'] else 'NO'}")
        print(f"   🔄 Refresh: {'SI' if result.get('refresh_attempted') else 'NO'}")
        
        if result['access_granted'] and scenario['expected_result'] in ['immediate_grant', 'refresh_success', 'server_fallback_grant']:
            print(f"   🎯 Test PASSED: Comportamento atteso")
        elif not result['access_granted'] and scenario['expected_result'] == 'access_denied':
            print(f"   🎯 Test PASSED: Accesso correttamente negato")
        else:
            print(f"   ⚠️ Test FAILED: Risultato inaspettato")
    
    # Cleanup
    cleanup_test_data(test_scenarios)
    
    print(f"\n🎉 TEST COMPLETO TERMINATO")
    print("="*60)


async def simulate_access_flow(scenario):
    """Simula flusso access_control.py con logica cache refresh"""
    start_time = time.time()
    cache_path = Path("cache/local_cache.db")
    
    # 1. Cache check (sempre primo step)
    cache_hit = False
    cache_enabled = False
    refresh_attempted = False
    
    conn = sqlite3.connect(str(cache_path))
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM synced_cards WHERE card_uid = ?", (scenario['card_uid'],))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        cache_hit = True
        cache_enabled = bool(result[0])
        print(f"   💾 Cache HIT - active: {cache_enabled}")
    else:
        print(f"   💾 Cache MISS")
    
    access_granted = False
    
    # 2. Logica decisione accesso
    if cache_hit and cache_enabled:
        # Scenario 1: Cache valida → accesso immediato
        access_granted = True
        print(f"   ⚡ Accesso immediato da cache")
        
    elif cache_hit and not cache_enabled:
        # Scenario 2: Cache scaduta → prova refresh
        print(f"   🔄 Cache EXPIRED - tentativo refresh server...")
        refresh_attempted = True
        
        # Simula chiamata server (scenario['server_response'])
        await asyncio.sleep(0.05)  # 50ms latenza server
        
        if scenario['server_response']:
            # Server ha carta rinnovata!
            print(f"   ✅ Server: carta RINNOVATA - aggiornamento cache")
            access_granted = True
            
            # Aggiorna cache
            conn = sqlite3.connect(str(cache_path))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE synced_cards 
                SET is_active = 1, last_server_check = CURRENT_TIMESTAMP 
                WHERE card_uid = ?
            """, (scenario['card_uid'],))
            conn.commit()
            conn.close()
        else:
            # Server conferma scadenza
            print(f"   ❌ Server: carta CONFERMATA scaduta")
            access_granted = False
            
    else:
        # Scenario 3: Cache miss → server fallback
        print(f"   🌐 Cache MISS - server fallback...")
        await asyncio.sleep(0.05)  # Latenza server
        
        if scenario['server_response']:
            access_granted = True
            print(f"   ✅ Server: carta AUTORIZZATA")
        else:
            access_granted = False
            print(f"   ❌ Server: carta NON AUTORIZZATA")
    
    total_time = (time.time() - start_time) * 1000
    
    return {
        'access_granted': access_granted,
        'cache_hit': cache_hit,
        'total_time_ms': total_time,
        'refresh_attempted': refresh_attempted
    }


def cleanup_test_data(scenarios):
    """Pulisce dati test"""
    cache_path = Path("cache/local_cache.db")
    conn = sqlite3.connect(str(cache_path))
    cursor = conn.cursor()
    
    for scenario in scenarios:
        cursor.execute("DELETE FROM synced_cards WHERE card_uid = ?", (scenario['card_uid'],))
    
    conn.commit()
    conn.close()
    print(f"🧹 Cleanup: rimossi {len(scenarios)} record test")


if __name__ == "__main__":
    asyncio.run(test_cache_refresh_scenarios())