#!/usr/bin/env python3
"""
Gestione configurazioni sistema RFID - Versione senza dotenv
"""
import os

def load_env_file():
    """Carica file .env manualmente senza dipendenza dotenv"""
    env_path = '.env'
    
    # Se lanciato da src/, cerca .env nella directory padre
    if not os.path.exists(env_path):
        env_path = '../.env'
    
    if not os.path.exists(env_path):
        print("⚠️ File .env non trovato")
        return
    
    try:
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Ignora linee vuote e commenti
                if not line or line.startswith('#'):
                    continue
                
                # Cerca formato KEY=VALUE
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Rimuovi virgolette se presenti
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Imposta variabile ambiente
                os.environ[key] = value
        
        print("✅ File .env caricato")
        
    except Exception as e:
        print(f"⚠️ Errore caricamento .env: {e}")

# Carica configurazioni
load_env_file()

class Config:
    """Configurazioni sistema"""
    
    # MQTT
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqbrk.ddns.net')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 8883))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'palestraUser')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '28dade03$')
    MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'True').lower() == 'true'
    
    # Tornello
    TORNELLO_ID = os.getenv('TORNELLO_ID', 'tornello_01')
    
    # Sistema Bidirezionale
    BIDIRECTIONAL_MODE = os.getenv('BIDIRECTIONAL_MODE', 'True').lower() == 'true'
    ENABLE_IN_READER = os.getenv('ENABLE_IN_READER', 'True').lower() == 'true'
    ENABLE_OUT_READER = os.getenv('ENABLE_OUT_READER', 'True').lower() == 'true'
    
    # RFID IN
    RFID_IN_RST_PIN = int(os.getenv('RFID_IN_RST_PIN', 22))
    RFID_IN_SDA_PIN = int(os.getenv('RFID_IN_SDA_PIN', 8))
    RFID_IN_ENABLE = os.getenv('RFID_IN_ENABLE', 'True').lower() == 'true'
    
    # RFID OUT
    RFID_OUT_RST_PIN = int(os.getenv('RFID_OUT_RST_PIN', 25))
    RFID_OUT_SDA_PIN = int(os.getenv('RFID_OUT_SDA_PIN', 7))
    RFID_OUT_ENABLE = os.getenv('RFID_OUT_ENABLE', 'False').lower() == 'true'
    
    # Relè IN
    RELAY_IN_PIN = int(os.getenv('RELAY_IN_PIN', 18))
    RELAY_IN_ACTIVE_TIME = int(os.getenv('RELAY_IN_ACTIVE_TIME', 2))
    RELAY_IN_ACTIVE_LOW = os.getenv('RELAY_IN_ACTIVE_LOW', 'False').lower() == 'true'
    RELAY_IN_INITIAL_STATE = os.getenv('RELAY_IN_INITIAL_STATE', 'LOW').upper()
    RELAY_IN_ENABLE = os.getenv('RELAY_IN_ENABLE', 'True').lower() == 'true'
    
    # Relè OUT
    RELAY_OUT_PIN = int(os.getenv('RELAY_OUT_PIN', 19))
    RELAY_OUT_ACTIVE_TIME = int(os.getenv('RELAY_OUT_ACTIVE_TIME', 2))
    RELAY_OUT_ACTIVE_LOW = os.getenv('RELAY_OUT_ACTIVE_LOW', 'False').lower() == 'true'
    RELAY_OUT_INITIAL_STATE = os.getenv('RELAY_OUT_INITIAL_STATE', 'LOW').upper()
    RELAY_OUT_ENABLE = os.getenv('RELAY_OUT_ENABLE', 'False').lower() == 'true'
    
    # Autenticazione
    AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'True').lower() == 'true'
    AUTH_TIMEOUT = int(os.getenv('AUTH_TIMEOUT', 5))
    AUTH_TOPIC_SUFFIX = os.getenv('AUTH_TOPIC_SUFFIX', 'auth_response')
    
    # Apertura Manuale
    MANUAL_OPEN_ENABLED = os.getenv('MANUAL_OPEN_ENABLED', 'True').lower() == 'true'
    MANUAL_OPEN_TOPIC_SUFFIX = os.getenv('MANUAL_OPEN_TOPIC_SUFFIX', 'manual_open')
    MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX = os.getenv('MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX', 'manual_response')
    MANUAL_OPEN_TIMEOUT = int(os.getenv('MANUAL_OPEN_TIMEOUT', 10))
    MANUAL_OPEN_AUTH_REQUIRED = os.getenv('MANUAL_OPEN_AUTH_REQUIRED', 'True').lower() == 'true'
    
    # Offline
    OFFLINE_MODE_ENABLED = os.getenv('OFFLINE_MODE_ENABLED', 'True').lower() == 'true'
    OFFLINE_ALLOW_ACCESS = os.getenv('OFFLINE_ALLOW_ACCESS', 'True').lower() == 'true'
    OFFLINE_SYNC_ENABLED = os.getenv('OFFLINE_SYNC_ENABLED', 'True').lower() == 'true'
    OFFLINE_STORAGE_FILE = os.getenv('OFFLINE_STORAGE_FILE', 'offline_queue.json')
    OFFLINE_MAX_QUEUE_SIZE = int(os.getenv('OFFLINE_MAX_QUEUE_SIZE', 1000))
    CONNECTION_CHECK_INTERVAL = int(os.getenv('CONNECTION_CHECK_INTERVAL', 30))
    CONNECTION_RETRY_ATTEMPTS = int(os.getenv('CONNECTION_RETRY_ATTEMPTS', 3))
    
    # Logging
    LOG_DIRECTORY = os.getenv('LOG_DIRECTORY', 'logs')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 30))
    ENABLE_CONSOLE_LOG = os.getenv('ENABLE_CONSOLE_LOG', 'False').lower() == 'true'
    
    # RFID Debounce
    RFID_DEBOUNCE_TIME = float(os.getenv('RFID_DEBOUNCE_TIME', '2.0'))

    # RFID Debounce
    RFID_DEBOUNCE_TIME = float(os.getenv('RFID_DEBOUNCE_TIME', '2.0'))
    
    # Configurazione formato UID
    UID_FORMAT_MODE = os.getenv('UID_FORMAT_MODE', 'remove_suffix')
    UID_CHARS_COUNT = int(os.getenv('UID_CHARS_COUNT', 2))
    UID_TARGET_LENGTH = int(os.getenv('UID_TARGET_LENGTH', 8))
    UID_DEBUG_MODE = os.getenv('UID_DEBUG_MODE', 'True').lower() == 'true'
    
    @classmethod
    def get_mqtt_topic(cls, action="badge"):
        return f"gate/{cls.TORNELLO_ID}/{action}"
    
    @classmethod
    def get_auth_response_topic(cls):
        return f"gate/{cls.TORNELLO_ID}/{cls.AUTH_TOPIC_SUFFIX}"
    
    @classmethod
    def get_manual_open_topic(cls):
        return f"gate/{cls.TORNELLO_ID}/{cls.MANUAL_OPEN_TOPIC_SUFFIX}"
    
    @classmethod
    def get_manual_response_topic(cls):
        return f"gate/{cls.TORNELLO_ID}/{cls.MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX}"
    
    @classmethod
    def validate_config(cls):
        """Validazione configurazione basilare"""
        errors = []
        
        if not cls.MQTT_BROKER:
            errors.append("MQTT_BROKER richiesto")
        if not cls.TORNELLO_ID:
            errors.append("TORNELLO_ID richiesto")
        if not cls.RFID_IN_ENABLE and not cls.RFID_OUT_ENABLE:
            errors.append("Almeno un lettore RFID deve essere abilitato")
        if not cls.RELAY_IN_ENABLE and not cls.RELAY_OUT_ENABLE:
            errors.append("Almeno un relè deve essere abilitato")
            
        return errors

# Test configurazione al caricamento
if __name__ == "__main__":
    print("🧪 Test configurazione")
    print(f"MQTT_BROKER: {Config.MQTT_BROKER}")
    print(f"TORNELLO_ID: {Config.TORNELLO_ID}")
    print(f"RELAY_IN_PIN: {Config.RELAY_IN_PIN}")
    
    errors = Config.validate_config()
    if errors:
        print("❌ Errori:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configurazione OK")