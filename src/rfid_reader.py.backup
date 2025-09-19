#!/usr/bin/env python3
"""
Lettore RFID con debounce per evitare letture multiple
"""
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from config import Config

class RFIDReader:
    """Lettore RFID con debounce"""
    
    def __init__(self, reader_id="default", rst_pin=None, sda_pin=None):
        self.reader_id = reader_id
        self.rst_pin = rst_pin or Config.RFID_IN_RST_PIN
        self.sda_pin = sda_pin or Config.RFID_IN_SDA_PIN
        self.reader = None
        self.is_initialized = False
        
        # Debounce per evitare letture multiple
        self.last_card_id = None
        self.last_read_time = 0
        self.debounce_time = Config.RFID_DEBOUNCE_TIME
    
    def initialize(self):
        """Inizializza lettore"""
        try:
            GPIO.setmode(GPIO.BCM)
            self.reader = SimpleMFRC522()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Errore init RFID {self.reader_id}: {e}")
            return False
    
    def read_card(self):
        """Legge card con debounce"""
        if not self.is_initialized:
            return None, None
        
        try:
            card_id, card_data = self.reader.read()
            current_time = time.time()
            
            # Debounce: ignora se stessa card letta di recente
            if (card_id == self.last_card_id and 
                (current_time - self.last_read_time) < self.debounce_time):
                return None, None  # Ignora lettura duplicata
            
            # Aggiorna debounce
            self.last_card_id = card_id
            self.last_read_time = current_time
            
            return card_id, card_data
            
        except Exception as e:
            print(f"Errore lettura RFID {self.reader_id}: {e}")
            return None, None
    
    def format_card_uid(self, card_id):
        """Formatta UID card secondo configurazione .env"""
        if card_id is None:
            return None
        
        try:
            # Converte in hex base
            hex_str = hex(card_id)[2:].upper()
            original_uid = hex_str
            
            # Applica formato secondo configurazione
            if Config.UID_FORMAT_MODE == 'remove_suffix':
                # Rimuove N caratteri dalla fine
                if len(hex_str) > Config.UID_CHARS_COUNT:
                    formatted_uid = hex_str[:-Config.UID_CHARS_COUNT]
                else:
                    formatted_uid = hex_str
                    
            elif Config.UID_FORMAT_MODE == 'truncate':
                # Prende primi N caratteri
                formatted_uid = hex_str[:Config.UID_CHARS_COUNT]
                
            elif Config.UID_FORMAT_MODE == 'take_last':
                # Prende ultimi N caratteri
                formatted_uid = hex_str[-Config.UID_CHARS_COUNT:]
                
            elif Config.UID_FORMAT_MODE == 'fixed_length':
                # Tronca o fa padding a lunghezza fissa
                if len(hex_str) > Config.UID_TARGET_LENGTH:
                    formatted_uid = hex_str[:Config.UID_TARGET_LENGTH]
                else:
                    formatted_uid = hex_str.zfill(Config.UID_TARGET_LENGTH)
                    
            else:
                # Modalità legacy (default zfill 8)
                formatted_uid = hex_str.zfill(8)
            
            # Debug se abilitato
            if Config.UID_DEBUG_MODE and original_uid != formatted_uid:
                print(f"🔧 UID Transform: {original_uid} → {formatted_uid} (mode: {Config.UID_FORMAT_MODE})")
            
            return formatted_uid
            
        except Exception as e:
            print(f"❌ Errore format UID: {e}")
            return str(card_id)
    
    def get_card_info(self, card_id, card_data):
        """Info complete card"""
        return {
            'raw_id': card_id,
            'uid_formatted': self.format_card_uid(card_id),
            'uid_hex': hex(card_id) if card_id else None,
            'data': card_data.strip() if card_data else None,
            'data_length': len(card_data) if card_data else 0
        }
    
    def test_connection(self):
        """Test connessione modulo"""
        if not self.is_initialized:
            return False
        try:
            test_reader = SimpleMFRC522()
            del test_reader
            return True
        except Exception as e:
            print(f"Test RFID {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Cleanup"""
        try:
            if self.is_initialized:
                GPIO.cleanup()
        except:
            pass