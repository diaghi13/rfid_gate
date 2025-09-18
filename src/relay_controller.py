#!/usr/bin/env python3
"""
Controller relè - Versione semplice che funziona
"""
import RPi.GPIO as GPIO
import time
import threading
import atexit
from config import Config

class RelayController:
    """Gestione singolo relè - versione semplice"""
    
    def __init__(self, relay_id="default", gpio_pin=None, active_time=None, active_low=None, initial_state=None):
        self.relay_id = relay_id
        self.gpio_pin = gpio_pin or Config.RELAY_IN_PIN
        self.active_time = active_time or Config.RELAY_IN_ACTIVE_TIME
        self.active_low = active_low if active_low is not None else Config.RELAY_IN_ACTIVE_LOW
        self.initial_state = initial_state or Config.RELAY_IN_INITIAL_STATE
        self.is_initialized = False
        self.is_active = False
        self._lock = threading.Lock()
        self._current_thread = None
        
        # Registra cleanup semplice
        atexit.register(self._simple_cleanup)
    
    def _simple_cleanup(self):
        """Cleanup semplice senza errori"""
        try:
            if self.is_initialized and self.gpio_pin:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_pin, GPIO.OUT)
                GPIO.output(self.gpio_pin, GPIO.LOW)  # Sempre LOW per sicurezza
        except:
            pass  # Ignora tutti gli errori durante atexit
    
    def initialize(self):
        """Inizializza GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Sempre spento inizialmente
            GPIO.output(self.gpio_pin, GPIO.LOW)
            
            self.is_initialized = True
            print(f"Relè {self.relay_id}: GPIO {self.gpio_pin} inizializzato")
            return True
            
        except Exception as e:
            print(f"Errore init relè {self.relay_id}: {e}")
            return False
    
    def activate(self, duration=None):
        """Attiva relè"""
        if not self.is_initialized:
            return False
        
        duration = duration or self.active_time
        
        with self._lock:
            # Interrompi thread precedente
            if self.is_active and self._current_thread:
                self._current_thread = None
            
            self.is_active = True
            
            # Nuovo thread
            thread = threading.Thread(
                target=self._activation_worker, 
                args=(duration,),
                daemon=False
            )
            self._current_thread = thread
            thread.start()
            
        return True
    
    def _activation_worker(self, duration):
        """Worker thread per attivazione"""
        current_thread = threading.current_thread()
        
        try:
            # Attiva
            self._set_relay_state(True)
            print(f"Relè {self.relay_id}: ON per {duration}s")
            
            # Aspetta con controllo interruzione
            elapsed = 0
            while elapsed < duration:
                with self._lock:
                    if self._current_thread != current_thread:
                        return
                
                sleep_time = min(0.1, duration - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time
            
            # Disattiva
            with self._lock:
                if self._current_thread == current_thread:
                    self._set_relay_state(False)
                    self.is_active = False
                    self._current_thread = None
                    print(f"Relè {self.relay_id}: OFF")
                
        except Exception as e:
            print(f"Errore thread relè {self.relay_id}: {e}")
            self._set_relay_state(False)
            with self._lock:
                self.is_active = False
                self._current_thread = None
    
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
        """Spegne immediatamente"""
        try:
            with self._lock:
                self.is_active = False
                self._current_thread = None
            
            if self.is_initialized:
                safe_level = GPIO.HIGH if self.active_low else GPIO.LOW
                GPIO.output(self.gpio_pin, safe_level)
                print(f"Relè {self.relay_id}: Spento forzatamente")
            
        except Exception as e:
            # Se GPIO normale fallisce, prova emergency
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_pin, GPIO.OUT)
                GPIO.output(self.gpio_pin, GPIO.LOW)
                print(f"Relè {self.relay_id}: Emergency stop")
            except:
                print(f"Warning: Impossibile spegnere relè {self.relay_id}")
    
    def reset_to_initial_state(self):
        """Ripristina stato sicuro"""
        self.force_off()
    
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
        try:
            with self._lock:
                self.is_active = False
                self._current_thread = None
            
            self.force_off()
            print(f"Cleanup relè {self.relay_id} completato")
            
        except Exception as e:
            print(f"Warning cleanup relè {self.relay_id}: {e}")