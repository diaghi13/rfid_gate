#!/usr/bin/env python3
"""
Test base per verificare installazione sistema
"""
import sys
import os

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test import moduli base"""
    try:
        from config import Config
        from rfid_manager import RFIDManager
        from relay_manager import RelayManager
        from mqtt_client import MQTTClient
        from offline_manager import OfflineManager
        from manual_control import ManualControl
        print("✅ Tutti i moduli importati correttamente")
        return True
    except Exception as e:
        print(f"❌ Errore import: {e}")
        return False

def test_config():
    """Test configurazione"""
    try:
        from config import Config
        errors = Config.validate_config()
        if errors:
            print("❌ Errori configurazione:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print("✅ Configurazione valida")
            return True
    except Exception as e:
        print(f"❌ Errore test config: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TEST BASE SISTEMA")
    print("===================")
    
    success = True
    success &= test_imports()
    success &= test_config()
    
    if success:
        print("\n✅ Tutti i test superati!")
        sys.exit(0)
    else:
        print("\n❌ Alcuni test falliti!")
        sys.exit(1)
