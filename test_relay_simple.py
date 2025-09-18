#!/usr/bin/env python3
"""
Test semplice per debug relè - senza dipendenze complesse
"""

import sys
import os
import time

# Simple path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def emergency_off():
    """Spegnimento emergenza"""
    print("🚨 SPEGNIMENTO EMERGENZA")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Pin da spegnere
        pins = [18, 19]  # Modifica se necessario
        
        for pin in pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                print(f"✅ GPIO {pin}: OFF")
            except Exception as e:
                print(f"❌ GPIO {pin}: {e}")
        
        GPIO.cleanup()
        print("✅ Emergenza completata")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

def test_manual_simple():
    """Test manuale semplificato"""
    print("🧪 TEST MANUALE SEMPLIFICATO")
    
    try:
        from config import Config
        from relay_controller import RelayController
        
        print(f"📊 Config: Pin={Config.RELAY_IN_PIN}, ActiveLow={Config.RELAY_IN_ACTIVE_LOW}")
        
        # Crea relè
        relay = RelayController(
            relay_id="test_simple",
            gpio_pin=Config.RELAY_IN_PIN,
            active_time=2,  # 2 secondi
            active_low=Config.RELAY_IN_ACTIVE_LOW,
            initial_state=Config.RELAY_IN_INITIAL_STATE
        )
        
        # Inizializza
        if not relay.initialize():
            print("❌ Errore inizializzazione")
            return False
        
        # Stato iniziale
        print(f"📋 Stato iniziale: {relay.get_status()}")
        
        print(f"\n⚡ ATTIVAZIONE per 2 secondi...")
        print("👀 Monitora il relè - dovrebbe:")
        print("   1. Attivarsi (LED/click)")
        print("   2. Rimanere attivo per 2s") 
        print("   3. Spegnersi automaticamente")
        print("   4. RIMANERE SPENTO")
        
        success = relay.activate(2)
        
        if success:
            print("✅ Comando inviato")
            
            # Aspetta completamento + margine
            time.sleep(3)
            
            # Verifica stato finale
            final_status = relay.get_status()
            print(f"\n📋 Stato finale:")
            print(f"   Attivo: {final_status['active']}")
            print(f"   GPIO: {final_status['gpio_state']}")
            
            if final_status['active']:
                print("❌ PROBLEMA: Relè ancora attivo!")
                relay.force_off_with_verification()
            elif final_status['gpio_state'] == "HIGH":
                print("❌ PROBLEMA: GPIO ancora HIGH!")
                relay.force_off()
            else:
                print("✅ TEST SUPERATO: Relè spento correttamente")
        else:
            print("❌ Comando fallito")
        
        # Cleanup
        relay.cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def monitor_gpio():
    """Monitor continuo dello stato GPIO"""
    print("👁️ MONITOR GPIO")
    print("Premi Ctrl+C per fermare")
    
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        pin = 18  # Modifica se necessario
        GPIO.setup(pin, GPIO.IN)
        
        last_state = None
        
        while True:
            current_state = GPIO.input(pin)
            state_str = "HIGH" if current_state else "LOW"
            
            if current_state != last_state:
                timestamp = time.strftime("%H:%M:%S")
                print(f"{timestamp} - GPIO {pin}: {state_str}")
                last_state = current_state
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitor fermato")
    except Exception as e:
        print(f"❌ Errore monitor: {e}")
    finally:
        try:
            GPIO.cleanup()
        except:
            pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Semplice Relè")
    parser.add_argument("--emergency", action="store_true", help="Spegnimento emergenza")
    parser.add_argument("--test", action="store_true", help="Test relè")
    parser.add_argument("--monitor", action="store_true", help="Monitor GPIO")
    
    args = parser.parse_args()
    
    if args.emergency:
        emergency_off()
    elif args.test:
        test_manual_simple()
    elif args.monitor:
        monitor_gpio()
    else:
        print("🔧 TEST RELÈ SEMPLIFICATO")
        print("="*30)
        print("--emergency  : Spegni tutti i relè")
        print("--test       : Test attivazione")
        print("--monitor    : Monitor GPIO")
        print()
        print("Esempio:")
        print("sudo python3 test_relay_simple.py --test")

if __name__ == "__main__":
    main()