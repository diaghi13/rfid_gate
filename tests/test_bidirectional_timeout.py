#!/usr/bin/env python3
"""
🕐 Test per il timeout del controllo bidirezionale

Testa che lo stato delle direzioni venga resettato automaticamente
dopo il timeout configurato.
"""

import pytest
import tempfile
import os
import asyncio
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import RFIDGateConfig, SystemConfig

@pytest.mark.asyncio
class TestBidirectionalTimeout:
    """Test timeout controllo bidirezionale"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup per ogni test"""
        # Crea database temporaneo
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)
        
        # Configurazione con timeout breve per test
        self.config = RFIDGateConfig()
        self.config.system = SystemConfig(
            tornello_id='test_tornello',
            bidirectional_mode=True,
            bidirectional_timeout_hours=1.0  # 1 ora per test
        )
        
        # Crea SyncManager
        self.sync_manager = SyncManager(self.config, self.db_path)
        
        yield  # Run test
        
        # Cleanup dopo ogni test
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    async def test_timeout_resets_state(self):
        """Test: Timeout resetta lo stato"""
        card_uid = "TEST123"
        
        # Simula accesso IN nel passato
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Inserisci stato con timestamp passato (2 ore fa)
        past_time = datetime.now() - timedelta(hours=2)
        past_time_str = past_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', (card_uid, 'in', past_time_str, 'test_tornello'))
        
        conn.commit()
        conn.close()
        
        # Prova nuovo accesso IN - dovrebbe essere permesso per timeout
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('Timeout scaduto', result['reason'])
        self.assertEqual(result['last_direction'], 'in')  # Info mantenuta
    
    async def test_no_timeout_blocks_access(self):
        """Test: Senza timeout blocca accesso consecutivo"""
        card_uid = "TEST123"
        
        # Accesso IN recente
        await self.sync_manager.update_user_direction(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        # Tentativo accesso IN immediato - dovrebbe essere bloccato
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Accesso consecutivo stesso tipo', result['reason'])
    
    async def test_timeout_configuration_works(self):
        """Test: Configurazione timeout personalizzata"""
        # Configurazione con timeout molto breve (0.01 ore = 36 secondi)
        config_short = RFIDGateConfig()
        config_short.system = SystemConfig(
            tornello_id='test_tornello',
            bidirectional_mode=True,
            bidirectional_timeout_hours=0.01  # 36 secondi per test veloce
        )
        
        sync_manager_short = SyncManager(config_short, self.db_path)
        card_uid = "TEST456"
        
        # Simula accesso con timestamp appena oltre il timeout
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 40 secondi fa (oltre il timeout di 36 secondi)
        past_time = datetime.now() - timedelta(seconds=40)
        past_time_str = past_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', (card_uid, 'out', past_time_str, 'test_tornello'))
        
        conn.commit()
        conn.close()
        
        # Accesso OUT dovrebbe essere permesso per timeout
        result = await sync_manager_short.check_bidirectional_access(
            card_uid=card_uid,
            direction="out",
            tornello_id="test_tornello"
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('Timeout scaduto', result['reason'])
    
    async def test_cleanup_removes_expired_states(self):
        """Test: Cleanup rimuove stati scaduti"""
        # Inserisci alcuni stati - alcuni scaduti, altri no
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Stato scaduto (2 ore fa, timeout è 1 ora)
        expired_time = now - timedelta(hours=2)
        expired_str = expired_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Stato valido (30 minuti fa)
        valid_time = now - timedelta(minutes=30)
        valid_str = valid_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', ('EXPIRED1', 'in', expired_str, 'test_tornello'))
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', ('VALID1', 'out', valid_str, 'test_tornello'))
        
        conn.commit()
        
        # Verifica che ci siano 2 record
        cursor.execute('SELECT COUNT(*) FROM user_direction_state')
        initial_count = cursor.fetchone()[0]
        self.assertEqual(initial_count, 2)
        
        conn.close()
        
        # Esegui cleanup
        removed_count = await self.sync_manager.cleanup_expired_direction_states()
        
        # Verifica che sia stato rimosso 1 record (quello scaduto)
        self.assertEqual(removed_count, 1)
        
        # Verifica che rimanga solo 1 record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_direction_state')
        final_count = cursor.fetchone()[0]
        self.assertEqual(final_count, 1)
        
        # Verifica che sia rimasto quello valido
        cursor.execute('SELECT card_uid FROM user_direction_state')
        remaining_card = cursor.fetchone()[0]
        self.assertEqual(remaining_card, 'VALID1')
        
        conn.close()
    
    async def test_invalid_timestamp_format_resets_state(self):
        """Test: Timestamp non valido resetta stato"""
        card_uid = "TEST789"
        
        # Inserisci record con timestamp corrotto
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', (card_uid, 'in', 'invalid-timestamp', 'test_tornello'))
        
        conn.commit()
        conn.close()
        
        # Controllo accesso dovrebbe resettare stato per timestamp non valido
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('Timestamp non valido', result['reason'])

# Test runner asincrono
class AsyncTestRunner:
    """Helper per eseguire test asincroni"""
    
    def run_async_test(self, test_method):
        """Esegue un test asincrono"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test_method())
        finally:
            loop.close()

# Test cases per il runner
if __name__ == '__main__':
    # Test specifici per timeout
    test_case = TestBidirectionalTimeout()
    runner = AsyncTestRunner()
    
    print("🕐 Testing Bidirectional Timeout...")
    
    try:
        # Test 1: Timeout resetta stato
        print("1. Testing timeout resets state...")
        test_case.setUp()
        runner.run_async_test(test_case.test_timeout_resets_state)
        test_case.tearDown()
        print("   ✅ Timeout resets state correctly")
        
        # Test 2: Senza timeout blocca
        print("2. Testing no timeout blocks access...")
        test_case.setUp()
        runner.run_async_test(test_case.test_no_timeout_blocks_access)
        test_case.tearDown()
        print("   ✅ No timeout blocks access correctly")
        
        # Test 3: Configurazione personalizzata
        print("3. Testing custom timeout configuration...")
        test_case.setUp()
        runner.run_async_test(test_case.test_timeout_configuration_works)
        test_case.tearDown()
        print("   ✅ Custom timeout configuration works")
        
        # Test 4: Cleanup rimuove scaduti
        print("4. Testing cleanup removes expired...")
        test_case.setUp()
        runner.run_async_test(test_case.test_cleanup_removes_expired_states)
        test_case.tearDown()
        print("   ✅ Cleanup removes expired states")
        
        # Test 5: Timestamp non valido
        print("5. Testing invalid timestamp handling...")
        test_case.setUp()
        runner.run_async_test(test_case.test_invalid_timestamp_format_resets_state)
        test_case.tearDown()
        print("   ✅ Invalid timestamp resets state")
        
        print()
        print("🎉 All timeout tests PASSED!")
        print("🕐 Timeout controllo bidirezionale funziona perfettamente!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup finale
        if hasattr(test_case, 'db_path') and os.path.exists(test_case.db_path):
            os.unlink(test_case.db_path)