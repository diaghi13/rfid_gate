#!/usr/bin/env python3
"""
Classe base per lettori RFID
"""
from abc import ABC, abstractmethod
import time

class BaseRFIDReader(ABC):
    """Classe base per tutti i lettori RFID"""
    
    def __init__(self, reader_id="default", **kwargs):
        self.reader_id = reader_id
        self.is_initialized = False
        self.last_card_id = None
        self.last_read_time = 0
        self.debounce_time = kwargs.get('debounce_time', 2.0)
        
        # Debounce per lettore separato - CHIAVE per dual reader
        self.reader_debounce_key = f"reader_{self.reader_id}"
    
    @abstractmethod
    def initialize(self):
        """Inizializza il lettore"""
        pass
    
    @abstractmethod
    def read_card(self):
        """Legge una card - ritorna (card_id, card_data)"""
        pass
    
    @abstractmethod
    def test_connection(self):
        """Testa la connessione del lettore"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Pulisce le risorse"""
        pass
    
    def apply_debounce(self, card_id):
        """Applica debounce PER LETTORE per evitare letture multiple"""
        current_time = time.time()
        
        # Debounce specifico per questo lettore
        if (card_id == self.last_card_id and 
            (current_time - self.last_read_time) < self.debounce_time):
            return False  # Ignora lettura duplicata DELLO STESSO LETTORE
        
        self.last_card_id = card_id
        self.last_read_time = current_time
        return True
    
    def format_card_uid(self, card_id):
        """Formatta UID card secondo configurazione"""
        if card_id is None:
            return None
        
        try:
            from config import Config
            
            # Converte in hex base
            if isinstance(card_id, int):
                hex_str = hex(card_id)[2:].upper()
            elif isinstance(card_id, (bytes, bytearray)):
                hex_str = ''.join([f'{b:02X}' for b in card_id])
            else:
                hex_str = str(card_id).upper()
            
            original_uid = hex_str
            
            # Applica formato secondo configurazione
            if Config.UID_FORMAT_MODE == 'remove_suffix':
                if len(hex_str) > Config.UID_CHARS_COUNT:
                    formatted_uid = hex_str[:-Config.UID_CHARS_COUNT]
                else:
                    formatted_uid = hex_str
                    
            elif Config.UID_FORMAT_MODE == 'truncate':
                formatted_uid = hex_str[:Config.UID_CHARS_COUNT]
                
            elif Config.UID_FORMAT_MODE == 'take_last':
                formatted_uid = hex_str[-Config.UID_CHARS_COUNT:]
                
            elif Config.UID_FORMAT_MODE == 'fixed_length':
                if len(hex_str) > Config.UID_TARGET_LENGTH:
                    formatted_uid = hex_str[:Config.UID_TARGET_LENGTH]
                else:
                    formatted_uid = hex_str.zfill(Config.UID_TARGET_LENGTH)
            else:
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
            'uid_hex': hex(card_id) if isinstance(card_id, int) else str(card_id),
            'data': card_data.strip() if card_data else None,
            'data_length': len(card_data) if card_data else 0,
            'reader_type': self.__class__.__name__
        }