#!/usr/bin/env python3
"""
Versione mock dei lettori per test su macOS/sviluppo
"""
from rfid_readers.base_reader import BaseRFIDReader
import time
import random

class MockMFRC522Reader(BaseRFIDReader):
    """Lettore MFRC522 mock per testing"""
    
    def __init__(self, reader_id="mfrc522_mock", **kwargs):
        super().__init__(reader_id, **kwargs)
        self.rst_pin = kwargs.get('rst_pin', 22)
        self.sda_pin = kwargs.get('sda_pin', 8)
    
    def initialize(self):
        print(f"🔧 Mock MFRC522 {self.reader_id} inizializzato (RST:{self.rst_pin}, SDA:{self.sda_pin})")
        self.is_initialized = True
        return True
    
    def read_card(self):
        # Simula lettura casuale per test
        if random.random() < 0.1:  # 10% di probabilità di lettura
            card_id = random.randint(1000000, 9999999)
            if self.apply_debounce(card_id):
                return card_id, "mock_data"
        return None, None
    
    def test_connection(self):
        return True
    
    def cleanup(self):
        self.is_initialized = False

class MockPN532Reader(BaseRFIDReader):
    """Lettore PN532 mock per testing"""
    
    def __init__(self, reader_id="pn532_mock", **kwargs):
        super().__init__(reader_id, **kwargs)
        self.interface = kwargs.get('interface', 'i2c')
        self.i2c_address = kwargs.get('i2c_address', 0x24)
    
    def initialize(self):
        print(f"🔧 Mock PN532 {self.reader_id} inizializzato ({self.interface.upper()}, addr:0x{self.i2c_address:02X})")
        self.is_initialized = True
        return True
    
    def read_card(self):
        # Simula lettura casuale per test
        if random.random() < 0.1:  # 10% di probabilità di lettura
            card_id = random.randint(1000000, 9999999)
            if self.apply_debounce(card_id):
                return card_id, ""
        return None, None
    
    def test_connection(self):
        return True
    
    def cleanup(self):
        self.is_initialized = False