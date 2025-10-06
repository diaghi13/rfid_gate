#!/usr/bin/env python3
"""
🧪 Performance Tests - RFID Gate System
=======================================

Test di performance e load testing per il sistema
"""

import unittest
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import statistics

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rfid_gate.utils.debounce import GlobalDebounceManager
from rfid_gate.hardware.readers.factory import ReaderFactory
from unittest.mock import Mock, patch


class TestPerformance(unittest.TestCase):
    """Test di performance del sistema"""
    
    def setUp(self):
        """Setup per test performance"""
        # Reset singleton debounce
        if hasattr(GlobalDebounceManager, '_instance'):
            GlobalDebounceManager._instance = None
    
    def test_debounce_performance(self):
        """Test performance sistema debounce"""
        debounce = GlobalDebounceManager.get_instance()
        debounce.configure_debounce_time(0.01)  # 10ms per test rapidi
        
        # Test con molte letture
        num_tests = 1000
        start_time = time.time()
        
        for i in range(num_tests):
            uid = f"UID{i:06d}"
            direction = "in" if i % 2 == 0 else "out"
            debounce.is_duplicate(uid, direction)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_check = (total_time / num_tests) * 1000  # ms
        
        print(f"\n📊 Debounce Performance:")
        print(f"   Total checks: {num_tests}")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Average per check: {avg_time_per_check:.3f}ms")
        print(f"   Checks per second: {num_tests/total_time:.0f}")
        
        # Performance assertion: dovrebbe gestire almeno 100 check/sec
        self.assertGreater(num_tests/total_time, 100)
        
        # Ogni check dovrebbe richiedere meno di 1ms
        self.assertLess(avg_time_per_check, 1.0)
    
    def test_concurrent_debounce_performance(self):
        """Test performance debounce con accesso concorrente"""
        debounce = GlobalDebounceManager.get_instance()
        debounce.configure_debounce_time(0.01)
        
        def worker_thread(thread_id, num_operations):
            """Worker thread per test concorrenti"""
            times = []
            for i in range(num_operations):
                start = time.time()
                uid = f"T{thread_id}_UID{i:04d}"
                direction = "in" if i % 2 == 0 else "out"
                debounce.is_duplicate(uid, direction)
                end = time.time()
                times.append((end - start) * 1000)  # ms
            return times
        
        # Test con 4 thread, 250 operazioni ciascuno
        num_threads = 4
        operations_per_thread = 250
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for thread_id in range(num_threads):
                future = executor.submit(worker_thread, thread_id, operations_per_thread)
                futures.append(future)
            
            # Raccogli risultati
            all_times = []
            for future in futures:
                thread_times = future.result()
                all_times.extend(thread_times)
        
        end_time = time.time()
        total_time = end_time - start_time
        total_operations = num_threads * operations_per_thread
        
        print(f"\n📊 Concurrent Debounce Performance:")
        print(f"   Threads: {num_threads}")
        print(f"   Total operations: {total_operations}")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Operations per second: {total_operations/total_time:.0f}")
        print(f"   Average time per operation: {statistics.mean(all_times):.3f}ms")
        print(f"   Max time per operation: {max(all_times):.3f}ms")
        
        # Performance assertions
        self.assertGreater(total_operations/total_time, 50)  # Almeno 50 ops/sec
        self.assertLess(max(all_times), 10.0)  # Max 10ms per operazione
    
    @patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522')
    def test_reader_creation_performance(self, mock_mfrc522):
        """Test performance creazione lettori"""
        mock_device = Mock()
        mock_mfrc522.return_value = mock_device
        
        num_readers = 100
        
        start_time = time.time()
        
        readers = []
        for i in range(num_readers):
            config = {
                'reader_type': 'mfrc522',
                'reader_id': f'reader_{i}',
                'direction': 'in' if i % 2 == 0 else 'out',
                'rst_pin': 22,
                'sda_pin': 8
            }
            reader = ReaderFactory.create_reader(config)
            readers.append(reader)
        
        end_time = time.time()
        creation_time = end_time - start_time
        avg_creation_time = (creation_time / num_readers) * 1000  # ms
        
        print(f"\n📊 Reader Creation Performance:")
        print(f"   Readers created: {num_readers}")
        print(f"   Total time: {creation_time:.3f}s")
        print(f"   Average creation time: {avg_creation_time:.3f}ms")
        print(f"   Creations per second: {num_readers/creation_time:.0f}")
        
        # Performance assertions
        self.assertLess(avg_creation_time, 10.0)  # Max 10ms per creazione
        self.assertEqual(len(readers), num_readers)
    
    def test_memory_usage_stability(self):
        """Test stabilità uso memoria durante operazioni ripetute"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        debounce = GlobalDebounceManager.get_instance()
        
        # Esegui molte operazioni per verificare memory leaks
        for cycle in range(10):
            for i in range(1000):
                uid = f"CYCLE{cycle}_UID{i:04d}"
                debounce.is_duplicate(uid, "in")
            
            # Reset periodico per simulare uso reale
            if cycle % 3 == 0:
                debounce.reset_stats()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n📊 Memory Usage:")
        print(f"   Initial memory: {initial_memory:.2f} MB")
        print(f"   Final memory: {final_memory:.2f} MB")
        print(f"   Memory increase: {memory_increase:.2f} MB")
        
        # Memory increase dovrebbe essere minimo (< 5MB)
        self.assertLess(memory_increase, 5.0)
    
    def test_high_frequency_card_reads(self):
        """Test gestione letture ad alta frequenza"""
        debounce = GlobalDebounceManager.get_instance()
        debounce.configure_debounce_time(0.1)  # 100ms
        
        # Simula letture molto frequenti della stessa carta
        uid = "HIGHFREQ12345678"
        direction = "in"
        
        read_times = []
        duplicate_count = 0
        
        # Test per 1 secondo con letture ogni 1ms
        start_time = time.time()
        while time.time() - start_time < 1.0:
            read_start = time.time()
            is_duplicate = debounce.is_duplicate(uid, direction)
            read_end = time.time()
            
            read_times.append((read_end - read_start) * 1000)  # ms
            
            if is_duplicate:
                duplicate_count += 1
            
            time.sleep(0.001)  # 1ms between reads
        
        total_reads = len(read_times)
        avg_read_time = statistics.mean(read_times)
        
        print(f"\n📊 High Frequency Read Performance:")
        print(f"   Total reads: {total_reads}")
        print(f"   Duplicates detected: {duplicate_count}")
        print(f"   Duplicate rate: {(duplicate_count/total_reads)*100:.1f}%")
        print(f"   Average read time: {avg_read_time:.3f}ms")
        print(f"   Max read time: {max(read_times):.3f}ms")
        
        # Performance assertions
        self.assertLess(avg_read_time, 0.5)  # Media < 0.5ms
        self.assertLess(max(read_times), 2.0)  # Max < 2ms
        self.assertGreater(duplicate_count, 0)  # Dovrebbe rilevare duplicati
    
    def test_stats_collection_performance(self):
        """Test performance raccolta statistiche"""
        debounce = GlobalDebounceManager.get_instance()
        
        # Genera molte operazioni per avere statistiche significative
        for i in range(1000):
            uid = f"STATS_UID_{i:04d}"
            direction = "in" if i % 3 == 0 else "out"
            debounce.is_duplicate(uid, direction)
        
        # Misura tempo di raccolta statistiche
        stats_times = []
        for _ in range(100):
            start = time.time()
            stats = debounce.get_stats()
            end = time.time()
            stats_times.append((end - start) * 1000)  # ms
        
        avg_stats_time = statistics.mean(stats_times)
        
        print(f"\n📊 Stats Collection Performance:")
        print(f"   Stats collections: {len(stats_times)}")
        print(f"   Average collection time: {avg_stats_time:.3f}ms")
        print(f"   Max collection time: {max(stats_times):.3f}ms")
        print(f"   Total checks in stats: {stats['total_checks']}")
        
        # Performance assertions
        self.assertLess(avg_stats_time, 1.0)  # Media < 1ms
        self.assertGreater(stats['total_checks'], 0)
    
    def test_edge_case_performance(self):
        """Test performance casi edge"""
        debounce = GlobalDebounceManager.get_instance()
        
        edge_cases = [
            ("", "in"),  # UID vuoto
            (None, "out"),  # UID None
            ("A" * 100, "in"),  # UID molto lungo
            ("🔴🟡🟢", "out"),  # UID con emoji
            ("12345678", "custom_direction"),  # Direzione custom
        ]
        
        for uid, direction in edge_cases:
            times = []
            for _ in range(100):
                start = time.time()
                try:
                    result = debounce.is_duplicate(uid, direction)
                    end = time.time()
                    times.append((end - start) * 1000)  # ms
                    # Verifica che restituisca sempre un bool
                    self.assertIsInstance(result, bool)
                except Exception as e:
                    self.fail(f"Exception with uid='{uid}', direction='{direction}': {e}")
            
            if times:  # Se ci sono misurazioni valide
                avg_time = statistics.mean(times)
                print(f"   Edge case '{uid}'/'{direction}': {avg_time:.3f}ms avg")
                
                # Anche i casi edge dovrebbero essere rapidi
                self.assertLess(avg_time, 2.0)


class TestLoadTesting(unittest.TestCase):
    """Test di carico per il sistema"""
    
    def test_sustained_load(self):
        """Test carico sostenuto"""
        debounce = GlobalDebounceManager.get_instance()
        debounce.configure_debounce_time(0.05)  # 50ms
        
        # Test per 5 secondi con carico costante
        duration = 5.0  # secondi
        target_rate = 100  # operazioni/secondo
        
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration:
            batch_start = time.time()
            
            # Batch di operazioni
            for i in range(10):
                uid = f"LOAD_{operations:06d}"
                direction = "in" if operations % 2 == 0 else "out"
                debounce.is_duplicate(uid, direction)
                operations += 1
            
            # Controlla rate
            batch_time = time.time() - batch_start
            expected_batch_time = 10 / target_rate  # 10 ops a target_rate
            
            if batch_time < expected_batch_time:
                time.sleep(expected_batch_time - batch_time)
        
        actual_duration = time.time() - start_time
        actual_rate = operations / actual_duration
        
        print(f"\n📊 Sustained Load Test:")
        print(f"   Duration: {actual_duration:.2f}s")
        print(f"   Operations: {operations}")
        print(f"   Target rate: {target_rate} ops/s")
        print(f"   Actual rate: {actual_rate:.1f} ops/s")
        
        # Verifica che il sistema abbia mantenuto il carico
        self.assertGreater(actual_rate, target_rate * 0.9)  # 90% del target


if __name__ == '__main__':
    unittest.main(verbosity=2)