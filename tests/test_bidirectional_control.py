#!/usr/bin/env python3
"""
🔄 Test per il controllo bidirezionale del tornello

Testa che gli utenti non possano fare accessi consecutivi nella stessa direzione
quando il tornello è configurato in modalità bidirezionale.
"""

import unittest
import tempfile
import os
import asyncio
from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import RFIDGateConfig, SystemConfig

class TestBidirectionalControl(unittest.TestCase):
    """Test controllo accessi bidirezionali"""
    
    def setUp(self):
        """Setup per ogni test"""
        # Crea database temporaneo
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)
        
        # Configurazione base
        self.config = RFIDGateConfig()
        self.config.system = SystemConfig(
            tornello_id='test_tornello',
            bidirectional_mode=True  # ✨ Modalità bidirezionale abilitata
        )
        
        # Crea SyncManager
        self.sync_manager = SyncManager(self.config, self.db_path)
    
    def tearDown(self):
        """Cleanup dopo ogni test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    async def test_first_access_allowed(self):
        """Test: Primo accesso sempre permesso"""
        card_uid = "TEST123"
        
        # Primo accesso - dovrebbe essere permesso
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['reason'], 'Prima lettura carta')
        self.assertIsNone(result['last_direction'])
    
    async def test_consecutive_same_direction_denied(self):
        """Test: Accessi consecutivi stessa direzione negati"""
        card_uid = "TEST123"
        
        # Primo accesso IN
        await self.sync_manager.update_user_direction(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        # Secondo accesso IN - dovrebbe essere negato
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Accesso consecutivo stesso tipo', result['reason'])
        self.assertEqual(result['last_direction'], 'in')
    
    async def test_opposite_direction_allowed(self):
        """Test: Direzione opposta permessa"""
        card_uid = "TEST123"
        
        # Primo accesso IN
        await self.sync_manager.update_user_direction(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        # Accesso OUT - dovrebbe essere permesso
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="out",
            tornello_id="test_tornello"
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('Accesso valido', result['reason'])
        self.assertEqual(result['last_direction'], 'in')
    
    async def test_direction_sequence_workflow(self):
        """Test: Sequenza completa IN -> OUT -> IN"""
        card_uid = "TEST123"
        
        # 1. Primo accesso IN (sempre permesso)
        result1 = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid, direction="in", tornello_id="test_tornello"
        )
        self.assertTrue(result1['valid'])
        
        await self.sync_manager.update_user_direction(
            card_uid=card_uid, direction="in", tornello_id="test_tornello"
        )
        
        # 2. Secondo accesso IN (negato)
        result2 = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid, direction="in", tornello_id="test_tornello"
        )
        self.assertFalse(result2['valid'])
        
        # 3. Accesso OUT (permesso)
        result3 = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid, direction="out", tornello_id="test_tornello"
        )
        self.assertTrue(result3['valid'])
        
        await self.sync_manager.update_user_direction(
            card_uid=card_uid, direction="out", tornello_id="test_tornello"
        )
        
        # 4. Nuovo accesso IN (permesso dopo OUT)
        result4 = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid, direction="in", tornello_id="test_tornello"
        )
        self.assertTrue(result4['valid'])
    
    async def test_different_tornelli_independent(self):
        """Test: Tornelli diversi sono indipendenti"""
        card_uid = "TEST123"
        
        # Accesso IN su tornello 1
        await self.sync_manager.update_user_direction(
            card_uid=card_uid, 
            direction="in", 
            tornello_id="tornello_1"
        )
        
        # Accesso IN su tornello 2 - dovrebbe essere permesso
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in", 
            tornello_id="tornello_2"
        )
        
        self.assertTrue(result['valid'])
        self.assertIn('Accesso valido', result['reason'])
    
    async def test_multiple_users_independent(self):
        """Test: Utenti diversi sono indipendenti"""
        # User 1 accesso IN
        await self.sync_manager.update_user_direction(
            card_uid="USER1", direction="in", tornello_id="test_tornello"
        )
        
        # User 2 accesso IN - dovrebbe essere permesso
        result = await self.sync_manager.check_bidirectional_access(
            card_uid="USER2", 
            direction="in", 
            tornello_id="test_tornello"
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['reason'], 'Prima lettura carta')

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
    # Test specifici per bidirectional control
    test_case = TestBidirectionalControl()
    runner = AsyncTestRunner()
    
    print("🔄 Testing Bidirectional Control...")
    
    # Setup
    test_case.setUp()
    
    try:
        # Test 1: Primo accesso
        print("1. Testing first access...")
        runner.run_async_test(test_case.test_first_access_allowed)
        print("   ✅ First access allowed")
        
        # Test 2: Accessi consecutivi
        print("2. Testing consecutive same direction...")
        test_case.setUp()  # Reset
        runner.run_async_test(test_case.test_consecutive_same_direction_denied)
        print("   ✅ Consecutive same direction denied")
        
        # Test 3: Direzione opposta
        print("3. Testing opposite direction...")
        test_case.setUp()  # Reset
        runner.run_async_test(test_case.test_opposite_direction_allowed)
        print("   ✅ Opposite direction allowed")
        
        # Test 4: Sequenza completa
        print("4. Testing full workflow...")
        test_case.setUp()  # Reset
        runner.run_async_test(test_case.test_direction_sequence_workflow)
        print("   ✅ Full workflow correct")
        
        # Test 5: Tornelli diversi
        print("5. Testing different turnstiles...")
        test_case.setUp()  # Reset
        runner.run_async_test(test_case.test_different_tornelli_independent)
        print("   ✅ Different turnstiles independent")
        
        # Test 6: Utenti diversi
        print("6. Testing different users...")
        test_case.setUp()  # Reset
        runner.run_async_test(test_case.test_multiple_users_independent)
        print("   ✅ Different users independent")
        
        print()
        print("🎉 All bidirectional control tests PASSED!")
        print("🔄 Tornello bidirezionale funziona correttamente!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        test_case.tearDown()