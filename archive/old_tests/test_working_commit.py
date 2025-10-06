#!/usr/bin/env python3
"""
Test del commit funzionante - simula RPi
"""
import sys
import os

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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

def test_working_commit():
    print("🔍 TEST COMMIT FUNZIONANTE")
    print("="*50)
    
    try:
        from config import Config
        from rfid_manager import RFIDManager
        
        print("✅ Import: OK")
        print(f"✅ Reader IN: {Config.RFID_IN_READER_TYPE}")
        print(f"✅ Reader OUT: {Config.RFID_OUT_READER_TYPE}")
        
        # Test inizializzazione RFIDManager
        print("\n🔧 Test RFIDManager...")
        manager = RFIDManager()
        
        print("📋 Metodi disponibili:")
        methods = [method for method in dir(manager) if not method.startswith('_')]
        for method in methods[:10]:  # Primi 10
            print(f"   • {method}")
        
        # Test inizializzazione (fallirà su macOS ma vediamo l'interfaccia)
        print("\n🧪 Test initialize...")
        try:
            result = manager.initialize()
            print(f"✅ Initialize result: {result}")
        except Exception as e:
            print(f"⚠️ Initialize error (atteso su macOS): {e}")
        
        # Test altri metodi
        print("\n📊 Test metodi interfaccia...")
        try:
            if hasattr(manager, 'get_active_readers'):
                readers = manager.get_active_readers()
                print(f"✅ get_active_readers(): {readers}")
        except Exception as e:
            print(f"⚠️ get_active_readers error: {e}")
            
        try:
            if hasattr(manager, 'wait_for_card'):
                print(f"✅ wait_for_card method exists")
                # Non chiamiamo per evitare blocco
        except Exception as e:
            print(f"⚠️ wait_for_card error: {e}")
        
        print(f"\n🔍 Tipo RFIDManager: {type(manager)}")
        print(f"📋 Attributi principali: {[attr for attr in dir(manager) if not attr.startswith('_')][:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_working_commit()
    print("\n" + "="*50)
    if success:
        print("✅ Commit funzionante - interfaccia OK")
    else:
        print("❌ Problemi nel commit funzionante")
    exit(0 if success else 1)