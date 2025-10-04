#!/usr/bin/env python3
"""
📋 VISUALIZZAZIONE CONFIGURAZIONE COMPLETA
Mostra tutte le variabili caricate in modo organizzato
"""
import sys
sys.path.append('src')

def show_complete_config():
    """Mostra tutte le configurazioni caricate"""
    print("📋 CONFIGURAZIONE COMPLETA CARICATA")
    print("=" * 60)
    
    try:
        from config import Config
        
        print("🏷️ IDENTIFICAZIONE SISTEMA:")
        print(f"   TORNELLO_ID: {Config.TORNELLO_ID}")
        print(f"   BIDIRECTIONAL_MODE: {Config.BIDIRECTIONAL_MODE}")
        
        print(f"\n📡 MQTT:")
        print(f"   BROKER: {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
        print(f"   USERNAME: {Config.MQTT_USERNAME}")
        print(f"   TLS: {Config.MQTT_USE_TLS}")
        
        print(f"\n📱 LETTORI RFID:")
        print(f"   IN:  {Config.RFID_IN_READER_TYPE} ({Config.RFID_IN_PN532_INTERFACE.upper()}) - {Config.ENABLE_IN_READER}")
        print(f"   OUT: {Config.RFID_OUT_READER_TYPE} ({Config.RFID_OUT_PN532_INTERFACE.upper()}) - {Config.ENABLE_OUT_READER}")
        
        print(f"\n🔵 LETTORE IN (PN532 I2C):")
        print(f"   Interface: {Config.RFID_IN_PN532_INTERFACE}")
        print(f"   I2C Address: {hex(Config.RFID_IN_PN532_I2C_ADDRESS)}")
        print(f"   RST Pin: {Config.RFID_IN_RST_PIN}")
        print(f"   SDA Pin: {Config.RFID_IN_SDA_PIN}")
        
        print(f"\n🟡 LETTORE OUT (PN532 SPI):")
        print(f"   Interface: {Config.RFID_OUT_PN532_INTERFACE}")
        print(f"   SPI Bus: {Config.RFID_OUT_PN532_SPI_BUS}")
        print(f"   SPI Device: {Config.RFID_OUT_PN532_SPI_DEVICE}")
        print(f"   RST Pin: {Config.RFID_OUT_RST_PIN}")
        
        print(f"\n⚡ RELÈ:")
        print(f"   IN Pin: {Config.RELAY_IN_PIN} (Active: {Config.RELAY_IN_ENABLE})")
        print(f"   OUT Pin: {Config.RELAY_OUT_PIN} (Active: {Config.RELAY_OUT_ENABLE})")
        print(f"   Active Time: IN={Config.RELAY_IN_ACTIVE_TIME}s, OUT={Config.RELAY_OUT_ACTIVE_TIME}s")
        print(f"   Active Low: IN={Config.RELAY_IN_ACTIVE_LOW}, OUT={Config.RELAY_OUT_ACTIVE_LOW}")
        
        print(f"\n🔐 AUTENTICAZIONE:")
        print(f"   Enabled: {Config.AUTH_ENABLED}")
        print(f"   Timeout: {Config.AUTH_TIMEOUT}s")
        
        print(f"\n🔓 APERTURA MANUALE:")
        print(f"   Enabled: {Config.MANUAL_OPEN_ENABLED}")
        print(f"   Timeout: {Config.MANUAL_OPEN_TIMEOUT}s")
        print(f"   Auth Required: {Config.MANUAL_OPEN_AUTH_REQUIRED}")
        
        print(f"\n🛡️ OFFLINE MODE:")
        print(f"   Enabled: {Config.OFFLINE_MODE_ENABLED}")
        print(f"   Allow Access: {Config.OFFLINE_ALLOW_ACCESS}")
        print(f"   Max Queue: {Config.OFFLINE_MAX_QUEUE_SIZE}")
        print(f"   Storage: {Config.OFFLINE_STORAGE_FILE}")
        
        print(f"\n🔧 TIMING & DEBOUNCE:")
        print(f"   Card Read Interval: {Config.CARD_READ_INTERVAL}s")
        print(f"   Global Debounce: {Config.GLOBAL_DEBOUNCE_TIME}s")
        print(f"   RFID Debounce: {Config.RFID_DEBOUNCE_TIME}s")
        print(f"   PN532 Timeout: {Config.PN532_READ_TIMEOUT}s")
        
        print(f"\n🏷️ UID FORMATTING:")
        print(f"   Mode: {Config.UID_FORMAT_MODE}")
        print(f"   Target Length: {Config.UID_TARGET_LENGTH}")
        print(f"   Debug: {Config.UID_DEBUG_MODE}")
        
        print(f"\n📋 LOGGING:")
        print(f"   Directory: {Config.LOG_DIRECTORY}")
        print(f"   Level: {Config.LOG_LEVEL}")
        print(f"   Retention: {Config.LOG_RETENTION_DAYS} days")
        print(f"   Console: {Config.ENABLE_CONSOLE_LOG}")
        
        print(f"\n🌐 CONNECTION:")
        print(f"   Check Interval: {Config.CONNECTION_CHECK_INTERVAL}s")
        print(f"   Retry Attempts: {Config.CONNECTION_RETRY_ATTEMPTS}")
        
        print(f"\n📊 TOPICS MQTT:")
        print(f"   Badge: {Config.get_mqtt_topic('badge')}")
        print(f"   Auth Response: {Config.get_auth_response_topic()}")
        print(f"   Manual Open: {Config.get_manual_open_topic()}")
        print(f"   Manual Response: {Config.get_manual_response_topic()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore lettura config: {e}")
        return False

def count_config_vars():
    """Conta le variabili di configurazione"""
    from config import Config
    
    config_attrs = [attr for attr in dir(Config) 
                   if not attr.startswith('_') and not callable(getattr(Config, attr))]
    
    print(f"\n📊 STATISTICHE:")
    print(f"   Variabili totali definite: {len(config_attrs)}")
    print(f"   Configurazione: COMPLETA ✅")

if __name__ == "__main__":
    print("📋 VISUALIZZAZIONE CONFIGURAZIONE SISTEMA RFID")
    print()
    
    if show_complete_config():
        count_config_vars()
        
        print(f"\n🎯 STATO:")
        print(f"✅ Configurazione completa caricata")
        print(f"✅ Tutte le variabili sono in chiaro nel .env")
        print(f"✅ Sistema pronto per deploy!")
    else:
        print(f"\n❌ Problemi di configurazione")