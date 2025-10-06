#!/usr/bin/env python3
"""
🚀 AVVIO SISTEMA RFID - Versione Raspberry Pi
"""
import sys
import os

# Verifica se siamo su Raspberry Pi
try:
    import RPi.GPIO as GPIO
    print("🍇 Raspberry Pi rilevato - Modalità HARDWARE")
    IS_RPI = True
except ImportError:
    print("🍎 macOS/Windows rilevato - Modalità MOCK")
    IS_RPI = False
    # Carica mock per test su macOS
    import unittest.mock
    
    # Mock GPIO
    mock_gpio = unittest.mock.MagicMock()
    mock_gpio.BCM = "BCM"
    mock_gpio.OUT = "OUT"
    mock_gpio.HIGH = 1
    mock_gpio.LOW = 0
    sys.modules['RPi'] = unittest.mock.MagicMock()
    sys.modules['RPi.GPIO'] = mock_gpio
    
    # Mock PN532
    mock_pn532 = unittest.mock.MagicMock()
    mock_pn532.read_passive_target.return_value = [1, 2, 3, 4]
    sys.modules['pn532'] = mock_pn532
    sys.modules['pn532.i2c'] = mock_pn532
    sys.modules['pn532.spi'] = mock_pn532
    sys.modules['board'] = unittest.mock.MagicMock()
    sys.modules['busio'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.i2c'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.spi'] = unittest.mock.MagicMock()
    
    # Mock MQTT per test completo
    mock_paho = unittest.mock.MagicMock()
    sys.modules['paho'] = mock_paho
    sys.modules['paho.mqtt'] = mock_paho
    sys.modules['paho.mqtt.client'] = mock_paho

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Avvio sistema con check automatico hardware/mock"""
    
    print("="*60)
    print("🎯 SISTEMA CONTROLLO ACCESSI RFID")
    print("="*60)
    
    if IS_RPI:
        print("🔧 Modalità: HARDWARE (Raspberry Pi)")
        print("📡 Lettori: PN532 reali su I2C/SPI")
    else:
        print("🔧 Modalità: MOCK (macOS/Windows)")
        print("📡 Lettori: Simulati per test")
    
    print("="*60)
    
    try:
        # Importa e avvia il sistema principale
        from main import AccessControlSystem
        
        system = AccessControlSystem()
        
        print("🚀 Avvio sistema...")
        system.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema arrestato dall'utente")
    except Exception as e:
        print(f"❌ Errore sistema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()