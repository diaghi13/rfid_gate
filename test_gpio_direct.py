#!/usr/bin/env python3
"""
Test GPIO diretto per capire il problema del relè
"""
import RPi.GPIO as GPIO
import time
import sys

def test_gpio_direct():
    """Test GPIO molto diretto"""
    pin = 18  # Cambia se usi pin diverso
    
    print(f"🧪 TEST GPIO DIRETTO - Pin {pin}")
    print("="*40)
    
    try:
        # Setup
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        print("1️⃣ Stato iniziale...")
        GPIO.output(pin, GPIO.LOW)
        state = GPIO.input(pin)
        print(f"   GPIO {pin} = {'HIGH' if state else 'LOW'}")
        time.sleep(1)
        
        print("2️⃣ Attivazione HIGH...")
        GPIO.output(pin, GPIO.HIGH)
        state = GPIO.input(pin)
        print(f"   GPIO {pin} = {'HIGH' if state else 'LOW'}")
        print("   Relè dovrebbe essere ATTIVO ora - controllalo!")
        time.sleep(3)
        
        print("3️⃣ Disattivazione LOW...")
        GPIO.output(pin, GPIO.LOW)
        state = GPIO.input(pin)
        print(f"   GPIO {pin} = {'HIGH' if state else 'LOW'}")
        print("   Relè dovrebbe essere SPENTO ora - controllalo!")
        time.sleep(1)
        
        print("4️⃣ Test completato - manteniamo LOW...")
        GPIO.output(pin, GPIO.LOW)
        
        # NON fare GPIO.cleanup() per vedere cosa succede
        print("⚠️ NON faccio GPIO.cleanup() - relè dovrebbe rimanere spento")
        print("💡 Controlla fisicamente il relè - è spento?")
        
        input("Premi ENTER quando hai controllato il relè...")
        
        print("5️⃣ Ora faccio GPIO.cleanup()...")
        GPIO.cleanup()
        
        print("💡 Controlla di nuovo il relè - si è riattivato dopo cleanup?")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def test_active_low():
    """Test con logica active LOW"""
    pin = 18
    
    print(f"🧪 TEST ACTIVE LOW - Pin {pin}")
    print("="*40)
    
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        print("1️⃣ Stato spento (HIGH per active low)...")
        GPIO.output(pin, GPIO.HIGH)
        state = GPIO.input(pin)
        print(f"   GPIO {pin} = {'HIGH' if state else 'LOW'}")
        time.sleep(1)
        
        print("2️⃣ Attivazione (LOW per active low)...")
        GPIO.output(pin, GPIO.LOW)
        state = GPIO.input(pin)
        print(f"   GPIO {pin} = {'HIGH' if state else 'LOW'}")
        print("   Relè dovrebbe essere ATTIVO ora!")
        time.sleep(3)
        
        print("3️⃣ Spegnimento (HIGH per active low)...")
        GPIO.output(pin, GPIO.HIGH)
        state = GPIO.input(pin)
        print(f"   GPIO {pin} = {'HIGH' if state else 'LOW'}")
        print("   Relè dovrebbe essere SPENTO ora!")
        
        print("4️⃣ Mantengo HIGH e NON faccio cleanup...")
        input("Premi ENTER dopo aver controllato il relè...")
        
        GPIO.cleanup()
        print("Fatto cleanup - controlla se si riattiva")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def force_low_permanent():
    """Forza LOW permanente"""
    pin = 18
    
    print(f"🔴 FORZA LOW PERMANENTE - Pin {pin}")
    print("="*30)
    
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        
        print(f"✅ GPIO {pin} forzato LOW")
        print("💡 Relè dovrebbe essere SPENTO")
        print("⚠️ NON faccio cleanup per mantenere LOW")
        
        # Verifica continua
        for i in range(10):
            state = GPIO.input(pin)
            print(f"Check {i+1}: GPIO {pin} = {'HIGH' if state else 'LOW'}")
            time.sleep(1)
        
        print("🔒 GPIO mantenuto LOW - relè dovrebbe rimanere spento")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

def check_config_active_low():
    """Controlla configurazione active_low"""
    print("🔍 CONTROLLO CONFIGURAZIONE")
    print("="*35)
    
    try:
        sys.path.insert(0, 'src')
        from config import Config
        
        print(f"RELAY_IN_PIN: {Config.RELAY_IN_PIN}")
        print(f"RELAY_IN_ACTIVE_LOW: {Config.RELAY_IN_ACTIVE_LOW}")
        print(f"RELAY_IN_INITIAL_STATE: {Config.RELAY_IN_INITIAL_STATE}")
        
        print("\n💡 Interpretazione:")
        if Config.RELAY_IN_ACTIVE_LOW:
            print("   - Relè si attiva con LOW")
            print("   - Relè si spegne con HIGH")
            print("   - Per spegnere definitivamente: GPIO.output(pin, GPIO.HIGH)")
        else:
            print("   - Relè si attiva con HIGH") 
            print("   - Relè si spegne con LOW")
            print("   - Per spegnere definitivamente: GPIO.output(pin, GPIO.LOW)")
            
        return Config.RELAY_IN_ACTIVE_LOW
        
    except Exception as e:
        print(f"❌ Errore config: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("🔧 TEST GPIO DIRETTO")
        print("="*25)
        print("Opzioni:")
        print("  direct     - Test GPIO diretto")
        print("  activelow  - Test active LOW")
        print("  force      - Forza LOW permanente")
        print("  config     - Controlla config")
        print()
        print("Esempi:")
        print("  sudo python3 test_gpio_direct.py direct")
        print("  sudo python3 test_gpio_direct.py config")
        return
    
    command = sys.argv[1].lower()
    
    if command == "direct":
        test_gpio_direct()
    elif command == "activelow":
        test_active_low()
    elif command == "force":
        force_low_permanent()
    elif command == "config":
        active_low = check_config_active_low()
        if active_low is not None:
            print(f"\n🔧 Per test corretto usa:")
            if active_low:
                print("  sudo python3 test_gpio_direct.py activelow")
            else:
                print("  sudo python3 test_gpio_direct.py direct")
    else:
        print(f"❌ Comando sconosciuto: {command}")

if __name__ == "__main__":
    main()
