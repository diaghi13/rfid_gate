#!/usr/bin/env python3
"""
Test risoluzione errore 'RFIDManager' object has no attribute 'start_reading'
"""
import sys
import os
sys.path.append('src')

def test_rfid_manager_methods():
    """Test per verificare che tutti i metodi richiesti esistano"""
    print("🧪 TEST: Verifica metodi RFIDManager")
    print("=" * 50)
    
    try:
        from rfid_manager import RFIDManager
        print("✅ Import RFIDManager riuscito")
        
        # Crea istanza
        rfid_manager = RFIDManager()
        print("✅ Istanza RFIDManager creata")
        
        # Lista metodi che main.py si aspetta
        required_methods = [
            'initialize',
            'start_reading',    # ❌ Era questo che mancava!
            'get_active_readers',
            'wait_for_card',
            'stop_reading',
            'cleanup',
            'get_next_card'
        ]
        
        print(f"\n📋 Verifica {len(required_methods)} metodi richiesti:")
        
        all_ok = True
        for method in required_methods:
            if hasattr(rfid_manager, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method} - MANCANTE!")
                all_ok = False
        
        print(f"\n📊 RISULTATO:")
        if all_ok:
            print("✅ ERRORE RISOLTO! Tutti i metodi sono presenti")
            print("✅ 'RFIDManager' object has no attribute 'start_reading' - FIXED")
        else:
            print("❌ Alcuni metodi sono ancora mancanti")
        
        # Test chiamata metodi (verifica che non diano AttributeError)
        print(f"\n🧪 Test chiamata metodi:")
        
        try:
            # Test start_reading (il metodo che causava l'errore)
            print("   🔵 Test start_reading()...")
            result = rfid_manager.start_reading()  # Non dovrebbe dare AttributeError
            print(f"   ✅ start_reading() chiamato (risultato: {result})")
        except AttributeError as e:
            print(f"   ❌ start_reading() - AttributeError: {e}")
            all_ok = False
        except Exception as e:
            print(f"   ⚠️ start_reading() - Altri errori (normale): {type(e).__name__}")
        
        try:
            # Test get_active_readers
            print("   🔵 Test get_active_readers()...")
            readers = rfid_manager.get_active_readers()
            print(f"   ✅ get_active_readers() - Risultato: {readers}")
        except AttributeError as e:
            print(f"   ❌ get_active_readers() - AttributeError: {e}")
            all_ok = False
        except Exception as e:
            print(f"   ⚠️ get_active_readers() - Altri errori (normale): {type(e).__name__}")
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

def main():
    print("🚀 TEST RISOLUZIONE ERRORE CRITICO")
    print("Errore: 'RFIDManager' object has no attribute 'start_reading'")
    print()
    
    success = test_rfid_manager_methods()
    
    print(f"\n🎯 CONCLUSIONE:")
    if success:
        print("✅ ERRORE CRITICO RISOLTO!")
        print("✅ Il sistema può ora essere avviato senza AttributeError")
        print("✅ Tutti i metodi richiesti da main.py sono presenti")
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Deploy su Raspberry Pi")
        print("   2. Test sistema completo")
        print("   3. Verifica hardware PN532")
    else:
        print("❌ Errore non completamente risolto")
        print("🔧 Controlla i metodi mancanti sopra")

if __name__ == "__main__":
    main()