#!/usr/bin/env python3
"""
Test semplificato per doppio RFID - DEBUG STEP BY STEP
"""
import time
import sys

# Test 1: Verifica configurazione
print("🔍 STEP 1: Verifica configurazione")
try:
    from config import Config
    print(f"✅ Config caricato")
    print(f"   RFID_IN:  RST={Config.RFID_IN_RST_PIN}, SDA={Config.RFID_IN_SDA_PIN}")
    print(f"   RFID_OUT: RST={Config.RFID_OUT_RST_PIN}, SDA={Config.RFID_OUT_SDA_PIN}")
except Exception as e:
    print(f"❌ Errore config: {e}")
    sys.exit(1)

# Test 2: Verifica GPIO
print("\n🔍 STEP 2: Verifica GPIO")
try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    print("✅ GPIO configurato")
except Exception as e:
    print(f"❌ Errore GPIO: {e}")
    sys.exit(1)

# Test 3: Verifica SPI
print("\n🔍 STEP 3: Verifica SPI")
try:
    import os
    if os.path.exists('/dev/spidev0.0'):
        print("✅ /dev/spidev0.0 disponibile")
    else:
        print("❌ /dev/spidev0.0 NON disponibile")
    
    if os.path.exists('/dev/spidev0.1'):
        print("✅ /dev/spidev0.1 disponibile")
    else:
        print("❌ /dev/spidev0.1 NON disponibile")
except Exception as e:
    print(f"❌ Errore SPI: {e}")

# Test 4: Test singolo lettore (quello che funziona)
print("\n🔍 STEP 4: Test RFID IN (dovrebbe funzionare)")
try:
    from mfrc522 import SimpleMFRC522
    
    reader1 = SimpleMFRC522(rst=Config.RFID_IN_RST_PIN, cs=Config.RFID_IN_SDA_PIN)
    print("✅ RFID IN creato")
    
    # Test veloce
    result = reader1.read_no_block()
    print("✅ RFID IN: Test lettura OK")
    
except Exception as e:
    print(f"❌ RFID IN errore: {e}")

# Test 5: Test secondo lettore (quello che NON funziona)
print("\n🔍 STEP 5: Test RFID OUT (problema qui)")
try:
    time.sleep(1)  # Pausa
    print("⏳ Pausa prima del secondo lettore...")
    
    reader2 = SimpleMFRC522(rst=Config.RFID_OUT_RST_PIN, cs=Config.RFID_OUT_SDA_PIN)
    print("✅ RFID OUT creato")
    
    # Test veloce
    result = reader2.read_no_block()
    print("✅ RFID OUT: Test lettura OK")
    
except Exception as e:
    print(f"❌ RFID OUT errore: {e}")
    print(f"   Questo è il problema principale!")

# Test 6: Test pin specifici
print("\n🔍 STEP 6: Test pin GPIO singoli")
test_pins = [Config.RFID_OUT_RST_PIN, Config.RFID_OUT_SDA_PIN]

for pin in test_pins:
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(pin, GPIO.LOW)
        print(f"✅ GPIO{pin}: Test OK")
    except Exception as e:
        print(f"❌ GPIO{pin}: Errore {e}")

GPIO.cleanup()

print("\n" + "="*50)
print("📝 RISULTATI:")
print("Se RFID IN funziona ma RFID OUT no, il problema è:")
print("1. Pin occupati/conflitto")
print("2. Modulo RFID OUT difettoso") 
print("3. Alimentazione insufficiente")
print("4. Cablaggio errato")
print("="*50)