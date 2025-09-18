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
    DIREZIONE = os.getenv('DIREZIONE', 'in')
    
    # Configurazioni Autenticazione
    AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'True').lower() == 'true'
    AUTH_TIMEOUT = int(os.getenv('AUTH_TIMEOUT', 5))
    AUTH_TOPIC_SUFFIX = os.getenv('AUTH_TOPIC_SUFFIX', 'auth_response')
    
    # Configurazioni Relè
    RELAY_PIN = int(os.getenv('RELAY_PIN', 18))
    RELAY_ACTIVE_TIME = int(os.getenv('RELAY_ACTIVE_TIME', 2))
    RELAY_ACTIVE_LOW = os.getenv('RELAY_ACTIVE_LOW', 'False').lower() == 'true'
    RELAY_INITIAL_STATE = os.getenv('RELAY_INITIAL_STATE', 'LOW').upper()
    
    # Configurazioni RFID
    RFID_RST_PIN = int(os.getenv('RFID_RST_PIN', 22))
    RFID_SDA_PIN = int(os.getenv('RFID_SDA_PIN', 8))
    
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
        
        if cls.RELAY_PIN < 1 or cls.RELAY_PIN > 40:
            errors.append(f"RELAY_PIN non valido: {cls.RELAY_PIN}")
        
        if cls.RELAY_INITIAL_STATE not in ['HIGH', 'LOW']:
            errors.append(f"RELAY_INITIAL_STATE deve essere HIGH o LOW: {cls.RELAY_INITIAL_STATE}")
        
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
        print(f"   ➡️  Direzione: {cls.DIREZIONE}")
        print(f"   🔐 Autenticazione: {'Attiva' if cls.AUTH_ENABLED else 'Disattiva'}")
        if cls.AUTH_ENABLED:
            print(f"   ⏱️  Timeout auth: {cls.AUTH_TIMEOUT}s")
        print(f"   ⚡ Relè GPIO: {cls.RELAY_PIN}")
        print(f"   ⏱️  Durata relè: {cls.RELAY_ACTIVE_TIME}s")
        print(f"   🔧 Logica relè: {'Attivo LOW' if cls.RELAY_ACTIVE_LOW else 'Attivo HIGH'}")
        print(f"   🔄 Stato iniziale: {cls.RELAY_INITIAL_STATE}")
        print(f"   📍 Topic badge: {cls.get_mqtt_topic()}")
        if cls.AUTH_ENABLED:
            print(f"   📍 Topic auth: {cls.get_auth_response_topic()}")