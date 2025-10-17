#!/usr/bin/env python3
"""
🧪 Test Membership Fee - Validazione Quota Associativa
====================================================

Test completi per il nuovo sistema di validazione che richiede:
1. Abbonamento attivo E valido 
2. Membership fee (quota associativa) attiva E valida

Scenari testati:
✅ Membership fee valida + abbonamento valido → AUTORIZZATO
❌ Membership fee scaduta + abbonamento valido → NEGATO  
❌ Membership fee valida + abbonamento scaduto → NEGATO
❌ Membership fee null + abbonamento valido → NEGATO
❌ Membership fee non attiva + abbonamento valido → NEGATO
✅ Carta whitelist → AUTORIZZATO (bypass completo)
"""

import asyncio
import sys
import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Aggiungi il path del progetto
project_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_path))

from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import RFIDGateConfig, SyncConfig


class MembershipFeeTestSuite:
    """Suite di test per validazione membership fee"""
    
    def __init__(self):
        self.test_db_path = "tests/fixtures/test_membership_fee.db"
        self.config = self._create_test_config()
        self.sync_manager = SyncManager(self.config, "tornello_test")
        self.logger = logging.getLogger("membership_fee_test")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _create_test_config(self) -> SyncConfig:
        """Crea configurazione di test"""
        return SyncConfig(
            cache_db_path=self.test_db_path,
            server_url="https://test-server.com",
            sync_endpoint="/api/sync",
            logs_endpoint="/api/logs", 
            updates_endpoint="/api/updates",
            health_endpoint="/api/health",
            connection_timeout=5,
            logs_sync_interval=5,
            updates_check_interval=15,
            daily_sync_time="02:00"
        )
    
    def _cleanup_test_db(self):
        """Rimuove database di test se esiste"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            print(f"🧹 Rimosso database di test: {self.test_db_path}")
    
    def _setup_test_data(self):
        """Inserisce dati di test nel database"""
        # Assicurati che il database sia inizializzato
        self.sync_manager._init_database()
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        test_cards = [
            # 1️⃣ SCENARIO: Membership fee valida + abbonamento valido → ✅ AUTORIZZATO
            {
                'card_uid': 'CARD001',
                'customer_id': 1,
                'customer_name': 'Mario Rossi',
                'in_white_list': 0,
                'active_subscriptions': json.dumps([{
                    'type': 'time_based',
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                }]),
                'active_membership_fee': json.dumps({
                    'start_date': yesterday.strftime('%Y-%m-%d'),
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                })
            },
            
            # 2️⃣ SCENARIO: Membership fee scaduta + abbonamento valido → ❌ NEGATO
            {
                'card_uid': 'CARD002',
                'customer_id': 2,
                'customer_name': 'Luigi Bianchi',
                'in_white_list': 0,
                'active_subscriptions': json.dumps([{
                    'type': 'time_based',
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                }]),
                'active_membership_fee': json.dumps({
                    'start_date': (yesterday - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'expiry_date': yesterday.strftime('%Y-%m-%d'),  # SCADUTA
                    'is_active': True
                })
            },
            
            # 3️⃣ SCENARIO: Membership fee valida + abbonamento scaduto → ❌ NEGATO
            {
                'card_uid': 'CARD003',
                'customer_id': 3,
                'customer_name': 'Giuseppe Verdi',
                'in_white_list': 0,
                'active_subscriptions': json.dumps([{
                    'type': 'time_based',
                    'expiry_date': yesterday.strftime('%Y-%m-%d'),  # SCADUTO
                    'is_active': True
                }]),
                'active_membership_fee': json.dumps({
                    'start_date': yesterday.strftime('%Y-%m-%d'),
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                })
            },
            
            # 4️⃣ SCENARIO: Membership fee null + abbonamento valido → ❌ NEGATO
            {
                'card_uid': 'CARD004',
                'customer_id': 4,
                'customer_name': 'Anna Neri',
                'in_white_list': 0,
                'active_subscriptions': json.dumps([{
                    'type': 'time_based',
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                }]),
                'active_membership_fee': None  # NULL
            },
            
            # 5️⃣ SCENARIO: Membership fee non attiva + abbonamento valido → ❌ NEGATO
            {
                'card_uid': 'CARD005',
                'customer_id': 5,
                'customer_name': 'Paolo Gialli',
                'in_white_list': 0,
                'active_subscriptions': json.dumps([{
                    'type': 'time_based',
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                }]),
                'active_membership_fee': json.dumps({
                    'start_date': yesterday.strftime('%Y-%m-%d'),
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': False  # NON ATTIVA
                })
            },
            
            # 6️⃣ SCENARIO: Carta whitelist → ✅ AUTORIZZATO (bypass completo)
            {
                'card_uid': 'WHITELIST001',
                'customer_id': 6,
                'customer_name': 'Staff Admin',
                'in_white_list': 1,  # WHITELIST
                'active_subscriptions': json.dumps([]),
                'active_membership_fee': None  # Anche NULL, ma whitelist bypassa tutto
            },
            
            # 7️⃣ SCENARIO: Single entrance + membership fee valida → ✅ AUTORIZZATO
            {
                'card_uid': 'CARD006',
                'customer_id': 7,
                'customer_name': 'Marco Blu',
                'in_white_list': 0,
                'active_subscriptions': json.dumps([{
                    'type': 'single_entrance',
                    'remaining_entrances': 5,
                    'is_active': True
                }]),
                'active_membership_fee': json.dumps({
                    'start_date': yesterday.strftime('%Y-%m-%d'),
                    'expiry_date': tomorrow.strftime('%Y-%m-%d'),
                    'is_active': True
                })
            }
        ]
        
        # Inserisci carte di test
        for card in test_cards:
            cursor.execute('''
                INSERT INTO synced_cards 
                (card_uid, customer_id, customer_name, in_white_list, 
                 active_subscriptions, active_membership_fee, last_sync, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                card['card_uid'],
                card['customer_id'],
                card['customer_name'],
                card['in_white_list'],
                card['active_subscriptions'],
                card['active_membership_fee'],
                datetime.now()
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Inserite {len(test_cards)} carte di test")
    
    async def test_scenario_1_valid_both(self):
        """Test 1: Membership fee valida + abbonamento valido → AUTORIZZATO"""
        print("\n1️⃣ TEST: Membership fee valida + abbonamento valido")
        
        result = await self.sync_manager.validate_card_offline('CARD001', 'in')
        
        assert result['authorized'] == True, f"Dovrebbe essere autorizzato, ricevuto: {result}"
        assert 'Quota associativa valida' in result['reason'], f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Mario Rossi'
        assert result['customer_id'] == 1
        assert result['subscription_info'] is not None
        assert result['membership_fee_info'] is not None
        
        print(f"   ✅ AUTORIZZATO: {result['reason']}")
        print(f"   👤 Cliente: {result['customer_name']} (ID: {result['customer_id']})")
        return True
    
    async def test_scenario_2_expired_membership(self):
        """Test 2: Membership fee scaduta + abbonamento valido → NEGATO"""
        print("\n2️⃣ TEST: Membership fee scaduta + abbonamento valido")
        
        result = await self.sync_manager.validate_card_offline('CARD002', 'in')
        
        assert result['authorized'] == False, f"Dovrebbe essere negato, ricevuto: {result}"
        assert 'scaduta' in result['reason'].lower(), f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Luigi Bianchi'
        
        print(f"   ❌ NEGATO: {result['reason']}")
        print(f"   👤 Cliente: {result['customer_name']} (ID: {result['customer_id']})")
        return True
    
    async def test_scenario_3_expired_subscription(self):
        """Test 3: Membership fee valida + abbonamento scaduto → NEGATO"""
        print("\n3️⃣ TEST: Membership fee valida + abbonamento scaduto")
        
        result = await self.sync_manager.validate_card_offline('CARD003', 'in')
        
        assert result['authorized'] == False, f"Dovrebbe essere negato, ricevuto: {result}"
        assert 'Nessun abbonamento valido' in result['reason'], f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Giuseppe Verdi'
        
        print(f"   ❌ NEGATO: {result['reason']}")
        print(f"   👤 Cliente: {result['customer_name']} (ID: {result['customer_id']})")
        return True
    
    async def test_scenario_4_null_membership(self):
        """Test 4: Membership fee null + abbonamento valido → NEGATO"""
        print("\n4️⃣ TEST: Membership fee null + abbonamento valido")
        
        result = await self.sync_manager.validate_card_offline('CARD004', 'in')
        
        assert result['authorized'] == False, f"Dovrebbe essere negato, ricevuto: {result}"
        assert 'Nessuna quota associativa' in result['reason'], f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Anna Neri'
        
        print(f"   ❌ NEGATO: {result['reason']}")
        print(f"   👤 Cliente: {result['customer_name']} (ID: {result['customer_id']})")
        return True
    
    async def test_scenario_5_inactive_membership(self):
        """Test 5: Membership fee non attiva + abbonamento valido → NEGATO"""
        print("\n5️⃣ TEST: Membership fee non attiva + abbonamento valido")
        
        result = await self.sync_manager.validate_card_offline('CARD005', 'in')
        
        assert result['authorized'] == False, f"Dovrebbe essere negato, ricevuto: {result}"
        assert 'non attiva' in result['reason'], f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Paolo Gialli'
        
        print(f"   ❌ NEGATO: {result['reason']}")
        print(f"   👤 Cliente: {result['customer_name']} (ID: {result['customer_id']})")
        return True
    
    async def test_scenario_6_whitelist_bypass(self):
        """Test 6: Carta whitelist → AUTORIZZATO (bypass completo)"""
        print("\n6️⃣ TEST: Carta whitelist (bypass membership fee)")
        
        result = await self.sync_manager.validate_card_offline('WHITELIST001', 'in')
        
        assert result['authorized'] == True, f"Whitelist dovrebbe essere sempre autorizzata, ricevuto: {result}"
        assert 'whitelist' in result['reason'].lower(), f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Staff Admin'
        assert result['subscription_info']['type'] == 'whitelist'
        
        print(f"   ✅ AUTORIZZATO: {result['reason']}")
        print(f"   👤 Staff: {result['customer_name']} (ID: {result['customer_id']})")
        return True
    
    async def test_scenario_7_single_entrance(self):
        """Test 7: Single entrance + membership fee valida → AUTORIZZATO"""
        print("\n7️⃣ TEST: Abbonamento single entrance + membership fee valida")
        
        result = await self.sync_manager.validate_card_offline('CARD006', 'in')
        
        assert result['authorized'] == True, f"Dovrebbe essere autorizzato, ricevuto: {result}"
        assert 'Quota associativa valida' in result['reason'], f"Reason errato: {result['reason']}"
        assert result['customer_name'] == 'Marco Blu'
        assert result['subscription_info']['type'] == 'single_entrance'
        
        print(f"   ✅ AUTORIZZATO: {result['reason']}")
        print(f"   👤 Cliente: {result['customer_name']} (ID: {result['customer_id']})")
        print(f"   🎫 Tipo: {result['subscription_info']['type']}")
        return True
    
    async def test_scenario_8_card_not_found(self):
        """Test 8: Carta non esistente → NEGATO"""
        print("\n8️⃣ TEST: Carta non esistente")
        
        result = await self.sync_manager.validate_card_offline('NOTFOUND', 'in')
        
        assert result['authorized'] == False, f"Carta inesistente dovrebbe essere negata, ricevuto: {result}"
        assert 'non trovata' in result['reason'].lower(), f"Reason errato: {result['reason']}"
        assert result['customer_name'] is None
        
        print(f"   ❌ NEGATO: {result['reason']}")
        return True
    
    async def run_all_tests(self):
        """Esegue tutti i test"""
        print("🧪 AVVIO TEST SUITE MEMBERSHIP FEE")
        print("=" * 70)
        
        # Setup
        self._cleanup_test_db()
        self._setup_test_data()
        
        tests = [
            self.test_scenario_1_valid_both,
            self.test_scenario_2_expired_membership,
            self.test_scenario_3_expired_subscription,
            self.test_scenario_4_null_membership,
            self.test_scenario_5_inactive_membership,
            self.test_scenario_6_whitelist_bypass,
            self.test_scenario_7_single_entrance,
            self.test_scenario_8_card_not_found
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"   🚨 ERRORE: {e}")
                failed += 1
        
        # Cleanup
        self._cleanup_test_db()
        
        print("\n" + "=" * 70)
        print("📊 RISULTATI TEST MEMBERSHIP FEE")
        print(f"✅ Test superati: {passed}")
        print(f"❌ Test falliti: {failed}")
        print(f"📈 Tasso successo: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            print("\n🎉 TUTTI I TEST SUPERATI!")
            print("✅ Sistema membership fee funziona correttamente")
            return True
        else:
            print(f"\n⚠️ {failed} TEST FALLITI")
            return False


async def main():
    """Funzione principale"""
    suite = MembershipFeeTestSuite()
    success = await suite.run_all_tests()
    
    if success:
        print("\n🚀 Sistema pronto per produzione!")
    else:
        print("\n🔧 Correggere errori prima del deploy")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())