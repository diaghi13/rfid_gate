#!/usr/bin/env python3
"""
Controller relè - Versione finale con cleanup corretto
"""
import RPi.GPIO as GPIO
import time
import threading
import atexit
import signal
import sys
from config import Config

class RelayController:
    """Gestione singolo relè con cleanup garantito"""
    
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
        
        # Registra cleanup automatico
        atexit.register(self._emergency_cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestisce segnali di terminazione"""
        print(f"\n🛑 Segnale {signum} ricevuto - Cleanup relè {self.relay_id}")
        self.force_off_immediate()
        sys.exit(0)
    
    def _emergency_cleanup(self):
        """Cleanup di emergenza chiamato automaticamente"""
        try:
            if self.is_initialized:
                # Cleanup semplice senza messaggi per evitare errori atexit
                try:
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(self.gpio_pin, GPIO.OUT)
                    GPIO.output(self.gpio_pin, GPIO.LOW)  # Sempre LOW per sicurezza
                except:
                    pass  # Ignora errori durante atexit
        except:
            pass
    
    def initialize(self):
        """Inizializza GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            
            # Stato iniziale SEMPRE spento per sicurezza
            safe_level = GPIO.HIGH if self.active_low else GPIO.LOW
            GPIO.output(self.gpio_pin, safe_level)
            
            self.is_initialized = True
            print(f"Relè {self.relay_id}: GPIO {self.gpio_pin} inizializzato (SPENTO)")
            
            # Test rapido per verificare funzionamento
            self._test_quick()
            
            return True
            
        except Exception as e:
            print(f"Errore init relè {self.relay_id}: {e}")
            return False
    
    def _test_quick(self):
        """Test rapido 0.1s per verificare funzionamento"""
        try:
            print(f"Test relè {self.relay_id}...")
            self._set_relay_state(True)
            time.sleep(0.1)
            self._set_relay_state(False)
            print(f"✅ Test relè {self.relay_id} OK")
        except Exception as e:
            print(f"⚠️ Test relè {self.relay_id}: {e}")
    
    def activate(self, duration=None):
        """Attiva relè per durata specificata"""
        if not self.is_initialized:
            return False
        
        duration = duration or self.active_time
        
        with self._lock:
            # Se già attivo, ferma thread precedente
            if self.is_active and self._current_thread:
                print(f"Relè {self.relay_id}: Stop thread precedente")
                self._current_thread = None
            
            self.is_active = True
            
            # Nuovo thread
            thread = threading.Thread(
                target=self._activation_worker, 
                args=(duration,),
                daemon=False  # NON daemon per garantire completamento
            )
            self._current_thread = thread
            thread.start()
            
        return True
    
    def _activation_worker(self, duration):
        """Worker thread per attivazione temporizzata"""
        current_thread = threading.current_thread()
        
        try:
            # Attiva relè
            self._set_relay_state(True)
            print(f"Relè {self.relay_id}: ON per {duration}s")
            
            # Attesa con controllo interruzione ogni 0.1s
            elapsed = 0
            while elapsed < duration:
                # Verifica se thread ancora valido
                with self._lock:
                    if self._current_thread != current_thread:
                        print(f"Relè {self.relay_id}: Thread interrotto")
                        return
                
                sleep_time = min(0.1, duration - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time
            
            # Disattiva relè
            with self._lock:
                if self._current_thread == current_thread:
                    self._set_relay_state(False)
                    self.is_active = False
                    self._current_thread = None
                    print(f"Relè {self.relay_id}: OFF (automatico)")
                
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
            
            # Verifica che il comando sia stato eseguito
            actual_state = GPIO.input(self.gpio_pin)
            expected_state = level
            
            if actual_state != expected_state:
                print(f"⚠️ Relè {self.relay_id}: Stato GPIO inaspettato!")
            
        except Exception as e:
            print(f"Errore GPIO {self.gpio_pin}: {e}")
    
    def force_off_immediate(self):
        """Spegnimento immediato garantito"""
        try:
            with self._lock:
                self.is_active = False
                self._current_thread = None
            
            # Spegni relè
            if self.is_initialized:
                try:
                    # Assicurati che GPIO sia configurato
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(self.gpio_pin, GPIO.OUT)
                    
                    safe_level = GPIO.HIGH if self.active_low else GPIO.LOW
                    GPIO.output(self.gpio_pin, safe_level)
                    
                    # Verifica spegnimento
                    time.sleep(0.01)
                    actual_state = GPIO.input(self.gpio_pin)
                    
                    if actual_state == safe_level:
                        print(f"✅ Relè {self.relay_id}: Spento con successo")
                    else:
                        print(f"⚠️ Relè {self.relay_id}: Secondo tentativo...")
                        GPIO.output(self.gpio_pin, safe_level)
                        time.sleep(0.01)
                        print(f"🔄 Relè {self.relay_id}: Spegnimento forzato")
                        
                except Exception as gpio_error:
                    # Se GPIO fallisce, prova spegnimento di base
                    try:
                        GPIO.setmode(GPIO.BCM)
                        GPIO.setup(self.gpio_pin, GPIO.OUT)
                        GPIO.output(self.gpio_pin, GPIO.LOW)  # Forza LOW come sicurezza
                        print(f"🔴 Relè {self.relay_id}: Spegnimento di emergenza")
                    except:
                        print(f"⚠️ Relè {self.relay_id}: Impossibile controllare GPIO")
            
        except Exception as e:
            print(f"Warning spegnimento relè {self.relay_id}: {e}")
    
    def force_off(self):
        """Alias per compatibilità"""
        self.force_off_immediate()
    
    def reset_to_initial_state(self):
        """Ripristina stato sicuro (sempre spento)"""
        self.force_off_immediate()
    
    def get_status(self):
        """Status relè"""
        gpio_state = "UNKNOWN"
        try:
            if self.is_initialized:
                actual_level = GPIO.input(self.gpio_pin)
                gpio_state = "HIGH" if actual_level else "LOW"
        except:
            pass
            
        return {
            'relay_id': self.relay_id,
            'initialized': self.is_initialized,
            'active': self.is_active,
            'pin': self.gpio_pin,
            'active_low': self.active_low,
            'duration': self.active_time,
            'gpio_state': gpio_state
        }
    
    def cleanup(self):
        """Cleanup completo"""
        try:
            print(f"🧹 Cleanup relè {self.relay_id}...")
            
            # Stop thread
            with self._lock:
                self.is_active = False
                self._current_thread = None
            
            # Spegni relè garantito
            self.force_off_immediate()
            
            print(f"✅ Cleanup relè {self.relay_id} completato")
            
        except Exception as e:
            print(f"⚠️ Warning cleanup relè {self.relay_id}: {e}")
    
    def __del__(self):
        """Destructor con cleanup silenzioso"""
        try:
            # Cleanup silenzioso per evitare errori durante garbage collection
            if self.is_initialized:
                try:
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(self.gpio_pin, GPIO.OUT)
                    GPIO.output(self.gpio_pin, GPIO.LOW)
                except:
                    pass
        except:
            pass

# Cleanup globale per emergenza
def emergency_cleanup_all():
    """Cleanup di emergenza per tutti i GPIO"""
    try:
        # Spegni i pin più comuni
        common_relay_pins = [18, 19, 20, 21, 16, 26]
        
        GPIO.setmode(GPIO.BCM)
        for pin in common_relay_pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)  # Forza LOW (sicuro per la maggior parte dei relè)
            except:
                pass
        
        GPIO.cleanup()
        print("🛑 Emergency cleanup GPIO completato")
        
    except Exception as e:
        print(f"⚠️ Emergency cleanup error: {e}")

# Registra cleanup globale
atexit.register(emergency_cleanup_all)