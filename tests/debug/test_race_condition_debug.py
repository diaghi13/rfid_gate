#!/usr/bin/env python3
"""
🧪 TEST DEBOUNCE RACE CONDITION
===============================

Test per verificare il problema delle due chiamate simultanee
rilevato nei log:

1777 16/10/2025, 17:51:58 F24FC4EB PIETRO SALERNO NEGATO "Cannot in again"
1776 16/10/2025, 17:51:58 F24FC4EB PIETRO SALERNO CONCESSO "Cache"

Questo test verifica:
- Sistema di debounce globale
- Race conditions possibili
- Timing del controllo bidirezionale
- Prevenzione letture duplicate
"""

import sys
import os
import asyncio
import time
import threading
from datetime import datetime
from pathlib import Path

# Aggiungi path per importare il sistema RFID
sys.path.append(str(Path(__file__).parent))

from rfid_gate.utils.debounce import GlobalDebounceManager
from rfid_gate.hardware.readers.base import CardEvent
from rfid_gate.network.sync_manager import SyncManager

class DebounceRaceConditionTester:
    """Tester per race conditions nel debounce"""
    
    def __init__(self):
        # Crea nuova istanza per test pulito
        self.debounce = GlobalDebounceManager(global_debounce_time=0.8)
        
        self.test_results = []
        
        print("🔧 CONFIGURAZIONE TEST RACE CONDITION")
        print("=" * 45)
        print(f"⏱️ Global Debounce Time: {self.debounce.global_debounce_time}s")
        print(f"🃏 Test Card: F24FC4EB (PIETRO SALERNO)")
        print()
    
    def test_single_thread_debounce(self):
        """Test debounce in singolo thread (comportamento normale)"""
        
        print("🧪 TEST 1: Debounce Singolo Thread")
        print("-" * 40)
        
        card_uid = "F24FC4EB"
        direction = "in"
        
        # Prima lettura
        start_time = time.time()
        result1 = self.debounce.is_duplicate(card_uid, direction, "reader_in")
        time1 = time.time()
        
        print(f"   Prima lettura: {result1} (duplicato: {'❌ NO' if not result1 else '✅ SÌ'})")
        
        # Seconda lettura immediata
        result2 = self.debounce.is_duplicate(card_uid, direction, "reader_in")
        time2 = time.time()
        
        print(f"   Seconda lettura: {result2} (duplicato: {'❌ NO' if not result2 else '✅ SÌ'})")
        print(f"   Intervallo: {(time2 - time1) * 1000:.1f}ms")
        
        # Terza lettura dopo breve pausa
        time.sleep(0.05)  # 50ms
        result3 = self.debounce.is_duplicate(card_uid, direction, "reader_in")
        time3 = time.time()
        
        print(f"   Terza lettura (+50ms): {result3} (duplicato: {'❌ NO' if not result3 else '✅ SÌ'})")
        print(f"   Intervallo totale: {(time3 - start_time) * 1000:.1f}ms")
        
        stats = self.debounce.get_stats()
        print(f"   Stats: {stats}")
        
        # Verifica comportamento atteso
        expected_ok = not result1 and result2 and result3
        
        print(f"\n   ✅ Risultato: {'CORRETTO' if expected_ok else 'PROBLEMA!'}")
        
        return {
            "test": "single_thread_debounce",
            "results": [result1, result2, result3],
            "timing": [(time1-start_time), (time2-start_time), (time3-start_time)],
            "stats": stats,
            "correct": expected_ok
        }
    
    def test_multithread_race_condition(self):
        """Test race condition multi-thread"""
        
        print(f"\n🧪 TEST 2: Race Condition Multi-Thread")
        print("-" * 45)
        
        card_uid = "F24FC4EB"
        direction = "in"
        results = []
        start_time = time.time()
        
        def read_card_thread(thread_id, delay_ms=0):
            """Simula lettura carta in thread separato"""
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            timestamp = time.time()
            is_duplicate = self.debounce.is_duplicate(card_uid, direction, f"reader_{thread_id}")
            
            results.append({
                'thread_id': thread_id,
                'timestamp': timestamp,
                'is_duplicate': is_duplicate,
                'relative_time_ms': (timestamp - start_time) * 1000
            })
            
            print(f"   Thread {thread_id}: {is_duplicate} (duplicato: {'✅ SÌ' if is_duplicate else '❌ NO'}) @ {(timestamp - start_time) * 1000:.1f}ms")
        
        # Crea 5 thread che leggono la stessa carta quasi simultaneamente
        threads = []
        for i in range(5):
            delay = i * 1  # 1ms di delay incrementale
            thread = threading.Thread(target=read_card_thread, args=(i, delay))
            threads.append(thread)
        
        # Avvia tutti i thread
        for thread in threads:
            thread.start()
        
        # Aspetta completamento
        for thread in threads:
            thread.join()
        
        # Ordina risultati per timestamp
        results_sorted = sorted(results, key=lambda x: x['timestamp'])
        
        print(f"\n   📊 RISULTATI ORDINATI:")
        for i, result in enumerate(results_sorted):
            status = "PRIMO" if i == 0 else "DUPLICATO" if result['is_duplicate'] else "BYPASS!"
            print(f"   {i+1}. Thread {result['thread_id']}: {status} @ {result['relative_time_ms']:.1f}ms")
        
        # Verifica: solo il primo dovrebbe passare
        first_should_pass = not results_sorted[0]['is_duplicate']
        others_should_block = all(r['is_duplicate'] for r in results_sorted[1:])
        
        race_condition_ok = first_should_pass and others_should_block
        
        print(f"\n   ✅ Race Condition: {'PREVENUTA' if race_condition_ok else 'RILEVATA!'}")
        
        if not race_condition_ok:
            bypassed = [r for r in results_sorted[1:] if not r['is_duplicate']]
            print(f"   ⚠️ Bypass rilevati: {len(bypassed)}")
            for bypass in bypassed:
                print(f"      - Thread {bypass['thread_id']} @ {bypass['relative_time_ms']:.1f}ms")
        
        return {
            "test": "multithread_race_condition",
            "results": results_sorted,
            "race_condition_prevented": race_condition_ok,
            "bypassed_count": len([r for r in results_sorted[1:] if not r['is_duplicate']])
        }
    
    def test_bidirectional_timing_issue(self):
        """Test timing issue nel controllo bidirezionale"""
        
        print(f"\n🧪 TEST 3: Timing Issue Controllo Bidirezionale")
        print("-" * 55)
        
        card_uid = "F24FC4EB"
        
        # Reset debounce per test pulito
        self.debounce.clear_all()
        
        # Simula scenario reale: 
        # 1. Prima lettura autorizzata (cache)
        # 2. Seconda lettura negata (controllo bidirezionale)
        
        print("   🔄 SCENARIO SIMULATO:")
        print("   1. Lettura carta → Cache hit → AUTORIZZATO")
        print("   2. Lettura carta → Controllo bidirezionale → NEGATO")
        print()
        
        # Step 1: Prima lettura (dovrebbe passare)
        print("   STEP 1: Prima lettura")
        time1 = time.time()
        result1 = self.debounce.is_duplicate(card_uid, "in", "reader_in")
        print(f"   Debounce result: {result1} (dovrebbe essere False)")
        
        # Simula breve processing time
        time.sleep(0.001)  # 1ms processing
        
        # Step 2: Seconda lettura immediata (controllo bidirezionale)
        print(f"\n   STEP 2: Seconda lettura (dopo 1ms)")
        time2 = time.time()
        result2 = self.debounce.is_duplicate(card_uid, "in", "reader_in")
        print(f"   Debounce result: {result2} (dovrebbe essere True)")
        
        interval_ms = (time2 - time1) * 1000
        print(f"   Intervallo: {interval_ms:.3f}ms")
        
        # Verifica se il sistema ha prevenuto la doppia lettura
        timing_issue_prevented = not result1 and result2
        
        print(f"\n   ✅ Timing Issue: {'PREVENUTO' if timing_issue_prevented else 'PRESENTE!'}")
        
        if not timing_issue_prevented:
            print(f"   ⚠️ PROBLEMA: Entrambe le letture sono passate!")
            print(f"      - Prima lettura: {'PASSATA' if not result1 else 'BLOCCATA'}")
            print(f"      - Seconda lettura: {'PASSATA' if not result2 else 'BLOCCATA'}")
        
        return {
            "test": "bidirectional_timing_issue",
            "first_read_blocked": result1,
            "second_read_blocked": result2,
            "interval_ms": interval_ms,
            "timing_issue_prevented": timing_issue_prevented
        }
    
    def test_real_scenario_reproduction(self):
        """Tenta di riprodurre lo scenario reale dei log"""
        
        print(f"\n🧪 TEST 4: Riproduzione Scenario Reale")
        print("-" * 45)
        
        card_uid = "F24FC4EB"
        
        # Reset per test pulito
        self.debounce.clear_all()
        
        print("   📋 SCENARIO DEI LOG:")
        print("   1777 17:51:58 F24FC4EB NEGATO 'Cannot in again'")
        print("   1776 17:51:58 F24FC4EB CONCESSO 'Cache'")
        print()
        
        # Simula timing molto stretto
        results = []
        
        # Thread 1: Processing cache (dovrebbe essere primo)
        def cache_processing():
            time.sleep(0.0001)  # Tiny delay
            timestamp = time.time()
            is_dup = self.debounce.is_duplicate(card_uid, "in", "cache_thread")
            results.append({
                'type': 'CACHE',
                'timestamp': timestamp,
                'blocked': is_dup,
                'result': 'CONCESSO' if not is_dup else 'NEGATO'
            })
        
        # Thread 2: Processing bidirectional (dovrebbe essere secondo)
        def bidirectional_processing():
            time.sleep(0.0002)  # Slightly more delay
            timestamp = time.time()
            is_dup = self.debounce.is_duplicate(card_uid, "in", "bidirectional_thread")
            results.append({
                'type': 'BIDIRECTIONAL',
                'timestamp': timestamp,
                'blocked': is_dup,
                'result': 'NEGATO' if is_dup else 'CONCESSO'
            })
        
        # Avvia processing simultaneo
        start_time = time.time()
        
        thread1 = threading.Thread(target=cache_processing)
        thread2 = threading.Thread(target=bidirectional_processing)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Ordina per timestamp
        results_sorted = sorted(results, key=lambda x: x['timestamp'])
        
        print("   🎯 RISULTATI RIPRODUZIONE:")
        for i, result in enumerate(results_sorted, 1):
            relative_time = (result['timestamp'] - start_time) * 1000
            print(f"   {i}. {result['type']}: {result['result']} @ {relative_time:.3f}ms")
        
        # Verifica se abbiamo riprodotto lo scenario
        scenario_reproduced = (
            len(results_sorted) == 2 and
            results_sorted[0]['result'] == 'CONCESSO' and
            results_sorted[1]['result'] == 'NEGATO'
        )
        
        print(f"\n   ✅ Scenario: {'RIPRODOTTO' if scenario_reproduced else 'NON RIPRODOTTO'}")
        
        return {
            "test": "real_scenario_reproduction",
            "results": results_sorted,
            "scenario_reproduced": scenario_reproduced
        }
    
    def generate_race_condition_report(self):
        """Report finale sui race condition"""
        
        print(f"\n{'='*70}")
        print("📊 REPORT RACE CONDITION DEBOUNCE")
        print(f"{'='*70}")
        
        print(f"🃏 CARTA TESTATA: F24FC4EB (PIETRO SALERNO)")
        print(f"⏱️ DEBOUNCE TIME: {self.debounce.global_debounce_time}s")
        print()
        
        print(f"📋 SUMMARY TEST:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result.get('correct', result.get('timing_issue_prevented', result.get('race_condition_prevented', False))) else "❌ FAIL"
            print(f"   {i}. {result['test']}: {status}")
        
        print()
        
        # Analisi problemi rilevati
        race_issues = [r for r in self.test_results if not r.get('race_condition_prevented', True)]
        timing_issues = [r for r in self.test_results if not r.get('timing_issue_prevented', True)]
        
        if race_issues or timing_issues:
            print(f"⚠️ PROBLEMI RILEVATI:")
            
            if race_issues:
                print(f"   🏃 Race Conditions: {len(race_issues)}")
                for issue in race_issues:
                    bypass_count = issue.get('bypassed_count', 0)
                    if bypass_count > 0:
                        print(f"      - {issue['test']}: {bypass_count} bypass rilevati")
            
            if timing_issues:
                print(f"   ⏱️ Timing Issues: {len(timing_issues)}")
        else:
            print(f"✅ NESSUN PROBLEMA RILEVATO")
        
        print()
        
        # Raccomandazioni
        print(f"💡 RACCOMANDAZIONI:")
        if race_issues:
            print(f"   1. 🔒 Implementare mutex nel debounce manager")
            print(f"   2. ⏱️ Aumentare debounce time a 1.0s")
            print(f"   3. 🔄 Aggiungere controllo atomico nelle operazioni")
        
        if timing_issues:
            print(f"   4. 📊 Implementare ordinamento timestamp nei log")
            print(f"   5. 🎯 Aggiungere ID univoco per ogni processo")
        
        if not race_issues and not timing_issues:
            print(f"   ✅ Sistema debounce funziona correttamente")

async def main():
    """Funzione principale"""
    
    print("🚀 TEST RACE CONDITION - DEBOUNCE SYSTEM")
    print("=" * 55)
    print(f"⏰ Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 OBIETTIVO:")
    print("   Verificare il problema delle due chiamate simultanee")
    print("   rilevato nei log per la carta F24FC4EB")
    print()
    
    tester = DebounceRaceConditionTester()
    
    try:
        # Test 1: Debounce normale
        result1 = tester.test_single_thread_debounce()
        tester.test_results.append(result1)
        
        # Test 2: Race condition multi-thread
        result2 = tester.test_multithread_race_condition()
        tester.test_results.append(result2)
        
        # Test 3: Timing issue bidirezionale
        result3 = tester.test_bidirectional_timing_issue()
        tester.test_results.append(result3)
        
        # Test 4: Riproduzione scenario reale
        result4 = tester.test_real_scenario_reproduction()
        tester.test_results.append(result4)
        
        # Report finale
        tester.generate_race_condition_report()
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto")
        return False
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n🏁 Test {'✅ COMPLETATO' if success else '❌ FALLITO'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Errore critico: {e}")
        sys.exit(1)