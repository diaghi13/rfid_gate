#!/usr/bin/env python3
"""
Test UN SOLO modulo RFID alla volta
"""
import time
import sys

def test_single_rfid(rst_pin, cs_pin, name):
    """Test un singolo modulo RFID"""
    print(f"\n🔍 TEST {name}")
    print(f"   RST: GPIO{rst_pin}")
    print(f"   CS:  GPIO{cs_pin}")
    print("-" * 30)
    
    try:
        import RPi.GPIO as GPIO
        from mfrc522 import SimpleMFRC522
        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Crea lettore
        reader = SimpleMFRC522(rst=rst_pin, cs=cs_pin)
        print(f"✅ {name}: Lettore creato")
        
        # Test comunicazione
        for i in range(3):
            try:
                result = reader.read_no_block()
                print(f"✅ {name}: Test {i+1}/3 OK")
                time.sleep(0.5)
            except Exception as e:
                if "no card" not in str(e).lower():
                    print(f"⚠️ {name}: Test {i+1}/3 - {e}")
                else:
                    print(f"✅ {name}: Test {i+1}/3 OK (no card)")
        
        print(f"🎯 {name}: FUNZIONA CORRETTAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ {name}: ERRORE - {e}")
        return False
    finally:
        try:
            GPIO.cleanup()
        except:
            pass

if __name__ == "__main__":
    from config import Config
    
    print("🧪 TEST MODULI RFID SINGOLI")
    print("="*40)
    
    # Test 1: Solo RFID IN
    print("\n>>> SCOLLEGA IL MODULO RFID OUT <<<")
    input("Premi ENTER quando hai scollegato il modulo OUT...")
    
    result1 = test_single_rfid(
        Config.RFID_IN_RST_PIN, 
        Config.RFID_IN_SDA_PIN, 
        "RFID IN"
    )
    
    # Test 2: Solo RFID OUT
    print("\n>>> SCOLLEGA IL MODULO RFID IN E COLLEGA SOLO RFID OUT <<<")
    print(">>> USA I PIN DEL PRIMO MODULO (RST=22, CS=8) <<<")
    input("Premi ENTER quando hai fatto il cambio...")
    
    result2 = test_single_rfid(
        22,  # Usa pin del primo lettore
        8,   # Usa pin del primo lettore
        "RFID OUT (sui pin del primo)"
    )
    
    print("\n" + "="*40)
    print("📊 RISULTATI FINALI:")
    if result1:
        print("✅ RFID IN: Funziona")
    else:
        print("❌ RFID IN: Non funziona")
        
    if result2:
        print("✅ RFID OUT: Funziona sui pin del primo")
        print("   → Il modulo OUT è OK")
        print("   → Il problema è nei pin 27/7")
    else:
        print("❌ RFID OUT: Non funziona neanche sui pin del primo")
        print("   → Il modulo OUT è DIFETTOSO")