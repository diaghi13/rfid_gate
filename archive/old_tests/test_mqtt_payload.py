#!/usr/bin/env python3
"""
🎯 TEST PAYLOAD MQTT - Verifica dati corretti
==================================================
Test per verificare che i payload MQTT contengano:
- card_uid: "A1234567" (stringa, non lista)
- raw_id: numero intero
- hex_id: "0xA1234567"
"""

import sys
import os
import time
import json
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

print("🎯 TEST PAYLOAD MQTT - Verifica dati corretti")
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
    print(f"📋 UID_FORMAT_MODE: {Config.UID_FORMAT_MODE}")
    print(f"📋 UID_CHARS_COUNT: {Config.UID_CHARS_COUNT}")
    print()
    
except Exception as e:
    print(f"❌ Errore config: {e}")
    sys.exit(1)

# Test creazione payload MQTT
print("📡 Test creazione payload MQTT...")
try:
    from rfid_manager import RFIDManager
    
    # Mock setup per simulare hardware
    with patch('adafruit_pn532.i2c.PN532_I2C') as mock_i2c:
        
        # Mock PN532 che restituisce UID specifico
        mock_pn532 = MagicMock()
        mock_pn532.firmware_version = (1, 6, 7)
        # Simula UID: 4C 18 44 71 (come nel tuo esempio)
        mock_pn532.read_passive_target.return_value = bytes([0x4C, 0x18, 0x44, 0x71])
        mock_i2c.return_value = mock_pn532
        
        # Inizializza manager con solo lettore IN
        os.environ['ENABLE_OUT_READER'] = 'False'  # Solo IN per test
        
        manager = RFIDManager()
        
        if manager.initialize():
            print("✅ RFID Manager inizializzato")
            
            if manager.start():
                print("✅ Manager avviato")
                
                # Attendi una card
                print("🔄 Attendo card...")
                card_info = manager.get_next_card(timeout=2.0)
                
                if card_info:
                    print("\n🎉 CARD RICEVUTA:")
                    print(f"  reader_id: {card_info.get('reader_id')}")
                    print(f"  card_id: {card_info.get('card_id')}")
                    print(f"  uid_formatted: {card_info.get('uid_formatted')}")
                    print(f"  raw_id: {card_info.get('raw_id')}")
                    print(f"  uid_hex: {card_info.get('uid_hex')}")
                    print(f"  direction: {card_info.get('direction')}")
                    
                    # Simula creazione payload MQTT come fa mqtt_client.py
                    from datetime import datetime
                    
                    payload = {
                        "card_uid": card_info.get('uid_formatted'),
                        "identificativo_tornello": Config.TORNELLO_ID,
                        "direzione": card_info.get('direction', 'unknown'),
                        "timestamp": datetime.now().isoformat(),
                        "raw_id": str(card_info.get('raw_id')),
                        "card_data": card_info.get('card_data'),
                        "hex_id": card_info.get('uid_hex'),
                        "auth_required": True,
                        "reader_id": card_info.get('reader_id', 'unknown')
                    }
                    
                    print("\n📤 PAYLOAD MQTT:")
                    print(json.dumps(payload, indent=2, ensure_ascii=False))
                    
                    # Verifica formato
                    print("\n✅ VERIFICA FORMATO:")
                    card_uid = payload["card_uid"]
                    raw_id = payload["raw_id"] 
                    hex_id = payload["hex_id"]
                    
                    print(f"card_uid: '{card_uid}' (tipo: {type(card_uid)})")
                    print(f"raw_id: '{raw_id}' (tipo: {type(raw_id)})")
                    print(f"hex_id: '{hex_id}' (tipo: {type(hex_id)})")
                    
                    if isinstance(card_uid, str) and not card_uid.startswith('['):
                        print("✅ card_uid corretto (stringa, non lista)")
                    else:
                        print("❌ card_uid errato (lista o formato sbagliato)")
                        
                    if raw_id and raw_id != "None":
                        print("✅ raw_id presente")
                    else:
                        print("❌ raw_id mancante o None")
                        
                    if hex_id and hex_id != "None":
                        print("✅ hex_id presente")
                    else:
                        print("❌ hex_id mancante o None")
                        
                else:
                    print("❌ Nessuna card ricevuta")
                    
                manager.stop()
                
        else:
            print("❌ Errore inizializzazione")
            
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 RISULTATO ATTESO:")
print('{"card_uid": "4C1844", "raw_id": "1276429425", "hex_id": "0x4C184471"}')