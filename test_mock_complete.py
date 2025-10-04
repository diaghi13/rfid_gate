#!/usr/bin/env python3
"""
Test con mock completo PN532 per simulare lettura carte
"""
import sys
import os
import time
from unittest.mock import Mock

# Mock RPi.GPIO
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

# Mock completo PN532
class MockPN532:
    def __init__(self, *args, **kwargs):
        print("🔧 MockPN532 creato")
        self.read_count = 0
        
    def read_passive_target(self, timeout=0.1):
        """Simula lettura carta ogni 3 chiamate"""
        self.read_count += 1
        if self.read_count % 30 == 0:  # Simula carta ogni 3 secondi
            print("📱 MockPN532: Simulando carta rilevata!")
            return bytes([0x12, 0x34, 0x56, 0x78])  # UID simulato
        return None

class MockI2C:
    def __init__(self, *args, **kwargs):
        pass

class MockBoard:
    SCL = "SCL"
    SDA = "SDA"

class MockBusio:
    @staticmethod
    def I2C(*args, **kwargs):
        return MockI2C()

# Mock dei moduli PN532 completi
sys.modules['board'] = MockBoard()
sys.modules['busio'] = MockBusio()
sys.modules['adafruit_pn532'] = Mock()
sys.modules['adafruit_pn532.i2c'] = Mock()
sys.modules['adafruit_pn532.i2c'].PN532_I2C = MockPN532

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_with_mock():
    print("🔍 TEST CON MOCK PN532 COMPLETO")
    print("="*50)
    
    try:
        from config import Config
        from rfid_manager import RFIDManager
        
        print("✅ Import: OK")
        
        # Crea manager
        manager = RFIDManager()
        print("✅ Manager creato")
        
        # Initialize
        print("\n🔧 Initialize con mock...")
        result = manager.initialize()
        print(f"📊 Initialize: {result}")
        print(f"📊 Readers: {list(manager.readers.keys())}")
        
        if result:
            # Start
            print("\n🚀 Start reading...")
            start_result = manager.start()
            print(f"📊 Start: {start_result}")
            
            # Test per 10 secondi
            print("\n⏱️ Test lettura 10 secondi...")
            start_time = time.time()
            cards_found = 0
            
            while time.time() - start_time < 10:
                # Controlla queue
                if not manager.card_queue.empty():
                    card = manager.get_next_card(timeout=0.1)
                    if card:
                        cards_found += 1
                        print(f"\n🎉 CARTA #{cards_found} TROVATA!")
                        print(f"   📋 Card info: {card}")
                
                time.sleep(0.1)
            
            print(f"\n📊 Risultati: {cards_found} carte simulate lette")
            
            # Stop
            manager.stop()
            manager.cleanup()
            
            return cards_found > 0
        else:
            print("❌ Initialize fallito anche con mock")
            return False
        
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_mock()
    print("\n" + "="*50)
    if success:
        print("✅ MOCK FUNZIONA - Il problema è nelle librerie hardware")
        print("🎯 Su Raspberry Pi con librerie dovrebbe funzionare")
    else:
        print("❌ PROBLEMA NEL CODICE - C'è un bug logico")
    exit(0 if success else 1)