#!/usr/bin/env python3
"""
Manager relè semplice
"""
import threading
import atexit
import RPi.GPIO as GPIO
from config import Config
from relay_controller import RelayController

class RelayManager:
    """Manager semplice per relè multipli"""
    
    def __init__(self):
        self.relays = {}
        self.is_initialized = False
        self._lock = threading.Lock()
        
        # Cleanup automatico
        atexit.register(self._cleanup_all)
    
    def _cleanup_all(self):
        """Cleanup automatico all'uscita"""
        try:
            # Spegni pin conosciuti
            pins_to_clean = []
            if Config.RELAY_IN_ENABLE:
                pins_to_clean.append(Config.RELAY_IN_PIN)
            if Config.RELAY_OUT_ENABLE:
                pins_to_clean.append(Config.RELAY_OUT_PIN)
            
            GPIO.setmode(GPIO.BCM)
            for pin in pins_to_clean:
                try:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
                except:
                    pass
            
            GPIO.cleanup()
            
        except:
            pass  # Silenzioso durante atexit
    
    def initialize(self):
        """Inizializza relè"""
        try:
            print("⚡ Inizializzazione Relay Manager...")
            
            # Relè IN
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
            
            # Relè OUT
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
            return True
            
        except Exception as e:
            print(f"❌ Errore RelayManager: {e}")
            return False
    
    def activate_relay(self, direction, duration=None):
        """Attiva relè"""
        with self._lock:
            if direction not in self.relays:
                print(f"❌ Relè {direction.upper()} non configurato")
                return False
            
            relay = self.relays[direction]
            result = relay.activate(duration)
            
            if result:
                print(f"⚡ Relè {direction.upper()}: attivato")
            else:
                print(f"❌ Relè {direction.upper()}: errore")
            
            return result
    
    def force_off_all(self):
        """Spegne tutti i relè"""
        with self._lock:
            for direction, relay in self.relays.items():
                relay.force_off()
                print(f"🔴 Relè {direction.upper()}: OFF")
    
    def reset_all_to_initial_state(self):
        """Reset tutti i relè"""
        self.force_off_all()
    
    def get_relay_status(self, direction):
        """Status relè specifico"""
        if direction in self.relays:
            status = self.relays[direction].get_status()
            status['direction'] = direction
            return status
        return None
    
    def get_all_status(self):
        """Status tutti i relè"""
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
        """Controlla se relè attivo"""
        if direction in self.relays:
            return self.relays[direction].is_active
        return False
    
    def get_active_relays(self):
        """Lista relè configurati"""
        return list(self.relays.keys())
    
    def cleanup(self):
        """Cleanup"""
        try:
            print("🛑 Cleanup RelayManager...")
            
            # Pulisci ogni relè
            for direction, relay in self.relays.items():
                relay.cleanup()
            
            # Cleanup GPIO finale
            try:
                GPIO.cleanup()
            except:
                pass
            
            print("✅ RelayManager cleanup OK")
            
        except Exception as e:
            print(f"Warning cleanup RelayManager: {e}")