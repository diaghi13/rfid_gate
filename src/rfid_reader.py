#!/usr/bin/env python3
"""
Lettore RFID thread-safe per doppio RFID - VERSIONE CORRETTA
"""
import RPi.GPIO as GPIO
import time
import threading
from config import Config

# Lock globale per sincronizzare accesso SPI
_spi_lock = threading.Lock()
_gpio_initialized = False

class RFIDReader:
    """Lettore RFID thread-safe per doppio RFID"""
    
    def __init__(self, reader_id="default", rst_pin=None, sda_pin=None):
        self.reader_id = reader_id
        self.rst_pin = rst_pin or Config.RFID_IN_RST_PIN
        self.sda_pin = sda_pin or Config.RFID_IN_SDA_PIN
        self.reader = None
        self.mfrc522_reader = None
        self.is_initialized = False
        
        # Debounce per evitare letture multiple
        self.last_card_id = None
        self.last_read_time = 0
        self.debounce_time = Config.RFID_DEBOUNCE_TIME
        
        print(f"🔧 RFID Reader {self.reader_id}: RST={self.rst_pin}, SDA={self.sda_pin}")
    
    def initialize(self):
        """Inizializza lettore con configurazione thread-safe"""
        global _gpio_initialized
        
        try:
            print(f"📡 Inizializzazione RFID {self.reader_id}")
            
            # Inizializza GPIO solo una volta globalmente
            with _spi_lock:
                if not _gpio_initialized:
                    GPIO.setwarnings(False)
                    GPIO.setmode(GPIO.BCM)
                    _gpio_initialized = True
                    print("⚙️ GPIO inizializzato globalmente")
            
            # Importa le classi necessarie
            from mfrc522 import MFRC522, SimpleMFRC522
            
            # Crea istanza MFRC522 con pin personalizzati
            self.mfrc522_reader = MFRC522(
                rst=self.rst_pin,
                cs=self.sda_pin,
                sck=11,  # Pin SPI condiviso
                mosi=10, # Pin SPI condiviso  
                miso=9   # Pin SPI condiviso
            )
            
            # Crea wrapper SimpleMFRC522
            self.reader = SimpleMFRC522()
            self.reader.READER = self.mfrc522_reader
            
            self.is_initialized = True
            print(f"✅ RFID {self.reader_id} inizializzato (RST:{self.rst_pin}, SDA:{self.sda_pin})")
            return True
            
        except ImportError as e:
            print(f"❌ Errore import libreria RFID: {e}")
            print("💡 Installa: pip install mfrc522")
            return False
        except Exception as e:
            print(f"❌ Errore init RFID {self.reader_id}: {e}")
            return False
    
    def read_card(self):
        """Legge card con gestione thread-safe per doppio RFID"""
        if not self.is_initialized or not self.reader:
            return None, None
        
        # Usa lock per evitare conflitti SPI
        with _spi_lock:
            try:
                # Verifica presenza card rapidamente
                self.reader.READER.init()
                (status, TagType) = self.reader.READER.request(self.reader.READER.PICC_REQIDL)
                
                if status != self.reader.READER.MI_OK:
                    return None, None
                
                # Leggi UID velocemente
                (status, uid) = self.reader.READER.SelectTagSN()
                if status != self.reader.READER.MI_OK:
                    return None, None
                
                # Converte UID in numero
                card_id = 0
                for i in range(len(uid)):
                    card_id = (card_id << 8) | uid[i]
                
                # Debounce check
                current_time = time.time()
                if (card_id == self.last_card_id and 
                    (current_time - self.last_read_time) < self.debounce_time):
                    return None, None
                
                # Aggiorna debounce
                self.last_card_id = card_id
                self.last_read_time = current_time
                
                print(f"📱 RFID {self.reader_id}: Card {hex(card_id)} rilevata")
                return card_id, ""  # Salta lettura dati per velocità
                
            except Exception as e:
                # Ignora errori comuni di timeout
                return None, None
            finally:
                try:
                    self.reader.READER.stop_crypto1()
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
        """Test connessione modulo"""
        if not self.is_initialized:
            return False
        
        try:
            print(f"🧪 Test connessione RFID {self.reader_id}...")
            
            # Configura pin
            self.reader.READER.RST = self.rst_pin
            self.reader.READER.SDA = self.sda_pin
            
            # Test inizializzazione
            self.reader.READER.init()
            
            # Test lettura registro versione
            version = self.reader.READER.read_register(0x37)  # VersionReg
            
            if version == 0x00 or version == 0xFF:
                print(f"❌ Test RFID {self.reader_id}: Modulo non risponde (version=0x{version:02X})")
                return False
            else:
                print(f"✅ Test RFID {self.reader_id} OK (version=0x{version:02X})")
                return True
                
        except Exception as e:
            print(f"❌ Test RFID {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Cleanup specifico per questo lettore"""
        try:
            if self.is_initialized:
                print(f"🧹 Cleanup RFID {self.reader_id}")
                if self.reader and hasattr(self.reader, 'READER'):
                    try:
                        self.reader.READER.stop_crypto1()
                    except:
                        pass
                self.reader = None
                self.mfrc522_reader = None
                self.is_initialized = False
        except Exception as e:
            print(f"⚠️ Errore cleanup RFID {self.reader_id}: {e}")