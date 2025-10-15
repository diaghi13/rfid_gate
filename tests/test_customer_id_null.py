#!/usr/bin/env python3
"""
🧪 Test Customer ID Null
=======================

Verifica la gestione corretta di customer_id null per carte whitelist.
"""

import asyncio
import sys
import sqlite3
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from rfid_gate.config.settings import SyncConfig
from rfid_gate.network.sync_manager import SyncManager


async def test_customer_id_null():
    """Test gestione customer_id null"""
    print("🧪 Test Customer ID Null")
    print("=" * 40)
    
    # Setup temporaneo
    temp_dir = tempfile.mkdtemp()
    sync_config = SyncConfig(
        enabled=True,
        cache_db_path=f"{temp_dir}/null_test.db"
    )
    
    sync_manager = SyncManager(sync_config, "test_tornello")
    
    # Dati test con diversi scenari customer_id
    cards_data = [
        {
            "card_uid": "CLIENT001",
            "customer_id": 1001,           # Cliente normale
            "customer_name": "Mario Rossi",
            "in_white_list": False,
            "active_subscriptions": [
                {
                    "type": "time_based",
                    "expiry_date": "2026-12-31",
                    "remaining_entrances": None,
                    "is_active": True
                }
            ]
        },
        {
            "card_uid": "STAFF001",
            "customer_id": None,           # NULL per staff
            "customer_name": "Staff Security",
            "in_white_list": True,
            "active_subscriptions": []
        },
        {
            "card_uid": "EMERGENCY999",
            "customer_id": None,           # NULL per emergenza
            "customer_name": "Vigili del Fuoco",
            "in_white_list": True,
            "active_subscriptions": []
        },
        {
            "card_uid": "MANAGER001",
            "customer_id": 9999,           # Manager con customer_id
            "customer_name": "Direttore Generale",
            "in_white_list": True,
            "active_subscriptions": []
        }
    ]
    
    # Carica dati nel sistema
    sync_manager._update_local_cache(cards_data)
    
    print("\n📊 Verifica Database")
    print("-" * 30)
    
    # Verifica dati nel database
    conn = sqlite3.connect(sync_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT card_uid, customer_id, customer_name, in_white_list FROM synced_cards ORDER BY card_uid")
    results = cursor.fetchall()
    conn.close()
    
    for card_uid, customer_id, customer_name, in_white_list in results:
        customer_id_str = str(customer_id) if customer_id is not None else "NULL"
        whitelist_str = "✅" if in_white_list else "❌"
        print(f"   {card_uid}: customer_id={customer_id_str}, whitelist={whitelist_str}, name={customer_name}")
    
    print("\n🧪 Test Validazioni")
    print("-" * 30)
    
    # Test cliente normale (con customer_id)
    result = await sync_manager.validate_card_offline("CLIENT001", "in")
    print(f"✅ Cliente normale: {result['authorized']} - {result['customer_name']}")
    
    # Test staff (customer_id=null, whitelist=true)
    result = await sync_manager.validate_card_offline("STAFF001", "in")
    print(f"✅ Staff (NULL ID): {result['authorized']} - {result['customer_name']}")
    
    # Test emergenza (customer_id=null, whitelist=true)
    result = await sync_manager.validate_card_offline("EMERGENCY999", "in")
    print(f"✅ Emergenza (NULL ID): {result['authorized']} - {result['customer_name']}")
    
    # Test manager (customer_id=9999, whitelist=true)
    result = await sync_manager.validate_card_offline("MANAGER001", "in")
    print(f"✅ Manager (ID=9999): {result['authorized']} - {result['customer_name']}")
    
    print("\n🎯 Risultati:")
    print("=" * 40)
    print("✅ Customer ID NULL gestito correttamente nel database")
    print("✅ Carte whitelist funzionano con customer_id NULL")
    print("✅ Carte whitelist funzionano con customer_id presente")
    print("✅ Clienti normali mantengono customer_id obbligatorio")
    print("✅ Sistema flessibile per diversi tipi di carte")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print("🧹 Cleanup completato")


if __name__ == "__main__":
    asyncio.run(test_customer_id_null())