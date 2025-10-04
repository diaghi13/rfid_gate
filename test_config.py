#!/usr/bin/env python3
"""
Test configurazione .env - Verifica parsing corretto
"""
import os
import sys
sys.path.append('/opt/rfid-gate/src')

def test_config_parsing():
    """Test che la configurazione si carichi correttamente"""
    print("🧪 TEST PARSING CONFIGURAZIONE")
    print("=" * 40)
    
    try:
        # Carica configurazione
        from config import Config
        
        print("✅ Config caricata correttamente")
        
        # Verifica valori critici
        critical_values = [
            ('CARD_READ_INTERVAL', Config.CARD_READ_INTERVAL),
            ('RFID_DEBOUNCE_TIME', Config.RFID_DEBOUNCE_TIME), 
            ('MQTT_TIMEOUT', Config.MQTT_TIMEOUT),
        ]
        
        print("\n📊 Valori critici:")
        for name, value in critical_values:
            print(f"   {name}: {value} ({type(value).__name__})")
        
        # Verifica valori PN532 se esistono
        pn532_values = []
        for attr in dir(Config):
            if attr.startswith('PN532_'):
                value = getattr(Config, attr, None)
                pn532_values.append((attr, value))
        
        if pn532_values:
            print("\n🔧 Configurazione PN532:")
            for name, value in pn532_values:
                print(f"   {name}: {value} ({type(value).__name__})")
        
        # Verifica configurazione lettori
        print(f"\n📡 Configurazione lettori:")
        print(f"   RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
        print(f"   RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
        
        if hasattr(Config, 'RFID_IN_PN532_INTERFACE'):
            print(f"   RFID_IN_PN532_INTERFACE: {Config.RFID_IN_PN532_INTERFACE}")
        if hasattr(Config, 'RFID_IN_PN532_I2C_ADDRESS'):
            print(f"   RFID_IN_PN532_I2C_ADDRESS: {hex(Config.RFID_IN_PN532_I2C_ADDRESS)}")
        
        print("\n✅ CONFIGURAZIONE VALIDA - Pronta per deployment")
        return True
        
    except ValueError as e:
        print(f"❌ Errore parsing configurazione: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return False

if __name__ == "__main__":
    success = test_config_parsing()
    
    if success:
        print("\n🚀 Sistema pronto per avvio con:")
        print("   python3 src/main.py")
    else:
        print("\n❌ Correggere configurazione prima dell'avvio")
        sys.exit(1)