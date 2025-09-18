#!/usr/bin/env python3
"""
Test minimo per verificare che funzioni tutto
"""
import sys
import os
import time

# Path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

def test_basic_relay():
    """Test base del relè"""
    print("🧪 TEST BASE RELÈ")
    print("="*25)
    
    try:
        # Import base
        from config import Config
        from relay_controller import RelayController
        
        print(f"📊 Config caricata: GPIO {Config.RELAY_IN_PIN}")
        
        # Crea relè semplice
        relay = RelayController(
            relay_id="test",
            gpio_pin=Config.RELAY_IN_PIN,
            active_time=2,
            active_low=Config.RELAY_IN_ACTIVE_LOW
        )
        
        # Inizializza
        if not relay.initialize():
            print("❌ Init fallita")
            return False
        
        print("✅ Relè inizializzato")
        
        # Attiva per 2 secondi
        print("⚡ Attivazione per 2 secondi...")
        if relay.activate(2):
            print("✅ Comando inviato")
            
            # Aspetta che finisca
            time.sleep(3)
            
            # Controlla status
            status = relay.get_status()
            if status['active']:
                print("⚠️ Relè ancora attivo - forzo stop")
                relay.force_off()
            else:
                print("✅ Relè spento automaticamente")
        else:
            print("❌ Comando fallito")
            return False
        
        # Cleanup
        relay.cleanup()
        print("✅ Test completato")
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

def emergency_off():
    """Spegnimento di emergenza semplice"""
    print("🚨 EMERGENCY OFF")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Pin più comuni
        for pin in [18, 19]:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                print(f"🔴 GPIO {pin}: OFF")
            except Exception as e:
                print(f"⚠️ GPIO {pin}: {e}")
        
        GPIO.cleanup()
        print("✅ Emergency off completato")
        
    except Exception as e:
        print(f"❌ Errore emergency: {e}")

def main():
    print("🔧 TEST MINIMO RELÈ")
    print("="*25)
    
    if len(sys.argv) > 1 and sys.argv[1] == "emergency":
        emergency_off()
        return
    
    print(f"📁 Src dir: {src_dir}")
    
    if not os.path.exists(src_dir):
        print("❌ Directory src non trovata")
        return
    
    # Test base
    success = test_basic_relay()
    
    if success:
        print("\n🎉 Test riuscito!")
    else:
        print("\n💡 Se il relè non si spegne:")
        print("   sudo python3 test_simple_minimal.py emergency")

if __name__ == "__main__":
    main()
