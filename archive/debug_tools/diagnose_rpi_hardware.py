#!/usr/bin/env python3
"""
🔍 DIAGNOSTICO RASPBERRY PI - Problemi reali lettura card
"""
import sys
import os
import time

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def diagnose_raspberry_pi():
    print("🍇 DIAGNOSTICO RASPBERRY PI REALE")
    print("="*60)
    
    # 1. Verifica importazioni
    print("1️⃣ VERIFICA IMPORTAZIONI")
    try:
        import RPi.GPIO as GPIO
        print("✅ RPi.GPIO disponibile")
    except ImportError:
        print("❌ RPi.GPIO NON disponibile - Non sei su Raspberry Pi!")
        return False
    
    try:
        import board
        import busio
        print("✅ board e busio disponibili")
    except ImportError as e:
        print(f"❌ board/busio mancanti: {e}")
        print("💡 Installa: sudo pip3 install adafruit-circuitpython-busio")
        return False
    
    try:
        from adafruit_pn532.i2c import PN532_I2C
        from adafruit_pn532.spi import PN532_SPI
        print("✅ adafruit_pn532 disponibile")
    except ImportError as e:
        print(f"❌ adafruit_pn532 mancante: {e}")
        print("💡 Installa: sudo pip3 install adafruit-circuitpython-pn532")
        return False
    
    # 2. Test I2C scan
    print("\n2️⃣ SCAN I2C BUS")
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Scan dispositivi I2C
        while not i2c.try_lock():
            pass
        
        print("🔍 Scanning I2C addresses...")
        devices = i2c.scan()
        i2c.unlock()
        
        if devices:
            print(f"📡 Dispositivi I2C trovati: {[hex(d) for d in devices]}")
            
            # Verifica se 0x24 è presente (PN532 default)
            if 0x24 in devices:
                print("✅ PN532 trovato all'indirizzo 0x24")
            else:
                print("⚠️ PN532 NON trovato a 0x24")
                if 0x48 in devices:
                    print("💡 Trovato dispositivo a 0x48 (possibile PN532 in modalità HSU)")
        else:
            print("❌ NESSUN dispositivo I2C trovato!")
            print("🔧 Verifica cablaggio:")
            print("   - VCC → 3.3V")
            print("   - GND → GND") 
            print("   - SDA → GPIO 2 (Pin 3)")
            print("   - SCL → GPIO 3 (Pin 5)")
            return False
            
    except Exception as e:
        print(f"❌ Errore I2C scan: {e}")
        return False
    
    # 3. Test PN532 diretto
    print("\n3️⃣ TEST PN532 DIRETTO")
    try:
        from config import Config
        
        print(f"Configurazione: {Config.RFID_IN_PN532_I2C_ADDRESS:#x}")
        
        # Test connessione diretta
        pn532 = PN532_I2C(i2c, address=Config.RFID_IN_PN532_I2C_ADDRESS)
        
        # Test firmware version
        ic, ver, rev, support = pn532.firmware_version
        print(f"✅ PN532 Firmware: IC={ic:#x}, Ver={ver}.{rev}")
        
        # Configura per lettura carte
        pn532.SAM_configuration()
        print("✅ SAM configurato")
        
        # Test lettura diretta
        print("\n🔄 TEST LETTURA DIRETTA")
        print("Passa una card ADESSO nei prossimi 10 secondi...")
        
        for attempt in range(20):  # 10 secondi, check ogni 0.5s
            print(f"⏳ Tentativo {attempt + 1}/20", end="\r")
            
            try:
                # Lettura non-blocking
                uid = pn532.read_passive_target(timeout=0.5)
                
                if uid is not None:
                    uid_hex = ' '.join([f'{i:02x}' for i in uid])
                    print(f"\n🎉 CARD TROVATA! UID: {uid_hex}")
                    print(f"📊 UID Length: {len(uid)} bytes")
                    print(f"📊 UID Raw: {list(uid)}")
                    return True
                    
            except Exception as e:
                print(f"\n⚠️ Errore lettura: {e}")
                
            time.sleep(0.5)
        
        print("\n⏰ Timeout - Nessuna card rilevata")
        print("\n🔍 POSSIBILI PROBLEMI:")
        print("1. 🎯 Card troppo lontana dal lettore")
        print("2. 🔄 Card non supportata (solo MIFARE/NTAG)")
        print("3. ⚡ Alimentazione insufficiente")
        print("4. 📡 Interferenze elettromagnetiche")
        print("5. 🔧 Cablaggio difettoso")
        
        return False
        
    except Exception as e:
        print(f"❌ Errore test PN532: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_wiring():
    print("\n" + "="*60)
    print("🔧 VERIFICA CABLAGGIO PN532")
    print("="*60)
    
    print("📋 CABLAGGIO CORRETTO:")
    print("PN532 → Raspberry Pi")
    print("VCC   → Pin 1  (3.3V)")
    print("GND   → Pin 6  (GND)")
    print("SDA   → Pin 3  (GPIO 2)")
    print("SCL   → Pin 5  (GPIO 3)")
    
    print("\n⚠️ VERIFICA ANCHE:")
    print("1. PN532 in modalità I2C (switch/jumper)")
    print("2. Alimentazione stabile 3.3V")
    print("3. Cavi non troppo lunghi (<20cm)")
    print("4. Saldature ben fatte")
    print("5. No conflitti altri dispositivi I2C")
    
    print("\n🔧 COMANDI UTILI:")
    print("i2cdetect -y 1    # Scan dispositivi I2C")
    print("dmesg | grep i2c  # Log I2C kernel")

def main():
    print("🎯 QUESTO È IL VERO TEST PER RASPBERRY PI")
    print("Identifica problemi reali di hardware/configurazione")
    print()
    
    if diagnose_raspberry_pi():
        print("\n✅ HARDWARE FUNZIONA - Il problema è nel software")
    else:
        print("\n❌ PROBLEMA HARDWARE IDENTIFICATO")
        diagnose_wiring()

if __name__ == "__main__":
    main()