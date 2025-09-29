#!/usr/bin/env python3
"""
Implementazione per lettore MFRC522
"""
try:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    print("⚠️ Librerie MFRC522 non disponibili (normale su macOS/Windows)")

from .base_reader import BaseRFIDReader

class MFRC522Reader(BaseRFIDReader):
    """Lettore RFID MFRC522 (compatibilità totale con codice esistente)"""
    
    def __init__(self, reader_id="mfrc522", rst_pin=None, sda_pin=None, **kwargs):
        super().__init__(reader_id, **kwargs)
        from config import Config
        
        self.rst_pin = rst_pin or Config.RFID_IN_RST_PIN
        self.sda_pin = sda_pin or Config.RFID_IN_SDA_PIN
        self.reader = None
    
    def initialize(self):
        """Inizializza lettore MFRC522"""
        if not HAS_HARDWARE:
            print(f"❌ MFRC522 {self.reader_id}: Hardware non disponibile")
            return False
            
        try:
            GPIO.setmode(GPIO.BCM)
            self.reader = SimpleMFRC522()
            self.is_initialized = True
            print(f"✅ MFRC522 {self.reader_id} inizializzato (RST:{self.rst_pin}, SDA:{self.sda_pin})")
            return True
        except Exception as e:
            print(f"❌ Errore init MFRC522 {self.reader_id}: {e}")
            return False
    
    def read_card(self):
        """Legge card con debounce (identico al comportamento originale)"""
        if not self.is_initialized or not HAS_HARDWARE:
            return None, None
        
        try:
            card_id, card_data = self.reader.read()
            
            if card_id is not None and not self.apply_debounce(card_id):
                return None, None  # Ignora per debounce
            
            return card_id, card_data
            
        except Exception as e:
            print(f"Errore lettura MFRC522 {self.reader_id}: {e}")
            return None, None
    
    def test_connection(self):
        """Test connessione MFRC522 (identico all'originale)"""
        if not self.is_initialized or not HAS_HARDWARE:
            return False
        try:
            test_reader = SimpleMFRC522()
            del test_reader
            return True
        except Exception as e:
            print(f"Test MFRC522 {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Cleanup MFRC522 (identico all'originale)"""
        try:
            if self.is_initialized and HAS_HARDWARE:
                GPIO.cleanup()
            self.is_initialized = False
        except:
            pass