#!/usr/bin/env python3
"""
Manager relè con cleanup garantito
"""
import threading
import atexit
import signal
import sys
import RPi.GPIO as GPIO
from config import Config
from relay_controller import RelayController

class RelayManager:
    """Manager per relè multipli con cleanup garantito"""
    
    def __init__(self):
        self.relays = {}
        self.is_initialized = False
        self._lock = threading.Lock()
        
        # Registra cleanup automatico
        atexit.register(self._emergency_cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestisce segnali di terminazione"""
        print(f"\n🛑 RelayManager - Segnale {signum} ricevuto")
        self.emergency_stop_all()
        sys.exit(0)
    
    def _emergency_cleanup(self):
        """Cleanup di emergenza"""
        try:
            self.emergency_stop_all()
        except:
            pass
    
    def initialize(self):
        """Inizializza i relè attivi"""
        try:
            print("⚡ Inizializzazione Relay Manager...")
            
            # Inizializza relè IN se abilitato
            if Config.RELAY_IN_ENABLE:
                print(f"🔵 Relè IN (GPIO {Config.RELAY_IN_PIN})")
                relay_in = RelayController(
                    relay_id="in",
                    gpio_pin=Config.RELAY_IN_PIN,
                    active_time=Config.RELAY_IN_ACTIVE_TIME,
                    active_low=Config.RELAY_IN_ACTIVE_LOW,
                    initial_state=Config.RELAY_IN_INITIAL_STATE
                )
                
                if relay_in.initialize():
                    self.relays["in"] = relay_in
                    print("✅ Relè IN OK")
                else:
                    print("❌ Relè IN fallito")
                    return False
            
            # Inizializza relè OUT se abilitato
            if Config.BIDIRECTIONAL_MODE and Config.RELAY_OUT_ENABLE:
                print(f"🔴 Relè OUT (GPIO {Config.RELAY_OUT_PIN})")
                relay_out = RelayController(
                    relay_id="out",
                    gpio_pin=Config.RELAY_OUT_PIN,
                    active_time=Config.RELAY_OUT_ACTIVE_TIME,
                    active_low=Config.RELAY_OUT_ACTIVE_LOW,
                    initial_state=Config.RELAY_OUT_INITIAL_STATE
                )
                
                if relay_out.initialize():
                    self.relays["out"] = relay_out
                    print("✅ Relè OUT OK")
                else:
                    print("❌ Relè OUT fallito")
                    return False
            
            if not self.relays:
                print("❌ Nessun relè configurato")
                return False
            
            self.is_initialized = True
            print(f"✅ RelayManager: {len(self.relays)} relè attivi")
            
            # Test finale
            self._test_all_relays_quick()
            
            return True
            
        except Exception as e:
            print(f"❌ Errore RelayManager: {e}")
            return False
    
    def _test_all_relays_quick(self):
        """Test rapido di tutti i relè (0.2s ciascuno)"""
        print("🧪 Test rapido relè...")
        for direction, relay in self.relays.items():
            try:
                print(f"  Test {direction}...", end=" ")
                relay.activate(0.2)  # Test molto breve
                print("OK")
            except Exception as e:
                print(f"Errore: {e}")
    
    def activate_relay(self, direction, duration=None):
        """Attiva relè per direzione specificata"""
        with self._lock:
            if direction not in self.relays:
                print(f"❌ Relè {direction.upper()} non configurato")
                return False
            
            relay = self.relays[direction]
            result = relay.activate(duration)
            
            if result:
                print(f"⚡ Relè {direction.upper()}: comando inviato")
            else:
                print(f"❌ Relè {direction.upper()}: comando fallito")
            
            return result
    
    def emergency_stop_all(self):
        """Spegnimento di emergenza di tutti i relè"""
        print("🚨 EMERGENCY STOP tutti i relè...")
        
        with self._lock:
            for direction, relay in self.relays.items():
                try:
                    relay.force_off_immediate()
                    print(f"🔴 Relè {direction.upper()}: STOP")
                except Exception as e:
                    print(f"⚠️ Relè {direction}: {e}")
        
        # Cleanup GPIO finale
        try:
            # Spegni pin specifici della configurazione
            GPIO.setmode(GPIO.BCM)
            
            if Config.RELAY_IN_ENABLE:
                GPIO.setup(Config.RELAY_IN_PIN, GPIO.OUT)
                GPIO.output(Config.RELAY_IN_PIN, GPIO.LOW)
                print(f"🔴 GPIO {Config.RELAY_IN_PIN} (IN): FORZATO LOW")
            
            if Config.RELAY_OUT_ENABLE:
                GPIO.setup(Config.RELAY_OUT_PIN, GPIO.OUT)
                GPIO.output(Config.RELAY_OUT_PIN, GPIO.LOW)
                print(f"🔴 GPIO {Config.RELAY_OUT_PIN} (OUT): FORZATO LOW")
            
            GPIO.cleanup()
            print("✅ Emergency stop completato")
            
        except Exception as e:
            print(f"⚠️ Warning emergency cleanup: {e}")
    
    def force_off_all(self):
        """Alias per emergency_stop_all"""
        self.emergency_stop_all()
    
    def reset_all_to_initial_state(self):
        """Ripristina tutti i relè allo stato sicuro"""
        with self._lock:
            for direction, relay in self.relays.items():
                relay.reset_to_initial_state()
    
    def get_relay_status(self, direction):
        """Status di un relè specifico"""
        if direction in self.relays:
            status = self.relays[direction].get_status()
            status['direction'] = direction
            return status
        return None
    
    def get_all_status(self):
        """Status di tutti i relè"""
        status = {
            'initialized': self.is_initialized,
            'active_relays': len(self.relays),
            'relays': {}
        }
        
        for direction, relay in self.relays.items():
            relay_status = relay.get_status()
            relay_status['direction'] = direction
            status['relays'][direction] = relay_status
        
        return status
    
    def is_relay_active(self, direction):
        """Controlla se relè è attivo"""
        if direction in self.relays:
            return self.relays[direction].is_active
        return False
    
    def get_active_relays(self):
        """Lista relè configurati"""
        return list(self.relays.keys())
    
    def cleanup(self):
        """Cleanup completo"""
        try:
            print("🛑 Cleanup RelayManager...")
            
            # Spegni tutti i relè
            self.emergency_stop_all()
            
            # Pulisci ogni relè
            for direction, relay in self.relays.items():
                try:
                    relay.cleanup()
                except Exception as e:
                    print(f"⚠️ Warning cleanup relè {direction}: {e}")
            
            self.relays.clear()
            
            # Cleanup finale GPIO
            try:
                GPIO.cleanup()
                print("🧹 GPIO cleanup finale completato")
            except:
                pass
            
            print("✅ RelayManager cleanup completato")
            
        except Exception as e:
            print(f"⚠️ Warning cleanup RelayManager: {e}")
    
    def __del__(self):
        """Destructor con cleanup garantito"""
        try:
            self.emergency_stop_all()
        except:
            pass