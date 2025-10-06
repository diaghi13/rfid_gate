#!/usr/bin/env python3
"""
Test semplificato per doppio RFID - VERSIONE CORRETTA
"""
import time
import sys

# CORREZIONE: Import globale all'inizio
print("🔍 STEP 0: Import librerie")
try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    from config import Config
    print("✅ Tutte le librerie importate correttamente")
except Exception as e:
    print(f"❌ Errore import: {e}")
    sys.exit(1)

# Test 1: Verifica configurazione
print("\n🔍 STEP 1: Verifica configurazione")
print(f"✅ Config caricato")
print(f"   RFID_IN:  RST={Config.RFID_IN_RST_PIN}, SDA={Config.RFID_IN_SDA_PIN}")
print(f"   RFID_OUT: RST={Config.RFID_OUT_RST_PIN}, SDA={Config.RFID_OUT_SDA_PIN}")

# Test 2: Verifica GPIO
print("\n🔍 STEP 2: Verifica GPIO")
try:
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

# Test 4: Test RFID IN (dovrebbe funzionare)
print("\n🔍 STEP 4: Test RFID IN")
reader1 = None
try:
    print(f"   Creazione con RST={Config.RFID_IN_RST_PIN}, CS={Config.RFID_IN_SDA_PIN}")
    reader1 = SimpleMFRC522(rst=Config.RFID_IN_RST_PIN, cs=Config.RFID_IN_SDA_PIN)
    print("✅ RFID IN creato")
    
    # Test veloce
    result = reader1.read_no_block()
    print("✅ RFID IN: Test lettura OK")
    
except Exception as e:
    print(f"❌ RFID IN errore: {e}")

# CORREZIONE: Pausa e cleanup esplicito prima del secondo test
print("\n🔍 STEP 4.5: Cleanup primo lettore")
try:
    if reader1:
        del reader1
    time.sleep(2)  # Pausa più lunga
    print("✅ Cleanup completato")
except Exception as e:
    print(f"⚠️ Cleanup warning: {e}")

# Test 5: Test RFID OUT
print("\n🔍 STEP 5: Test RFID OUT")
reader2 = None
try:
    print(f"   Creazione con RST={Config.RFID_OUT_RST_PIN}, CS={Config.RFID_OUT_SDA_PIN}")
    reader2 = SimpleMFRC522(rst=Config.RFID_OUT_RST_PIN, cs=Config.RFID_OUT_SDA_PIN)
    print("✅ RFID OUT creato")
    
    # Test veloce
    result = reader2.read_no_block()
    print("✅ RFID OUT: Test lettura OK")
    
except Exception as e:
    print(f"❌ RFID OUT errore: {e}")
    print(f"   Tipo errore: {type(e).__name__}")
    print(f"   Dettagli: {str(e)}")

# Test 6: Test pin GPIO individualmente
print("\n🔍 STEP 6: Test pin GPIO singoli")
test_pins = [
    (Config.RFID_OUT_RST_PIN, "RFID_OUT_RST"),
    (Config.RFID_OUT_SDA_PIN, "RFID_OUT_SDA")
]

for pin, name in test_pins:
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(pin, GPIO.LOW)
        print(f"✅ {name} (GPIO{pin}): Test OK")
    except Exception as e:
        print(f"❌ {name} (GPIO{pin}): Errore {e}")

# Test 7: Test costruttore senza parametri
print("\n🔍 STEP 7: Test costruttore senza parametri")
try:
    reader3 = SimpleMFRC522()  # Senza parametri
    print("✅ Costruttore senza parametri: OK")
    
    # Configurazione manuale
    if hasattr(reader3, 'READER'):
        reader3.READER.RST = Config.RFID_OUT_RST_PIN
        reader3.READER.CS = Config.RFID_OUT_SDA_PIN
        if hasattr(reader3.READER, 'SDA'):
            reader3.READER.SDA = Config.RFID_OUT_SDA_PIN
        print("✅ Configurazione manuale: OK")
        
        # Test lettura
        result = reader3.read_no_block()
        print("✅ Test lettura con config manuale: OK")
    
except Exception as e:
    print(f"❌ Test costruttore senza parametri: {e}")

# Cleanup finale
try:
    GPIO.cleanup()
    print("\n✅ Cleanup finale completato")
except:
    pass

print("\n" + "="*50)
print("📝 ANALISI RISULTATI:")
print("1. Se STEP 4 OK e STEP 5 fallisce → problema pin/hardware")
print("2. Se STEP 7 OK → problema nel costruttore con parametri")
print("3. Se tutto fallisce → problema libreria/SPI")
print("="*50)