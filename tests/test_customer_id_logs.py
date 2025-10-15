#!/usr/bin/env python3
"""
🧪 Test Customer ID in Logs
==========================

Test per verificare che customer_id sia correttamente incluso
nei log di accesso e sincronizzato con il server.
"""

import unittest
import sqlite3
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import SyncConfig


class TestCustomerIdInLogs(unittest.TestCase):
    """Test inclusione customer_id nei log di accesso"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_logs.db")
        
        self.sync_config = SyncConfig(
            server_url="http://test-server.com",
            cache_db_path=self.db_path,
            logs_sync_interval=1  # 1 minuto per test rapidi
        )
        
        self.sync_manager = SyncManager(self.sync_config, "TEST_GATE")
    
    def tearDown(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_customer_id_in_database_schema(self):
        """Test che customer_id sia presente nello schema database"""
        
        # Verifica schema tabella pending_logs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(pending_logs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Verifica che customer_id sia presente
        self.assertIn('customer_id', column_names)
        
        print("✅ Schema database: customer_id presente in pending_logs")
        print(f"📋 Colonne: {column_names}")
        
        conn.close()
    
    async def test_log_access_with_customer_id(self):
        """Test logging accesso con customer_id"""
        
        # Test con customer_id presente
        await self.sync_manager.log_access(
            card_uid="CUSTOMER123",
            direction="in",
            result="authorized", 
            reason="Accesso autorizzato",
            customer_id=12345,
            customer_name="Mario Rossi",
            reader_type="mfrc522",
            metadata={"test": "data"}
        )
        
        # Verifica nel database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT card_uid, customer_id, customer_name, result, reason
            FROM pending_logs 
            WHERE card_uid = ?
        ''', ("CUSTOMER123",))
        
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "CUSTOMER123")  # card_uid
        self.assertEqual(result[1], 12345)          # customer_id
        self.assertEqual(result[2], "Mario Rossi")  # customer_name
        self.assertEqual(result[3], "authorized")   # result
        
        print("✅ Log con customer_id salvato correttamente")
        print(f"📦 Dati: {result}")
        
        conn.close()
    
    async def test_log_access_without_customer_id(self):
        """Test logging accesso senza customer_id (carte sconosciute/whitelist)"""
        
        # Test senza customer_id (es. carta sconosciuta)
        await self.sync_manager.log_access(
            card_uid="UNKNOWN123",
            direction="in",
            result="denied",
            reason="Carta non riconosciuta",
            customer_id=None,  # Nessun customer_id
            customer_name=None,
            reader_type="pn532"
        )
        
        # Verifica nel database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT card_uid, customer_id, customer_name, result, reason
            FROM pending_logs 
            WHERE card_uid = ?
        ''', ("UNKNOWN123",))
        
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "UNKNOWN123")   # card_uid
        self.assertIsNone(result[1])               # customer_id = NULL
        self.assertIsNone(result[2])               # customer_name = NULL
        self.assertEqual(result[3], "denied")       # result
        
        print("✅ Log senza customer_id gestito correttamente")
        print(f"📦 Dati: {result}")
        
        conn.close()
    
    async def test_sync_logs_payload_includes_customer_id(self):
        """Test che il payload di sync includa customer_id"""
        
        # Aggiungi diversi log con e senza customer_id
        await self.sync_manager.log_access(
            card_uid="CUSTOMER456",
            direction="in",
            result="authorized",
            reason="Abbonamento valido",
            customer_id=67890,
            customer_name="Giulia Bianchi"
        )
        
        await self.sync_manager.log_access(
            card_uid="WHITELIST789",
            direction="out", 
            result="authorized",
            reason="Carta whitelist",
            customer_id=None,  # Whitelist senza customer_id
            customer_name="Staff Member"
        )
        
        # Mock della chiamata HTTP per verificare payload
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Forza sync online
            self.sync_manager.is_online = True
            success = await self.sync_manager._sync_logs()
            
            # Verifica che la chiamata sia stata fatta
            self.assertTrue(success)
            mock_post.assert_called_once()
            
            # Estrai il payload inviato
            call_args = mock_post.call_args
            payload = call_args[1]['json']  # keyword arguments
            logs_sent = payload['logs']
            
            # Verifica che customer_id sia nel payload
            customer_log = next(log for log in logs_sent if log['card_uid'] == 'CUSTOMER456')
            whitelist_log = next(log for log in logs_sent if log['card_uid'] == 'WHITELIST789')
            
            # Verifica customer con ID
            self.assertEqual(customer_log['customer_id'], 67890)
            self.assertEqual(customer_log['customer_name'], 'Giulia Bianchi')
            
            # Verifica whitelist senza ID  
            self.assertIsNone(whitelist_log['customer_id'])
            self.assertEqual(whitelist_log['customer_name'], 'Staff Member')
            
            print("✅ Payload sync include customer_id correttamente")
            print(f"📤 Customer log: {customer_log}")
            print(f"📤 Whitelist log: {whitelist_log}")
    
    async def test_validate_card_returns_customer_id(self):
        """Test che validate_card_offline restituisca customer_id per i log"""
        
        # Prepara dati di test nella cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO synced_cards 
            (card_uid, customer_id, customer_name, in_white_list, active_subscriptions)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            "TESTCARD999",
            99999,
            "Test Customer",
            0,  # Not in whitelist
            '[{"type": "time_based", "expiry_date": "2025-12-31", "is_active": true}]'
        ))
        conn.commit()
        conn.close()
        
        # Test validazione
        result = await self.sync_manager.validate_card_offline("TESTCARD999", "in")
        
        # Verifica che customer_id sia nella risposta
        self.assertTrue(result['authorized'])
        self.assertEqual(result['customer_id'], 99999)
        self.assertEqual(result['customer_name'], "Test Customer")
        
        print("✅ validate_card_offline restituisce customer_id")
        print(f"📋 Risultato: {result}")
    
    async def test_whitelist_customer_id_nullable(self):
        """Test che carte whitelist possano avere customer_id NULL"""
        
        # Prepara carta whitelist senza customer_id
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO synced_cards 
            (card_uid, customer_id, customer_name, in_white_list, active_subscriptions)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            "WHITELIST001",
            None,  # Nessun customer_id
            "Security Staff", 
            1,     # In whitelist
            '[]'   # Nessun abbonamento necessario
        ))
        conn.commit()
        conn.close()
        
        # Test validazione
        result = await self.sync_manager.validate_card_offline("WHITELIST001", "in")
        
        # Verifica risultato
        self.assertTrue(result['authorized'])
        self.assertIsNone(result['customer_id'])  # customer_id può essere None
        self.assertEqual(result['customer_name'], "Security Staff")
        self.assertEqual(result['reason'], "Carta in whitelist - accesso sempre autorizzato")
        
        print("✅ Whitelist con customer_id NULL funziona")
        print(f"📋 Risultato: {result}")


def run_async_test(coro):
    """Helper per eseguire test async"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Wrapper per test async
    class AsyncTestCase(TestCustomerIdInLogs):
        def test_customer_id_schema(self):
            run_async_test(self.test_customer_id_in_database_schema())
        
        def test_log_with_customer_id(self):
            run_async_test(self.test_log_access_with_customer_id())
        
        def test_log_without_customer_id(self):
            run_async_test(self.test_log_access_without_customer_id())
        
        def test_sync_payload(self):
            run_async_test(self.test_sync_logs_payload_includes_customer_id())
        
        def test_validate_response(self):
            run_async_test(self.test_validate_card_returns_customer_id())
        
        def test_whitelist_nullable(self):
            run_async_test(self.test_whitelist_customer_id_nullable())
    
    unittest.main(verbosity=2)