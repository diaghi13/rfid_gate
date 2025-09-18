#!/usr/bin/env python3
"""
Script di debug per testare il funzionamento dei relè
"""

import sys
import os
import time
import threading

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from relay_controller import RelayController
from relay_manager import RelayManager

def test_single_relay():
    """Test di un singolo relè con debug dettagliato"""
    print("🧪 TEST SINGOLO RELÈ CON DEBUG")
    print("="*50)
    
    try:
        # Crea relè di test
        relay = RelayController(
            relay_id="test",
            gpio_pin=Config.RELAY_IN_PIN,
            active_time=3,
            active_low=Config.RELAY_IN_ACTIVE_LOW,
            initial_state=Config.RELAY_IN_INITIAL_STATE
        )
        
        print(f"📊 Configurazione relè:")
        print(f"   GPIO Pin: {relay.gpio_pin}")
        print(f"   Active Low: {relay.active_low}")
        print(f"   Initial State: {relay.initial_state}")
        
        # Inizializza
        if not relay.initialize():
            print("❌ Errore inizializzazione relè")
            return False
        
        # Stato iniziale
        status = relay.get_status()
        print(f"\n📋 Stato iniziale:")
        print(f"   Inizializzato: {status['initialized']}")
        print(f"   Attivo: {status['active']}")
        print(f"   GPIO State: {status['gpio_state']}")
        
        # Test attivazione
        print(f"\n⚡ Test attivazione per 3 secondi...")
        success = relay.activate(3)
        
        if success:
            print("✅ Comando attivazione inviato")
            
            # Monitor dello stato durante l'attivazione
            for i in range(5):  # Monitor per 5 secondi
                time.sleep(1)
                status = relay.get_status()
                print(f"   Secondo {i+1}: Attivo={status['active']}, GPIO={status['gpio_state']}")
                
                if not status['active'] and i < 3:
                    print("⚠️ Relè si è spento prima del previsto!")
        else:
            print("❌ Errore comando attivazione")
        
        # Stato finale
        time.sleep(1)
        status = relay.get_status()
        print(f"\n📋 Stato finale:")
        print(f"   Attivo: {status['active']}")
        print(f"   GPIO State: {status['gpio_state']}")
        
        # Cleanup
        relay.cleanup()
        print("🧹 Cleanup completato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        return False

def test_relay_manager():
    """Test del RelayManager completo"""
    print("\n🧪 TEST RELAY MANAGER")
    print("="*50)
    
    try:
        # Inizializza manager
        manager = RelayManager()
        if not manager.initialize():
            print("❌ Errore inizializzazione RelayManager")
            return False
        
        available_relays = manager.get_active_relays()
        print(f"📊 Relè disponibili: {available_relays}")
        
        if not available_relays:
            print("❌ Nessun relè configurato")
            return False
        
        # Test ogni relè disponibile
        for direction in available_relays:
            print(f"\n⚡ Test relè {direction.upper()}...")
            
            status_before = manager.get_relay_status(direction)
            print(f"   Stato prima: Attivo={status_before['active']}, GPIO={status_before.get('gpio_state', 'N/A')}")
            
            # Attiva relè
            success = manager.activate_relay(direction, 2)
            
            if success:
                print(f"✅ Relè {direction} attivato")
                
                # Monitor per 3 secondi
                for i in range(4):
                    time.sleep(1)
                    status = manager.get_relay_status(direction)
                    print(f"   Secondo {i+1}: Attivo={status['active']}, GPIO={status.get('gpio_state', 'N/A')}")
                
            else:
                print(f"❌ Errore attivazione relè {direction}")
            
            # Verifica spegnimento finale
            final_status = manager.get_relay_status(direction)
            if final_status['active']:
                print(f"⚠️ Relè {direction} ancora attivo! Forzo spegnimento...")
                relay = manager.relays.get(direction)
                if relay:
                    relay.force_off_with_verification()
        
        # Cleanup
        manager.cleanup()
        print("🧹 Cleanup RelayManager completato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test RelayManager: {e}")
        return False

def test_manual_open_simulation():
    """Simula apertura manuale completa"""
    print("\n🧪 TEST SIMULAZIONE APERTURA MANUALE")
    print("="*50)
    
    try:
        from manual_control import ManualControl
        from logger import AccessLogger
        
        # Setup componenti
        logger = AccessLogger(Config.LOG_DIRECTORY)
        manager = RelayManager()
        
        if not manager.initialize():
            print("❌ RelayManager non inizializzato")
            return False
        
        manual_control = ManualControl(None, manager, logger)
        manual_control.is_enabled = True
        
        print("📋 Configurazione:")
        print(f"   Relè disponibili: {manager.get_active_relays()}")
        
        # Test apertura locale
        print("\n🔓 Test apertura manuale locale...")
        success = manual_control.manual_open_local('in', 2, 'test_user')
        
        if success:
            print("✅ Apertura manuale completata")
            
            # Verifica che il relè sia spento dopo il test
            time.sleep(3)
            for direction in manager.get_active_relays():
                status = manager.get_relay_status(direction)
                if status['active']:
                    print(f"⚠️ Relè {direction} ancora attivo dopo test!")
                    relay = manager.relays.get(direction)
                    if relay:
                        relay.force_off_with_verification()
                else:
                    print(f"✅ Relè {direction} spento correttamente")
        else:
            print("❌ Apertura manuale fallita")
        
        # Statistiche
        stats = manual_control.get_stats()
        print(f"\n📊 Statistiche: {stats}")
        
        # Cleanup
        manager.cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore simulazione: {e}")
        return False

def emergency_relay_off():
    """Spegnimento di emergenza di tutti i relè"""
    print("🚨 SPEGNIMENTO EMERGENZA TUTTI I RELÈ")
    print("="*40)
    
    try:
        import RPi.GPIO as GPIO
        
        # Lista dei pin da forzare OFF
        pins_to_check = [
            Config.RELAY_IN_PIN,
            Config.RELAY_OUT_PIN if hasattr(Config, 'RELAY_OUT_PIN') else None
        ]
        
        GPIO.setmode(GPIO.BCM)
        
        for pin in pins_to_check:
            if pin is not None:
                try:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)  # Forza LOW
                    print(f"🔴 GPIO {pin}: Forzato LOW")
                    
                    # Verifica
                    state = GPIO.input(pin)
                    print(f"📊 GPIO {pin}: Stato attuale = {'HIGH' if state else 'LOW'}")
                    
                except Exception as e:
                    print(f"❌ Errore GPIO {pin}: {e}")
        
        GPIO.cleanup()
        print("✅ Spegnimento emergenza completato")
        
    except Exception as e:
        print(f"❌ Errore spegnimento emergenza: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Debug Relè")
    parser.add_argument("--single", action="store_true", help="Test singolo relè")
    parser.add_argument("--manager", action="store_true", help="Test RelayManager")
    parser.add_argument("--manual", action="store_true", help="Test apertura manuale")
    parser.add_argument("--emergency-off", action="store_true", help="Spegnimento emergenza")
    parser.add_argument("--all", action="store_true", help="Tutti i test")
    
    args = parser.parse_args()
    
    if args.emergency_off:
        emergency_relay_off()
    elif args.all:
        test_single_relay()
        test_relay_manager()
        test_manual_open_simulation()
    elif args.single:
        test_single_relay()
    elif args.manager:
        test_relay_manager()
    elif args.manual:
        test_manual_open_simulation()
    else:
        print("🔧 TEST DEBUG RELÈ")
        print("="*30)
        print("Opzioni:")
        print("  --single      : Test singolo relè")
        print("  --manager     : Test RelayManager")
        print("  --manual      : Test apertura manuale")
        print("  --emergency-off : Spegnimento emergenza")
        print("  --all         : Tutti i test")
        print()
        print("Esempi:")
        print("  sudo python3 test_relay.py --single")
        print("  sudo python3 test_relay.py --emergency-off")

if __name__ == "__main__":
    main()