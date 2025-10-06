#!/usr/bin/env python3
"""
Test pin per pin per doppio RFID
"""
import time

def test_specific_pins():
    """Test pin specifici uno alla volta"""
    import RPi.GPIO as GPIO
    from config import Config
    
    print("🔍 TEST PIN SPECIFICI")
    print("-" * 30)
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # Test tutti i pin uno per uno
    pins_to_test = [
        Config.RFID_IN_RST_PIN,
        Config.RFID_IN_SDA_PIN,
        Config.RFID_OUT_RST_PIN,
        Config.RFID_OUT_SDA_PIN
    ]
    
    for pin in pins_to_test:
        try:
            print(f"Test GPIO{pin}...", end="")
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.LOW)
            print(" ✅ OK")
        except Exception as e:
            print(f" ❌ ERRORE: {e}")
    
    GPIO.cleanup()

def test_rfid_with_fixed_pins():
    """Test RFID con pin sicuramente funzionanti"""
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
    
    print("\n🔍 TEST RFID CON PIN SICURI")
    print("-" * 30)
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # Pin sicuramente liberi e funzionanti
    safe_pins = [
        (22, 8, "Configurazione 1"),   # Pin originali primo lettore
        (23, 24, "Configurazione 2"),  # Pin alternativi
        (16, 26, "Configurazione 3"),  # Altri pin alternativi
    ]
    
    for rst_pin, cs_pin, config_name in safe_pins:
        try:
            print(f"\n{config_name}: RST={rst_pin}, CS={cs_pin}")
            reader = SimpleMFRC522(rst=rst_pin, cs=cs_pin)
            result = reader.read_no_block()
            print(f"✅ {config_name}: FUNZIONA")
            del reader
            time.sleep(1)
        except Exception as e:
            print(f"❌ {config_name}: {e}")
    
    GPIO.cleanup()

if __name__ == "__main__":
    test_specific_pins()
    test_rfid_with_fixed_pins()