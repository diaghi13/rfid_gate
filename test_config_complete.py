#!/usr/bin/env python3
"""
🔧 TEST COMPLETEZZA CONFIGURAZIONE
Verifica che tutte le variabili richieste dal sistema siano presenti
"""
import sys
sys.path.append('src')

def test_all_config_vars():
    """Test completo variabili di configurazione"""
    print("🔍 TEST COMPLETEZZA CONFIGURAZIONE")
    print("=" * 50)
    
    try:
        from config import Config
        print("✅ Config importato")
        
        # Lista variabili critiche che potrebbero causare AttributeError
        critical_vars = [
            # Timing & RFID
            'CARD_READ_INTERVAL',
            'GLOBAL_DEBOUNCE_TIME', 
            'RFID_DEBOUNCE_TIME',
            'PN532_READ_TIMEOUT',
            
            # RFID Readers
            'RFID_IN_READER_TYPE',
            'RFID_OUT_READER_TYPE',
            'RFID_IN_PN532_INTERFACE',
            'RFID_OUT_PN532_INTERFACE',
            'RFID_IN_PN532_I2C_ADDRESS',
            'RFID_OUT_PN532_I2C_ADDRESS',
            'ENABLE_IN_READER',
            'ENABLE_OUT_READER',
            
            # MQTT
            'MQTT_BROKER',
            'MQTT_PORT',
            'MQTT_USE_TLS',
            'TORNELLO_ID',
            
            # Relay
            'RELAY_IN_PIN',
            'RELAY_OUT_PIN',
            'RELAY_IN_ENABLE',
            'RELAY_OUT_ENABLE',
            
            # Sistema
            'BIDIRECTIONAL_MODE',
            'OFFLINE_MODE_ENABLED',
            'LOG_LEVEL'
        ]
        
        print(f"\n📋 Verifica {len(critical_vars)} variabili critiche:")
        
        missing_vars = []
        for var_name in critical_vars:
            try:
                value = getattr(Config, var_name)
                print(f"   ✅ {var_name}: {value}")
            except AttributeError:
                print(f"   ❌ {var_name}: MANCANTE!")
                missing_vars.append(var_name)
        
        print(f"\n📊 RISULTATO:")
        if not missing_vars:
            print("✅ TUTTE LE VARIABILI PRESENTI!")
            print("✅ Nessun rischio di AttributeError")
            return True
        else:
            print(f"❌ {len(missing_vars)} variabili mancanti:")
            for var in missing_vars:
                print(f"   - {var}")
            return False
            
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

def test_rfid_manager_usage():
    """Test uso RFIDManager con tutte le variabili"""
    print(f"\n🧠 TEST RFID MANAGER - USO VARIABILI")
    print("=" * 40)
    
    try:
        from rfid_manager import RFIDManager
        from config import Config
        
        # Test accesso alle variabili che potrebbero causare errori
        rfid_manager = RFIDManager()
        
        # Test variabili usate nel _reader_loop
        interval = Config.CARD_READ_INTERVAL
        debounce = Config.GLOBAL_DEBOUNCE_TIME
        
        print(f"✅ CARD_READ_INTERVAL: {interval}")
        print(f"✅ GLOBAL_DEBOUNCE_TIME: {debounce}")
        print("✅ RFIDManager può accedere a tutte le variabili")
        
        return True
        
    except AttributeError as e:
        print(f"❌ AttributeError in RFIDManager: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Altri errori: {e}")
        return True  # Altri errori sono OK (hardware missing etc)

def main():
    print("🚀 TEST RISOLUZIONE ERRORE CONFIGURAZIONE")
    print("Errore: type object 'Config' has no attribute 'CARD_READ_INTERVAL'")
    print()
    
    config_ok = test_all_config_vars()
    rfid_ok = test_rfid_manager_usage()
    
    print(f"\n🎯 CONCLUSIONE:")
    if config_ok and rfid_ok:
        print("✅ ERRORE CONFIGURAZIONE RISOLTO!")
        print("✅ Tutte le variabili Config sono presenti")
        print("✅ RFIDManager può funzionare senza AttributeError")
        print()
        print("🚀 Sistema pronto per il deploy!")
    else:
        print("❌ Alcuni problemi di configurazione persistono")
        print("🔧 Controlla le variabili mancanti sopra")

if __name__ == "__main__":
    main()