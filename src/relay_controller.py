#!/usr/bin/env python3
"""
Modulo per il controllo del relè - VERSIONE CORRETTA E ROBUSTA
Risolve tutti i problemi di riattivazione e instabilità
"""

import RPi.GPIO as GPIO
import time
import threading
from config import Config

class RelayController:
    """Classe per gestire un singolo relè in modo sicuro e stabile"""
    
    def __init__(self, relay_id="default", gpio_pin=None, active_time=None, active_low=None, initial_state=None):
        """
        Inizializza il controller del relè
        
        Args:
            relay_id (str): Identificativo del relè
            gpio_pin (int): Pin GPIO da utilizzare
            active_time (float): Durata predefinita di attivazione in secondi
            active_low (bool): True se il relè è attivo con segnale LOW
            initial_state (str): Stato iniziale 'HIGH' o 'LOW'
        """
        self.relay_id = relay_id
        self.gpio_pin = gpio_pin or Config.RELAY_IN_PIN
        self.active_time = active_time or Config.RELAY_IN_ACTIVE_TIME
        self.active_low = active_low if active_low is not None else Config.RELAY_IN_ACTIVE_LOW
        self.initial_state = initial_state or Config.RELAY_IN_INITIAL_STATE
        
        # Stato del relè
        self.is_initialized = False
        self.is_active = False
        
        # Threading e controllo
        self._lock = threading.Lock()
        self._stop_requested = False
        self._activation_thread = None
        
        # Statistiche per debug
        self._activation_count = 0
        self._error_count = 0
        self._last_operation_time = None
    
    def initialize(self):
        """Inizializza il GPIO per il relè in modo sicuro"""
        try:
            with self._lock:
                if self.is_initialized:
                    print(f"⚠️ Relè {self.relay_id} già inizializzato")
                    return True
                
                # Configura GPIO mode solo se necessario
                try:
                    GPIO.setmode(GPIO.BCM)
                except RuntimeError as e:
                    if "already been set" in str(e):
                        # GPIO già configurato, continua
                        pass
                    else:
                        raise e
                
                # Setup pin come output
                GPIO.setup(self.gpio_pin, GPIO.OUT)
                
                # Imposta stato iniziale sicuro
                if self.initial_state == 'HIGH':
                    initial_gpio_state = GPIO.HIGH
                else:
                    initial_gpio_state = GPIO.LOW
                
                GPIO.output(self.gpio_pin, initial_gpio_state)
                time.sleep(0.05)  # Stabilizzazione hardware
                
                self.is_initialized = True
                self._stop_requested = False
                self._last_operation_time = time.time()
                
                # Verifica configurazione
                current_state = self._read_gpio_state()
                expected_state = "HIGH" if initial_gpio_state else "LOW"
                
                print(f"🔌 Relè {self.relay_id} inizializzato su GPIO {self.gpio_pin}")
                print(f"⚙️  Logica: {'Attivo LOW' if self.active_low else 'Attivo HIGH'}")
                print(f"🔄 Stato iniziale: {self.initial_state} (GPIO: {current_state})")
                
                if current_state != expected_state:
                    print(f"⚠️ Warning: Stato GPIO non corrispondente (atteso {expected_state})")
                
                return True
                
        except Exception as e:
            print(f"❌ Errore inizializzazione relè {self.relay_id}: {e}")
            self._error_count += 1
            return False
    
    def _read_gpio_state(self):
        """Legge lo stato GPIO senza reinizializzare (CORREZIONE CRITICA)"""
        try:
            if not self.is_initialized:
                return "UNINITIALIZED"
            
            # IMPORTANTE: NON reinizializzare GPIO qui!
            state = GPIO.input(self.gpio_pin)
            return "HIGH" if state else "LOW"
            
        except Exception as e:
            print(f"❌ Errore lettura GPIO {self.gpio_pin}: {e}")
            self._error_count += 1
            return "ERROR"
    
    def _set_gpio_state(self, gpio_high):
        """Imposta stato GPIO con stabilizzazione hardware"""
        try:
            if not self.is_initialized:
                return False
            
            state_value = GPIO.HIGH if gpio_high else GPIO.LOW
            state_name = "HIGH" if gpio_high else "LOW"
            
            print(f"🔧 Impostando GPIO {self.gpio_pin} = {state_name}")
            
            # Imposta stato
            GPIO.output(self.gpio_pin, state_value)
            
            # Pausa critica per stabilizzazione hardware
            time.sleep(0.02)
            
            # Verifica che sia stato impostato correttamente
            actual_state = self._read_gpio_state()
            if actual_state != state_name:
                print(f"⚠️ Warning: GPIO non nel stato atteso (impostato: {state_name}, letto: {actual_state})")
                # Riprova una volta
                GPIO.output(self.gpio_pin, state_value)
                time.sleep(0.02)
                actual_state = self._read_gpio_state()
                print(f"🔄 Secondo tentativo: {actual_state}")
            
            return actual_state == state_name
            
        except Exception as e:
            print(f"❌ Errore impostazione GPIO: {e}")
            self._error_count += 1
            return False
    
    def _set_relay_state(self, active):
        """
        Imposta lo stato logico del relè (attivo/inattivo)
        
        Args:
            active (bool): True per attivare, False per disattivare
        """
        if active:
            # Relè attivo
            gpio_high = not self.active_low  # LOW se active_low, HIGH altrimenti
            action = "ATTIVAZIONE"
        else:
            # Relè inattivo
            gpio_high = self.active_low  # HIGH se active_low, LOW altrimenti
            action = "DISATTIVAZIONE"
        
        print(f"⚡ {action} relè {self.relay_id}")
        success = self._set_gpio_state(gpio_high)
        
        if success:
            print(f"✅ {action} relè {self.relay_id} completata")
        else:
            print(f"❌ {action} relè {self.relay_id} fallita!")
        
        return success
    
    def test_relay(self, duration=1):
        """
        Testa il relè con un ciclo completo on/off
        
        Args:
            duration (float): Durata del test in secondi
            
        Returns:
            bool: True se test completato con successo
        """
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        print(f"\n🧪 Test relè {self.relay_id} per {duration}s...")
        
        try:
            # Stato iniziale
            initial_state = self._read_gpio_state()
            print(f"📊 Stato iniziale: {initial_state}")
            
            # Attiva
            if not self._set_relay_state(True):
                return False
            
            active_state = self._read_gpio_state()
            print(f"📊 Stato attivo: {active_state}")
            
            # Aspetta
            time.sleep(duration)
            
            # Disattiva
            if not self._set_relay_state(False):
                return False
            
            final_state = self._read_gpio_state()
            print(f"📊 Stato finale: {final_state}")
            
            # Verifica che sia tornato allo stato iniziale
            time.sleep(0.2)
            final_check = self._read_gpio_state()
            
            if final_check == initial_state:
                print(f"✅ Test relè {self.relay_id} completato con successo!")
                return True
            else:
                print(f"⚠️ Warning: Stato finale diverso da quello iniziale")
                print(f"   Iniziale: {initial_state}, Finale: {final_check}")
                return False
            
        except Exception as e:
            print(f"❌ Errore durante test: {e}")
            self._error_count += 1
            # Tenta di spegnere in caso di errore
            try:
                self._set_relay_state(False)
            except:
                pass
            return False
    
    def activate(self, duration=None):
        """
        Attiva il relè per la durata specificata
        
        Args:
            duration (float): Durata in secondi (usa self.active_time se None)
            
        Returns:
            bool: True se attivazione avviata con successo
        """
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        duration = duration or self.active_time
        
        with self._lock:
            if self.is_active:
                print(f"⚠️ Relè {self.relay_id} già attivo, comando ignorato")
                return False
            
            # Reset flags e imposta come attivo
            self._stop_requested = False
            self.is_active = True
            self._activation_count += 1
        
        print(f"\n🔛 Attivazione relè {self.relay_id} per {duration}s...")
        print(f"📊 Stato prima attivazione: {self._read_gpio_state()}")
        
        try:
            # Esegui attivazione sincrona
            success = self._execute_activation(duration)
            return success
            
        except Exception as e:
            print(f"❌ Errore attivazione relè {self.relay_id}: {e}")
            self._error_count += 1
            with self._lock:
                self.is_active = False
                self._stop_requested = True
            return False
    
    def _execute_activation(self, duration):
        """Esegue l'attivazione del relè in modo sicuro"""
        try:
            # Attiva il relè
            if not self._set_relay_state(True):
                return False
            
            print(f"⚡ Relè {self.relay_id} ATTIVATO!")
            print(f"📊 Stato GPIO dopo attivazione: {self._read_gpio_state()}")
            
            # Ciclo di attesa con controlli periodici
            start_time = time.time()
            check_interval = 0.1
            elapsed = 0
            
            print(f"⏱️  Attesa {duration}s per spegnimento automatico...")
            
            while elapsed < duration:
                time.sleep(check_interval)
                elapsed = time.time() - start_time
                
                # Controlla se dobbiamo fermarci
                with self._lock:
                    if not self.is_active or self._stop_requested:
                        print(f"🛑 Relè {self.relay_id} fermato anticipatamente dopo {elapsed:.1f}s")
                        break
                
                # Controllo sicurezza ogni secondo
                if int(elapsed) != int(elapsed - check_interval):
                    current_state = self._read_gpio_state()
                    expected_on = "HIGH" if not self.active_low else "LOW"
                    if current_state != expected_on:
                        print(f"⚠️ ATTENZIONE: Relè cambiato stato inaspettatamente!")
                        print(f"   Stato attuale: {current_state}, Atteso: {expected_on}")
            
            # Disattivazione sicura
            return self._safe_deactivation(elapsed)
            
        except Exception as e:
            print(f"❌ Errore durante attivazione: {e}")
            self._error_count += 1
            return False
        finally:
            # Assicurati che sia marcato come inattivo
            with self._lock:
                self.is_active = False
                self._stop_requested = False
            self._last_operation_time = time.time()
    
    def _safe_deactivation(self, elapsed_time):
        """Disattivazione sicura con verifica multipla"""
        print(f"🔄 Disattivazione relè {self.relay_id} dopo {elapsed_time:.1f}s...")
        
        # Tentativo di disattivazione con verifica
        expected_off_state = "HIGH" if self.active_low else "LOW"
        
        for attempt in range(3):
            # Disattiva
            if not self._set_relay_state(False):
                print(f"❌ Tentativo {attempt + 1} di disattivazione fallito")
                continue
            
            # Aspetta stabilizzazione progressivamente più lunga
            stabilization_time = 0.1 + (attempt * 0.1)
            time.sleep(stabilization_time)
            
            # Verifica stato
            current_state = self._read_gpio_state()
            print(f"📊 Tentativo {attempt + 1}: GPIO = {current_state} (atteso OFF: {expected_off_state})")
            
            if current_state == expected_off_state:
                print(f"✅ Relè {self.relay_id} disattivato correttamente!")
                
                # Doppia verifica dopo 0.5 secondi
                time.sleep(0.5)
                final_check = self._read_gpio_state()
                if final_check == expected_off_state:
                    print(f"✅ Verifica finale OK: {final_check}")
                    return True
                else:
                    print(f"⚠️ Relè si è riattivato! Stato finale: {final_check}")
                    # Continua con i tentativi
            
            if attempt < 2:
                print(f"🔄 Riprovo spegnimento (tentativo {attempt + 2}/3)...")
        
        # Se arriviamo qui, c'è un problema serio
        print(f"❌ ERRORE CRITICO: Impossibile spegnere relè {self.relay_id}!")
        return False
    
    def force_off(self):
        """Spegnimento forzato immediato"""
        print(f"🔴 Spegnimento FORZATO relè {self.relay_id}...")
        
        with self._lock:
            self._stop_requested = True
            self.is_active = False
        
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        # Spegnimento multiplo con verifica
        return self._force_off_with_retries()
    
    def _force_off_with_retries(self):
        """Spegnimento forzato con tentativi multipli"""
        expected_off_state = "HIGH" if self.active_low else "LOW"
        
        for attempt in range(5):  # Più tentativi per force_off
            print(f"🔨 Tentativo forzato {attempt + 1}/5...")
            
            try:
                # Forza stato GPIO direttamente
                off_gpio_value = GPIO.HIGH if self.active_low else GPIO.LOW
                GPIO.output(self.gpio_pin, off_gpio_value)
                
                # Aspetta stabilizzazione crescente
                time.sleep(0.1 + (attempt * 0.05))
                
                # Verifica
                current_state = self._read_gpio_state()
                print(f"   Risultato: {current_state} (atteso: {expected_off_state})")
                
                if current_state == expected_off_state:
                    print(f"✅ Spegnimento forzato riuscito al tentativo {attempt + 1}")
                    return True
                    
            except Exception as e:
                print(f"❌ Errore tentativo {attempt + 1}: {e}")
        
        print(f"❌ SPEGNIMENTO FORZATO FALLITO per relè {self.relay_id}!")
        return False
    
    def emergency_stop(self):
        """Arresto di emergenza - ferma tutto immediatamente"""
        print(f"🚨 ARRESTO DI EMERGENZA relè {self.relay_id}!")
        
        with self._lock:
            self._stop_requested = True
            self.is_active = False
        
        if self.is_initialized:
            try:
                # Forza stato di sicurezza
                emergency_gpio = GPIO.HIGH if self.active_low else GPIO.LOW
                GPIO.output(self.gpio_pin, emergency_gpio)
                
                time.sleep(0.2)
                final_state = self._read_gpio_state()
                print(f"🚨 Stato dopo arresto emergenza: {final_state}")
                
                return True
            except Exception as e:
                print(f"❌ Errore arresto emergenza: {e}")
                return False
        
        return False
    
    def reset_to_initial_state(self):
        """Ripristina il relè allo stato iniziale configurato"""
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        print(f"🔄 Ripristino relè {self.relay_id} allo stato iniziale...")
        
        with self._lock:
            self._stop_requested = True
            self.is_active = False
        
        try:
            if self.initial_state == 'HIGH':
                success = self._set_gpio_state(True)
            else:
                success = self._set_gpio_state(False)
            
            if success:
                print(f"✅ Relè {self.relay_id} ripristinato allo stato iniziale: {self.initial_state}")
            else:
                print(f"❌ Errore ripristino stato iniziale")
            
            return success
            
        except Exception as e:
            print(f"❌ Errore ripristino: {e}")
            return False
    
    def get_status(self):
        """Restituisce stato completo del relè"""
        gpio_state = self._read_gpio_state()
        expected_off = "HIGH" if self.active_low else "LOW"
        expected_on = "LOW" if self.active_low else "HIGH"
        
        return {
            'relay_id': self.relay_id,
            'initialized': self.is_initialized,
            'active': self.is_active,
            'pin': self.gpio_pin,
            'active_low': self.active_low,
            'initial_state': self.initial_state,
            'duration': self.active_time,
            'gpio_state': gpio_state,
            'expected_off_state': expected_off,
            'expected_on_state': expected_on,
            'is_relay_off': gpio_state == expected_off,
            'is_relay_on': gpio_state == expected_on,
            'activation_count': self._activation_count,
            'error_count': self._error_count,
            'last_operation': self._last_operation_time
        }
    
    def print_status(self):
        """Stampa stato dettagliato del relè"""
        status = self.get_status()
        print(f"\n📊 STATO RELÈ {status['relay_id']}:")
        print(f"   🔌 Inizializzato: {status['initialized']}")
        print(f"   ⚡ Attivo: {status['active']}")
        print(f"   📍 GPIO Pin: {status['pin']}")
        print(f"   🔄 Logica Active Low: {status['active_low']}")
        print(f"   🎯 Stato GPIO: {status['gpio_state']}")
        print(f"   ✅ Relè OFF: {status['is_relay_off']} (atteso: {status['expected_off_state']})")
        print(f"   🔛 Relè ON: {status['is_relay_on']} (atteso: {status['expected_on_state']})")
        print(f"   📈 Attivazioni: {status['activation_count']}")
        print(f"   ❌ Errori: {status['error_count']}")
        if status['last_operation']:
            last_op = time.time() - status['last_operation']
            print(f"   ⏰ Ultima operazione: {last_op:.1f}s fa")
    
    def monitor_stability(self, duration=10, interval=0.5):
        """
        Monitora la stabilità del relè per un periodo
        
        Args:
            duration (float): Durata monitoraggio in secondi
            interval (float): Intervallo tra le letture in secondi
        """
        print(f"🔍 Monitoraggio stabilità relè {self.relay_id} per {duration}s...")
        
        start_time = time.time()
        last_state = self._read_gpio_state()
        state_changes = 0
        readings = 0
        
        print(f"📊 Stato iniziale: {last_state}")
        
        while time.time() - start_time < duration:
            time.sleep(interval)
            current_state = self._read_gpio_state()
            readings += 1
            
            if current_state != last_state:
                state_changes += 1
                elapsed = time.time() - start_time
                print(f"⚠️ CAMBIO STATO a {elapsed:.1f}s: {last_state} → {current_state}")
                last_state = current_state
        
        print(f"📈 Monitoraggio completato:")
        print(f"   📊 Letture totali: {readings}")
        print(f"   🔄 Cambi di stato: {state_changes}")
        print(f"   📊 Stato finale: {last_state}")
        
        if state_changes == 0:
            print(f"✅ Relè STABILE durante il monitoraggio")
        else:
            print(f"⚠️ Relè INSTABILE - {state_changes} cambi di stato!")
        
        return state_changes == 0
    
    def cleanup(self):
        """Pulizia sicura delle risorse"""
        try:
            if self.is_initialized:
                print(f"🧹 Cleanup relè {self.relay_id}...")
                
                # Ferma tutte le operazioni
                with self._lock:
                    self._stop_requested = True
                    self.is_active = False
                
                # Attendi eventuale thread
                if self._activation_thread and self._activation_thread.is_alive():
                    self._activation_thread.join(timeout=1.0)
                
                # Spegnimento sicuro
                time.sleep(0.2)
                self._force_off_with_retries()
                
                print(f"🧹 Cleanup relè {self.relay_id} completato")
                
        except Exception as e:
            print(f"⚠️ Warning cleanup relè {self.relay_id}: {e}")
    
    def __del__(self):
        """Distruttore - pulizia automatica"""
        try:
            self.cleanup()
        except:
            pass  # Ignora errori nel distruttore