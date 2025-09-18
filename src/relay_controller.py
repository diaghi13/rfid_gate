#!/usr/bin/env python3
"""
Modulo per il controllo del relè
"""

import RPi.GPIO as GPIO
import time
import threading
from config import Config

class RelayController:
    """Classe per gestire un singolo relè"""
    
    def __init__(self, relay_id="default", gpio_pin=None, active_time=None, active_low=None, initial_state=None):
        self.relay_id = relay_id
        self.gpio_pin = gpio_pin or Config.RELAY_IN_PIN
        self.active_time = active_time or Config.RELAY_IN_ACTIVE_TIME
        self.active_low = active_low if active_low is not None else Config.RELAY_IN_ACTIVE_LOW
        self.initial_state = initial_state or Config.RELAY_IN_INITIAL_STATE
        self.is_initialized = False
        self.is_active = False
        self._lock = threading.Lock()
    
    def initialize(self):
        """Inizializza il GPIO per il relè"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Imposta lo stato iniziale configurabile
            if self.initial_state == 'HIGH':
                initial_state = GPIO.HIGH
            else:  # Default LOW
                initial_state = GPIO.LOW
            
            GPIO.output(self.gpio_pin, initial_state)
            
            self.is_initialized = True
            print(f"🔌 Relè {self.relay_id} configurato su GPIO {self.gpio_pin}")
            print(f"⚙️  Logica: {'Attivo LOW' if self.active_low else 'Attivo HIGH'}")
            print(f"🔄 Stato iniziale: {self.initial_state} ({'HIGH' if initial_state else 'LOW'})")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione relè {self.relay_id}: {e}")
            return False
    
    def test_relay(self, duration=1):
        """
        Testa il relè attivandolo per un breve periodo
        Args: duration (int) - Durata del test in secondi
        """
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        print(f"\n🧪 Test relè {self.relay_id} per {duration} secondo(i)...")
        
        try:
            self._set_relay_state(True)
            print(f"🔛 Relè {self.relay_id} attivato (test)")
            time.sleep(duration)
            self._set_relay_state(False)
            print(f"🔴 Relè {self.relay_id} disattivato (test)")
            print(f"✅ Test relè {self.relay_id} completato!")
            return True
            
        except Exception as e:
            print(f"❌ Errore test relè {self.relay_id}: {e}")
            return False
    
    def activate(self, duration=None):
        """
        Attiva il relè per la durata specificata
        Args: duration (int) - Durata in secondi (usa self.active_time se None)
        """
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        duration = duration or self.active_time
        
        with self._lock:
            if self.is_active:
                print(f"⚠️ Relè {self.relay_id} già attivo, ignoro il comando")
                return False
            
            # Marca come attivo PRIMA di avviare il thread
            self.is_active = True
        
        try:
            print(f"\n🔛 Attivazione relè {self.relay_id} per {duration} secondi...")
            
            # NON usare thread separato per evitare problemi di concorrenza
            # Esegui direttamente in modo sincrono
            self._execute_relay_activation(duration)
            
            return True
            
        except Exception as e:
            print(f"❌ Errore attivazione relè {self.relay_id}: {e}")
            with self._lock:
                self.is_active = False
            return False
    
    def _execute_relay_activation(self, duration):
        """Esegue l'attivazione del relè in modo sincrono"""
        try:
            # Attiva il relè
            self._set_relay_state(True)
            print(f"⚡ Relè {self.relay_id} ATTIVATO!")
            
            # Aspetta la durata specificata
            start_time = time.time()
            print(f"⏱️ Aspetto {duration}s per spegnimento automatico...")
            
            # Sleep con controllo periodico
            sleep_interval = 0.1
            elapsed = 0
            
            while elapsed < duration:
                time.sleep(sleep_interval)
                elapsed = time.time() - start_time
                
                # Controlla se dobbiamo fermarci anticipatamente
                with self._lock:
                    if not self.is_active:
                        print(f"🛑 Relè {self.relay_id} fermato anticipatamente")
                        break
            
            # Disattiva il relè
            self._set_relay_state(False)
            print(f"🔴 Relè {self.relay_id} disattivato dopo {elapsed:.1f}s")
            
            # Verifica che sia effettivamente spento
            time.sleep(0.1)
            gpio_state = self.get_gpio_state()
            expected_off_state = "LOW" if not self.active_low else "HIGH"
            
            if gpio_state != expected_off_state:
                print(f"⚠️ GPIO {self.gpio_pin} non nello stato atteso! Attuale: {gpio_state}, Atteso: {expected_off_state}")
                # Riprova una volta
                self._set_relay_state(False)
                time.sleep(0.1)
                gpio_state = self.get_gpio_state()
                print(f"🔄 Dopo secondo tentativo: {gpio_state}")
            
        except Exception as e:
            print(f"❌ Errore durante attivazione relè {self.relay_id}: {e}")
        finally:
            with self._lock:
                self.is_active = False
            print(f"✅ Attivazione relè {self.relay_id} terminata")
    
    def _set_relay_state(self, active):
        """
        Imposta lo stato del relè
        Args: active (bool) - True per attivare, False per disattivare
        """
        if active:
            state = GPIO.LOW if self.active_low else GPIO.HIGH
            action = "ATTIVAZIONE"
        else:
            state = GPIO.HIGH if self.active_low else GPIO.LOW
            action = "DISATTIVAZIONE"
        
        print(f"🔧 {action} relè {self.relay_id}: GPIO {self.gpio_pin} = {'HIGH' if state else 'LOW'}")
        GPIO.output(self.gpio_pin, state)
    
    def force_off(self):
        """Forza lo spegnimento del relè"""
        if self.is_initialized:
            self._set_relay_state(False)
            with self._lock:
                self.is_active = False
            print(f"🔴 Relè {self.relay_id} forzato OFF")
    
    def reset_to_initial_state(self):
        """Ripristina il relè allo stato iniziale configurato"""
        if self.is_initialized:
            if self.initial_state == 'HIGH':
                GPIO.output(self.gpio_pin, GPIO.HIGH)
            else:
                GPIO.output(self.gpio_pin, GPIO.LOW)
            
            with self._lock:
                self.is_active = False
            print(f"🔄 Relè {self.relay_id} ripristinato allo stato iniziale: {self.initial_state}")
    
    def get_gpio_state(self):
        """Legge lo stato effettivo del GPIO"""
        try:
            # Legge lo stato del pin GPIO
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            state = GPIO.input(self.gpio_pin)
            return "HIGH" if state else "LOW"
        except Exception as e:
            print(f"❌ Errore lettura GPIO {self.gpio_pin}: {e}")
            return "UNKNOWN"
    
    def force_off_with_verification(self):
        """Forza lo spegnimento del relè con verifica"""
        print(f"🔴 Forzando spegnimento relè {self.relay_id}...")
        
        if self.is_initialized:
            try:
                # Forza stato OFF
                self._set_relay_state(False)
                
                # Aspetta stabilizzazione
                time.sleep(0.1)
                
                # Verifica stato GPIO
                gpio_state = self.get_gpio_state()
                expected_off_state = "LOW" if not self.active_low else "HIGH"
                
                print(f"📊 Stato GPIO {self.gpio_pin}: {gpio_state} (Atteso OFF: {expected_off_state})")
                
                with self._lock:
                    self.is_active = False
                
                if gpio_state == expected_off_state:
                    print(f"✅ Relè {self.relay_id} spento correttamente")
                    return True
                else:
                    print(f"⚠️ Relè {self.relay_id} potrebbe essere ancora attivo!")
                    return False
                    
            except Exception as e:
                print(f"❌ Errore spegnimento forzato relè {self.relay_id}: {e}")
                return False
        
        return False
        """Restituisce lo stato attuale del relè"""
    def get_status(self):
        """Restituisce lo stato del relè"""
        gpio_state = self.get_gpio_state()
        return {
            'relay_id': self.relay_id,
            'initialized': self.is_initialized,
            'active': self.is_active,
            'pin': self.gpio_pin,
            'active_low': self.active_low,
            'initial_state': self.initial_state,
            'duration': self.active_time,
            'gpio_state': gpio_state
        }
    
    def cleanup(self):
        """Pulizia delle risorse GPIO"""
        try:
            if self.is_initialized:
                print(f"🧹 Cleanup relè {self.relay_id}...")
                
                # Ferma qualsiasi attivazione in corso
                with self._lock:
                    self.is_active = False
                
                # Aspetta un momento per stabilizzazione
                time.sleep(0.2)
                
                # Ripristina lo stato iniziale
                self.reset_to_initial_state()
                
                # NON fare GPIO.cleanup() qui per evitare interferenze
                print(f"🧹 Relè {self.relay_id} cleanup completato")
        except Exception as e:
            print(f"⚠️ Warning cleanup relè {self.relay_id}: {e}")
    
    def __del__(self):
        """Destructor - pulisce automaticamente le risorse"""
        self.cleanup()