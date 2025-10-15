#!/usr/bin/env python3
"""
🚀 Independent Relay System - Completamente Autonomo
===================================================
Sistema relay con thread completamente indipendenti che si autogestiscono.
Ogni attivazione crea un thread che:
1. Attiva il relay
2. Aspetta la durata
3. Disattiva il relay  
4. Termina automaticamente

Zero interferenze, zero race conditions, massima semplicità.
"""

import time
import threading
from typing import Optional
from abc import ABC, abstractmethod


class IndependentRelay(ABC):
    """
    Relay con thread completamente indipendenti.
    Ogni attivazione è un thread separato che si autogestisce.
    """
    
    def __init__(self, relay_id: str, pin: int, active_time: float = 1.0, active_low: bool = True):
        self.relay_id = relay_id
        self.pin = pin
        self.active_time = active_time
        self.active_low = active_low
        self.is_setup = False
        
        # Statistics 
        self.stats = {
            'activations_total': 0,
            'activations_successful': 0,
            'activations_failed': 0
        }
    
    @abstractmethod 
    def _setup_hardware(self) -> bool:
        """Setup hardware specifico (GPIO, etc)"""
        pass
    
    @abstractmethod
    def _set_hardware_state(self, state: bool) -> bool:
        """
        Imposta stato hardware.
        Args:
            state: True per ON (relay attivo), False per OFF (relay spento)
        """
        pass
    
    async def initialize(self) -> bool:
        """Inizializza il relay"""
        try:
            if self._setup_hardware():
                # Imposta stato iniziale (spento)
                self._set_hardware_state(False)
                self.is_setup = True
                print(f"✅ {self.relay_id} inizializzato")
                return True
            else:
                print(f"❌ {self.relay_id} inizializzazione fallita")
                return False
        except Exception as e:
            print(f"❌ Errore init {self.relay_id}: {e}")
            return False
    
    def activate(self, duration: Optional[float] = None) -> bool:
        """
        Attiva relay con thread completamente indipendente.
        
        Args:
            duration: Durata attivazione (usa default se None)
            
        Returns:
            bool: True se thread avviato con successo
        """
        if not self.is_setup:
            print(f"❌ {self.relay_id} non inizializzato")
            return False
        
        actual_duration = duration if duration is not None else self.active_time
        
        print(f"🔛 Relè {self.relay_id}: activating")
        
        def independent_worker():
            """Thread worker completamente indipendente"""
            thread_name = threading.current_thread().name
            print(f"🧵 {self.relay_id}: Avvio thread indipendente per {actual_duration}s...")
            print(f"🧵 THREAD START: {self.relay_id} worker avviato (ID: {thread_name})")
            
            try:
                # 1. ATTIVA RELAY
                print(f"🔛 {self.relay_id}: Tentativo attivazione")
                success = self._set_hardware_state(True)
                if not success:
                    print(f"❌ {self.relay_id}: Fallimento attivazione hardware")
                    self.stats['activations_failed'] += 1
                    return
                
                print(f"⚡ Relè {self.relay_id}: on")
                print(f"⚡ {self.relay_id}: ON per {actual_duration}s (thread {thread_name})")
                start_time = time.time()
                
                # 2. ASPETTA (sleep semplice)
                time.sleep(actual_duration)
                
                # 3. DISATTIVA RELAY
                print(f"⏰ {self.relay_id}: Timer completato dopo {actual_duration:.2f}s - Disattivazione...")
                print(f"🔛 {self.relay_id}: Tentativo disattivazione")
                success = self._set_hardware_state(False)
                if not success:
                    print(f"❌ {self.relay_id}: Fallimento disattivazione hardware")
                    self.stats['activations_failed'] += 1
                    return
                
                actual_time = time.time() - start_time
                self.stats['activations_successful'] += 1
                print(f"⚡ Relè {self.relay_id}: off")
                print(f"✅ {self.relay_id}: OFF dopo {actual_time:.2f}s (thread {thread_name})")
                
            except Exception as e:
                print(f"💥 {self.relay_id}: EXCEPTION nel thread {thread_name}: {e}")
                # Emergency shutdown
                try:
                    self._set_hardware_state(False)
                    print(f"🔧 {self.relay_id}: Spegnimento di emergenza completato")
                except Exception as emergency_e:
                    print(f"💥 {self.relay_id}: ERRORE spegnimento di emergenza: {emergency_e}")
                
                self.stats['activations_failed'] += 1
                    
            finally:
                print(f"🧵 THREAD END: {self.relay_id} worker terminato (ID: {thread_name})")
        
        # Start completely independent thread
        try:
            self.stats['activations_total'] += 1
            
            thread = threading.Thread(
                target=independent_worker,
                name=f"{self.relay_id}_independent_{int(time.time())}"
            )
            thread.daemon = True  # Dies with main process
            thread.start()
            
            print(f"🚪 Apertura {self.relay_id} attivata")
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio thread {self.relay_id}: {e}")
            self.stats['activations_failed'] += 1
            return False


class IndependentGPIORelay(IndependentRelay):
    """Implementazione GPIO del relay indipendente"""
    
    def _setup_hardware(self) -> bool:
        """Setup GPIO"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            
            # Stato iniziale HIGH (relay spento con active_low=True)
            initial_state = GPIO.HIGH
            GPIO.output(self.pin, initial_state)
            
            print(f"✅ GPIO {self.relay_id} inizializzato - Pin: {self.pin}")
            return True
            
        except Exception as e:
            print(f"❌ Errore setup GPIO {self.relay_id}: {e}")
            return False
    
    def _set_hardware_state(self, state: bool) -> bool:
        """Imposta stato GPIO"""
        try:
            import RPi.GPIO as GPIO
            
            # Logica active_low
            if self.active_low:
                gpio_state = GPIO.LOW if state else GPIO.HIGH
                logic_explanation = f"active_low=True → {state}={'LOW' if state else 'HIGH'}"
            else:
                gpio_state = GPIO.HIGH if state else GPIO.LOW
                logic_explanation = f"active_low=False → {state}={'HIGH' if state else 'LOW'}"
                
            print(f"🔧 {self.relay_id}: GPIO.output(pin={self.pin}, state={'HIGH' if gpio_state else 'LOW'}) - {logic_explanation}")
            GPIO.output(self.pin, gpio_state)
            
            # Verifica lettura pin
            actual_state = GPIO.input(self.pin)
            expected_state_name = 'HIGH' if gpio_state else 'LOW'
            actual_state_name = 'HIGH' if actual_state else 'LOW'
            
            if actual_state == gpio_state:
                print(f"✅ {self.relay_id}: GPIO command completed successfully - Pin reads {actual_state_name}")
            else:
                print(f"⚠️ {self.relay_id}: GPIO MISMATCH! Expected {expected_state_name}, but pin reads {actual_state_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore GPIO {self.relay_id}: {e}")
            return False


# Test usage
if __name__ == "__main__":
    import asyncio
    
    async def test_independent_relay():
        """Test relay indipendente"""
        
        print("🧪 Test Independent Relay System")
        print("=" * 50)
        
        # Crea relay
        relay = IndependentGPIORelay("relay_in", pin=18, active_time=2.0)
        
        # Inizializza
        success = await relay.initialize()
        if not success:
            print("❌ Inizializzazione fallita")
            return
        
        print("\n🚀 Test attivazione...")
        
        # Attiva relay
        success = relay.activate()
        if success:
            print("✅ Thread indipendente avviato")
            print("📋 Il relay si dovrebbe attivare e rilasciare automaticamente dopo 2 secondi")
            
            # Aspetta un po' per vedere l'output
            await asyncio.sleep(3)
            
            print(f"\n📊 Statistiche finali:")
            print(f"   Attivazioni totali: {relay.stats['activations_total']}")
            print(f"   Attivazioni riuscite: {relay.stats['activations_successful']}")
            print(f"   Attivazioni fallite: {relay.stats['activations_failed']}")
        else:
            print("❌ Attivazione fallita")
    
    # Esegui test
    asyncio.run(test_independent_relay())