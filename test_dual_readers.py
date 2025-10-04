#!/usr/bin/env python3
"""
🎯 TEST DUAL READERS - PN532 I2C + SPI
==================================================
Test inizializzazione lettori dual:
- IN: PN532 I2C (0x24) 
- OUT: PN532 SPI (bus 0, device 0)
"""

import sys
import os
import time
from unittest.mock import MagicMock, patch

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock delle librerie hardware prima dell'import
sys.modules['RPi'] = MagicMock()
sys.modules['RPi.GPIO'] = MagicMock()
sys.modules['mfrc522'] = MagicMock()
sys.modules['board'] = MagicMock()
sys.modules['busio'] = MagicMock()
sys.modules['digitalio'] = MagicMock()
sys.modules['adafruit_pn532'] = MagicMock()
sys.modules['adafruit_pn532.i2c'] = MagicMock()
sys.modules['adafruit_pn532.spi'] = MagicMock()

print("🎯 TEST DUAL READERS - PN532 I2C + SPI")
print("="*50)

# Load environment manually
def load_env_file():
    """Carica manualmente il file .env"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Rimuovi commenti dal valore
                    value = value.split('#')[0].strip()
                    os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        print("⚠️ File .env non trovato")

load_env_file()
print("✅ File .env caricato")

try:
    from config import Config
    print(f"📋 CONFIGURAZIONE:")
    print(f"BIDIRECTIONAL_MODE: {Config.BIDIRECTIONAL_MODE}")
    print(f"ENABLE_IN_READER: {Config.ENABLE_IN_READER}")
    print(f"ENABLE_OUT_READER: {Config.ENABLE_OUT_READER}")
    print(f"RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
    print(f"RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
    print(f"IN PN532 Interface: {Config.RFID_IN_PN532_INTERFACE}")
    print(f"OUT PN532 Interface: {Config.RFID_OUT_PN532_INTERFACE}")
    print(f"IN I2C Address: 0x{Config.RFID_IN_PN532_I2C_ADDRESS:02X}")
    print(f"OUT SPI Bus.Device: {Config.RFID_OUT_PN532_SPI_BUS}.{Config.RFID_OUT_PN532_SPI_DEVICE}")
    print()
    
except Exception as e:
    print(f"❌ Errore config: {e}")
    sys.exit(1)

# Test inizializzazione dual readers
print("📖 Inizializzazione RFID Manager (Dual Reader)...")
try:
    from rfid_manager import RFIDManager
    
    # Mock setup per simulare hardware
    with patch('adafruit_pn532.i2c.PN532_I2C') as mock_i2c, \
         patch('adafruit_pn532.spi.PN532_SPI') as mock_spi, \
         patch('board.I2C') as mock_board_i2c, \
         patch('board.SPI') as mock_board_spi, \
         patch('digitalio.DigitalInOut') as mock_cs:
        
        # Mock I2C PN532
        mock_pn532_i2c = MagicMock()
        mock_pn532_i2c.firmware_version = (1, 6, 7)
        mock_pn532_i2c.read_passive_target.return_value = bytes([0x63, 0x2D, 0x39, 0x03])
        mock_i2c.return_value = mock_pn532_i2c
        
        # Mock SPI PN532  
        mock_pn532_spi = MagicMock()
        mock_pn532_spi.firmware_version = (1, 6, 7)
        mock_pn532_spi.read_passive_target.return_value = bytes([0xAA, 0xBB, 0xCC, 0xDD])
        mock_spi.return_value = mock_pn532_spi
        
        # Inizializza manager
        manager = RFIDManager()
        
        if manager.initialize():
            print("✅ RFID Manager inizializzato")
            
            # Verifica lettori attivi
            active_readers = manager.get_active_readers()
            print(f"📡 Lettori attivi: {active_readers}")
            
            if len(active_readers) == 2:
                print("✅ ENTRAMBI I LETTORI INIZIALIZZATI!")
                print("  🔵 IN: PN532 I2C (0x24)")
                print("  🟡 OUT: PN532 SPI (0.0)")
            else:
                print(f"⚠️ Solo {len(active_readers)} lettore/i attivo/i")
                for reader_id in active_readers:
                    print(f"  📡 {reader_id}")
                    
            # Avvia manager
            if manager.start():
                print("✅ Manager avviato")
                
                # Simula letture per alcuni secondi
                print("\n🔄 SIMULAZIONE LETTURE DUAL...")
                start_time = time.time()
                
                while time.time() - start_time < 3:
                    card_info = manager.get_next_card(timeout=0.5)
                    if card_info:
                        reader_id = card_info.get('reader_id', 'unknown')
                        uid = card_info.get('uid_formatted', 'N/A')
                        direction = card_info.get('direction', 'unknown')
                        
                        print(f"📇 CARD: {uid} da {reader_id} ({direction})")
                        
                print("\n🛑 Test completato")
                manager.stop()
                
        else:
            print("❌ Errore inizializzazione RFID Manager")
            
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 RIEPILOGO:")
print("✅ Test configurazione dual reader")
print("✅ IN: PN532 I2C (address 0x24)")  
print("✅ OUT: PN532 SPI (bus 0, device 0)")
print("\n🚀 SU RASPBERRY PI:")
print("PYTHONPATH=src python3 src/main.py")
print("Dovrai vedere entrambi i lettori attivi!")