#!/usr/bin/env python3
"""
🔌 MFRC522 RFID Reader - Refactored Version
==========================================

Implementazione robusta del lettore MFRC522 con:
- Async/await support
- Gestione errori avanzata
- Compatibilità completa con il sistema esistente
"""

import asyncio
import time
from typing import Optional
from rfid_gate.hardware.readers.base import BaseRFIDReader

# Import condizionale per hardware
try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    # Mock per development
    class GPIO:
        BCM = "BCM"
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def cleanup(): pass
    
    class SimpleMFRC522:
        def read(self): return None, None


class MFRC522Reader(BaseRFIDReader):
    """
    Lettore RFID MFRC522 - Compatibilità totale con codice esistente.
    
    Mantiene il comportamento originale ma aggiunge:
    - Architettura asincrona
    - Gestione errori migliorata
    - Statistics tracking
    - Status monitoring
    """
    
    def __init__(self, reader_id: str = "MFRC522", direction: str = "in", 
                 rst_pin: Optional[int] = None, sda_pin: Optional[int] = None, **kwargs):
        super().__init__(reader_id, direction)
        
        # Configurazione pin (con fallback ai default)
        self.rst_pin = rst_pin or 22  # Default da Config
        self.sda_pin = sda_pin or 8   # Default da Config
        self.reader = None
        
        print(f"📡 MFRC522Reader {reader_id} creato - RST:{self.rst_pin}, SDA:{self.sda_pin}")
    
    def get_reader_type(self) -> str:
        """Restituisce tipo lettore"""
        return "mfrc522"
    
    async def _hardware_init(self) -> bool:
        """
        Inizializzazione hardware MFRC522.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        if not HAS_HARDWARE:
            print(f"❌ MFRC522 {self.reader_id}: Hardware non disponibile (normale su dev)")
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            def _init_gpio():
                """Inizializzazione GPIO sincrona"""
                GPIO.setmode(GPIO.BCM)
                return SimpleMFRC522()
            
            # Esegui inizializzazione in thread per evitare blocchi
            self.reader = await loop.run_in_executor(None, _init_gpio)
            
            print(f"✅ MFRC522 {self.reader_id} inizializzato (RST:{self.rst_pin}, SDA:{self.sda_pin})")
            return True
            
        except Exception as e:
            print(f"❌ Errore init MFRC522 {self.reader_id}: {e}")
            return False
    
    async def _hardware_read(self) -> Optional[bytes]:
        """
        Lettura hardware MFRC522 con timeout.
        
        Returns:
            Optional[bytes]: Dati raw della carta o None
        """
        if not self.reader or not HAS_HARDWARE:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            def _read_card():
                """Lettura sincrona da eseguire in thread"""
                try:
                    card_id, card_data = self.reader.read()
                    
                    if card_id is not None:
                        # Converti ID in bytes per compatibilità
                        # MFRC522 restituisce un int, convertiamo in bytes
                        return card_id.to_bytes(4, byteorder='big')
                    
                    return None
                    
                except Exception as e:
                    print(f"   ⚠️ Errore lettura MFRC522: {e}")
                    return None
            
            # Esegui lettura in thread con timeout breve
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _read_card),
                timeout=0.5
            )
            
            return result
            
        except asyncio.TimeoutError:
            # Timeout normale, non è un errore critico
            return None
        except Exception as e:
            print(f"   ⚠️ MFRC522 {self.reader_id} errore lettura: {e}")
            return None
    
    async def _hardware_cleanup(self) -> None:
        """Cleanup hardware MFRC522"""
        try:
            if HAS_HARDWARE:
                loop = asyncio.get_event_loop()
                
                def _cleanup_gpio():
                    """Cleanup GPIO sincrono"""
                    try:
                        GPIO.cleanup()
                    except Exception as e:
                        print(f"   ⚠️ Errore GPIO cleanup: {e}")
                
                await loop.run_in_executor(None, _cleanup_gpio)
            
            self.reader = None
            print(f"   🧹 MFRC522 {self.reader_id} cleanup completato")
            
        except Exception as e:
            print(f"   ⚠️ MFRC522 {self.reader_id} cleanup error: {e}")
    
    def get_hardware_info(self) -> dict:
        """Informazioni specifiche hardware MFRC522"""
        return {
            'rst_pin': self.rst_pin,
            'sda_pin': self.sda_pin,
            'hardware_available': HAS_HARDWARE,
            'gpio_mode': 'BCM' if HAS_HARDWARE else 'mock'
        }
    
    def __str__(self) -> str:
        return f"MFRC522({self.reader_id}, {self.direction}, {self.status.value})"


# Export
__all__ = ['MFRC522Reader']