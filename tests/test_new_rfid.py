#!/usr/bin/env python3
"""
Test semplice per il nuovo sistema RFID ricostruito
"""
import sys
import time

# Aggiungi src al path
sys.path.insert(0, 'src')

def test_simple_rfid():
    """Test base del sistema RFID ricostruito"""
    print("🧪 TEST SISTEMA RFID RICOSTRUITO")
    print("=" * 50)
    
    try:
        from config import Config
        from rfid_reader import RFIDReader
        from rfid_manager import RFIDManager
        
        print("✅ Import moduli: OK")
        
        # Test 1: Configurazione
        print(f"\n📋 CONFIGURAZIONE:")
        print(f"   RFID_IN abilitato: {Config.RFID_IN_ENABLE}")
        print(f"   RFID_OUT abilitato: {Config.RFID_OUT_ENABLE}")
        print(f"   Modalità bidirezionale: {Config.BIDIRECTIONAL_MODE}")
        
        if Config.RFID_IN_ENABLE:
            print(f"   RFID IN: RST={Config.RFID_IN_RST_PIN}, CS={Config.RFID_IN_SDA_PIN}")
        
        if Config.RFID_OUT_ENABLE:
            print(f"   RFID OUT: RST={Config.RFID_OUT_RST_PIN}, CS={Config.RFID_OUT_SDA_PIN}")
        
        # Test 2: Lettore singolo
        print(f"\n🔍 TEST LETTORE SINGOLO:")
        reader = RFIDReader("test", Config.RFID_IN_RST_PIN, Config.RFID_IN_SDA_PIN)
        
        if reader.initialize():
            print("✅ Inizializzazione: OK")
            
            if reader.test_connection():
                print("✅ Test connessione: OK")
                
                # Test lettura veloce
                print("📖 Test lettura veloce (3 tentativi)...")
                for i in range(3):
                    card_id, card_data = reader.read_card()
                    if card_id:
                        print(f"🎉 Card rilevata: {reader.format_card_uid(card_id)}")
                        break
                    time.sleep(0.5)
                else:
                    print("ℹ️ Nessuna card rilevata (normale se non avvicini una card)")
                
            else:
                print("❌ Test connessione: FALLITO")
            
            reader.cleanup()
        else:
            print("❌ Inizializzazione: FALLITA")
            return False
        
        # Test 3: Manager completo
        print(f"\n🎯 TEST MANAGER COMPLETO:")
        manager = RFIDManager()
        
        if manager.initialize():
            print("✅ Manager inizializzato")
            
            # Test status
            status = manager.get_reader_status()
            print(f"📊 Lettori attivi: {status['active_readers']}")
            
            # Test tutti i lettori
            if manager.test_all_readers():
                print("✅ Tutti i lettori: OK")
                
                # Test thread (breve)
                if manager.start_reading():
                    print("✅ Thread avviati")
                    print("⏳ Monitoraggio per 5 secondi...")
                    print("💡 Avvicina una card per testare...")
                    
                    cards_detected = 0
                    start_time = time.time()
                    
                    while time.time() - start_time < 5:
                        card_info = manager.get_next_card(timeout=1)
                        if card_info:
                            cards_detected += 1
                            print(f"🎉 Card #{cards_detected}: {card_info['uid_formatted']} su {card_info['direction'].upper()}")
                            
                            if cards_detected >= 2:  # Limite per test
                                break
                    
                    manager.stop_reading()
                    print(f"📊 Test completato: {cards_detected} card rilevate")
                    
                else:
                    print("❌ Avvio thread: FALLITO")
            else:
                print("❌ Test lettori: FALLITO")
            
            manager.cleanup()
        else:
            print("❌ Manager inizializzazione: FALLITA")
            return False
        
        print("\n✅ TUTTI I TEST COMPLETATI")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRORE TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale"""
    print("🚀 TEST SISTEMA RFID RICOSTRUITO")
    print("Questo test verifica il nuovo codice semplificato")
    print("=" * 60)
    
    success = test_simple_rfid()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SISTEMA RFID: FUNZIONANTE")
        print("💡 Ora puoi usare il nuovo codice nel sistema principale")
    else:
        print("💔 SISTEMA RFID: PROBLEMI RILEVATI")
        print("🔧 Controlla la configurazione hardware e software")
    
    print("=" * 60)

if __name__ == "__main__":
    main()