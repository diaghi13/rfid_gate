#!/usr/bin/env python3
"""
🔥 Test REST Real-time Fallback per Gap Sync Resolution
=====================================================

Simula il scenario reale con chiamate REST:
1. Cliente si iscrive → carta registrata nel sistema centrale
2. Gap di sync (15 minuti) → carta non ancora nel cache Raspberry  
3. Cliente prova subito ad entrare → carta non trovata nel cache locale
4. Raspberry fa chiamata REST real-time → GET /api/cards/validate/{card_uid}
5. Server risponde con dati carta → Raspberry autorizza accesso E aggiorna cache
6. Prossimi accessi usano cache locale per performance

Endpoint REST: GET {server_url}/api/cards/validate/{card_uid}
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

class MockHTTPResponse:
    """Mock per aiohttp response"""
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json_data = json_data or {}
    
    async def json(self):
        return self._json_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass

class MockHTTPSession:
    """Mock per aiohttp session"""
    def __init__(self, responses):
        self.responses = responses
    
    def get(self, url):
        return self.responses.get(url, MockHTTPResponse(404))
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass

class TestRESTRealTimeFallback:
    def __init__(self):
        self.logger = logging.getLogger("test_rest_realtime")
        
        # Configura test environment con endpoint REST
        config = SyncConfig(
            server_url="http://localhost:8000",
            fallback_server_url="http://localhost:8000",
            fallback_endpoint="/api/cards/validate",
            fallback_timeout=3,
            cache_db_path="test_rest_cache.db"
        )
        
        self.sync_manager = SyncManager(config, "TEST_GATE")
        
        # Mock server responses
        self.server_cards = {
            "NEWCARD001": {
                "card_uid": "NEWCARD001", 
                "customer_id": 9999,
                "customer_name": "Test User REST",
                "in_white_list": False,
                "active_subscriptions": [
                    {
                        "type": "time_based",
                        "expiry_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        "is_active": True
                    }
                ],
                "subscription_info": {
                    "active_subscriptions": [
                        {
                            "type": "time_based",
                            "expiry_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                            "is_active": True
                        }
                    ]
                }
            },
            "NEWCARD002": {
                "card_uid": "NEWCARD002",
                "customer_id": 9998, 
                "customer_name": "Whitelist REST",
                "in_white_list": True,
                "active_subscriptions": [],
                "subscription_info": {
                    "in_white_list": True,
                    "active_subscriptions": []
                }
            }
        }
    
    def _create_mock_responses(self):
        """Crea mock responses per i test"""
        responses = {}
        
        # Response per NEWCARD001
        url1 = f"{self.sync_manager.config.server_url}{self.sync_manager.config.card_validate_endpoint}/NEWCARD001"
        responses[url1] = MockHTTPResponse(200, self.server_cards["NEWCARD001"])
        
        # Response per NEWCARD002
        url2 = f"{self.sync_manager.config.server_url}{self.sync_manager.config.card_validate_endpoint}/NEWCARD002"
        responses[url2] = MockHTTPResponse(200, self.server_cards["NEWCARD002"])
        
        # Response per carta non trovata
        url3 = f"{self.sync_manager.config.server_url}{self.sync_manager.config.card_validate_endpoint}/UNKNOWN999"
        responses[url3] = MockHTTPResponse(404)
        
        return responses
    
    async def setup_test_environment(self):
        """Setup ambiente di test"""
        print("🔧 Setup ambiente di test REST...")
        
        # Rimuovi cache esistente
        if os.path.exists("test_rest_cache.db"):
            os.remove("test_rest_cache.db")
        
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
        
        # Mock del metodo _create_aiohttp_session
        mock_responses = self._create_mock_responses()
        self.sync_manager._create_aiohttp_session = lambda timeout: MockHTTPSession(mock_responses)
    
    async def test_scenario_completo_rest(self):
        """
        🎯 TEST SCENARIO COMPLETO: Cliente si iscrive → Gap sync → Accesso immediato via REST
        """
        print("\n" + "="*60)
        print("🎯 SCENARIO COMPLETO: Risoluzione gap sync via REST")
        print("="*60)
        
        print("\n1️⃣ FASE 1: Cliente si iscrive (carta registrata nel sistema centrale)")
        print("   → Carta NEWCARD001 aggiunta al server")
        print("   → Gap di sync attivo (carta non ancora nel cache Raspberry)")
        
        print("\n2️⃣ FASE 2: Verifica stato cache locale PRIMA del fallback")
        # Disabilitiamo temporaneamente il sistema online per testare solo il cache
        original_online_state = self.sync_manager.is_online
        self.sync_manager.is_online = False
        
        result_cache = await self.sync_manager.validate_card_offline("NEWCARD001")
        print(f"   ❌ Cache locale: {result_cache['reason']}")
        assert not result_cache['authorized'], "La carta non dovrebbe essere nel cache"
        
        # Ripristiniamo lo stato online
        self.sync_manager.is_online = original_online_state
        
        print("\n3️⃣ FASE 3: Cliente prova subito ad entrare")
        print("   🔥 Raspberry rileva carta non in cache → Avvia fallback REST real-time")
        
        expected_url = f"{self.sync_manager.config.server_url}{self.sync_manager.config.card_validate_endpoint}/NEWCARD001"
        print(f"   📡 URL chiamata: {expected_url}")
        
        # Il sistema è online, quindi dovrebbe fare fallback REST
        result_rest = await self.sync_manager.validate_card_offline("NEWCARD001")
        
        print(f"   ✅ Risultato REST: {result_rest['reason']}")
        print(f"   📝 Cliente: {result_rest['customer_name']}")
        print(f"   🎫 Autorizzato: {result_rest['authorized']}")
        print(f"   📡 Modalità: {'REST Real-time' if not result_rest['offline_mode'] else 'Cache'}")
        
        assert result_rest['authorized'], "La carta dovrebbe essere autorizzata via REST"
        assert not result_rest['offline_mode'], "Dovrebbe essere da REST real-time"
        assert "REST" in result_rest['reason'], "Il motivo dovrebbe menzionare REST"
        
        print("\n4️⃣ FASE 4: Verifica cache aggiornato immediatamente")
        result_cached = await self.sync_manager.validate_card_offline("NEWCARD001")
        
        print(f"   💾 Cache aggiornato: {result_cached['authorized']}")
        print(f"   📁 Modalità: {'Cache locale' if result_cached['offline_mode'] else 'Real-time'}")
        
        assert result_cached['authorized'], "La carta dovrebbe ora essere nel cache"
        assert result_cached['offline_mode'], "Ora dovrebbe essere da cache locale"
        
        print("\n5️⃣ FASE 5: Accessi successivi usano cache (performance)")
        for i in range(3):
            result = await self.sync_manager.validate_card_offline("NEWCARD001")
            assert result['offline_mode'], f"Accesso {i+1} dovrebbe essere da cache"
        print("   🚀 3 accessi successivi: tutti da cache locale (performance ottimale)")
        
        return result_rest
    
    async def test_carta_whitelist_rest(self):
        """TEST: Carta whitelist via REST"""
        print("\n🏷️ TEST: Carta whitelist via REST fallback")
        
        result = await self.sync_manager.validate_card_offline("NEWCARD002")
        
        assert result['authorized'] == True
        assert result['customer_name'] == "Whitelist REST"
        assert not result['offline_mode']  # Da REST real-time
        
        print("✅ Carta whitelist autorizzata via REST")
        return result
    
    async def test_carta_non_trovata_rest(self):
        """TEST: Carta non trovata via REST (404)"""
        print("\n❌ TEST: Carta non trovata via REST")
        
        result = await self.sync_manager.validate_card_offline("UNKNOWN999")
        
        assert result['authorized'] == False
        assert result['reason'] == 'Carta non trovata nella cache locale'
        assert result['offline_mode'] == True
        
        print("✅ Carta non trovata correttamente gestita")
        return result
    
    async def test_sistema_offline_no_rest(self):
        """TEST: Sistema offline - nessun fallback REST"""
        print("\n📴 TEST: Sistema offline - no fallback REST")
        
        # Simula sistema offline
        self.sync_manager.is_online = False
        
        result = await self.sync_manager.validate_card_offline("OFFLINE_TEST")
        
        assert result['authorized'] == False
        assert result['reason'] == 'Carta non trovata nella cache locale'
        assert result['offline_mode'] == True
        
        print("✅ Sistema offline: nessun tentativo REST")
        
        # Ripristina online
        self.sync_manager.is_online = True
        return result
    
    async def print_cache_status(self):
        """Mostra stato cache finale"""
        print("\n📊 STATO FINALE CACHE:")
        
        conn = sqlite3.connect("test_rest_cache.db")
        cursor = conn.cursor()
        
        cursor.execute('SELECT card_uid, customer_name, in_white_list FROM synced_cards WHERE is_active = 1')
        cards = cursor.fetchall()
        
        print(f"   Carte in cache: {len(cards)}")
        for card in cards:
            print(f"   - {card[0]}: {card[1]} (whitelist: {card[2]})")
        
        conn.close()
    
    async def run_all_tests(self):
        """Esegue tutti i test REST"""
        print("🚀 AVVIO TEST REST REAL-TIME FALLBACK")
        print("=" * 60)
        
        try:
            await self.setup_test_environment()
            
            # 🎯 Test scenario completo (il più importante!)
            await self.test_scenario_completo_rest()
            
            # Test aggiuntivi
            await self.test_carta_whitelist_rest()
            await self.test_carta_non_trovata_rest()
            await self.test_sistema_offline_no_rest()
            
            await self.print_cache_status()
            
            print("\n" + "=" * 60)
            print("🎉 TUTTI I TEST REST COMPLETATI CON SUCCESSO!")
            print("✅ Il sistema di fallback REST risolve il gap di sync!")
            print("🔥 Cliente si iscrive → Accesso immediato via REST")
            print("💾 Cache aggiornato immediatamente per performance")
            print("🚀 Accessi successivi da cache locale")
            print("📡 Endpoint: GET /api/cards/validate/{card_uid}")
            
        except Exception as e:
            print(f"\n❌ ERRORE NEI TEST: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if os.path.exists("test_rest_cache.db"):
                os.remove("test_rest_cache.db")
            print("\n🧹 Cleanup completato")

async def main():
    """Entry point"""
    test = TestRESTRealTimeFallback()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())