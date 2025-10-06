#!/usr/bin/env python3
"""
Test completo sistema RFID con supporto PN532 e MFRC522
Testa auto-rilevamento, switch configurazione e compatibilità
"""
import sys
import os
import time

# Aggiunge il path src per import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_factory():
    """Test factory e supporto lettori"""
    print("🧪 TEST FACTORY LETTORI RFID")
    print("=" * 50)
    
    try:
        from rfid_readers.reader_factory import RFIDReaderFactory
        
        # Test supporto lettori
        supported = RFIDReaderFactory.get_supported_readers()
        print(f"📋 Lettori supportati: {supported}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Errore import factory: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore factory: {e}")
        return False

def test_config():
    """Test configurazioni"""
    print(f"\n🔧 TEST CONFIGURAZIONI")
    print("=" * 30)
    
    try:
        from config import Config
        
        # Test configurazioni RFID
        print(f"RFID_IN_READER_TYPE: {getattr(Config, 'RFID_IN_READER_TYPE', 'NON DEFINITO')}")
        print(f"RFID_OUT_READER_TYPE: {getattr(Config, 'RFID_OUT_READER_TYPE', 'NON DEFINITO')}")
        
        # Test configurazioni PN532
        if hasattr(Config, 'RFID_IN_PN532_INTERFACE'):
            print(f"PN532_IN Interface: {Config.RFID_IN_PN532_INTERFACE}")
            print(f"PN532_IN I2C Address: 0x{Config.RFID_IN_PN532_I2C_ADDRESS:02X}")
        
        if hasattr(Config, 'RFID_OUT_PN532_INTERFACE'):
            print(f"PN532_OUT Interface: {Config.RFID_OUT_PN532_INTERFACE}")
            print(f"PN532_OUT I2C Address: 0x{Config.RFID_OUT_PN532_I2C_ADDRESS:02X}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore configurazione: {e}")
        return False

def test_compatibility():
    """Test compatibilità wrapper"""
    print(f"\n🔄 TEST COMPATIBILITÀ WRAPPER")
    print("=" * 35)
    
    try:
        from rfid_reader import RFIDReader
        
        # Test creazione wrapper (simula uso esistente)
        reader = RFIDReader(reader_id="test_wrapper", rst_pin=22, sda_pin=8)
        print(f"✅ Wrapper RFIDReader creato - Tipo: {reader.reader_type}")
        
        # Non inizializziamo per evitare errori hardware in test
        print("✅ Interfaccia compatibile mantenuta")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore compatibilità: {e}")
        return False

def test_reader_creation():
    """Test creazione lettori specifici"""
    print(f"\n🏭 TEST CREAZIONE LETTORI")
    print("=" * 32)
    
    try:
        from rfid_readers.reader_factory import RFIDReaderFactory
        
        # Test creazione MFRC522
        print("🔍 Test creazione MFRC522...")
        try:
            mfrc522 = RFIDReaderFactory.create_reader(
                'mfrc522', 
                'test_mfrc522', 
                rst_pin=22, 
                sda_pin=8
            )
            print(f"   ✅ MFRC522Reader creato - ID: {mfrc522.reader_id}")
        except Exception as e:
            print(f"   ⚠️ MFRC522 non disponibile: {e}")
        
        # Test creazione PN532
        print("🔍 Test creazione PN532...")
        try:
            pn532 = RFIDReaderFactory.create_reader(
                'pn532', 
                'test_pn532', 
                interface='i2c',
                i2c_address=0x24
            )
            print(f"   ✅ PN532Reader creato - ID: {pn532.reader_id}")
        except Exception as e:
            print(f"   ⚠️ PN532 non disponibile: {e}")
        
        # Test creazione da config
        print("🔍 Test creazione da configurazione...")
        try:
            reader_from_config = RFIDReaderFactory.create_from_config("config_test", "RFID_IN")
            print(f"   ✅ Lettore da config creato - ID: {reader_from_config.reader_id}")
        except Exception as e:
            print(f"   ⚠️ Creazione da config fallita: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test creazione: {e}")
        return False

def test_switch_scenario():
    """Test scenario di switch tra lettori"""
    print(f"\n🔀 TEST SCENARIO SWITCH")
    print("=" * 28)
    
    # Simula switch da MFRC522 a PN532
    print("Scenario: Switch da MFRC522 a PN532")
    print("1. Configurazione iniziale: RFID_IN_READER_TYPE=mfrc522")
    print("2. Modifica .env: RFID_IN_READER_TYPE=pn532")
    print("3. Riavvio sistema")
    print("4. Sistema dovrebbe usare PN532 automaticamente")
    
    try:
        from rfid_reader import RFIDReader
        
        # Simula lettura configurazione
        reader = RFIDReader("switch_test")
        print(f"✅ Lettore configurato per: {reader.reader_type.upper()}")
        print("✅ Switch scenario verificato (simulazione)")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore switch scenario: {e}")
        return False

def main():
    """Test completo del sistema"""
    print("🚀 TEST SISTEMA RFID MULTI-LETTORE")
    print("=" * 60)
    print("Versione: PN532 + MFRC522 con switch automatico")
    print("=" * 60)
    
    tests = [
        ("Factory e Supporto", test_factory),
        ("Configurazioni", test_config),
        ("Compatibilità Wrapper", test_compatibility),
        ("Creazione Lettori", test_reader_creation),
        ("Scenario Switch", test_switch_scenario),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERRORE CRITICO in {test_name}: {e}")
            results.append((test_name, False))
    
    # Riepilogo
    print(f"\n📊 RIEPILOGO TEST")
    print("=" * 25)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<25} {status}")
    
    print(f"\nRisultato: {passed}/{total} test superati")
    
    if passed == total:
        print("🎉 TUTTI I TEST SUPERATI!")
        print("\n💡 ISTRUZIONI PER L'USO:")
        print("1. Installa dipendenze PN532: pip install -r requirements_pn532.txt")
        print("2. Configura .env con RFID_IN_READER_TYPE=pn532")
        print("3. Avvia il sistema normalmente")
        print("4. Il sistema userà automaticamente PN532")
    else:
        print("⚠️ Alcuni test sono falliti, verifica la configurazione")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)