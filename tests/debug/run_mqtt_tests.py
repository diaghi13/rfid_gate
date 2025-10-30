#!/usr/bin/env python3
"""
🧪 MQTT Test Runner
==================
Script di utilità per eseguire tutti i test MQTT dalla cartella corretta
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Esegue comando e mostra output"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            text=True,
            cwd="/Users/davidedonghi/Apps/_micro services/rfid_gate"
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completato con successo")
        else:
            print(f"❌ {description} fallito (exit code: {result.returncode})")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Errore esecuzione: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 MQTT TEST SUITE RUNNER")
    print("Esegue tutti i test MQTT dalla cartella tests/debug/")
    print()
    
    # Verifica che siamo nella directory corretta
    current_dir = Path.cwd()
    if not (current_dir / "tests" / "debug").exists():
        print("❌ Errore: Esegui questo script dalla directory root del progetto rfid_gate")
        return False
    
    tests = [
        {
            'cmd': 'python3 tests/debug/test_mqtt_patch.py',
            'description': 'Test Patch MQTT Resilienza'
        },
        {
            'cmd': 'python3 tests/debug/test_mqtt_real.py',
            'description': 'Test Connessione MQTT Reale'
        }
    ]
    
    results = []
    
    for test in tests:
        success = run_command(test['cmd'], test['description'])
        results.append({'test': test['description'], 'success': success})
    
    # Risultati finali
    print(f"\n{'='*60}")
    print("📊 RISULTATI FINALI")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['test']}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    
    print(f"\n🎯 SUMMARY: {passed_tests}/{total_tests} test passati")
    
    if passed_tests == total_tests:
        print("🎉 TUTTI I TEST MQTT SONO PASSATI!")
        print("\n✅ Sistema MQTT completamente funzionale e resiliente")
    else:
        print("⚠️ Alcuni test sono falliti - controllare la configurazione")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)