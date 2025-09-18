#!/usr/bin/env python3
"""
Gestione delle configurazioni del sistema RFID
Carica le impostazioni dal file .env
"""

import os
from dotenv import load_dotenv

# Carica il file .env
load_dotenv()

class Config:
    """Classe per gestire tutte le configurazioni del sistema"""
    
    # Configurazioni MQTT
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqbrk.ddns.net')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 8883))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'palestraUser')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '28dade03$')
    MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'True').lower() == 'true'
    
    # Configurazioni Tornello
    TORNELLO_ID = os.getenv('TORNELLO_ID', 'tornello_01')
    
    # Configurazioni Sistema Bidirezionale
    BIDIRECTIONAL_MODE = os.getenv('BIDIRECTIONAL_MODE', 'True').lower() == 'true'
    ENABLE_IN_READER = os.getenv('ENABLE_IN_READER', 'True').lower() == 'true'
    ENABLE_OUT_READER = os.getenv('ENABLE_OUT_READER', 'True').lower() == 'true'
    
    # Configurazioni RFID Reader IN
    RFID_IN_RST_PIN = int(os.getenv('RFID_IN_RST_PIN', 22))
    RFID_IN_SDA_PIN = int(os.getenv('RFID_IN_SDA_PIN', 8))
    RFID_IN_ENABLE = os.getenv('RFID_IN_ENABLE', 'True').lower() == 'true'
    
    # Configurazioni RFID Reader OUT
    RFID_OUT_RST_PIN = int(os.getenv('RFID_OUT_RST_PIN', 25))
    RFID_OUT_SDA_PIN = int(os.getenv('RFID_OUT_SDA_PIN', 7))
    RFID_OUT_ENABLE = os.getenv('RFID_OUT_ENABLE', 'False').lower() == 'true'
    
    # Configurazioni Relè Canale IN
    RELAY_IN_PIN = int(os.getenv('RELAY_IN_PIN', 18))
    RELAY_IN_ACTIVE_TIME = int(os.getenv('RELAY_IN_ACTIVE_TIME', 2))
    RELAY_IN_ACTIVE_LOW = os.getenv('RELAY_IN_ACTIVE_LOW', 'False').lower() == 'true'
    RELAY_IN_INITIAL_STATE = os.getenv('RELAY_IN_INITIAL_STATE', 'LOW').upper()
    RELAY_IN_ENABLE = os.getenv('RELAY_IN_ENABLE', 'True').lower() == 'true'
    
    # Configurazioni Relè Canale OUT
    RELAY_OUT_PIN = int(os.getenv('RELAY_OUT_PIN', 19))
    RELAY_OUT_ACTIVE_TIME = int(os.getenv('RELAY_OUT_ACTIVE_TIME', 2))
    RELAY_OUT_ACTIVE_LOW = os.getenv('RELAY_OUT_ACTIVE_LOW', 'False').lower() == 'true'
    RELAY_OUT_INITIAL_STATE = os.getenv('RELAY_OUT_INITIAL_STATE', 'LOW').upper()
    RELAY_OUT_ENABLE = os.getenv('RELAY_OUT_ENABLE', 'False').lower() == 'true'
    
    # Configurazioni Autenticazione
    AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'True').lower() == 'true'
    AUTH_TIMEOUT = int(os.getenv('AUTH_TIMEOUT', 5))
    AUTH_TOPIC_SUFFIX = os.getenv('AUTH_TOPIC_SUFFIX', 'auth_response')
    
    # Configurazioni Fallback Offline
    OFFLINE_MODE_ENABLED = os.getenv('OFFLINE_MODE_ENABLED', 'True').lower() == 'true'
    OFFLINE_ALLOW_ACCESS = os.getenv('OFFLINE_ALLOW_ACCESS', 'True').lower() == 'true'
    OFFLINE_SYNC_ENABLED = os.getenv('OFFLINE_SYNC_ENABLED', 'True').lower() == 'true'
    OFFLINE_STORAGE_FILE = os.getenv('OFFLINE_STORAGE_FILE', 'offline_queue.json')
    OFFLINE_MAX_QUEUE_SIZE = int(os.getenv('OFFLINE_MAX_QUEUE_SIZE', 1000))
    CONNECTION_CHECK_INTERVAL = int(os.getenv('CONNECTION_CHECK_INTERVAL', 30))
    CONNECTION_RETRY_ATTEMPTS = int(os.getenv('CONNECTION_RETRY_ATTEMPTS', 3))
    
    # Configurazioni Logging
    LOG_DIRECTORY = os.getenv('LOG_DIRECTORY', 'logs')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 30))
    ENABLE_CONSOLE_LOG = os.getenv('ENABLE_CONSOLE_LOG', 'False').lower() == 'true'
    
    @classmethod
    def get_mqtt_topic(cls, action="badge"):
        """Genera il topic MQTT"""
        return f"gate/{cls.TORNELLO_ID}/{action}"
    
    @classmethod
    def get_auth_response_topic(cls):
        """Genera il topic per le risposte di autenticazione"""
        return f"gate/{cls.TORNELLO_ID}/{cls.AUTH_TOPIC_SUFFIX}"
    
    @classmethod
    def validate_config(cls):
        """Valida la configurazione"""
        errors = []
        
        if not cls.MQTT_BROKER:
            errors.append("MQTT_BROKER non configurato")
        
        if not cls.MQTT_USERNAME:
            errors.append("MQTT_USERNAME non configurato")
        
        if not cls.MQTT_PASSWORD:
            errors.append("MQTT_PASSWORD non configurato")
        
        if not cls.TORNELLO_ID:
            errors.append("TORNELLO_ID non configurato")
        
        # Validazione configurazione RFID
        if cls.RFID_IN_ENABLE and cls.RFID_OUT_ENABLE and cls.RFID_IN_SDA_PIN == cls.RFID_OUT_SDA_PIN:
            errors.append("RFID_IN_SDA_PIN e RFID_OUT_SDA_PIN non possono essere uguali")
        
        # Validazione configurazione Relè
        if cls.RELAY_IN_ENABLE and cls.RELAY_OUT_ENABLE and cls.RELAY_IN_PIN == cls.RELAY_OUT_PIN:
            errors.append("RELAY_IN_PIN e RELAY_OUT_PIN non possono essere uguali")
        
        # Validazione stati iniziali
        for state_name, state_value in [
            ('RELAY_IN_INITIAL_STATE', cls.RELAY_IN_INITIAL_STATE),
            ('RELAY_OUT_INITIAL_STATE', cls.RELAY_OUT_INITIAL_STATE)
        ]:
            if state_value not in ['HIGH', 'LOW']:
                errors.append(f"{state_name} deve essere HIGH o LOW: {state_value}")
        
        # Validazione PIN ranges
        for pin_name, pin_value in [
            ('RELAY_IN_PIN', cls.RELAY_IN_PIN),
            ('RELAY_OUT_PIN', cls.RELAY_OUT_PIN),
            ('RFID_IN_RST_PIN', cls.RFID_IN_RST_PIN),
            ('RFID_OUT_RST_PIN', cls.RFID_OUT_RST_PIN),
            ('RFID_IN_SDA_PIN', cls.RFID_IN_SDA_PIN),
            ('RFID_OUT_SDA_PIN', cls.RFID_OUT_SDA_PIN)
        ]:
            if pin_value < 1 or pin_value > 40:
                errors.append(f"{pin_name} non valido: {pin_value}")
        
        # Validazione logica del sistema
        if not cls.RFID_IN_ENABLE and not cls.RFID_OUT_ENABLE:
            errors.append("Almeno un lettore RFID deve essere abilitato")
        
        if not cls.RELAY_IN_ENABLE and not cls.RELAY_OUT_ENABLE:
            errors.append("Almeno un relè deve essere abilitato")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Stampa la configurazione attuale (senza password)"""
        print("📋 Configurazione attuale:")
        print(f"   🌐 MQTT Broker: {cls.MQTT_BROKER}:{cls.MQTT_PORT}")
        print(f"   🔐 TLS: {'Attivo' if cls.MQTT_USE_TLS else 'Disattivo'}")
        print(f"   👤 Username: {cls.MQTT_USERNAME}")
        print(f"   🔑 Password: {'*' * len(cls.MQTT_PASSWORD)}")
        print(f"   🏷️  Tornello: {cls.TORNELLO_ID}")
        print(f"   🔄 Modalità bidirezionale: {'Attiva' if cls.BIDIRECTIONAL_MODE else 'Disattiva'}")
        
        # Configurazione RFID
        print(f"   📖 RFID IN: {'Attivo' if cls.RFID_IN_ENABLE else 'Disattivo'}")
        if cls.RFID_IN_ENABLE:
            print(f"      └─ RST: GPIO {cls.RFID_IN_RST_PIN}, SDA: GPIO {cls.RFID_IN_SDA_PIN}")
        
        if cls.BIDIRECTIONAL_MODE:
            print(f"   📖 RFID OUT: {'Attivo' if cls.RFID_OUT_ENABLE else 'Disattivo'}")
            if cls.RFID_OUT_ENABLE:
                print(f"      └─ RST: GPIO {cls.RFID_OUT_RST_PIN}, SDA: GPIO {cls.RFID_OUT_SDA_PIN}")
        
        # Configurazione Relè
        print(f"   ⚡ Relè IN: {'Attivo' if cls.RELAY_IN_ENABLE else 'Disattivo'}")
        if cls.RELAY_IN_ENABLE:
            logic = "Attivo LOW" if cls.RELAY_IN_ACTIVE_LOW else "Attivo HIGH"
            print(f"      └─ GPIO {cls.RELAY_IN_PIN}, Durata: {cls.RELAY_IN_ACTIVE_TIME}s")
            print(f"      └─ Logica: {logic}, Iniziale: {cls.RELAY_IN_INITIAL_STATE}")
        
        if cls.BIDIRECTIONAL_MODE:
            print(f"   ⚡ Relè OUT: {'Attivo' if cls.RELAY_OUT_ENABLE else 'Disattivo'}")
            if cls.RELAY_OUT_ENABLE:
                logic = "Attivo LOW" if cls.RELAY_OUT_ACTIVE_LOW else "Attivo HIGH"
                print(f"      └─ GPIO {cls.RELAY_OUT_PIN}, Durata: {cls.RELAY_OUT_ACTIVE_TIME}s")
                print(f"      └─ Logica: {logic}, Iniziale: {cls.RELAY_OUT_INITIAL_STATE}")
        
        print(f"   🔐 Autenticazione: {'Attiva' if cls.AUTH_ENABLED else 'Disattiva'}")
        if cls.AUTH_ENABLED:
            print(f"      └─ Timeout: {cls.AUTH_TIMEOUT}s")
        
        # Configurazione Offline
        print(f"   🌐 Fallback Offline: {'Attivo' if cls.OFFLINE_MODE_ENABLED else 'Disattivo'}")
        if cls.OFFLINE_MODE_ENABLED:
            print(f"      └─ Accesso offline: {'Consentito' if cls.OFFLINE_ALLOW_ACCESS else 'Negato'}")
            print(f"      └─ Sync automatica: {'Attiva' if cls.OFFLINE_SYNC_ENABLED else 'Disattiva'}")
            print(f"      └─ Max coda: {cls.OFFLINE_MAX_QUEUE_SIZE} elementi")
        
        print(f"   📝 Log Directory: {cls.LOG_DIRECTORY}")
        print(f"   📍 Topic badge: {cls.get_mqtt_topic()}")
        if cls.AUTH_ENABLED:
            print(f"   📍 Topic auth: {cls.get_auth_response_topic()}")