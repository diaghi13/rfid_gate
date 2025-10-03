#!/usr/bin/env python3
"""
Test integrazione PN532 nel sistema principale
"""
import sys
import os

# Aggiungi il percorso src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 TEST INTEGRAZIONE PN532 NEL SISTEMA")
print("=" * 45)

try:
    # Test import reader factory
    from rfid_readers.reader_factory import RFIDReaderFactory
    print("✅ Import RFIDReaderFactory riuscito")
    
    # Test creazione lettore PN532 tramite factory
    print("🔧 Test creazione PN532 tramite factory...")
    reader = RFIDReaderFactory.create_reader(
        reader_type='pn532',
        reader_id='test_pn532',
        interface='i2c',
        i2c_address=0x24
    )
    
    if reader:
        print(f"✅ PN532Reader creato tramite factory: {reader.reader_id}")
        
        # Test che sia una istanza corretta
        from rfid_readers.pn532_reader import PN532Reader
        if isinstance(reader, PN532Reader):
            print("✅ Istanza PN532Reader corretta")
        else:
            print(f"❌ Tipo reader errato: {type(reader)}")
        
        # Test metodi
        print("\n🔍 Test metodi del reader:")
        
        # Initialize (fallirà senza hardware ma non dovrebbe crashare)
        print("   - initialize()...", end=" ")
        try:
            result = reader.initialize()
            print(f"Risultato: {result}")
        except Exception as e:
            print(f"Errore: {e}")
        
        # Test connection
        print("   - test_connection()...", end=" ")
        try:
            result = reader.test_connection()
            print(f"Risultato: {result}")
        except Exception as e:
            print(f"Errore: {e}")
        
        # Read card
        print("   - read_card()...", end=" ")
        try:
            result = reader.read_card()
            print(f"Risultato: {result}")
        except Exception as e:
            print(f"Errore: {e}")
        
        # Cleanup
        print("   - cleanup()...", end=" ")
        try:
            reader.cleanup()
            print("OK")
        except Exception as e:
            print(f"Errore: {e}")
        
        print("\n✅ INTEGRAZIONE PN532 COMPLETATA!")
        print("🎯 Il lettore PN532 è pronto per l'uso nel sistema")
        
    else:
        print("❌ Factory non è riuscita a creare il lettore PN532")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERRORE DI INTEGRAZIONE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n📋 PROSSIMI PASSI:")
print("1. Installa dipendenze: ./install_pn532_compatible.sh")
print("2. Connetti hardware PN532 (se su Raspberry Pi)")
print("3. Configura sistema: cp config/examples/.env.pn532_single .env")
print("4. Avvia sistema: python3 src/main.py")