#!/usr/bin/env python3
"""
Lettore RFID con debounce per evitare letture multiple
WRAPPER COMPATIBILITÀ - Usa il nuovo sistema modulare ma mantiene interfaccia esistente
"""
import time
from config import Config
from rfid_readers.reader_factory import RFIDReaderFactory

class RFIDReader:
    """Lettore RFID con debounce - WRAPPER per compatibilità totale"""
    
    def __init__(self, reader_id="default", rst_pin=None, sda_pin=None):
        self.reader_id = reader_id
        self.rst_pin = rst_pin or Config.RFID_IN_RST_PIN
        self.sda_pin = sda_pin or Config.RFID_IN_SDA_PIN
        self.is_initialized = False
        
        # Debounce per evitare letture multiple
        self.last_card_id = None
        self.last_read_time = 0
        self.debounce_time = Config.RFID_DEBOUNCE_TIME
        
        # Nuovo sistema: determina tipo lettore dalla configurazione
        self.reader_type = getattr(Config, 'RFID_IN_READER_TYPE', 'mfrc522')
        self.actual_reader = None
        
        print(f"🔧 RFIDReader {reader_id}: configurato per {self.reader_type.upper()}")
    
    def initialize(self):
        """Inizializza lettore usando nuovo sistema modulare"""
        try:
            # Crea il lettore appropriato basato sulla configurazione
            if self.reader_type.lower() == 'pn532':
                # Usa PN532 con configurazione dalla config
                self.actual_reader = RFIDReaderFactory.create_from_config(self.reader_id, "RFID_IN")
            else:
                # Usa MFRC522 con i parametri esistenti
                self.actual_reader = RFIDReaderFactory.create_reader(
                    'mfrc522', 
                    self.reader_id,
                    rst_pin=self.rst_pin,
                    sda_pin=self.sda_pin,
                    debounce_time=self.debounce_time
                )
            
            # Inizializza il lettore effettivo
            if self.actual_reader.initialize():
                self.is_initialized = True
                print(f"✅ RFIDReader {self.reader_id} inizializzato ({self.reader_type.upper()})")
                return True
            else:
                print(f"❌ Fallimento inizializzazione {self.reader_type.upper()}")
                return False
                
        except Exception as e:
            print(f"❌ Errore init RFID {self.reader_id}: {e}")
            return False
    
    def read_card(self):
        """Legge card con debounce - Usa lettore effettivo"""
        if not self.is_initialized or not self.actual_reader:
            return None, None
        
        try:
            # Il debounce è gestito dai lettori individuali
            return self.actual_reader.read_card()
            
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
        """Test connessione modulo - Usa lettore effettivo"""
        if not self.is_initialized or not self.actual_reader:
            return False
        
        try:
            return self.actual_reader.test_connection()
        except Exception as e:
            print(f"Test RFID {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Cleanup - Usa lettore effettivo"""
        try:
            if self.actual_reader:
                self.actual_reader.cleanup()
            self.is_initialized = False
        except:
            pass