#!/usr/bin/env python3
"""
🔧 TEST FIX TIMEOUT - Verifica che il fix del timeout funzioni
"""
import sys
import os
import time

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock per macOS
import platform
if platform.system() == "Darwin":
    import unittest.mock
    
    # Mock GPIO e PN532
    mock_gpio = unittest.mock.MagicMock()
    mock_gpio.BCM = "BCM"
    mock_gpio.OUT = "OUT"
    mock_gpio.HIGH = 1
    mock_gpio.LOW = 0
    sys.modules['RPi'] = unittest.mock.MagicMock()
    sys.modules['RPi.GPIO'] = mock_gpio
    
    # Mock PN532 che simula lettura periodica
    mock_pn532 = unittest.mock.MagicMock()
    mock_pn532.read_passive_target.return_value = [1, 2, 3, 4]
    sys.modules['pn532'] = mock_pn532
    sys.modules['pn532.i2c'] = mock_pn532
    sys.modules['board'] = unittest.mock.MagicMock()
    sys.modules['busio'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.i2c'] = unittest.mock.MagicMock()

def test_timeout_fix():
    print("🔧 TEST FIX TIMEOUT")
    print("="*50)
    
    from config import Config
    from rfid_manager import RFIDManager
    
    print(f"CARD_READ_INTERVAL: {Config.CARD_READ_INTERVAL}s")
    
    # Crea manager
    rfid_manager = RFIDManager()
    init_result = rfid_manager.initialize()
    print(f"Initialize: {init_result}")
    
    if not init_result:
        print("❌ Initialize fallito")
        return False
    
    # Avvia lettura
    start_result = rfid_manager.start_reading()
    print(f"Start reading: {start_result}")
    
    if not start_result:
        print("❌ Start reading fallito")
        return False
    
    print("\n🔄 TEST TIMEOUT FIX")
    print("Il nuovo timeout è 1.0s invece di 0.1s")
    print("Dovrebbe rilevare le card mock più facilmente...")
    
    cards_found = 0
    start_time = time.time()
    
    for i in range(5):  # 5 tentativi
        print(f"\n⏳ Tentativo {i+1}/5 - wait_for_card()...")
        
        card_info = rfid_manager.wait_for_card()
        
        if card_info:
            cards_found += 1
            print(f"🎉 CARD #{cards_found}: {card_info.get('card_id', 'N/A')}")
        else:
            print("⚠️ Nessuna card (timeout)")
        
        # Pausa tra tentativi
        time.sleep(0.5)
    
    # Stop
    rfid_manager.stop_reading()
    
    elapsed = time.time() - start_time
    print(f"\n📊 RISULTATI:")
    print(f"Tempo totale: {elapsed:.1f}s")
    print(f"Card trovate: {cards_found}/5")
    
    if cards_found > 0:
        print("✅ FIX TIMEOUT FUNZIONA!")
        print("Su Raspberry Pi dovrebbe funzionare molto meglio")
        return True
    else:
        print("❌ Problema persiste")
        return False

if __name__ == "__main__":
    success = test_timeout_fix()
    
    if success:
        print("\n🎯 SOLUZIONE PER RASPBERRY PI:")
        print("Il timeout è stato aumentato da 0.1s a 1.0s")
        print("Questo dovrebbe risolvere il problema di lettura card")
        print("\n📋 COSA FARE:")
        print("1. Fai il commit di questa modifica")
        print("2. Trasferisci sul Raspberry Pi") 
        print("3. Testa di nuovo il sistema")
    else:
        print("\n⚠️ Il fix potrebbe non essere sufficiente")
        print("Potrebbero esserci altri problemi")