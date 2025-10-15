#!/usr/bin/env python3
"""
🔥 Test MQTT Real-time Fallback per Gap Sync Resolution
=====================================================

Simula il scenario reale:
1. Cliente si iscrive → carta registrata nel sistema centrale
2. Gap di sync (15 minuti) → carta non ancora nel cache Raspberry  
3. Cliente prova subito ad entrare → carta non trovata nel cache locale
4. Raspberry fa chiamata MQTT real-time → server risponde con dati carta
5. Raspberry autorizza accesso E aggiorna cache immediatamente
6. Prossimi accessi usano cache locale

Questo test simula il flusso MQTT corretto invece di REST.
"""

import asyncio
import os
import sys
import json
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Aggiungi path per import
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.network.mqtt import AuthRequest
from rfid_gate.config.settings import SyncConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockMQTTClient:
    """
    Simula AsyncMQTTClient per testare il fallback MQTT real-time
    """
    
    def __init__(self):
        # Simula database server con carte registrate di recente
        self.server_cards = {
            "NEWCARD001": {
                "authorized": True,
                "customer_id": 9999,
                "customer_name": "Test User MQTT",
                "subscription_info": {
                    "type": "time_based",
                    "expiry_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                    "is_active": True,
                    "in_white_list": False,
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
                "authorized": True,
                "customer_id": 9998, 
                "customer_name": "Whitelist MQTT",
                "subscription_info": {
                    "type": "whitelist",
                    "in_white_list": True,
                    "active_subscriptions": []
                }
            }
        }
    
    async def connect(self):
        """Simula connessione MQTT"""
        print(f"🔌 Mock MQTT: Connesso al broker")
        return True
    
    async def disconnect(self):
        """Simula disconnessione MQTT"""
        print(f"🔌 Mock MQTT: Disconnesso dal broker")
        return True
    
    async def send_auth_request(self, auth_request: AuthRequest):
        """Simula invio richiesta di autenticazione MQTT"""
        # Simula delay di rete
        await asyncio.sleep(0.1)
        
        card_uid = auth_request.card_uid
        
        if card_uid in self.server_cards:
            response = self.server_cards[card_uid]
            print(f"🔥 Mock MQTT: Carta {card_uid} autorizzata!")
            return response
        else:
            print(f"❌ Mock MQTT: Carta {card_uid} non autorizzata")
            return {"authorized": False, "reason": "Carta non trovata"}

class TestMQTTRealTimeFallback:
    def __init__(self):
        self.logger = logging.getLogger("test_mqtt_realtime")
        self.mock_mqtt = MockMQTTClient()
        
        # Configura test environment
        config = SyncConfig(
            server_url="mqtt://localhost:1883",  # MQTT broker
            cache_db_path="test_mqtt_cache.db"
        )
        
        self.sync_manager = SyncManager(config, "TEST_GATE")
        
        # Mock del metodo _check_realtime_fallback per usare MQTT mock
        self.sync_manager._check_realtime_fallback = self._mock_mqtt_realtime_fallback
        
    async def _mock_mqtt_realtime_fallback(self, card_uid: str):
        """Mock del metodo _check_realtime_fallback che usa MockMQTTClient"""
        try:
            # Simula creazione AuthRequest
            auth_request = AuthRequest(
                card_uid=card_uid,
                identificativo_tornello=self.sync_manager.tornello_id,
                direzione="in",
                timestamp=time.time(),
                auth_required=True,
                fallback_mode=True
            )
            
            self.logger.info(f"🔥 Mock MQTT: Tentativo real-time per carta {card_uid}")
            
            # Simula timeout con asyncio.wait_for
            response = await asyncio.wait_for(
                self.mock_mqtt.send_auth_request(auth_request),
                timeout=3.0
            )
            
            if response and response.get('authorized'):
                self.logger.info(f"🔥 Mock MQTT: Carta {card_uid} autorizzata!")
                
                # Formatta risposta compatibile con cache  
                return {
                    'card_uid': card_uid,
                    'customer_id': response.get('customer_id'),
                    'customer_name': response.get('customer_name', ''),
                    'in_white_list': response.get('subscription_info', {}).get('in_white_list', False),
                    'active_subscriptions': response.get('subscription_info', {}).get('active_subscriptions', []),
                    'subscription_info': response.get('subscription_info', {})
                }
            else:
                self.logger.debug(f"❌ Mock MQTT: Carta {card_uid} non autorizzata")
                return None
                
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ Mock MQTT: Timeout per carta {card_uid}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Mock MQTT: Errore fallback: {e}")
            return None
    
    async def setup_test_environment(self):
        """Setup ambiente di test"""
        print("🔧 Setup ambiente di test MQTT...")
        
        # Rimuovi cache esistente
        if os.path.exists("test_mqtt_cache.db"):
            os.remove("test_mqtt_cache.db")
        
        # Inizializza database
        self.sync_manager._init_database()
        
        # Simula sistema online
        self.sync_manager.is_online = True
        
        # Connetti mock MQTT
        await self.mock_mqtt.connect()
        
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
    
    async def test_scenario_completo(self):
        """
        🎯 TEST SCENARIO COMPLETO: Cliente si iscrive → Gap sync → Accesso immediato
        """
        print("\n" + "="*60)
        print("🎯 SCENARIO COMPLETO: Risoluzione gap sync via MQTT")
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
        print("   🔥 Raspberry rileva carta non in cache → Avvia fallback MQTT real-time")
        
        # Il sistema è online, quindi dovrebbe fare fallback MQTT
        result_mqtt = await self.sync_manager.validate_card_offline("NEWCARD001")
        
        print(f"   ✅ Risultato MQTT: {result_mqtt['reason']}")
        print(f"   📝 Cliente: {result_mqtt['customer_name']}")
        print(f"   🎫 Autorizzato: {result_mqtt['authorized']}")
        print(f"   📡 Modalità: {'MQTT Real-time' if not result_mqtt['offline_mode'] else 'Cache'}")
        
        assert result_mqtt['authorized'], "La carta dovrebbe essere autorizzata via MQTT"
        assert not result_mqtt['offline_mode'], "Dovrebbe essere da MQTT real-time"
        assert "MQTT" in result_mqtt['reason'], "Il motivo dovrebbe menzionare MQTT"
        
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
        
        return result_mqtt
    
    async def test_carta_whitelist_mqtt(self):
        """TEST: Carta whitelist via MQTT"""
        print("\n🏷️ TEST: Carta whitelist via MQTT fallback")
        
        result = await self.sync_manager.validate_card_offline("NEWCARD002")
        
        assert result['authorized'] == True
        assert result['customer_name'] == "Whitelist MQTT"
        assert not result['offline_mode']  # Da MQTT real-time
        
        print("✅ Carta whitelist autorizzata via MQTT")
        return result
    
    async def test_carta_sconosciuta_mqtt(self):
        """TEST: Carta sconosciuta anche via MQTT"""
        print("\n❌ TEST: Carta completamente sconosciuta")
        
        result = await self.sync_manager.validate_card_offline("UNKNOWN999")
        
        assert result['authorized'] == False
        assert result['reason'] == 'Carta non trovata nella cache locale'
        assert result['offline_mode'] == True
        
        print("✅ Carta sconosciuta correttamente negata")
        return result
    
    async def test_sistema_offline_no_mqtt(self):
        """TEST: Sistema offline - nessun fallback MQTT"""
        print("\n📴 TEST: Sistema offline - no fallback MQTT")
        
        # Simula sistema offline
        self.sync_manager.is_online = False
        
        result = await self.sync_manager.validate_card_offline("NEWCARD_OFFLINE")
        
        assert result['authorized'] == False
        assert result['reason'] == 'Carta non trovata nella cache locale'
        assert result['offline_mode'] == True
        
        print("✅ Sistema offline: nessun tentativo MQTT")
        
        # Ripristina online
        self.sync_manager.is_online = True
        return result
    
    async def print_cache_status(self):
        """Mostra stato cache finale"""
        print("\n📊 STATO FINALE CACHE:")
        
        conn = sqlite3.connect("test_mqtt_cache.db")
        cursor = conn.cursor()
        
        cursor.execute('SELECT card_uid, customer_name, in_white_list FROM synced_cards WHERE is_active = 1')
        cards = cursor.fetchall()
        
        print(f"   Carte in cache: {len(cards)}")
        for card in cards:
            print(f"   - {card[0]}: {card[1]} (whitelist: {card[2]})")
        
        conn.close()
    
    async def run_all_tests(self):
        """Esegue tutti i test MQTT"""
        print("🚀 AVVIO TEST MQTT REAL-TIME FALLBACK")
        print("=" * 60)
        
        try:
            await self.setup_test_environment()
            
            # 🎯 Test scenario completo (il più importante!)
            await self.test_scenario_completo()
            
            # Test aggiuntivi
            await self.test_carta_whitelist_mqtt()
            await self.test_carta_sconosciuta_mqtt()
            await self.test_sistema_offline_no_mqtt()
            
            await self.print_cache_status()
            
            print("\n" + "=" * 60)
            print("🎉 TUTTI I TEST MQTT COMPLETATI CON SUCCESSO!")
            print("✅ Il sistema di fallback MQTT risolve il gap di sync!")
            print("🔥 Cliente si iscrive → Accesso immediato via MQTT")
            print("💾 Cache aggiornato immediatamente per performance")
            print("🚀 Accessi successivi da cache locale")
            
        except Exception as e:
            print(f"\n❌ ERRORE NEI TEST: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            await self.mock_mqtt.disconnect()
            if os.path.exists("test_mqtt_cache.db"):
                os.remove("test_mqtt_cache.db")
            print("\n🧹 Cleanup completato")

async def main():
    """Entry point"""
    test = TestMQTTRealTimeFallback()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())