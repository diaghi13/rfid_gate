#!/usr/bin/env python3
"""
Modulo per il controllo del relè
"""

import RPi.GPIO as GPIO
import time
import threading
from config import Config

class RelayController:
    """Classe per gestire il relè"""
    
    def __init__(self):
        self.is_initialized = False
        self.is_active = False
        self._lock = threading.Lock()
    
    def initialize(self):
        """Inizializza il GPIO per il relè"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(Config.RELAY_PIN, GPIO.OUT)
            
            # Imposta lo stato iniziale (relè spento)
            initial_state = GPIO.HIGH if Config.RELAY_ACTIVE_LOW else GPIO.LOW
            GPIO.output(Config.RELAY_PIN, initial_state)
            
            self.is_initialized = True
            print(f"🔌 Relè configurato su GPIO {Config.RELAY_PIN}")
            print(f"⚙️  Logica: {'Attivo LOW' if Config.RELAY_ACTIVE_LOW else 'Attivo HIGH'}")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione relè: {e}")
            return False
    
    def test_relay(self, duration=1):
        """
        Testa il relè attivandolo per un breve periodo
        Args: duration (int) - Durata del test in secondi
        """
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        print(f"\n🧪 Test relè per {duration} secondo(i)...")
        
        try:
            self._set_relay_state(True)
            print("🔛 Relè attivato (test)")
            time.sleep(duration)
            self._set_relay_state(False)
            print("🔴 Relè disattivato (test)")
            print("✅ Test relè completato!")
            return True
            
        except Exception as e:
            print(f"❌ Errore test relè: {e}")
            return False
    
    def activate(self, duration=None):
        """
        Attiva il relè per la durata specificata
        Args: duration (int) - Durata in secondi (usa Config.RELAY_ACTIVE_TIME se None)
        """
        if not self.is_initialized:
            print("❌ Relè non inizializzato")
            return False
        
        duration = duration or Config.RELAY_ACTIVE_TIME
        
        with self._lock:
            if self.is_active:
                print("⚠️ Relè già attivo, ignoro il comando")
                return False
        
        try:
            print(f"\n🔛 Attivazione relè per {duration} secondi...")
            
            # Attiva il relè in un thread separato per non bloccare
            thread = threading.Thread(target=self._activate_thread, args=(duration,))
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Errore attivazione relè: {e}")
            return False
    
    def _activate_thread(self, duration):
        """Thread per l'attivazione temporizzata del relè"""
        with self._lock:
            self.is_active = True
        
        try:
            # Attiva il relè
            self._set_relay_state(True)
            print("⚡ Relè ATTIVATO!")
            
            # Aspetta la durata specificata
            time.sleep(duration)
            
            # Disattiva il relè
            self._set_relay_state(False)
            print("🔴 Relè disattivato")
            
        except Exception as e:
            print(f"❌ Errore nel thread relè: {e}")
        finally:
            with self._lock:
                self.is_active = False
    
    def _set_relay_state(self, active):
        """
        Imposta lo stato del relè
        Args: active (bool) - True per attivare, False per disattivare
        """
        if active:
            state = GPIO.LOW if Config.RELAY_ACTIVE_LOW else GPIO.HIGH
        else:
            state = GPIO.HIGH if Config.RELAY_ACTIVE_LOW else GPIO.LOW
        
        GPIO.output(Config.RELAY_PIN, state)
    
    def force_off(self):
        """Forza lo spegnimento del relè"""
        if self.is_initialized:
            self._set_relay_state(False)
            with self._lock:
                self.is_active = False
            print("🔴 Relè forzato OFF")
    
    def get_status(self):
        """Restituisce lo stato attuale del relè"""
        return {
            'initialized': self.is_initialized,
            'active': self.is_active,
            'pin': Config.RELAY_PIN,
            'active_low': Config.RELAY_ACTIVE_LOW,
            'duration': Config.RELAY_ACTIVE_TIME
        }
    
    def cleanup(self):
        """Pulizia delle risorse GPIO"""
        try:
            if self.is_initialized:
                self.force_off()
                # Non facciamo GPIO.cleanup() qui perché potrebbe interferire con RFID
                print("🧹 Relè cleanup completato")
        except Exception as e:
            print(f"⚠️ Warning cleanup relè: {e}")
    
    def __del__(self):
        """Destructor - pulisce automaticamente le risorse"""
        self.cleanup()