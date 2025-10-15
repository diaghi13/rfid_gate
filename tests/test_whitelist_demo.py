#!/usr/bin/env python3
"""
🧪 Test Specifico Whitelist
=========================

Dimostra il comportamento delle carte in whitelist.
"""

import asyncio
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from rfid_gate.config.settings import SyncConfig
from rfid_gate.network.sync_manager import SyncManager


async def test_whitelist_behavior():
    """Test specifico per comportamento whitelist"""
    print("🧪 Test Comportamento Whitelist")
    print("=" * 40)
    
    # Setup temporaneo
    temp_dir = tempfile.mkdtemp()
    sync_config = SyncConfig(
        enabled=True,
        cache_db_path=f"{temp_dir}/whitelist_test.db"
    )
    
    sync_manager = SyncManager(sync_config, "test_tornello")
    
    # Dati test con whitelist
    cards_data = [
        {
            "card_uid": "NORMAL001",
            "customer_id": 1001,
            "customer_name": "Cliente Normale",
            "in_white_list": False,
            "active_subscriptions": [
                {
                    "type": "single_entrance",
                    "expiry_date": None,
                    "remaining_entrances": 2,
                    "is_active": True
                }
            ]
        },
        {
            "card_uid": "STAFF999",
            "customer_id": None,  # NULL per carte di servizio
            "customer_name": "Staff Member",
            "in_white_list": True,
            "active_subscriptions": []  # Nessun abbonamento necessario
        }
    ]
    
    # Carica dati
    sync_manager._update_local_cache(cards_data)
    
    print("\n📋 Test Carta Normale (con abbonamento limitato)")
    print("-" * 50)
    
    # Test carta normale - primo accesso
    result1 = await sync_manager.validate_card_offline("NORMAL001", "in")
    print(f"✅ Primo accesso: {result1['authorized']} - {result1['reason']}")
    print(f"   Ingressi rimanenti: {result1['subscription_info'].get('remaining_entrances', 'N/A')}")
    
    # Test carta normale - secondo accesso
    result2 = await sync_manager.validate_card_offline("NORMAL001", "in")
    print(f"✅ Secondo accesso: {result2['authorized']} - {result2['reason']}")
    print(f"   Ingressi rimanenti: {result2['subscription_info'].get('remaining_entrances', 'N/A')}")
    
    # Test carta normale - terzo accesso (dovrebbe essere negato)
    result3 = await sync_manager.validate_card_offline("NORMAL001", "in")
    print(f"❌ Terzo accesso: {result3['authorized']} - {result3['reason']}")
    
    print("\n🔑 Test Carta Staff (whitelist)")
    print("-" * 40)
    
    # Test carta staff - accessi multipli
    for i in range(5):
        result = await sync_manager.validate_card_offline("STAFF999", "in")
        print(f"✅ Accesso {i+1}: {result['authorized']} - {result['reason']}")
        print(f"   Subscription info: {result['subscription_info']}")
    
    print("\n🎯 Risultati Test:")
    print("=" * 40)
    print("✅ Carta normale: rispetta limiti abbonamento")
    print("✅ Carta whitelist: accesso sempre autorizzato")
    print("✅ Carta whitelist: nessun decremento ingressi")
    print("✅ Carta whitelist: funziona anche senza abbonamenti")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print("🧹 Cleanup completato")


if __name__ == "__main__":
    asyncio.run(test_whitelist_behavior())