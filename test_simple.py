#!/usr/bin/env python3
"""
Test semplificato per debug rapido
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def emergency_off():
    """Spegnimento emergenza tutti i relè"""
    print("🚨 SPEGNIMENTO EMERGENZA")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        pins = [18, 19]  # Modifica se diversi
        
        for pin in pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                print(f"✅ GPIO {pin}: OFF")
            except Exception as e:
                print(f"❌ GPIO {pin}: {e}")
        
        GPIO.cleanup()
        print("✅ Spegnimento completato")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

def test_relay():
    """Test relè rapido"""
    print("🧪 TEST RELÈ RAPIDO")
    
    try:
        from config import Config
        from relay_controller import RelayController
        
        print(f"📊 Config: Pin={Config.RELAY_IN_PIN}, ActiveLow={Config.RELAY_IN_ACTIVE_LOW}")
        
        # Crea relè
        relay = RelayController(
            relay_id="test",
            gpio_pin=Config.RELAY_IN_PIN,
            active_time=2,
            active_low=Config.RELAY_IN_ACTIVE_LOW,
            initial_state=Config.RELAY_IN_INITIAL_STATE
        )
        
        if not relay.initialize():
            print("❌ Init fallita")
            return False
        
        print("⚡ ATTIVAZIONE 2s - Controlla relè...")
        success = relay.activate(2)
        
        if success:
            print("✅ Comando inviato")
            time.sleep(3)  # Aspetta completamento
            
            status = relay.get_status()
            print(f"📋 Stato finale: Attivo={status['active']}")
            
            if status['active']:
                print("⚠️ Relè ancora attivo - forzo OFF")
                relay.force_off()
            else:
                print("✅ Test OK - Relè spento automaticamente")
        else:
            print("❌ Comando fallito")
        
        relay.cleanup()
        return success
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def test_manual_control():
    """Test controllo manuale"""
    print("🧪 TEST CONTROLLO MANUALE")
    
    try:
        from relay_manager import RelayManager
        from manual_control import ManualControl
        from logger import AccessLogger
        
        # Init componenti
        logger = AccessLogger("logs")
        relay_manager = RelayManager()
        
        if not relay_manager.initialize():
            print("❌ RelayManager init fallita")
            return False
        
        manual_control = ManualControl(None, relay_manager, logger)
        manual_control.is_enabled = True
        
        print("🔓 Test apertura locale...")
        success = manual_control.manual_open_local('in', 2, 'test_user')
        
        if success:
            print("✅ Apertura manuale OK")
            time.sleep(3)
            
            # Verifica spegnimento
            for direction in relay_manager.get_active_relays():
                status = relay_manager.get_relay_status(direction)
                if status['active']:
                    print(f"⚠️ Relè {direction} ancora attivo!")
                    relay_manager.force_off_all()
                else:
                    print(f"✅ Relè {direction} spento correttamente")
        else:
            print("❌ Apertura manuale fallita")
        
        relay_manager.cleanup()
        return success
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def test_rfid_debounce():
    """Test debounce RFID"""
    print("🧪 TEST RFID DEBOUNCE")
    
    try:
        from rfid_reader import RFIDReader
        
        reader = RFIDReader("test")
        
        if not reader.initialize():
            print("❌ RFID init fallita")
            return False
        
        print("📱 Prova ad appoggiare e rimuovere la stessa card velocemente...")
        print("   Dovrebbe essere letta solo UNA volta per appoggio")
        print("   Premi Ctrl+C per fermare")
        
        count = 0
        while True:
            card_id, card_data = reader.read_card()
            
            if card_id is not None:
                count += 1
                card_info = reader.get_card_info(card_id, card_data)
                print(f"#{count}: Card {card_info['uid_formatted']} - {time.strftime('%H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n✅ Test debounce completato")
        return True
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Rapidi Sistema")
    parser.add_argument("--emergency", action="store_true", help="Spegni tutti i relè")
    parser.add_argument("--relay", action="store_true", help="Test relè")
    parser.add_argument("--manual", action="store_true", help="Test controllo manuale")
    parser.add_argument("--rfid", action="store_true", help="Test RFID debounce")
    
    args = parser.parse_args()
    
    if args.emergency:
        emergency_off()
    elif args.relay:
        test_relay()
    elif args.manual:
        test_manual_control()
    elif args.rfid:
        test_rfid_debounce()
    else:
        print("🔧 TEST RAPIDI SISTEMA")
        print("="*30)
        print("--emergency  : Spegni relè")
        print("--relay      : Test relè")
        print("--manual     : Test controllo manuale")
        print("--rfid       : Test RFID debounce")
        print()
        print("Esempi:")
        print("sudo python3 test_simple.py --relay")
        print("sudo python3 test_simple.py --emergency")

if __name__ == "__main__":
    main()