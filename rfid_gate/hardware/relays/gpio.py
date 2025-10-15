#!/usr/bin/env python3
"""
🔌 GPIO Relay Controller - Hardware Implementation
=================================================

Implementazione relè GPIO per Raspberry Pi con:
- Gestione GPIO avanzata
- Async/await support
- Auto-cleanup
- Error recovery
"""

import asyncio
import atexit
from typing import Optional
from rfid_gate.hardware.relays.base import BaseRelayController, RelayState

# Import condizionale per hardware
try:
    import RPi.GPIO as GPIO
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    # Mock per development
    class GPIO:
        BCM = "BCM"
        OUT = "OUT"
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def cleanup(): pass


class GPIORelayController(BaseRelayController):
    """
    Controller relè GPIO per Raspberry Pi.
    
    Supporta:
    - Relè attivi HIGH e LOW
    - Auto-cleanup su exit
    - Error recovery
    - Thread-safe operations
    """
    
    # Registry globale per cleanup automatico
    _global_relays = set()
    _cleanup_registered = False
    
    def __init__(self, relay_id: str = "GPIO_RELAY", direction: str = "in", 
                 pin: int = 18, **kwargs):
        super().__init__(relay_id, direction)
        
        self.pin = pin
        self.is_setup = False
        
        # Registra per cleanup globale
        self._register_for_cleanup()
        
        print(f"📡 GPIORelay {relay_id} creato - Pin: {self.pin}")
    
    @classmethod
    def _register_for_cleanup(cls):
        """Registra cleanup automatico globale"""
        if not cls._cleanup_registered:
            atexit.register(cls._cleanup_all_relays)
            cls._cleanup_registered = True
    
    @classmethod
    def _cleanup_all_relays(cls):
        """Cleanup automatico di tutti i relè registrati"""
        if not HAS_HARDWARE:
            return
        
        try:
            print("🧹 Cleanup automatico relè GPIO...")
            
            # Spegni tutti i pin registrati
            GPIO.setmode(GPIO.BCM)
            for relay in cls._global_relays.copy():
                try:
                    GPIO.setup(relay.pin, GPIO.OUT)
                    GPIO.output(relay.pin, GPIO.LOW)
                except Exception:
                    pass  # Ignora errori durante cleanup
            
            GPIO.cleanup()
            cls._global_relays.clear()
            
        except Exception:
            pass  # Silenzioso durante atexit
    
    def get_relay_type(self) -> str:
        """Restituisce tipo relè"""
        return "gpio"
    
    async def _hardware_init(self) -> bool:
        """
        Inizializzazione hardware GPIO.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        if not HAS_HARDWARE:
            print(f"❌ GPIO {self.relay_id}: Hardware non disponibile (normale su dev)")
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            def _init_gpio():
                """Inizializzazione GPIO sincrona"""
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.pin, GPIO.OUT)
                
                # Stato iniziale - LOGICA CORRETTA LEGACY
                # initial_state = "HIGH" → GPIO HIGH (relè spento con active_low=True)
                # initial_state = "LOW"  → GPIO LOW  (relè spento con active_low=False)
                if self.initial_state == "HIGH":
                    initial_state = GPIO.HIGH
                else:
                    initial_state = GPIO.LOW
                
                GPIO.output(self.pin, initial_state)
                return True
            
            # Esegui inizializzazione in thread per evitare blocchi
            success = await loop.run_in_executor(None, _init_gpio)
            
            if success:
                self.is_setup = True
                # Registra nel registry globale
                self._global_relays.add(self)
                
                print(f"✅ GPIO {self.relay_id} inizializzato - Pin: {self.pin}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"❌ Errore init GPIO {self.relay_id}: {e}")
            return False
    
    async def _hardware_set_state(self, state: bool) -> bool:
        """
        Imposta stato hardware GPIO.
        
        Args:
            state: True per ON (relè attivo), False per OFF (relè spento)
            
        Returns:
            bool: True se operazione riuscita
        """
        if not self.is_setup or not HAS_HARDWARE:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            def _set_gpio():
                """Imposta GPIO sincrono"""
                # LOGICA CORRETTA per active_low
                if self.active_low:
                    # Con active_low=True: ON=LOW, OFF=HIGH
                    gpio_state = GPIO.LOW if state else GPIO.HIGH
                else:
                    # Con active_low=False: ON=HIGH, OFF=LOW  
                    gpio_state = GPIO.HIGH if state else GPIO.LOW
                    
                GPIO.output(self.pin, gpio_state)
                return True
            
            # Esegui in thread per evitare blocchi
            success = await loop.run_in_executor(None, _set_gpio)
            return success
            
        except Exception as e:
            print(f"❌ Errore set state GPIO {self.relay_id}: {e}")
            return False
    
    def _sync_hardware_set_state(self, state: bool) -> bool:
        """
        Versione sincrona di _hardware_set_state per threading.
        Identica alla logica della versione async ma senza asyncio.
        
        Args:
            state: True per ON (relè attivo), False per OFF (relè spento)
            
        Returns:
            bool: True se operazione riuscita
        """
        if not self.is_setup or not HAS_HARDWARE:
            return False
        
        try:
            # LOGICA CORRETTA per active_low (IDENTICA AL LEGACY)
            if self.active_low:
                # Con active_low=True: ON=LOW, OFF=HIGH
                gpio_state = GPIO.LOW if state else GPIO.HIGH
            else:
                # Con active_low=False: ON=HIGH, OFF=LOW  
                gpio_state = GPIO.HIGH if state else GPIO.LOW
                
            GPIO.output(self.pin, gpio_state)
            return True
            
        except Exception as e:
            print(f"❌ Errore sync set state GPIO {self.relay_id}: {e}")
            return False
    
    async def _hardware_cleanup(self) -> None:
        """Cleanup hardware GPIO"""
        try:
            if HAS_HARDWARE and self.is_setup:
                loop = asyncio.get_event_loop()
                
                def _cleanup_gpio():
                    """Cleanup GPIO sincrono"""
                    try:
                        # Spegni pin
                        GPIO.setup(self.pin, GPIO.OUT)
                        GPIO.output(self.pin, GPIO.LOW)
                    except Exception as e:
                        print(f"   ⚠️ Errore spegnimento pin {self.pin}: {e}")
                
                await loop.run_in_executor(None, _cleanup_gpio)
            
            # Rimuovi dal registry
            self._global_relays.discard(self)
            self.is_setup = False
            
            print(f"   🧹 GPIO {self.relay_id} cleanup completato")
            
        except Exception as e:
            print(f"   ⚠️ GPIO {self.relay_id} cleanup error: {e}")
    
    def get_hardware_info(self) -> dict:
        """Informazioni specifiche hardware GPIO"""
        return {
            'pin': self.pin,
            'active_low': self.active_low,
            'initial_state': self.initial_state,
            'hardware_available': HAS_HARDWARE,
            'is_setup': self.is_setup,
            'gpio_mode': 'BCM' if HAS_HARDWARE else 'mock'
        }
    
    async def test_relay(self, duration: float = 0.5) -> bool:
        """
        Test rapido del relè.
        
        Args:
            duration: Durata test in secondi
            
        Returns:
            bool: True se test riuscito
        """
        if not self.is_setup:
            print(f"❌ {self.relay_id} non inizializzato per test")
            return False
        
        try:
            print(f"🧪 Test relè {self.relay_id}...")
            
            # ON
            success = await self._hardware_set_state(not self.active_low)
            if not success:
                return False
            
            await asyncio.sleep(duration)
            
            # OFF
            success = await self._hardware_set_state(self.active_low)
            if not success:
                return False
            
            print(f"✅ Test {self.relay_id} completato")
            return True
            
        except Exception as e:
            print(f"❌ Errore test {self.relay_id}: {e}")
            return False
    
    async def close(self):
        """Chiude il relè e resetta lo stato (alias per cleanup)"""
        await self.cleanup()
    
    async def cleanup(self):
        """Cleanup del relè GPIO"""
        try:
            if self.is_setup and HAS_HARDWARE:
                # Resetta pin a stato iniziale (stesso calcolo dell'inizializzazione)
                initial_gpio_state = GPIO.HIGH if self.initial_state == "HIGH" else GPIO.LOW
                GPIO.output(self.pin, initial_gpio_state)
                print(f"🧹 {self.relay_id} cleanup - pin {self.pin} reset a {self.initial_state}")
            
            # Rimuovi dalla registry globale
            if self in self._global_relays:
                self._global_relays.discard(self)
            
            self.is_setup = False
            self.state = RelayState.OFF
            
        except Exception as e:
            print(f"❌ Errore cleanup {self.relay_id}: {e}")
    
    def __str__(self) -> str:
        return f"GPIO({self.relay_id}, pin={self.pin}, {self.direction}, {self.state.value})"


# Export
__all__ = ['GPIORelayController']