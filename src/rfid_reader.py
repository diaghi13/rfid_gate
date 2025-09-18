#!/usr/bin/env python3
"""
Modulo per la gestione del lettore RFID RC522
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from config import Config

class RFIDReader:
    """Classe per gestire il lettore RFID RC522"""
    
    def __init__(self, reader_id="default", rst_pin=None, sda_pin=None):
        self.reader_id = reader_id
        self.rst_pin = rst_pin or Config.RFID_IN_RST_PIN
        self.sda_pin = sda_pin or Config.RFID_IN_SDA_PIN
        self.reader = None
        self.is_initialized = False
    
    def initialize(self):
        """Inizializza il lettore RFID"""
        try:
            GPIO.setmode(GPIO.BCM)
            self.reader = SimpleMFRC522()
            self.is_initialized = True
            print("✅ Lettore RFID inizializzato correttamente")
            return True
        except Exception as e:
            print(f"❌ Errore inizializzazione RFID: {e}")
            return False
    
    def test_connection(self):
        """Testa la connessione al modulo RC522"""
        if not self.is_initialized:
            return False
        
        try:
            # Tentativo di creare un'istanza per testare la connessione
            test_reader = SimpleMFRC522()
            del test_reader
            print("✅ Connessione RC522 verificata")
            return True
        except Exception as e:
            print(f"❌ Test connessione RC522 fallito: {e}")
            print("🔧 Verifica:")
            print("   - Collegamenti SPI corretti")
            print("   - SPI abilitato (sudo raspi-config)")
            print("   - Alimentazione 3.3V al modulo")
            return False
    
    def read_card(self):
        """
        Legge una card RFID e restituisce i dati
        Returns: tuple (card_id, card_data) o (None, None) se errore
        """
        if not self.is_initialized:
            print("❌ Lettore RFID non inizializzato")
            return None, None
        
        try:
            print("⏳ In attesa di una card...")
            card_id, card_data = self.reader.read()
            return card_id, card_data
        except Exception as e:
            print(f"❌ Errore lettura card: {e}")
            return None, None
    
    def format_card_uid(self, card_id):
        """
        Formatta l'ID della card in formato MIFARE standard
        Args: card_id (int) - ID numerico della card
        Returns: str - UID formattato (es: "C67BD905")
        """
        if card_id is None:
            return None
        
        try:
            # Converte in esadecimale e formatta (8 caratteri, maiuscolo)
            formatted_uid = hex(card_id)[2:].upper().zfill(8)
            return formatted_uid
        except Exception as e:
            print(f"❌ Errore formattazione UID: {e}")
            return str(card_id)
    
    def get_card_info(self, card_id, card_data):
        """
        Restituisce un dizionario con tutte le informazioni della card
        """
        return {
            'raw_id': card_id,
            'uid_formatted': self.format_card_uid(card_id),
            'uid_hex': hex(card_id) if card_id else None,
            'data': card_data.strip() if card_data else None,
            'data_length': len(card_data) if card_data else 0
        }
    
    def cleanup(self):
        """Pulizia delle risorse GPIO"""
        try:
            if self.is_initialized:
                GPIO.cleanup()
                print("🧹 RFID cleanup completato")
        except Exception as e:
            print(f"⚠️ Warning cleanup RFID: {e}")
    
    def __del__(self):
        """Destructor - pulisce automaticamente le risorse"""
        self.cleanup()