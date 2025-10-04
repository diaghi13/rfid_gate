#!/usr/bin/env python3
"""
Test debug completo per capire dove si blocca il sistema
"""
import sys
import os
import time

# Mock RPi.GPIO per macOS
class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    
    @staticmethod
    def setmode(mode): pass
    @staticmethod
    def setup(pin, mode, initial=None): pass
    @staticmethod
    def output(pin, state): pass
    @staticmethod
    def input(pin): return 0
    @staticmethod
    def cleanup(): pass

sys.modules['RPi'] = type('MockRPi', (), {})()
sys.modules['RPi.GPIO'] = MockGPIO

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_complete_flow():
    print("🔍 DEBUG COMPLETO - TRACCIAMENTO FLUSSO")
    print("="*60)
    
    try:
        from config import Config
        from rfid_manager import RFIDManager
        
        print("✅ Import: OK")
        
        # Crea manager
        manager = RFIDManager()
        print("✅ Manager creato")
        
        # Test initialize
        print("\n🔧 FASE 1: Initialize")
        result = manager.initialize()
        print(f"📊 Initialize result: {result}")
        print(f"📊 Readers attivi: {list(manager.readers.keys())}")
        print(f"📊 Is initialized: {manager.is_initialized}")
        
        if not result:
            print("❌ Initialize fallito - sistema non può funzionare")
            return False
        
        # Test start
        print("\n🚀 FASE 2: Start")
        start_result = manager.start()
        print(f"📊 Start result: {start_result}")
        print(f"📊 Running: {manager.running}")
        print(f"📊 Thread attivi: {list(manager.reader_threads.keys())}")
        
        # Aspetta un momento per i thread
        print("\n⏱️ FASE 3: Attesa thread (3 secondi)")
        time.sleep(3)
        
        # Test queue
        print("\n📦 FASE 4: Test queue")
        print(f"📊 Queue size: {manager.card_queue.qsize()}")
        
        # Test manuale read_card sui readers
        print("\n🧪 FASE 5: Test manuale read_card")
        for reader_id, reader in manager.readers.items():
            print(f"\n🔍 Test reader {reader_id}:")
            print(f"   📊 Type: {type(reader)}")
            print(f"   📊 Initialized: {getattr(reader, 'is_initialized', 'N/A')}")
            
            try:
                result = reader.read_card()
                print(f"   📊 read_card() result: {result}")
                print(f"   📊 result type: {type(result)}")
            except Exception as e:
                print(f"   ❌ read_card() error: {e}")
        
        # Stop
        print("\n🛑 FASE 6: Stop")
        manager.stop()
        manager.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE DEBUG: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 DEBUG COMPLETO RFID SYSTEM")
    print("🎯 Obiettivo: Trovare dove si blocca la lettura")
    print()
    
    success = debug_complete_flow()
    
    print("\n" + "="*60)
    if success:
        print("✅ Debug completato - analizza i risultati sopra")
    else:
        print("❌ Debug fallito")
        
    exit(0 if success else 1)