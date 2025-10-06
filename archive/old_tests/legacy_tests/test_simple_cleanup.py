#!/usr/bin/env python3
"""
Cleanup GPIO e test RFID semplice
Risolve conflitti GPIO prima del test
"""
import sys
import time

def cleanup_gpio():
    """Pulisce completamente GPIO"""
    print("🧹 CLEANUP GPIO COMPLETO")
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
        print("✅ GPIO cleanup completato")
        time.sleep(1)  # Pausa per stabilizzazione
        return True
    except Exception as e:
        print(f"⚠️ Errore cleanup GPIO: {e}")
        return False

def test_simple_card_reading():
    """Test semplificato lettura card"""
    print("\n🧪 TEST SEMPLIFICATO LETTURA CARD")
    print("=" * 50)
    
    try:
        # Aggiungi src al path
        sys.path.insert(0, 'src')
        
        from config import Config
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
        
        print("✅ Import moduli: OK")
        
        # Configura GPIO pulito
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO configurato: OK")
        
        # Crea lettore base (senza parametri)
        print("🔧 Creazione lettore base...")
        reader = SimpleMFRC522()
        
        # Configura pin manualmente
        if hasattr(reader, 'READER'):
            hw_reader = reader.READER
            
            print(f"🔧 Configurazione pin manuale:")
            print(f"   RST: {Config.RFID_IN_RST_PIN}")
            print(f"   CS: {Config.RFID_IN_SDA_PIN}")
            
            # Pin prima
            old_rst = getattr(hw_reader, 'RST', 'Non impostato')
            old_cs = getattr(hw_reader, 'CS', None) or getattr(hw_reader, 'SDA', 'Non impostato')
            print(f"   Pin di default: RST={old_rst}, CS/SDA={old_cs}")
            
            # Configura pin
            hw_reader.RST = Config.RFID_IN_RST_PIN
            if hasattr(hw_reader, 'CS'):
                hw_reader.CS = Config.RFID_IN_SDA_PIN
            if hasattr(hw_reader, 'SDA'):
                hw_reader.SDA = Config.RFID_IN_SDA_PIN
            
            # Pin dopo
            new_rst = getattr(hw_reader, 'RST', 'Errore')
            new_cs = getattr(hw_reader, 'CS', None) or getattr(hw_reader, 'SDA', 'Errore')
            print(f"   Pin configurati: RST={new_rst}, CS/SDA={new_cs}")
            
            if new_rst == Config.RFID_IN_RST_PIN and new_cs == Config.RFID_IN_SDA_PIN:
                print("✅ Pin configurati correttamente!")
            else:
                print("⚠️ Pin potrebbero non essere configurati correttamente")
        
        # Test lettura
        print(f"\n📖 TEST LETTURA CARD")
        print("💡 Avvicina una card RFID ADESSO...")
        print("⏳ Provo per 15 secondi...")
        
        cards_found = 0
        for i in range(30):  # 30 tentativi = 15 secondi
            try:
                print(f"   Tentativo {i+1}/30...", end='')
                
                if hasattr(reader, 'read_no_block'):
                    card_id, card_data = reader.read_no_block()
                else:
                    card_id, card_data = reader.read()
                
                if card_id is not None:
                    cards_found += 1
                    print(f" 🎉 CARD TROVATA!")
                    print(f"   📊 ID: {card_id}")
                    print(f"   📊 Hex: {hex(card_id)}")
                    print(f"   📊 Dati: '{card_data}'")
                    
                    if cards_found >= 3:  # Limite per test
                        print("✅ Test completato - multiple card rilevate")
                        break
                else:
                    print(" ⚪")
                
            except Exception as e:
                error_msg = str(e).lower()
                if any(skip in error_msg for skip in ["no card", "timeout", "nothing"]):
                    print(" ⚪")
                else:
                    print(f" ❌ {e}")
            
            time.sleep(0.5)
        
        print(f"\n📊 RISULTATO FINALE:")
        print(f"   Card rilevate: {cards_found}")
        
        if cards_found > 0:
            print("🎉 SUCCESSO! Il lettore RFID funziona!")
            print("💡 Il problema era nella configurazione GPIO/pin")
        else:
            print("❌ NESSUNA CARD RILEVATA")
            print("💡 Possibili cause:")
            print("   1. Card non compatibile")
            print("   2. Cablaggio errato") 
            print("   3. Alimentazione insufficiente")
            print("   4. Pin non configurati correttamente")
        
        # Cleanup
        GPIO.cleanup()
        return cards_found > 0
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 TEST SEMPLIFICATO RFID CON CLEANUP")
    print("Questo test risolve i conflitti GPIO e testa la lettura base")
    print("=" * 60)
    
    # Step 1: Cleanup GPIO
    if not cleanup_gpio():
        print("❌ Cleanup GPIO fallito")
        return
    
    # Step 2: Test lettura semplificata
    success = test_simple_card_reading()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 VERDETTO: RFID FUNZIONA!")
        print("💡 Il problema era nella configurazione GPIO/pin")
        print("🔧 Ora possiamo correggere il RFIDReader principale")
    else:
        print("💔 VERDETTO: RFID NON FUNZIONA")
        print("🔧 Il problema è hardware/cablaggio/card")
    print("=" * 60)

if __name__ == "__main__":
    main()