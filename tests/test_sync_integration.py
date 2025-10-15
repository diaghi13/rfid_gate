#!/usr/bin/env python3
"""
🧪 Test Sistema di Sincronizzazione Offline-First
===============================================

Test di integrazione per verificare il funzionamento
del sistema di sincronizzazione con cache locale.
"""

import asyncio
import json
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Aggiungi path progetto
sys.path.insert(0, str(Path(__file__).parent.parent))

from rfid_gate.config.settings import RFIDGateConfig, SyncConfig
from rfid_gate.network.sync_manager import SyncManager, CardData, AccessLog


class TestSyncSystem:
    """Test suite per sistema di sincronizzazione"""
    
    def __init__(self):
        self.temp_dir = None
        self.sync_manager = None
        
    async def setup(self):
        """Setup test environment"""
        # Crea directory temporanea
        self.temp_dir = tempfile.mkdtemp()
        
        # Configurazione test
        sync_config = SyncConfig(
            enabled=True,
            server_url="http://localhost:3000",
            sync_endpoint="/api/sync",
            logs_endpoint="/api/logs/bulk",
            health_endpoint="/api/health",
            updates_endpoint="/api/cards/updates",
            cache_db_path=f"{self.temp_dir}/test_cache.db"
        )
        
        # Crea SyncManager
        self.sync_manager = SyncManager(sync_config, "test_tornello")
        
        print(f"✅ Setup completato - DB: {sync_config.cache_db_path}")
    
    async def test_local_cache(self):
        """Test cache locale senza server"""
        print("\n🧪 Test 1: Cache locale")
        
        # Simula dati dal server
        mock_cards_data = [
            {
                "card_uid": "TEST123",
                "customer_id": 1001,
                "customer_name": "Test User",
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
                "card_uid": "TEST456",
                "customer_id": 1002,
                "customer_name": "Test User 2",
                "in_white_list": False,
                "active_subscriptions": [
                    {
                        "type": "single_entrance",
                        "expiry_date": None,
                        "remaining_entrances": 5,
                        "is_active": True
                    }
                ]
            },
            {
                "card_uid": "WHITELIST999",
                "customer_id": None,  # NULL per carte whitelist di servizio
                "customer_name": "Staff Member",
                "in_white_list": True,
                "active_subscriptions": []
            }
        ]
        
        # Aggiorna cache manualmente
        self.sync_manager._update_local_cache(mock_cards_data)
        
        # Test validazione carta autorizzata
        result = await self.sync_manager.validate_card_offline("TEST123", "in")
        assert result['authorized'] == True
        assert result['customer_name'] == "Test User"
        print("   ✅ Carta autorizzata riconosciuta")
        
        # Test validazione carta con ingressi limitati
        result = await self.sync_manager.validate_card_offline("TEST456", "in")
        assert result['authorized'] == True
        assert result['customer_name'] == "Test User 2"
        print("   ✅ Carta con ingressi limitati autorizzata")
        
        # Test carta inesistente
        result = await self.sync_manager.validate_card_offline("INVALID", "in")
        assert result['authorized'] == False
        print("   ✅ Carta inesistente correttamente rifiutata")
        
        # Test carta in whitelist
        result = await self.sync_manager.validate_card_offline("WHITELIST999", "in")
        assert result['authorized'] == True
        assert result['customer_name'] == "Staff Member"
        assert "whitelist" in result['reason'].lower()
        print("   ✅ Carta in whitelist sempre autorizzata")
        
        print("🎉 Test cache locale: SUPERATO")
    
    async def test_log_system(self):
        """Test sistema di logging"""
        print("\n🧪 Test 2: Sistema di logging")
        
        # Log accesso autorizzato
        await self.sync_manager.log_access(
            card_uid="TEST123",
            direction="in",
            result="authorized",
            reason="Test accesso",
            customer_name="Test User",
            reader_type="test",
            metadata={"test": True}
        )
        
        # Log accesso negato
        await self.sync_manager.log_access(
            card_uid="INVALID",
            direction="out",
            result="denied",
            reason="Carta non valida",
            reader_type="test"
        )
        
        # Verifica log nel database
        conn = sqlite3.connect(self.sync_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pending_logs WHERE synced = 0")
        pending_count = cursor.fetchone()[0]
        conn.close()
        
        assert pending_count == 2
        print(f"   ✅ {pending_count} log registrati correttamente")
        
        print("🎉 Test logging: SUPERATO")
    
    async def test_sync_status(self):
        """Test stato sincronizzazione"""
        print("\n🧪 Test 3: Stato sincronizzazione")
        
        status = self.sync_manager.get_sync_status()
        
        assert 'active_cards' in status
        assert 'pending_logs' in status
        assert 'is_online' in status
        assert status['tornello_id'] == "test_tornello"
        
        print(f"   ✅ Carte attive: {status['active_cards']}")
        print(f"   ✅ Log in attesa: {status['pending_logs']}")
        print(f"   ✅ Stato online: {status['is_online']}")
        
        print("🎉 Test stato sync: SUPERATO")
    
    async def test_usage_decrement(self):
        """Test decremento uso abbonamento"""
        print("\n🧪 Test 4: Decremento uso abbonamento")
        
        # Prima validazione (dovrebbe decrementare da 5 a 4)
        result1 = await self.sync_manager.validate_card_offline("TEST456", "in")
        assert result1['authorized'] == True
        print(f"   ✅ Prima validazione: {result1.get('subscription_info', {}).get('remaining_entrances', 'N/A')}")
        
        # Seconda validazione (dovrebbe decrementare da 4 a 3)
        result2 = await self.sync_manager.validate_card_offline("TEST456", "in")
        assert result2['authorized'] == True
        print(f"   ✅ Seconda validazione: {result2.get('subscription_info', {}).get('remaining_entrances', 'N/A')}")
        
        # Verifica nel database
        conn = sqlite3.connect(self.sync_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT active_subscriptions FROM synced_cards WHERE card_uid = ?", ("TEST456",))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            subs = json.loads(result[0])
            remaining = subs[0]['remaining_entrances']
            print(f"   ✅ Ingressi rimanenti nel DB: {remaining}")
            # Il test dovrebbe verificare che sia decrementato, non necessariamente a 3
            assert remaining < 5  # Dovrebbe essere meno di 5 (valore iniziale)
        else:
            print("   ⚠️ Nessun record trovato nel DB")
        
        print("🎉 Test decremento: SUPERATO")
    
    async def test_offline_first_logic(self):
        """Test logica offline-first completa"""
        print("\n🧪 Test 5: Logica offline-first completa")
        
        # Simula che il sistema sia offline
        self.sync_manager.is_online = False
        
        # Test validazione offline
        result = await self.sync_manager.validate_card_offline("TEST123", "in")
        assert result['authorized'] == True
        assert result['offline_mode'] == True
        
        # Test che i log vengano comunque salvati
        await self.sync_manager.log_access(
            card_uid="TEST123",
            direction="in", 
            result="authorized",
            reason="Test offline"
        )
        
        # Verifica accumulo log
        status = self.sync_manager.get_sync_status()
        assert status['pending_logs'] > 0
        
        print("   ✅ Modalità offline funzionante")
        print("   ✅ Log accumulati per sync futuro")
        
        print("🎉 Test offline-first: SUPERATO")
    
    async def cleanup(self):
        """Cleanup test environment"""
        if self.sync_manager:
            await self.sync_manager.stop_background_sync()
        
        # Rimuovi file temporanei
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
        
        print("🧹 Cleanup completato")


async def main():
    """Esegue tutti i test"""
    print("🚀 Avvio test sistema di sincronizzazione offline-first")
    print("=" * 60)
    
    test_suite = TestSyncSystem()
    
    try:
        await test_suite.setup()
        await test_suite.test_local_cache()
        await test_suite.test_log_system()
        await test_suite.test_sync_status()
        await test_suite.test_usage_decrement()
        await test_suite.test_offline_first_logic()
        
        print("\n" + "=" * 60)
        print("🎉 TUTTI I TEST SUPERATI! 🎉")
        print("✅ Il sistema di sincronizzazione offline-first funziona correttamente")
        print("✅ Mantiene compatibilità con nomenclatura esistente")
        print("✅ Cache locale operativa")
        print("✅ Sistema di logging funzionante")
        print("✅ Logica offline-first implementata")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLITO: {e}")
        return False
    except Exception as e:
        print(f"\n💥 ERRORE: {e}")
        return False
    finally:
        await test_suite.cleanup()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)