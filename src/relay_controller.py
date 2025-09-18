#!/usr/bin/env python3
"""
Controller relè - Versione corretta senza thread duplicati
"""
import RPi.GPIO as GPIO
import time
import threading
from config import Config

class RelayController:
    """Gestione singolo relè"""
    
    def __init__(self, relay_id="default", gpio_pin=None, active_time=None, active_low=None, initial_state=None):
        self.relay_id = relay_id
        self.gpio_pin = gpio_pin or Config.RELAY_IN_PIN
        self.active_time = active_time or Config.RELAY_IN_ACTIVE_TIME
        self.active_low = active_low if active_low is not None else Config.RELAY_IN_ACTIVE_LOW
        self.initial_state = initial_state or Config.RELAY_IN_INITIAL_STATE
        self.is_initialized = False
        self.is_active = False
        self._lock = threading.Lock()
        self._current_thread = None  # Track del thread corrente
    
    def initialize(self):
        """Inizializza GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Stato iniziale
            initial_level = GPIO.HIGH if self.initial_state == 'HIGH' else GPIO.LOW
            GPIO.output(self.gpio_pin, initial_level)
            
            self.is_initialized = True
            print(f"Relè {self.relay_id}: GPIO {self.gpio_pin} inizializzato")
            return True
            
        except Exception as e:
            print(f"Errore init relè {self.relay_id}: {e}")
            return False
    
    def activate(self, duration=None):
        """Attiva relè per durata specificata"""
        if not self.is_initialized:
            return False
        
        duration = duration or self.active_time
        
        with self._lock:
            # Se già attivo, interrompi il thread precedente
            if self.is_active and self._current_thread:
                print(f"Relè {self.relay_id}: Interruzione attivazione precedente")
                self._current_thread = None  # Il thread precedente si fermerà
            
            self.is_active = True
            
            # Nuovo thread
            thread = threading.Thread(target=self._activation_worker, args=(duration,))
            thread.daemon = True
            self._current_thread = thread
            thread.start()
            
        return True
    
    def _activation_worker(self, duration):
        """Worker thread per attivazione temporizzata"""
        current_thread = threading.current_thread()
        
        try:
            # Attiva
            self._set_relay_state(True)
            print(f"Relè {self.relay_id}: ON per {duration}s")
            
            # Wait con controllo interruzione
            start_time = time.time()
            while (time.time() - start_time) < duration:
                # Controlla se questo thread è ancora quello corrente
                with self._lock:
                    if self._current_thread != current_thread:
                        print(f"Relè {self.relay_id}: Thread interrotto")
                        return
                
                time.sleep(0.1)
            
            # Disattiva solo se questo è ancora il thread corrente
            with self._lock:
                if self._current_thread == current_thread:
                    self._set_relay_state(False)
                    self.is_active = False
                    self._current_thread = None
                    print(f"Relè {self.relay_id}: OFF")
                
        except Exception as e:
            print(f"Errore thread relè {self.relay_id}: {e}")
            with self._lock:
                self.is_active = False
                self._current_thread = None
            self._set_relay_state(False)
    
    def _set_relay_state(self, active):
        """Imposta stato GPIO"""
        try:
            if active:
                level = GPIO.LOW if self.active_low else GPIO.HIGH
            else:
                level = GPIO.HIGH if self.active_low else GPIO.LOW
            
            GPIO.output(self.gpio_pin, level)
        except Exception as e:
            print(f"Errore GPIO {self.gpio_pin}: {e}")
    
    def force_off(self):
        """Spegne immediatamente il relè"""
        with self._lock:
            self.is_active = False
            self._current_thread = None
        
        self._set_relay_state(False)
        print(f"Relè {self.relay_id}: Spento forzatamente")
    
    def reset_to_initial_state(self):
        """Ripristina stato iniziale"""
        self.force_off()
        
        initial_level = GPIO.HIGH if self.initial_state == 'HIGH' else GPIO.LOW
        GPIO.output(self.gpio_pin, initial_level)
    
    def get_status(self):
        """Status relè"""
        return {
            'relay_id': self.relay_id,
            'initialized': self.is_initialized,
            'active': self.is_active,
            'pin': self.gpio_pin,
            'active_low': self.active_low,
            'duration': self.active_time
        }
    
    def cleanup(self):
        """Cleanup"""
        if self.is_initialized:
            self.reset_to_initial_state()