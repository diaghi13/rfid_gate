#!/usr/bin/env python3
"""
Lettore RFID con debounce per evitare letture multiple - VERSIONE CORRETTA PER DOPPIO RFID
"""
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from config import Config

class RFIDReader:
    """Lettore RFID con debounce - VERSIONE CORRETTA"""
    
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
        
        print(f"🔧 RFID Reader {self.reader_id}: RST={self.rst_pin}, SDA={self.sda_pin}")
    
    def initialize(self):
        """Inizializza lettore con pin specifici"""
        try:
            print(f"📡 Inizializzazione RFID {self.reader_id} (RST:{self.rst_pin}, SDA:{self.sda_pin})")
            
            # CRITICO: NON chiamare GPIO.setmode() qui - può causare conflitti
            # Lascia che sia il manager principale a gestire GPIO.setmode()
            
            # Importa MFRC522 base per configurazione pin personalizzata
            from mfrc522 import MFRC522
            
            # Configura pin specifici per questo lettore
            self.mfrc522_reader = MFRC522()
            self.mfrc522_reader.RST = self.rst_pin
            self.mfrc522_reader.SDA = self.sda_pin
            
            # Crea SimpleMFRC522 wrapper
            self.reader = SimpleMFRC522()
            # Sostituisci il reader interno con quello configurato
            self.reader.READER = self.mfrc522_reader
            
            self.is_initialized = True
            print(f"✅ RFID {self.reader_id} inizializzato")
            return True
            
        except Exception as e:
            print(f"❌ Errore init RFID {self.reader_id}: {e}")
            return False
    
    def read_card(self):
        """Legge card con debounce e gestione timeout"""
        if not self.is_initialized:
            return None, None
        
        try:
            # Usa il metodo read standard con timeout corto
            # per evitare blocchi infiniti che impediscono il funzionamento dell'altro lettore
            
            # Salva configurazione GPIO attuale
            old_rst = getattr(self.reader.READER, 'RST', None)
            old_sda = getattr(self.reader.READER, 'SDA', None)
            
            # Imposta pin per questo lettore
            self.reader.READER.RST = self.rst_pin
            self.reader.READER.SDA = self.sda_pin
            
            # Inizializza SPI per questo lettore
            self.reader.READER.spi_open()
            self.reader.READER.init()
            
            # Tenta lettura rapida
            card_id, card_data = self.reader.READER.read_no_halt()
            
            if card_id == 0:  # Nessuna card
                return None, None
            
            # Leggi dati se card presente
            if card_data is None:
                try:
                    card_data = self.reader.READER.read_string_data()
                except:
                    card_data = ""
            
            current_time = time.time()
            
            # Debounce: ignora se stessa card letta di recente
            if (card_id == self.last_card_id and 
                (current_time - self.last_read_time) < self.debounce_time):
                return None, None  # Ignora lettura duplicata
            
            # Aggiorna debounce
            self.last_card_id = card_id
            self.last_read_time = current_time
            
            print(f"📱 RFID {self.reader_id}: Card {hex(card_id)} rilevata")
            
            return card_id, card_data
            
        except Exception as e:
            # Non stampare errori continui - solo errori significativi
            error_str = str(e).lower()
            if "timeout" not in error_str and "no card" not in error_str and "error" in error_str:
                print(f"⚠️ Errore lettura RFID {self.reader_id}: {e}")
            return None, None
        finally:
            # Cleanup SPI per questo lettore
            try:
                if hasattr(self.reader.READER, 'spi_close'):
                    self.reader.READER.spi_close()
            except:
                pass
    
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
            
            elif Config.UID_FORMAT_MODE == 'compatible':
                # Modalità compatibile - rimuove ultimi 2 caratteri per default
                if len(hex_str) > 2:
                    formatted_uid = hex_str[:-2]
                else:
                    formatted_uid = hex_str
                    
            else:
                # Modalità legacy (default zfill 8)
                formatted_uid = hex_str.zfill(8)
            
            # Debug se abilitato
            if Config.UID_DEBUG_MODE and original_uid != formatted_uid:
                print(f"🔧 UID Transform {self.reader_id}: {original_uid} → {formatted_uid} (mode: {Config.UID_FORMAT_MODE})")
            
            return formatted_uid
            
        except Exception as e:
            print(f"❌ Errore format UID {self.reader_id}: {e}")
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
        """Test connessione modulo con pin specifici"""
        if not self.is_initialized:
            return False
        
        try:
            print(f"🧪 Test connessione RFID {self.reader_id}...")
            
            # Configura pin per test
            self.reader.READER.RST = self.rst_pin
            self.reader.READER.SDA = self.sda_pin
            
            # Test base: verifica che il modulo risponda
            self.reader.READER.spi_open()
            self.reader.READER.init()
            
            # Tenta una lettura veloce per verificare comunicazione
            try:
                version = self.reader.READER.read(0x37)  # Registro versione
                if version == 0x00 or version == 0xFF:
                    print(f"❌ Test RFID {self.reader_id}: Modulo non risponde (version=0x{version:02X})")
                    return False
                else:
                    print(f"✅ Test RFID {self.reader_id} OK (version=0x{version:02X})")
                    return True
            except Exception as e:
                print(f"❌ Test RFID {self.reader_id} fallito: {e}")
                return False
            finally:
                try:
                    self.reader.READER.spi_close()
                except:
                    pass
                
        except Exception as e:
            print(f"❌ Test RFID {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Cleanup specifico per questo lettore"""
        try:
            if self.is_initialized and self.reader:
                print(f"🧹 Cleanup RFID {self.reader_id}")
                # Non chiamare GPIO.cleanup() qui - lasciare al manager principale
                self.reader = None
                self.is_initialized = False
        except Exception as e:
            print(f"⚠️ Errore cleanup RFID {self.reader_id}: {e}")