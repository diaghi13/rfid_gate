#!/usr/bin/env python3
"""
🔥 Test Real-time Fallback per Gap Sync Resolution

Simula il scenario critico:
1. Sistema online con cache sync di 15 minuti 
2. Carta nuova registrata sul server (ma non ancora in cache locale)
3. Accesso immediato - dovrebbe usare fallback real-time
4. Verifica che la carta viene trovata e cached

Questo test simula il server endpoint /api/cards/validate/{card_uid}
"""

import asyncio
import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Aggiungi path per import
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import SyncConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockRealTimeServer:
    """
    Simula server con endpoint /api/cards/validate/{card_uid}
    per testare il fallback real-time
    """
    
    def __init__(self):
        # Simula database server con carte registrate di recente
        self.server_cards = {
            "NEWCARD001": {
                "card_uid": "NEWCARD001", 
                "customer_id": 9999,
                "customer_name": "Test User Real-time",
                "in_white_list": False,
                "active_subscriptions": [
                    {
                        "type": "time_based",
                        "expiry_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        "is_active": True
                    }
                ]
            },
            "NEWCARD002": {
                "card_uid": "NEWCARD002",
                "customer_id": 9998, 
                "customer_name": "Whitelist Real-time",
                "in_white_list": True,
                "active_subscriptions": []
            }
        }
    
    async def validate_card(self, card_uid: str):
        """Simula GET /api/cards/validate/{card_uid}"""
        # Simula delay di rete
        await asyncio.sleep(0.1)
        
        if card_uid in self.server_cards:
            print(f"🔥 Mock Server: Carta {card_uid} trovata!")
            return self.server_cards[card_uid]
        else:
            print(f"❌ Mock Server: Carta {card_uid} non trovata")
            return None

class TestRealTimeFallback:
    def __init__(self):
        self.logger = logging.getLogger("test_realtime")
        self.mock_server = MockRealTimeServer()
        
        # Configura test environment
        config = SyncConfig(
            server_url="http://localhost:8000",  # Mock
            cache_db_path="test_cache.db"
        )
        
        self.sync_manager = SyncManager(config, "TEST_GATE")
        
        # Monkey-patch il metodo _check_realtime_fallback per usare mock server
        self.sync_manager._check_realtime_fallback = self._mock_realtime_fallback
        
    async def _mock_realtime_fallback(self, card_uid: str):
        """Mock del metodo _check_realtime_fallback che usa MockRealTimeServer"""
        try:
            card_data = await self.mock_server.validate_card(card_uid)
            if card_data:
                self.logger.info(f"🔥 Mock: Carta {card_uid} trovata via real-time!")
                return card_data
            else:
                self.logger.debug(f"❌ Mock: Carta {card_uid} non trovata")
                return None
        except Exception as e:
            self.logger.error(f"❌ Mock: Errore real-time fallback: {e}")
            return None
    
    async def setup_test_environment(self):
        """Setup ambiente di test"""
        print("🔧 Setup ambiente di test...")
        
        # Rimuovi cache esistente
        if os.path.exists("test_cache.db"):
            os.remove("test_cache.db")
        
        # Inizializza database
        self.sync_manager._init_database()
        
        # Simula sistema online
        self.sync_manager.is_online = True
        
        # Aggiungi alcune carte esistenti nel cache (simulate sync precedente)
        existing_cards = [
            {
                "card_uid": "EXISTING001",
                "customer_id": 1001,
                "customer_name": "Existing User 1", 
                "in_white_list": False,
                "active_subscriptions": [
                    {
                        "type": "time_based",
                        "expiry_date": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                        "is_active": True
                    }
                ]
            }
        ]
        
        self.sync_manager._update_local_cache(existing_cards)
        print(f"✅ Cache inizializzato con {len(existing_cards)} carte esistenti")
    
    async def test_existing_card_normal_flow(self):
        """Test 1: Carta esistente nel cache - flow normale"""
        print("\n📋 TEST 1: Carta esistente (flow normale)")
        
        result = await self.sync_manager.validate_card_offline("EXISTING001")
        
        assert result['authorized'] == True
        assert result['customer_name'] == "Existing User 1"
        assert result['offline_mode'] == True  # Da cache locale
        
        print("✅ Carta esistente validata correttamente da cache")
        return result
    
    async def test_new_card_realtime_fallback(self):
        """
        🔥 TEST 2: Carta nuova (GAP SCENARIO) - fallback real-time
        Questo è il test critico per la risoluzione del gap!
        """
        print("\n🔥 TEST 2: Carta nuova - Fallback Real-time (GAP RESOLUTION)")
        
        # Questa carta NON è nel cache locale, ma è sul server
        result = await self.sync_manager.validate_card_offline("NEWCARD001")
        
        assert result['authorized'] == True
        assert result['customer_name'] == "Test User Real-time"
        assert result['offline_mode'] == False  # Viene da real-time, non cache
        assert result['reason'] == 'Carta trovata via fallback real-time'
        
        print("🔥 Carta nuova trovata via real-time fallback!")
        print(f"   Customer: {result['customer_name']}")
        print(f"   Authorized: {result['authorized']}")
        print(f"   Mode: {'Real-time' if not result['offline_mode'] else 'Cache'}")
        
        # Verifica che la carta sia stata cached immediatamente
        cached_result = await self.sync_manager.validate_card_offline("NEWCARD001")
        assert cached_result['offline_mode'] == True  # Ora dovrebbe essere da cache
        print("✅ Carta ora in cache per accessi futuri")
        
        return result
    
    async def test_whitelist_card_realtime_fallback(self):
        """TEST 3: Carta whitelist via real-time"""
        print("\n🏷️ TEST 3: Carta whitelist via real-time")
        
        result = await self.sync_manager.validate_card_offline("NEWCARD002")
        
        assert result['authorized'] == True
        assert result['customer_name'] == "Whitelist Real-time"
        # Per carte whitelist trovate via real-time, il subscription_info viene dal server
        # Non ha necessariamente la struttura subscription_info standard
        assert result['offline_mode'] == False  # Da real-time
        
        print("✅ Carta whitelist trovata via real-time")
        return result
    
    async def test_unknown_card_final_denial(self):
        """TEST 4: Carta completamente sconosciuta - negazione finale"""
        print("\n❌ TEST 4: Carta sconosciuta (negazione finale)")
        
        result = await self.sync_manager.validate_card_offline("UNKNOWN999")
        
        assert result['authorized'] == False
        assert result['reason'] == 'Carta non trovata nella cache locale'
        assert result['offline_mode'] == True
        
        print("✅ Carta sconosciuta correttamente negata")
        return result
    
    async def test_offline_mode_no_fallback(self):
        """TEST 5: Sistema offline - nessun fallback"""
        print("\n📴 TEST 5: Sistema offline - no fallback")
        
        # Simula sistema offline
        self.sync_manager.is_online = False
        
        # Usa una carta diversa che non è in cache
        result = await self.sync_manager.validate_card_offline("OFFLINE_TEST")
        
        assert result['authorized'] == False
        assert result['reason'] == 'Carta non trovata nella cache locale'
        assert result['offline_mode'] == True
        
        print("✅ Sistema offline: no fallback real-time")
        
        # Ripristina online per altri test
        self.sync_manager.is_online = True
        return result
    
    async def print_cache_status(self):
        """Mostra stato cache per debugging"""
        print("\n📊 STATO CACHE:")
        
        conn = sqlite3.connect("test_cache.db")
        cursor = conn.cursor()
        
        cursor.execute('SELECT card_uid, customer_name, in_white_list FROM synced_cards WHERE is_active = 1')
        cards = cursor.fetchall()
        
        print(f"   Carte in cache: {len(cards)}")
        for card in cards:
            print(f"   - {card[0]}: {card[1]} (whitelist: {card[2]})")
        
        conn.close()
    
    async def run_all_tests(self):
        """Esegue tutti i test"""
        print("🚀 AVVIO TEST REAL-TIME FALLBACK")
        print("=" * 50)
        
        try:
            await self.setup_test_environment()
            
            # Test 1: Flow normale
            await self.test_existing_card_normal_flow()
            
            # Test 2: 🔥 IL TEST CRITICO - Gap resolution!
            await self.test_new_card_realtime_fallback()
            
            # Test 3: Whitelist real-time
            await self.test_whitelist_card_realtime_fallback()
            
            # Test 4: Carta sconosciuta
            await self.test_unknown_card_final_denial()
            
            # Test 5: Sistema offline
            await self.test_offline_mode_no_fallback()
            
            await self.print_cache_status()
            
            print("\n" + "=" * 50)
            print("🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!")
            print("✅ Il sistema di fallback real-time risolve il gap di sync!")
            print("🔥 Le carte nuove vengono validate immediatamente")
            
        except Exception as e:
            print(f"\n❌ ERRORE NEI TEST: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if os.path.exists("test_cache.db"):
                os.remove("test_cache.db")
            print("\n🧹 Cleanup completato")

async def main():
    """Entry point"""
    test = TestRealTimeFallback()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())