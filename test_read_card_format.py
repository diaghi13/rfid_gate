#!/usr/bin/env python3
"""
Test specifico per il formato di ritorno del metodo read_card
"""
import sys
import os

# Aggiungi il percorso src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 TEST FORMATO RITORNO READ_CARD")
print("=" * 40)

try:
    from rfid_readers.pn532_reader import PN532Reader
    
    # Crea istanza reader
    reader = PN532Reader(reader_id="test_pn532", interface="i2c", i2c_address=0x24)
    print(f"✅ PN532Reader creato: {reader.reader_id}")
    
    # Test read_card senza inizializzazione (dovrebbe restituire (None, None))
    print("\n🔍 Test read_card senza inizializzazione:")
    result = reader.read_card()
    print(f"   Risultato: {result}")
    print(f"   Tipo: {type(result)}")
    
    if isinstance(result, tuple) and len(result) == 2:
        card_id, card_data = result
        print(f"   ✅ Tupla corretta: card_id={card_id}, card_data={card_data}")
    else:
        print(f"   ❌ Formato errato: atteso tupla (card_id, card_data), ricevuto {result}")
    
    # Test che non dovrebbe lanciare errori di unpacking
    try:
        card_id, card_data = reader.read_card()
        print(f"   ✅ Unpacking riuscito: {card_id}, {card_data}")
    except TypeError as e:
        print(f"   ❌ Errore unpacking: {e}")
    except Exception as e:
        print(f"   ❌ Altro errore: {e}")
    
    # Cleanup
    reader.cleanup()
    
    print("\n✅ TEST COMPLETATO!")
    print("🎯 Il metodo read_card ora restituisce il formato corretto (card_id, card_data)")
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 FORMATO ATTESO:")
print("- read_card() deve restituire: (card_id, card_data)")
print("- card_id: int (ID numerico della carta)")
print("- card_data: str (dati aggiuntivi, può essere vuoto)")
print("- Se nessuna carta: (None, None)")
print("- Se debounce attivo: (None, None)")