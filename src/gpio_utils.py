#!/usr/bin/env python3
"""
Utility GPIO robuste per evitare errori setmode
"""
import RPi.GPIO as GPIO
import threading

class GPIOManager:
    """Manager globale GPIO per evitare conflitti setmode"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GPIOManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
    
    def safe_setup_pin(self, pin, mode, initial_state=None):
        """Setup sicuro di un pin GPIO"""
        try:
            # Assicurati che setmode sia chiamato
            try:
                GPIO.setmode(GPIO.BCM)
            except:
                # GPIO già configurato, va bene
                pass
            
            GPIO.setup(pin, mode)
            
            if mode == GPIO.OUT and initial_state is not None:
                GPIO.output(pin, initial_state)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Errore setup GPIO {pin}: {e}")
            return False
    
    def safe_output(self, pin, state):
        """Output sicuro su pin GPIO"""
        try:
            try:
                GPIO.setmode(GPIO.BCM)
            except:
                pass
            
            GPIO.output(pin, state)
            return True
            
        except Exception as e:
            print(f"⚠️ Errore output GPIO {pin}: {e}")
            return False
    
    def safe_input(self, pin):
        """Input sicuro da pin GPIO"""
        try:
            try:
                GPIO.setmode(GPIO.BCM)
            except:
                pass
            
            return GPIO.input(pin)
            
        except Exception as e:
            print(f"⚠️ Errore input GPIO {pin}: {e}")
            return None
    
    def safe_cleanup(self):
        """Cleanup sicuro GPIO"""
        try:
            GPIO.cleanup()
            self._initialized = False
            return True
        except Exception as e:
            print(f"⚠️ Warning GPIO cleanup: {e}")
            return False
    
    def emergency_stop_pin(self, pin):
        """Spegnimento di emergenza di un pin specifico"""
        try:
            try:
                GPIO.setmode(GPIO.BCM)
            except:
                pass
            
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # Sempre LOW per sicurezza
            return True
            
        except Exception as e:
            print(f"⚠️ Emergency stop GPIO {pin}: {e}")
            return False

# Istanza globale
gpio_manager = GPIOManager()

def safe_gpio_setup(pin, mode, initial_state=None):
    """Funzione helper per setup GPIO sicuro"""
    return gpio_manager.safe_setup_pin(pin, mode, initial_state)

def safe_gpio_output(pin, state):
    """Funzione helper per output GPIO sicuro"""
    return gpio_manager.safe_output(pin, state)

def safe_gpio_input(pin):
    """Funzione helper per input GPIO sicuro"""
    return gpio_manager.safe_input(pin)

def emergency_gpio_stop(pin):
    """Funzione helper per stop emergenza GPIO"""
    return gpio_manager.emergency_stop_pin(pin)

def safe_gpio_cleanup():
    """Funzione helper per cleanup GPIO sicuro"""
    return gpio_manager.safe_cleanup()
