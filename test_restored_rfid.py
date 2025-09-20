#!/usr/bin/env python3
"""
Test della versione RFID ripristinata dai backup
"""
import sys
import time

# Aggiungi src al path
sys.path.insert(0, 'src')

def test_restored_rfid():
    """Test del sistema RFID ripristinato"""
    print("🔄 TEST SISTEMA RFID RIPRISTINATO")
    print("=" * 50)
    
    try:
        from config import Config
        from rfid_reader import RFIDReader
        from rfid_manager import RFIDManager
        
        print("✅ Import moduli: OK")
        print(f"📋 Configurazione: RFID IN abilitato = {Config.RFID_IN_ENABLE}")
        
        # Test 1: Reader singolo
        print(f"\n🔍 TEST 1: READER SINGOLO")
        reader = RFIDReader("test")
        
        if reader.initialize():
            print("✅ Reader inizializzato")
            
            if reader.test_connection():
                print("✅ Test connessione OK")
                
                print("📖 Test lettura veloce (avvicina card)...")
                for i in range(5):
                    card_id, card_data = reader.read_card()
                    if card_id:
                        uid_formatted = reader.format_card_uid(card_id)
                        print(f"🎉 CARD RILEVATA: {uid_formatted}")
                        break
                    time.sleep(0.5)
                else:
                    print("ℹ️ Nessuna card (normale se non avvicinata)")
            else:
                print("❌ Test connessione fallito")
                return False
            
            reader.cleanup()
        else:
            print("❌ Inizializzazione reader fallita")
            return False
        
        # Test 2: Manager completo
        print(f"\n🎯 TEST 2: MANAGER COMPLETO")
        manager = RFIDManager()
        
        if manager.initialize():
            print("✅ Manager inizializzato")
            
            if manager.start_reading():
                print("✅ Thread di lettura avviati")
                print("⏳ Monitoraggio per 10 secondi...")
                print("💡 Avvicina una card RFID...")
                
                cards_detected = 0
                start_time = time.time()
                
                while time.time() - start_time < 10:
                    card_info = manager.get_next_card(timeout=1)
                    if card_info:
                        cards_detected += 1
                        print(f"🎉 Card #{cards_detected}: {card_info['uid_formatted']} su {card_info['direction'].upper()}")
                        
                        if cards_detected >= 2:
                            break
                
                manager.stop_reading()
                manager.cleanup()
                
                print(f"📊 Risultato: {cards_detected} card rilevate")
                
                if cards_detected > 0:
                    print("🎉 SISTEMA RFID RIPRISTINATO: FUNZIONANTE!")
                    return True
                else:
                    print("⚠️ Nessuna card rilevata")
                    return False
            else:
                print("❌ Avvio thread fallito")
                return False
        else:
            print("❌ Inizializzazione manager fallita")
            return False
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale"""
    print("🔄 TEST VERSIONE RFID RIPRISTINATA")
    print("Verifica che il rollback ai file backup funzioni")
    print("=" * 60)
    
    success = test_restored_rfid()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESSO! Il sistema RFID è tornato funzionante")
        print("💡 Ora puoi usare il sistema principale:")
        print("   sudo python3 src/main.py")
    else:
        print("💔 Il sistema RFID non funziona ancora")
        print("🔧 Prova il sistema minimalista:")
        print("   sudo python3 minimal_rfid.py")
    print("=" * 60)

if __name__ == "__main__":
    main()