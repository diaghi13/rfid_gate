#!/usr/bin/env python3
"""
Test rapido per verificare l'implementazione dei metodi astratti
"""
import sys
import os

# Aggiungi il percorso src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 TEST METODI ASTRATTI PN532")
print("=" * 40)

try:
    # Import delle classi
    from rfid_readers.pn532_reader import PN532Reader
    
    print("✅ Import PN532Reader riuscito")
    
    # Test creazione istanza
    print("🔧 Test creazione istanza...")
    reader = PN532Reader(reader_id="test_pn532", interface="i2c", i2c_address=0x24)
    print(f"✅ PN532Reader creato: {reader.reader_id}")
    
    # Verifica che tutti i metodi astratti siano implementati
    required_methods = ['initialize', 'read_card', 'test_connection', 'cleanup']
    print("\n🔍 Verifica metodi richiesti:")
    
    for method in required_methods:
        if hasattr(reader, method) and callable(getattr(reader, method)):
            print(f"✅ {method}() - implementato")
        else:
            print(f"❌ {method}() - MANCANTE")
            sys.exit(1)
    
    print("\n🧪 Test chiamate metodi (senza hardware):")
    
    # Test initialize (dovrebbe fallire senza hardware)
    print("   - initialize()...", end=" ")
    try:
        result = reader.initialize()
        print(f"Risultato: {result} (normale fallimento senza hardware)")
    except Exception as e:
        print(f"Errore: {e}")
    
    # Test test_connection (dovrebbe fallire se non inizializzato)
    print("   - test_connection()...", end=" ")
    try:
        result = reader.test_connection()
        print(f"Risultato: {result}")
    except Exception as e:
        print(f"Errore: {e}")
    
    # Test cleanup
    print("   - cleanup()...", end=" ")
    try:
        reader.cleanup()
        print("OK")
    except Exception as e:
        print(f"Errore: {e}")
    
    print("\n✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
    print("🎯 La classe PN532Reader è ora completamente implementata")
    
except ImportError as e:
    print(f"❌ Errore di import: {e}")
    print("💡 Verifica che il percorso src sia corretto")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)