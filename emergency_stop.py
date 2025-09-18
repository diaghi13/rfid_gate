#!/usr/bin/env python3
"""
Spegnimento di emergenza per tutti i relè
"""
import RPi.GPIO as GPIO
import time
import sys

def emergency_stop_all():
    """Spegnimento di emergenza di tutti i possibili relè"""
    print("🚨 SPEGNIMENTO DI EMERGENZA TUTTI I RELÈ")
    print("="*50)
    
    # Pin più comuni per relè
    relay_pins = [18, 19, 20, 21, 16, 26, 13, 6, 5, 25, 24, 23]
    
    try:
        GPIO.setmode(GPIO.BCM)
        
        spenti = 0
        for pin in relay_pins:
            try:
                # Configura pin come output
                GPIO.setup(pin, GPIO.OUT)
                
                # Leggi stato attuale
                current_state = GPIO.input(pin)
                
                # Forza a LOW (sicuro per la maggior parte dei setup)
                GPIO.output(pin, GPIO.LOW)
                
                # Verifica
                time.sleep(0.01)
                new_state = GPIO.input(pin)
                
                if current_state != GPIO.LOW:
                    print(f"🔴 GPIO {pin}: {('HIGH' if current_state else 'LOW')} → LOW")
                    spenti += 1
                else:
                    print(f"✅ GPIO {pin}: già LOW")
                    
            except Exception as e:
                print(f"⚠️ GPIO {pin}: errore - {e}")
        
        # Cleanup finale
        GPIO.cleanup()
        
        print(f"\n✅ Spegnimento completato: {spenti} pin modificati")
        print("🔒 Tutti i relè dovrebbero ora essere spenti")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante spegnimento: {e}")
        return False

def check_relay_states():
    """Controlla stato attuale dei relè"""
    print("🔍 CONTROLLO STATO RELÈ")
    print("="*30)
    
    relay_pins = [18, 19, 20, 21, 16, 26]
    
    try:
        GPIO.setmode(GPIO.BCM)
        
        for pin in relay_pins:
            try:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
                state = GPIO.input(pin)
                state_str = "HIGH" if state else "LOW"
                
                # Indicatore visivo
                if state:
                    indicator = "🔴 ATTIVO" if pin in [18, 19] else "⚡ HIGH"
                else:
                    indicator = "✅ SPENTO"
                
                print(f"GPIO {pin:2d}: {state_str:4s} - {indicator}")
                
            except Exception as e:
                print(f"GPIO {pin:2d}: errore - {e}")
        
        GPIO.cleanup()
        
    except Exception as e:
        print(f"❌ Errore controllo: {e}")

def force_specific_relay_off(pin):
    """Forza spegnimento di un relè specifico"""
    print(f"🔴 SPEGNIMENTO FORZATO GPIO {pin}")
    print("="*35)
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        # Stato prima
        old_state = GPIO.input(pin)
        print(f"Stato prima: {'HIGH' if old_state else 'LOW'}")
        
        # Forza LOW
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        
        # Verifica
        new_state = GPIO.input(pin)
        print(f"Stato dopo: {'HIGH' if new_state else 'LOW'}")
        
        if new_state == GPIO.LOW:
            print("✅ Relè spento con successo")
        else:
            print("❌ Relè potrebbe essere ancora attivo")
            
            # Secondo tentativo
            print("🔄 Secondo tentativo...")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.1)
            
            final_state = GPIO.input(pin)
            if final_state == GPIO.LOW:
                print("✅ Spento al secondo tentativo")
            else:
                print("❌ Problema hardware possibile")
        
        GPIO.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("🔧 EMERGENCY STOP RELÈ")
        print("="*25)
        print("Opzioni:")
        print("  all     - Spegni tutti i relè")
        print("  check   - Controlla stato relè")
        print("  <pin>   - Spegni relè specifico")
        print()
        print("Esempi:")
        print("  sudo python3 emergency_stop.py all")
        print("  sudo python3 emergency_stop.py check")
        print("  sudo python3 emergency_stop.py 18")
        return
    
    command = sys.argv[1].lower()
    
    if command == "all":
        emergency_stop_all()
    elif command == "check":
        check_relay_states()
    elif command.isdigit():
        pin = int(command)
        force_specific_relay_off(pin)
    else:
        print(f"❌ Comando sconosciuto: {command}")

if __name__ == "__main__":
    main()