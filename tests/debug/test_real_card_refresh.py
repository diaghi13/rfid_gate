#!/usr/bin/env python3
"""
🧪 Test Cache Refresh con Carta Reale
===================================

Test del sistema cache refresh usando una carta reale del server
"""

import asyncio
import sqlite3
from pathlib import Path
from cache_refresh_strategy import CacheRefreshManager
from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import RFIDGateConfig


async def test_real_card_refresh():
    """Test cache refresh con carta reale"""
    print("🧪 TEST CACHE REFRESH - CARTA REALE")
    print("="*50)
    
    # Usa una carta reale dal test precedente
    real_card_uid = "02D9BAEB"  # STEFANO TOMMASETTI con subscription attiva
    
    cache_path = Path("cache/local_cache.db")
    
    # 1. Setup: Metti carta in cache come SCADUTA
    print(f"🔧 Setup: Carta {real_card_uid} in cache come SCADUTA")
    
    conn = sqlite3.connect(str(cache_path))
    cursor = conn.cursor()
    
    # Assicura che tabella abbia colonna last_server_check
    try:
        cursor.execute('ALTER TABLE synced_cards ADD COLUMN last_server_check TIMESTAMP')
    except sqlite3.OperationalError:
        pass  # Già esistente
    
    # Inserisci carta come scaduta
    cursor.execute("""
        INSERT OR REPLACE INTO synced_cards 
        (card_uid, is_active, customer_name, last_sync)
        VALUES (?, 0, 'STEFANO TOMMASETTI (SCADUTO)', CURRENT_TIMESTAMP)
    """, (real_card_uid,))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Carta inserita in cache come SCADUTA")
    
    # 2. Test Cache Refresh
    print(f"\n🔄 Test Cache Refresh...")
    
    config = RFIDGateConfig.from_env()
    sync_manager = SyncManager(config.sync, config.system.tornello_id)
    refresh_mgr = CacheRefreshManager(sync_manager)
    
    result = await refresh_mgr.handle_denied_card_refresh(real_card_uid)
    
    if result:
        print(f"✅ REFRESH RIUSCITO - Carta ora autorizzata!")
        
        # Verifica stato cache aggiornato
        conn = sqlite3.connect(str(cache_path))
        cursor = conn.cursor()
        cursor.execute("SELECT is_active, customer_name FROM synced_cards WHERE card_uid = ?", (real_card_uid,))
        cache_result = cursor.fetchone()
        conn.close()
        
        if cache_result:
            active, name = cache_result
            print(f"📋 Cache aggiornata:")
            print(f"   Stato: {'ATTIVA' if active else 'INATTIVA'}")
            print(f"   Nome: {name}")
        
    else:
        print(f"❌ REFRESH FALLITO - Carta ancora negata")
    
    # 3. Cleanup
    print(f"\n🧹 Cleanup...")
    conn = sqlite3.connect(str(cache_path))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM synced_cards WHERE card_uid = ?", (real_card_uid,))
    conn.commit()
    conn.close()
    
    print(f"✅ Test completato")


if __name__ == "__main__":
    asyncio.run(test_real_card_refresh())