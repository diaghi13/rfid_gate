#!/usr/bin/env python3
"""
Test completo con mock per verificare la logica del sistema
"""
import sys
import os
import time
from datetime import datetime

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock delle librerie hardware PRIMA dell'importazione
import unittest.mock

# Mock per PN532
mock_pn532 = unittest.mock.MagicMock()
mock_pn532.read_passive_target.return_value = [1, 2, 3, 4]  # Card fittizia
sys.modules['pn532'] = mock_pn532
sys.modules['pn532.i2c'] = mock_pn532
sys.modules['pn532.spi'] = mock_pn532
sys.modules['pn532.uart'] = mock_pn532

# Mock per librerie GPIO
mock_gpio = unittest.mock.MagicMock()
sys.modules['RPi'] = mock_gpio
sys.modules['RPi.GPIO'] = mock_gpio

# Mock per SPI/I2C
mock_spi = unittest.mock.MagicMock()
mock_i2c = unittest.mock.MagicMock()
sys.modules['spidev'] = mock_spi
sys.modules['board'] = mock_i2c
sys.modules['busio'] = mock_i2c

def test_system_with_mocks():
    print("🧪 TEST SISTEMA CON MOCK")
    print("="*60)
    
    # Ora importa dopo i mock
    from config import Config
    from rfid_manager import RFIDManager
    
    # Crea un mock reader custom che simula la lettura di card
    class MockPN532Reader:
        def __init__(self, *args, **kwargs):
            self.initialized = False
            self.card_count = 0
            self.direction = kwargs.get('direction', 'in')
        
        def initialize(self):
            print(f"🔧 Mock PN532 {self.direction} inizializzato")
            self.initialized = True
            return True
        
        def test_connection(self):
            print(f"🔗 Mock PN532 {self.direction} connection test OK")
            return True
        
        def read_card(self):
            # Simula lettura card ogni 3 chiamate
            self.card_count += 1
            if self.card_count % 3 == 0:
                card_id = f"MOCK_CARD_{self.card_count:03d}"
                print(f"📱 Mock reader {self.direction}: Card rilevata {card_id}")
                return (card_id, {"data": "mock_data", "type": "mock"})
            return None
        
        def cleanup(self):
            print(f"🧹 Mock PN532 {self.direction} cleaned up")
    
    # Patch del reader factory per usare i mock
    from rfid_readers.reader_factory import RFIDReaderFactory
    
    original_create = RFIDReaderFactory.create_reader
    
    def mock_create_reader(reader_type, reader_id, **config):
        print(f"🏭 Factory mock: Creating {reader_type} reader for {reader_id}")
        return MockPN532Reader(direction=reader_id, **config)
    
    RFIDReaderFactory.create_reader = mock_create_reader
    
    try:
        # Test RFIDManager
        print("\n1️⃣ TEST RFID MANAGER CON MOCK")
        rfid_manager = RFIDManager()
        
        # Inizializza
        init_result = rfid_manager.initialize()
        print(f"✅ Inizializzazione: {init_result}")
        
        if init_result:
            # Verifica lettori attivi
            active_readers = rfid_manager.get_active_readers()
            print(f"📱 Lettori attivi: {active_readers}")
            
            # Avvia lettura
            start_result = rfid_manager.start_reading()
            print(f"✅ Start reading: {start_result}")
            
            if start_result:
                print("\n🔄 SISTEMA MOCK IN ASCOLTO")
                print("Simulazione lettura card per 15 secondi...")
                
                start_time = time.time()
                timeout = 15
                cards_found = 0
                
                while (time.time() - start_time) < timeout and cards_found < 3:
                    try:
                        # Controlla se ci sono card in coda
                        if not rfid_manager.card_queue.empty():
                            card_info = rfid_manager.card_queue.get_nowait()
                            cards_found += 1
                            print(f"\n🎉 CARD #{cards_found} dalla coda: {card_info}")
                            
                            # Simula processo di autenticazione
                            uid = card_info.get('uid_formatted', 'N/A')
                            direction = card_info.get('direction', 'unknown')
                            print(f"🔐 Elaborazione card {uid} ({direction})")
                            print(f"✅ Mock: Accesso autorizzato")
                            print(f"⚡ Mock: Relè attivato")
                            print("-"*40)
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"⚠️ Errore nel test: {e}")
                        break
                
                print(f"\n📊 Test completato: {cards_found} card processate")
                
                # Ferma lettura
                rfid_manager.stop_reading()
                print("🛑 Lettura fermata")
                
            else:
                print("❌ Impossibile avviare lettura")
        else:
            print("❌ Inizializzazione fallita")
    
    finally:
        # Ripristina factory originale
        RFIDReaderFactory.create_reader = original_create
    
    print("\n" + "="*60)
    print("🧪 TEST MOCK COMPLETATO")
    
    print("\n💡 ANALISI RISULTATI:")
    print("Se questo test funziona ma il sistema reale no,")
    print("il problema è nelle librerie hardware PN532.")
    print("Su Raspberry Pi con librerie installate dovrebbe funzionare.")
    
    return True

if __name__ == "__main__":
    test_system_with_mocks()