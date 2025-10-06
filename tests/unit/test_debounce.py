#!/usr/bin/env python3
"""
🧪 Test Debounce System
======================

Test per il sistema di debounce globale.
Verifica prevenzione duplicati e anti-crosstalk.
"""

import time
import unittest
from rfid_gate.utils.debounce import GlobalDebounceManager, DebounceEntry


class TestGlobalDebounceManager(unittest.TestCase):
    """Test per il manager globale di debounce"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.debounce = GlobalDebounceManager(global_debounce_time=0.5)
    
    def test_initialization(self):
        """Test inizializzazione manager"""
        self.assertEqual(self.debounce.global_debounce_time, 0.5)
        self.assertEqual(len(self.debounce.last_reads), 0)
        self.assertIsNone(self.debounce.global_last_read)
        self.assertEqual(self.debounce.stats['total_checks'], 0)
    
    def test_first_read_not_duplicate(self):
        """Test che la prima lettura non sia duplicata"""
        uid = "12345678"
        direction = "in"
        reader_id = "reader_in"
        
        is_duplicate = self.debounce.is_duplicate(uid, direction, reader_id)
        
        self.assertFalse(is_duplicate)
        self.assertEqual(self.debounce.stats['total_checks'], 1)
        self.assertEqual(self.debounce.stats['duplicates_detected'], 0)
    
    def test_immediate_duplicate_same_direction(self):
        """Test duplicato immediato stessa direzione"""
        uid = "12345678"
        direction = "in"
        reader_id = "reader_in"
        
        # Prima lettura
        self.assertFalse(self.debounce.is_duplicate(uid, direction, reader_id))
        
        # Seconda lettura immediata - dovrebbe essere duplicato
        self.assertTrue(self.debounce.is_duplicate(uid, direction, reader_id))
        self.assertEqual(self.debounce.stats['duplicates_detected'], 1)
    
    def test_different_uids_not_duplicate(self):
        """Test che UID diversi non siano considerati duplicati"""
        direction = "in"
        reader_id = "reader_in"
        
        # Prima carta
        self.assertFalse(self.debounce.is_duplicate("12345678", direction, reader_id))
        
        # Carta diversa - non dovrebbe essere duplicato
        self.assertFalse(self.debounce.is_duplicate("87654321", direction, reader_id))
        self.assertEqual(self.debounce.stats['duplicates_detected'], 0)
    
    def test_global_debounce_different_directions(self):
        """Test debounce globale tra direzioni diverse"""
        uid = "12345678"
        reader_in = "reader_in"
        reader_out = "reader_out"
        
        # Lettura in entrata
        self.assertFalse(self.debounce.is_duplicate(uid, "in", reader_in))
        
        # Lettura in uscita immediata dello stesso UID - dovrebbe essere bloccata
        self.assertTrue(self.debounce.is_duplicate(uid, "out", reader_out))
        self.assertEqual(self.debounce.stats['global_blocks'], 1)
    
    def test_debounce_expires_after_time(self):
        """Test che il debounce scada dopo il tempo configurato"""
        uid = "12345678"
        direction = "in"
        reader_id = "reader_in"
        
        # Prima lettura
        self.assertFalse(self.debounce.is_duplicate(uid, direction, reader_id))
        
        # Simula passaggio tempo maggiore del debounce
        time.sleep(0.6)  # Maggiore di 0.5 secondi configurati
        
        # Dovrebbe permettere la lettura
        self.assertFalse(self.debounce.is_duplicate(uid, direction, reader_id))
    
    def test_configure_debounce_time(self):
        """Test configurazione tempo di debounce"""
        custom_debounce = GlobalDebounceManager(global_debounce_time=1.0)
        self.assertEqual(custom_debounce.global_debounce_time, 1.0)
    
    def test_multiple_directions_tracking(self):
        """Test tracciamento multiple direzioni"""
        uid = "12345678"
        
        # Lettura in entrata
        self.debounce.is_duplicate(uid, "in", "reader_in")
        
        # Lettura in uscita (bloccata da debounce globale)
        self.debounce.is_duplicate(uid, "out", "reader_out")
        
        # Verifica che entrambe le direzioni siano tracciate
        self.assertIn("in", self.debounce.last_reads)
        # "out" potrebbe non essere in last_reads se bloccato
    
    def test_stats_tracking(self):
        """Test tracciamento statistiche"""
        uid1 = "12345678"
        uid2 = "87654321"
        
        # Varie operazioni
        self.debounce.is_duplicate(uid1, "in", "reader_in")
        self.debounce.is_duplicate(uid1, "in", "reader_in")  # Duplicato
        self.debounce.is_duplicate(uid2, "out", "reader_out")
        self.debounce.is_duplicate(uid1, "out", "reader_out")  # Globale
        
        stats = self.debounce.get_stats()
        self.assertEqual(stats['total_checks'], 4)
        self.assertGreaterEqual(stats['duplicates_detected'], 1)
    
    def test_reset_stats(self):
        """Test reset statistiche"""
        uid = "12345678"
        
        # Genera alcune statistiche
        self.debounce.is_duplicate(uid, "in", "reader_in")
        self.debounce.is_duplicate(uid, "in", "reader_in")  # Duplicato
        
        # Reset
        self.debounce.reset_stats()
        
        stats = self.debounce.get_stats()
        self.assertEqual(stats['total_checks'], 0)
        self.assertEqual(stats['duplicates_detected'], 0)
        self.assertEqual(stats['global_blocks'], 0)
        self.assertEqual(stats['direction_blocks'], 0)
    
    def test_last_read_info(self):
        """Test informazioni ultima lettura"""
        uid = "12345678"
        direction = "in"
        reader_id = "reader_in"
        
        # Prima lettura
        self.debounce.is_duplicate(uid, direction, reader_id)
        
        last_read = self.debounce.get_last_read_info(direction)
        self.assertIsNotNone(last_read)
        self.assertEqual(last_read.uid, uid)
        self.assertEqual(last_read.direction, direction)
        self.assertEqual(last_read.reader_id, reader_id)
    
    def test_edge_case_empty_uid(self):
        """Test caso edge con UID vuoto"""
        # UID vuoto dovrebbe essere gestito correttamente
        self.assertFalse(self.debounce.is_duplicate("", "in", "reader_in"))
        self.assertFalse(self.debounce.is_duplicate("", "in", "reader_in"))
    
    def test_edge_case_none_uid(self):
        """Test caso edge con UID None"""
        # UID None dovrebbe essere gestito correttamente
        self.assertFalse(self.debounce.is_duplicate(None, "in", "reader_in"))
    
    def test_long_uid_handling(self):
        """Test gestione UID lunghi"""
        long_uid = "A" * 100  # UID molto lungo
        
        self.assertFalse(self.debounce.is_duplicate(long_uid, "in", "reader_in"))
        self.assertTrue(self.debounce.is_duplicate(long_uid, "in", "reader_in"))
    
    def test_concurrent_access_simulation(self):
        """Test simulazione accesso concorrente"""
        uid = "12345678"
        
        # Simula accessi rapidi da lettori diversi
        results = []
        for i in range(5):
            direction = "in" if i % 2 == 0 else "out"
            reader_id = f"reader_{direction}"
            result = self.debounce.is_duplicate(uid, direction, reader_id)
            results.append(result)
        
        # Primo accesso dovrebbe essere accettato, altri duplicati
        self.assertFalse(results[0])  # Primo accesso OK
        # Altri dovrebbero essere per lo più duplicati
        duplicate_count = sum(1 for r in results[1:] if r)
        self.assertGreater(duplicate_count, 0)


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rfid_gate.utils.debounce import GlobalDebounceManager


class TestGlobalDebounceManager(unittest.TestCase):
    """Test del sistema di debounce globale"""
    
    def setUp(self):
        """Setup per ogni test"""
        # Reset singleton per ogni test
        if hasattr(GlobalDebounceManager, '_instance'):
            GlobalDebounceManager._instance = None
        
        self.debounce = GlobalDebounceManager.get_instance()
        self.debounce.global_debounce_time = 0.1  # 100ms per test rapidi
    
    def test_singleton_pattern(self):
        """Test che sia un singleton"""
        instance1 = GlobalDebounceManager.get_instance()
        instance2 = GlobalDebounceManager.get_instance()
        
        self.assertIs(instance1, instance2)
    
    def test_first_read_not_duplicate(self):
        """Test che la prima lettura non sia duplicata"""
        result = self.debounce.is_duplicate("123456", "in")
        
        self.assertFalse(result)
        self.assertEqual(self.debounce.stats['total_checks'], 1)
        self.assertEqual(self.debounce.stats['duplicates_detected'], 0)
    
    def test_immediate_duplicate_same_direction(self):
        """Test duplicato immediato stessa direzione"""
        uid = "123456"
        direction = "in"
        
        # Prima lettura
        result1 = self.debounce.is_duplicate(uid, direction)
        # Seconda lettura immediata
        result2 = self.debounce.is_duplicate(uid, direction)
        
        self.assertFalse(result1)
        self.assertTrue(result2)
        self.assertEqual(self.debounce.stats['duplicates_detected'], 1)
    
    def test_global_debounce_different_directions(self):
        """Test debounce globale tra direzioni diverse"""
        uid = "123456"
        
        # Prima lettura IN
        result1 = self.debounce.is_duplicate(uid, "in")
        # Lettura immediata OUT (stesso UID)
        result2 = self.debounce.is_duplicate(uid, "out")
        
        self.assertFalse(result1)
        self.assertTrue(result2)  # Bloccata dal debounce globale
        self.assertEqual(self.debounce.stats['global_blocks'], 1)
    
    def test_debounce_expires_after_time(self):
        """Test che il debounce scada dopo il tempo configurato"""
        uid = "123456"
        direction = "in"
        
        # Prima lettura
        result1 = self.debounce.is_duplicate(uid, direction)
        
        # Simula passaggio del tempo
        with patch('time.time') as mock_time:
            # Tempo attuale + debounce_time + 0.01
            mock_time.return_value = time.time() + self.debounce.global_debounce_time + 0.01
            
            result2 = self.debounce.is_duplicate(uid, direction)
        
        self.assertFalse(result1)
        self.assertFalse(result2)  # Non più duplicato dopo scadenza
    
    def test_different_uids_not_duplicate(self):
        """Test che UID diversi non siano considerati duplicati"""
        result1 = self.debounce.is_duplicate("123456", "in")
        result2 = self.debounce.is_duplicate("789ABC", "in")
        
        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertEqual(self.debounce.stats['duplicates_detected'], 0)
    
    def test_stats_tracking(self):
        """Test tracciamento statistiche"""
        # Reset stats
        self.debounce.reset_stats()
        
        self.debounce.is_duplicate("111111", "in")    # Prima lettura
        self.debounce.is_duplicate("111111", "in")    # Duplicato direzione
        self.debounce.is_duplicate("111111", "out")   # Duplicato globale
        self.debounce.is_duplicate("222222", "in")    # Nuovo UID
        
        stats = self.debounce.get_stats()
        
        self.assertEqual(stats['total_checks'], 4)
        self.assertEqual(stats['duplicates_detected'], 2)
        self.assertEqual(stats['global_blocks'], 1)
        self.assertEqual(stats['direction_blocks'], 1)
        self.assertIn('in', stats['tracked_directions'])
        self.assertIn('out', stats['tracked_directions'])
    
    def test_reset_stats(self):
        """Test reset statistiche"""
        # Genera alcune statistiche
        self.debounce.is_duplicate("123456", "in")
        self.debounce.is_duplicate("123456", "in")
        
        # Reset
        self.debounce.reset_stats()
        stats = self.debounce.get_stats()
        
        self.assertEqual(stats['total_checks'], 0)
        self.assertEqual(stats['duplicates_detected'], 0)
        self.assertEqual(stats['global_blocks'], 0)
        self.assertEqual(stats['direction_blocks'], 0)
    
    def test_configure_debounce_time(self):
        """Test configurazione tempo di debounce"""
        new_time = 0.5
        self.debounce.configure_debounce_time(new_time)
        
        self.assertEqual(self.debounce.global_debounce_time, new_time)
    
    def test_last_read_info(self):
        """Test informazioni ultima lettura"""
        uid = "ABCDEF"
        direction = "out"
        
        self.debounce.is_duplicate(uid, direction)
        stats = self.debounce.get_stats()
        
        self.assertIn('last_global_read', stats)
        last_read = stats['last_global_read']
        
        self.assertEqual(last_read['uid'], uid)
        self.assertEqual(last_read['direction'], direction)
        self.assertIsInstance(last_read['timestamp'], float)
    
    def test_multiple_directions_tracking(self):
        """Test tracciamento multiple direzioni"""
        self.debounce.is_duplicate("111", "in")
        self.debounce.is_duplicate("222", "out")
        self.debounce.is_duplicate("333", "manual")  # Direzione custom
        
        stats = self.debounce.get_stats()
        directions = stats['tracked_directions']
        
        self.assertIn('in', directions)
        self.assertIn('out', directions)
        self.assertIn('manual', directions)
        self.assertEqual(len(directions), 3)
    
    def test_edge_case_empty_uid(self):
        """Test caso edge con UID vuoto"""
        result1 = self.debounce.is_duplicate("", "in")
        result2 = self.debounce.is_duplicate("", "in")
        
        # Dovrebbe gestire anche UID vuoti
        self.assertFalse(result1)
        self.assertTrue(result2)
    
    def test_edge_case_none_uid(self):
        """Test caso edge con UID None"""
        result1 = self.debounce.is_duplicate(None, "in")
        result2 = self.debounce.is_duplicate(None, "in")
        
        # Dovrebbe gestire anche UID None senza errori
        self.assertFalse(result1)
        # Potrebbe essere True o False a seconda dell'implementazione
        # Ma non dovrebbe crashare
        self.assertIsInstance(result2, bool)
    
    def test_long_uid_handling(self):
        """Test gestione UID lunghi"""
        long_uid = "A" * 100  # UID molto lungo
        
        result1 = self.debounce.is_duplicate(long_uid, "in")
        result2 = self.debounce.is_duplicate(long_uid, "in")
        
        self.assertFalse(result1)
        self.assertTrue(result2)
    
    def test_concurrent_access_simulation(self):
        """Test simulazione accesso concorrente"""
        uid = "CONCURRENT"
        
        # Simula letture molto rapide
        results = []
        for i in range(10):
            direction = "in" if i % 2 == 0 else "out"
            result = self.debounce.is_duplicate(uid, direction)
            results.append(result)
        
        # La prima dovrebbe essere False, le altre True (duplicate)
        self.assertFalse(results[0])
        # Almeno alcune delle successive dovrebbero essere True
        self.assertTrue(any(results[1:]))


if __name__ == '__main__':
    unittest.main(verbosity=2)