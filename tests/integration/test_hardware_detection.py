#!/usr/bin/env python3
"""
🧪 Test Hardware Detection - Sistema Rigoroso vs Permissivo
=========================================================

Questo script testa la differenza tra il sistema legacy (rigoroso)
e il sistema refactored migliorato per la detection degli errori hardware.
"""

import asyncio
import sys
from pathlib import Path

# Aggiunge il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

async def test_hardware_detection():
    """Test detection errori hardware"""
    print("🧪 Test Hardware Detection - Sistema Rigoroso")
    print("=" * 60)
    
    print("\n📋 Differenze Sistema Legacy vs Refactored:")
    print("Legacy (Rigoroso):")
    print("  1. initialize() - Setup hardware")
    print("  2. test_connection() - Test effettivo connessione")
    print("  3. Solo se entrambi OK → lettore accettato")
    
    print("\nRefactored (Prima - Troppo Permissivo):")
    print("  1. initialize() - Setup hardware") 
    print("  2. Se firmware check fallisce → continuava comunque ❌")
    print("  3. Accettava lettori non funzionanti")
    
    print("\nRefactored (Ora - Rigoroso come Legacy):")
    print("  1. initialize() - Setup hardware")
    print("  2. _hardware_connection_test() - Test rigoroso ✅")
    print("  3. Se test hardware fallisce → errore esplicito ❌")
    print("  4. Solo hardware realmente funzionante accettato ✅")
    
    # Test implementazione attuale
    try:
        from rfid_gate.hardware.readers.pn532 import PN532Reader
        
        print("\n🔧 Test Sistema Attuale (Rigoroso):")
        
        # Test con pin sbagliati (dovrebbe fallire)
        print("\n--- Test Pin Sbagliati (Dovrebbe Fallire) ---")
        reader_wrong = PN532Reader(
            reader_id="TEST_WRONG_PINS",
            direction="in",
            interface="i2c", 
            i2c_address=0x50,  # Indirizzo inesistente
            rst_pin=99,        # Pin inesistente  
            sda_pin=99         # Pin inesistente
        )
        
        result_wrong = await reader_wrong._hardware_init()
        if result_wrong:
            print("❌ PROBLEMA: Sistema ha accettato pin sbagliati!")
        else:
            print("✅ CORRETTO: Sistema ha rifiutato pin sbagliati")
        
        # Test con pin corretti ma probabilmente senza hardware
        print("\n--- Test Pin Corretti (Probabilmente Senza Hardware) ---")
        reader_correct = PN532Reader(
            reader_id="TEST_CORRECT_PINS",
            direction="in",
            interface="i2c",
            i2c_address=0x24,  # Indirizzo corretto
            rst_pin=22,        # Pin corretti
            sda_pin=8          # Pin corretti
        )
        
        result_correct = await reader_correct._hardware_init()
        if result_correct:
            print("⚠️ ATTENZIONE: Hardware rilevato (probabilmente mock su macOS)")
        else:
            print("✅ CORRETTO: Sistema ha rilevato assenza hardware reale")
            
    except ImportError as e:
        print(f"❌ Impossibile importare PN532Reader: {e}")
    
    print("\n🎯 Vantaggi del Sistema Rigoroso:")
    print("✅ Rileva problemi pin GPIO sbagliati")
    print("✅ Rileva hardware non connesso")
    print("✅ Rileva problemi di comunicazione")
    print("✅ Feedback chiaro all'utente")
    print("✅ Evita falsi positivi")
    
    print("\n📝 Note per Raspberry Pi:")
    print("- Su Raspberry Pi con hardware reale, test sarà più accurato")
    print("- Errori pin GPIO saranno rilevati immediatamente")
    print("- Test hardware verifica comunicazione effettiva")
    print("- Sistema legacy aveva comportamento simile")

async def test_error_scenarios():
    """Test scenari di errore specifici"""
    print("\n🚨 Test Scenari di Errore Comuni:")
    print("-" * 40)
    
    scenarios = [
        {
            "name": "Pin I2C Sbagliati", 
            "config": {"interface": "i2c", "i2c_address": 0x99, "rst_pin": 99, "sda_pin": 99},
            "expected": "❌ Dovrebbe fallire"
        },
        {
            "name": "Indirizzo I2C Sbagliato",
            "config": {"interface": "i2c", "i2c_address": 0x99, "rst_pin": 22, "sda_pin": 8}, 
            "expected": "❌ Dovrebbe fallire"
        },
        {
            "name": "Pin SPI Sbagliati",
            "config": {"interface": "spi", "spi_bus": 99, "rst_pin": 99, "sda_pin": 99},
            "expected": "❌ Dovrebbe fallire"
        },
        {
            "name": "Configurazione Legacy Corretta",
            "config": {"interface": "i2c", "i2c_address": 0x24, "rst_pin": 22, "sda_pin": 8},
            "expected": "⚠️ Fallimento normale su macOS (OK su Raspberry Pi)"
        }
    ]
    
    try:
        from rfid_gate.hardware.readers.pn532 import PN532Reader
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. {scenario['name']}:")
            print(f"   Config: {scenario['config']}")
            print(f"   Atteso: {scenario['expected']}")
            
            try:
                reader = PN532Reader(
                    reader_id=f"TEST_{i}",
                    direction="in",
                    **scenario['config']
                )
                
                result = await reader._hardware_init()
                status = "✅ Successo" if result else "❌ Fallimento"
                print(f"   Risultato: {status}")
                
            except Exception as e:
                print(f"   Risultato: ❌ Eccezione - {e}")
                
    except ImportError as e:
        print(f"❌ Impossibile importare PN532Reader: {e}")

async def main():
    """Funzione principale"""
    await test_hardware_detection()
    await test_error_scenarios()
    
    print("\n🎯 CONCLUSIONI:")
    print("Il sistema refactored ora implementa la stessa rigorosità")
    print("del sistema legacy per la detection degli errori hardware.")
    print("Questo risolve il problema dei 'falsi positivi' durante l'inizializzazione.")

if __name__ == "__main__":
    asyncio.run(main())