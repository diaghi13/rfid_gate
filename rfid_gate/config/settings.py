#!/usr/bin/env python3
"""
🔧 RFID Gate Configuration - Type-Safe Settings
==============================================

Sistema di configurazione moderno con validazione e type safety.
Mantiene compatibilità totale con il sistema esistente.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ReaderType(str, Enum):
    """Tipi di lettori RFID supportati"""
    MFRC522 = "mfrc522"
    PN532 = "pn532"


class PN532Interface(str, Enum):
    """Interfacce PN532 supportate"""
    I2C = "i2c"
    SPI = "spi" 
    UART = "uart"


class UIDFormatMode(str, Enum):
    """Modalità formattazione UID"""
    REMOVE_SUFFIX = "remove_suffix"
    FIXED_LENGTH = "fixed_length"
    RAW = "raw"


def load_env_file() -> None:
    """
    Carica file .env manualmente senza dipendenza dotenv
    Mantiene compatibilità con implementazione esistente
    """
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
                
                # Rimuovi commenti inline
                if '#' in value:
                    value = value.split('#')[0].strip()
                
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


@dataclass
class MQTTConfig:
    """Configurazione MQTT"""
    broker: str = "mqbrk.ddns.net"
    port: int = 8883
    username: str = "palestraUser"
    password: str = "28dade03$"
    use_tls: bool = True
    keep_alive: int = 60
    
    # Topics
    card_read_topic: str = "rfid_gate/card_read"
    auth_response_topic: str = "rfid_gate/auth_response"
    manual_open_topic: str = "rfid_gate/manual_open"
    
    @classmethod
    def from_env(cls) -> 'MQTTConfig':
        """Crea configurazione da variabili ambiente"""
        return cls(
            broker=os.getenv('MQTT_BROKER', cls.broker),
            port=int(os.getenv('MQTT_PORT', cls.port)),
            username=os.getenv('MQTT_USERNAME', cls.username),
            password=os.getenv('MQTT_PASSWORD', cls.password),
            use_tls=os.getenv('MQTT_USE_TLS', 'True').lower() == 'true',
            keep_alive=int(os.getenv('MQTT_KEEP_ALIVE', cls.keep_alive)),
            card_read_topic=os.getenv('MQTT_CARD_READ_TOPIC', cls.card_read_topic),
            auth_response_topic=os.getenv('MQTT_AUTH_RESPONSE_TOPIC', cls.auth_response_topic),
            manual_open_topic=os.getenv('MQTT_MANUAL_OPEN_TOPIC', cls.manual_open_topic)
        )


@dataclass 
class RFIDReaderConfig:
    """Configurazione singolo lettore RFID"""
    enabled: bool = True
    reader_type: ReaderType = ReaderType.MFRC522
    
    # MFRC522 pins
    rst_pin: int = 22
    sda_pin: int = 8
    
    # PN532 configuration
    pn532_interface: PN532Interface = PN532Interface.I2C
    pn532_i2c_address: int = 0x24
    pn532_spi_bus: int = 0
    pn532_spi_device: int = 0
    pn532_uart_port: str = "/dev/serial0"
    pn532_uart_baudrate: int = 115200


@dataclass
class RelayConfig:
    """Configurazione singolo relè"""
    enabled: bool = True
    pin: int = 18
    active_time: int = 2
    active_low: bool = False
    initial_state: str = "LOW"


@dataclass
class SystemConfig:
    """Configurazione generale sistema"""
    tornello_id: str = "tornello_01"
    bidirectional_mode: bool = True
    enable_in_reader: bool = True
    enable_out_reader: bool = True
    
    # Timing
    rfid_debounce_time: float = 2.0
    card_read_interval: float = 0.15
    global_debounce_time: float = 0.8
    
    # Bidirectional Control
    bidirectional_timeout_hours: float = 24.0  # Reset stato dopo 24 ore
    
    # UID Formatting
    uid_format_mode: UIDFormatMode = UIDFormatMode.REMOVE_SUFFIX
    uid_chars_count: int = 2
    uid_target_length: int = 8
    uid_debug_mode: bool = True


@dataclass
class AuthConfig:
    """Configurazione autenticazione"""
    enabled: bool = True
    timeout: int = 5
    topic_suffix: str = "auth_response"
    
    # Manual open
    manual_open_enabled: bool = True
    manual_open_topic_suffix: str = "manual_open"
    manual_open_response_topic_suffix: str = "manual_response"
    manual_open_timeout: int = 10
    manual_open_auth_required: bool = True


@dataclass
class OfflineConfig:
    """Configurazione modalità offline"""
    enabled: bool = True
    allow_access: bool = True
    sync_enabled: bool = True
    storage_file: str = "offline_queue.json"
    max_queue_size: int = 1000
    connection_check_interval: int = 30
    connection_retry_attempts: int = 3


@dataclass
class SyncConfig:
    """Configurazione sistema di sincronizzazione"""
    enabled: bool = True
    server_url: str = "http://localhost:3000"
    sync_endpoint: str = "/api/sync"
    logs_endpoint: str = "/api/logs/bulk"
    health_endpoint: str = "/api/health"
    updates_endpoint: str = "/api/cards/updates"
    
    # Timing
    daily_sync_time: str = "06:00"
    updates_check_interval: int = 15  # minuti
    logs_sync_interval: int = 5  # minuti
    connection_timeout: int = 30  # secondi
    
    # Database
    cache_db_path: str = "cache/local_cache.db"
    max_pending_logs: int = 1000
    
    # Retry logic
    max_retries: int = 3
    retry_delay: int = 5  # secondi


@dataclass
class LoggingConfig:
    """Configurazione logging"""
    directory: str = "logs"
    level: str = "INFO"
    retention_days: int = 30
    enable_console_log: bool = False


@dataclass
class RFIDGateConfig:
    """
    Configurazione completa del sistema RFID Gate
    
    Mantiene compatibilità totale con la classe Config esistente
    ma aggiunge type safety e validazione moderna.
    """
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    rfid_in: RFIDReaderConfig = field(default_factory=RFIDReaderConfig)
    rfid_out: RFIDReaderConfig = field(default_factory=RFIDReaderConfig)
    relay_in: RelayConfig = field(default_factory=RelayConfig)
    relay_out: RelayConfig = field(default_factory=RelayConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    offline: OfflineConfig = field(default_factory=OfflineConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def from_env(cls) -> 'RFIDGateConfig':
        """Crea configurazione completa da variabili ambiente"""
        
        # Carica prima il file .env
        load_env_file()
        
        # MQTT Config
        mqtt = MQTTConfig.from_env()
        
        # System Config
        system = SystemConfig(
            tornello_id=os.getenv('TORNELLO_ID', 'tornello_01'),
            bidirectional_mode=os.getenv('BIDIRECTIONAL_MODE', 'True').lower() == 'true',
            enable_in_reader=os.getenv('ENABLE_IN_READER', 'True').lower() == 'true',
            enable_out_reader=os.getenv('ENABLE_OUT_READER', 'True').lower() == 'true',
            rfid_debounce_time=float(os.getenv('RFID_DEBOUNCE_TIME', '2.0')),
            card_read_interval=float(os.getenv('CARD_READ_INTERVAL', '0.15')),
            global_debounce_time=float(os.getenv('GLOBAL_DEBOUNCE_TIME', '0.8')),
            bidirectional_timeout_hours=float(os.getenv('BIDIRECTIONAL_TIMEOUT_HOURS', '24.0')),
            uid_format_mode=UIDFormatMode(os.getenv('UID_FORMAT_MODE', 'remove_suffix')),
            uid_chars_count=int(os.getenv('UID_CHARS_COUNT', 2)),
            uid_target_length=int(os.getenv('UID_TARGET_LENGTH', 8)),
            uid_debug_mode=os.getenv('UID_DEBUG_MODE', 'True').lower() == 'true'
        )
        
        # RFID IN Config
        rfid_in = RFIDReaderConfig(
            enabled=os.getenv('RFID_IN_ENABLE', 'True').lower() == 'true',
            reader_type=ReaderType(os.getenv('RFID_IN_READER_TYPE', 'mfrc522')),
            rst_pin=int(os.getenv('RFID_IN_RST_PIN', 22)),
            sda_pin=int(os.getenv('RFID_IN_SDA_PIN', 8)),
            pn532_interface=PN532Interface(os.getenv('RFID_IN_PN532_INTERFACE', 'i2c')),
            pn532_i2c_address=int(os.getenv('RFID_IN_PN532_I2C_ADDRESS', '0x24'), 16),
            pn532_spi_bus=int(os.getenv('RFID_IN_PN532_SPI_BUS', '0')),
            pn532_spi_device=int(os.getenv('RFID_IN_PN532_SPI_DEVICE', '0')),
            pn532_uart_port=os.getenv('RFID_IN_PN532_UART_PORT', '/dev/serial0'),
            pn532_uart_baudrate=int(os.getenv('RFID_IN_PN532_UART_BAUDRATE', '115200'))
        )
        
        # RFID OUT Config
        rfid_out = RFIDReaderConfig(
            enabled=os.getenv('RFID_OUT_ENABLE', 'False').lower() == 'true',
            reader_type=ReaderType(os.getenv('RFID_OUT_READER_TYPE', 'mfrc522')),
            rst_pin=int(os.getenv('RFID_OUT_RST_PIN', 25)),
            sda_pin=int(os.getenv('RFID_OUT_SDA_PIN', 7)),
            pn532_interface=PN532Interface(os.getenv('RFID_OUT_PN532_INTERFACE', 'i2c')),
            pn532_i2c_address=int(os.getenv('RFID_OUT_PN532_I2C_ADDRESS', '0x25'), 16),
            pn532_spi_bus=int(os.getenv('RFID_OUT_PN532_SPI_BUS', '1')),
            pn532_spi_device=int(os.getenv('RFID_OUT_PN532_SPI_DEVICE', '0')),
            pn532_uart_port=os.getenv('RFID_OUT_PN532_UART_PORT', '/dev/serial1'),
            pn532_uart_baudrate=int(os.getenv('RFID_OUT_PN532_UART_BAUDRATE', '115200'))
        )
        
        # Relay IN Config
        relay_in = RelayConfig(
            enabled=os.getenv('RELAY_IN_ENABLE', 'True').lower() == 'true',
            pin=int(os.getenv('RELAY_IN_PIN', 18)),
            active_time=int(os.getenv('RELAY_IN_ACTIVE_TIME', 2)),
            active_low=os.getenv('RELAY_IN_ACTIVE_LOW', 'False').lower() == 'true',
            initial_state=os.getenv('RELAY_IN_INITIAL_STATE', 'LOW').upper()
        )
        
        # Relay OUT Config
        relay_out = RelayConfig(
            enabled=os.getenv('RELAY_OUT_ENABLE', 'False').lower() == 'true',
            pin=int(os.getenv('RELAY_OUT_PIN', 19)),
            active_time=int(os.getenv('RELAY_OUT_ACTIVE_TIME', 2)),
            active_low=os.getenv('RELAY_OUT_ACTIVE_LOW', 'False').lower() == 'true',
            initial_state=os.getenv('RELAY_OUT_INITIAL_STATE', 'LOW').upper()
        )
        
        # Auth Config
        auth = AuthConfig(
            enabled=os.getenv('AUTH_ENABLED', 'True').lower() == 'true',
            timeout=int(os.getenv('AUTH_TIMEOUT', 5)),
            topic_suffix=os.getenv('AUTH_TOPIC_SUFFIX', 'auth_response'),
            manual_open_enabled=os.getenv('MANUAL_OPEN_ENABLED', 'True').lower() == 'true',
            manual_open_topic_suffix=os.getenv('MANUAL_OPEN_TOPIC_SUFFIX', 'manual_open'),
            manual_open_response_topic_suffix=os.getenv('MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX', 'manual_response'),
            manual_open_timeout=int(os.getenv('MANUAL_OPEN_TIMEOUT', 10)),
            manual_open_auth_required=os.getenv('MANUAL_OPEN_AUTH_REQUIRED', 'True').lower() == 'true'
        )
        
        # Offline Config
        offline = OfflineConfig(
            enabled=os.getenv('OFFLINE_MODE_ENABLED', 'True').lower() == 'true',
            allow_access=os.getenv('OFFLINE_ALLOW_ACCESS', 'True').lower() == 'true',
            sync_enabled=os.getenv('OFFLINE_SYNC_ENABLED', 'True').lower() == 'true',
            storage_file=os.getenv('OFFLINE_STORAGE_FILE', 'offline_queue.json'),
            max_queue_size=int(os.getenv('OFFLINE_MAX_QUEUE_SIZE', 1000)),
            connection_check_interval=int(os.getenv('CONNECTION_CHECK_INTERVAL', 30)),
            connection_retry_attempts=int(os.getenv('CONNECTION_RETRY_ATTEMPTS', 3))
        )
        
        # Logging Config
        logging_config = LoggingConfig(
            directory=os.getenv('LOG_DIRECTORY', 'logs'),
            level=os.getenv('LOG_LEVEL', 'INFO'),
            retention_days=int(os.getenv('LOG_RETENTION_DAYS', 30)),
            enable_console_log=os.getenv('ENABLE_CONSOLE_LOG', 'False').lower() == 'true'
        )
        
        # Sync Config
        sync = SyncConfig(
            enabled=os.getenv('SYNC_ENABLED', 'True').lower() == 'true',
            server_url=os.getenv('SYNC_SERVER_URL', 'http://localhost:3000'),
            sync_endpoint=os.getenv('SYNC_ENDPOINT', '/api/sync'),
            logs_endpoint=os.getenv('SYNC_LOGS_ENDPOINT', '/api/logs/bulk'),
            health_endpoint=os.getenv('SYNC_HEALTH_ENDPOINT', '/api/health'),
            updates_endpoint=os.getenv('SYNC_UPDATES_ENDPOINT', '/api/cards/updates'),
            daily_sync_time=os.getenv('SYNC_DAILY_TIME', '06:00'),
            updates_check_interval=int(os.getenv('SYNC_UPDATES_INTERVAL', 15)),
            logs_sync_interval=int(os.getenv('SYNC_LOGS_INTERVAL', 5)),
            connection_timeout=int(os.getenv('SYNC_CONNECTION_TIMEOUT', 30)),
            cache_db_path=os.getenv('SYNC_CACHE_DB_PATH', 'cache/local_cache.db'),
            max_pending_logs=int(os.getenv('SYNC_MAX_PENDING_LOGS', 1000)),
            max_retries=int(os.getenv('SYNC_MAX_RETRIES', 3)),
            retry_delay=int(os.getenv('SYNC_RETRY_DELAY', 5))
        )
        
        return cls(
            mqtt=mqtt,
            system=system,
            rfid_in=rfid_in,
            rfid_out=rfid_out,
            relay_in=relay_in,
            relay_out=relay_out,
            auth=auth,
            offline=offline,
            sync=sync,
            logging=logging_config
        )
    
    def get_mqtt_topic(self, action: str = "badge") -> str:
        """Genera topic MQTT per azione specifica"""
        return f"gate/{self.system.tornello_id}/{action}"
    
    def get_auth_response_topic(self) -> str:
        """Topic per risposta autenticazione"""
        return f"gate/{self.system.tornello_id}/{self.auth.topic_suffix}"
    
    def get_manual_open_topic(self) -> str:
        """Topic per apertura manuale"""
        return f"gate/{self.system.tornello_id}/{self.auth.manual_open_topic_suffix}"
    
    def get_manual_response_topic(self) -> str:
        """Topic per risposta apertura manuale"""
        return f"gate/{self.system.tornello_id}/{self.auth.manual_open_response_topic_suffix}"
    
    def validate(self) -> List[str]:
        """Validazione configurazione completa"""
        errors = []
        
        # Validazione MQTT
        if not self.mqtt.broker:
            errors.append("MQTT_BROKER richiesto")
        if not (1 <= self.mqtt.port <= 65535):
            errors.append("MQTT_PORT deve essere tra 1 e 65535")
        
        # Validazione sistema
        if not self.system.tornello_id:
            errors.append("TORNELLO_ID richiesto")
        
        # Validazione lettori
        if not self.rfid_in.enabled and not self.rfid_out.enabled:
            errors.append("Almeno un lettore RFID deve essere abilitato")
        
        # Validazione relè
        if not self.relay_in.enabled and not self.relay_out.enabled:
            errors.append("Almeno un relè deve essere abilitato")
        
        # Validazione timing
        if self.system.rfid_debounce_time < 0:
            errors.append("RFID_DEBOUNCE_TIME deve essere >= 0")
        if self.system.card_read_interval < 0:
            errors.append("CARD_READ_INTERVAL deve essere >= 0")
        
        return errors


# 🔄 MANTIENI COMPATIBILITÀ CON CODICE ESISTENTE
# Crea istanza Config compatibile con il vecchio sistema
_config_instance = RFIDGateConfig.from_env()

class Config:
    """
    Wrapper per mantenere compatibilità totale con il codice esistente.
    Tutti gli attributi esistenti sono mappati alla nuova struttura.
    """
    
    # MQTT - Mappatura diretta
    MQTT_BROKER = _config_instance.mqtt.broker
    MQTT_PORT = _config_instance.mqtt.port
    MQTT_USERNAME = _config_instance.mqtt.username
    MQTT_PASSWORD = _config_instance.mqtt.password
    MQTT_USE_TLS = _config_instance.mqtt.use_tls
    
    # Tornello
    TORNELLO_ID = _config_instance.system.tornello_id
    
    # Sistema Bidirezionale
    BIDIRECTIONAL_MODE = _config_instance.system.bidirectional_mode
    ENABLE_IN_READER = _config_instance.system.enable_in_reader
    ENABLE_OUT_READER = _config_instance.system.enable_out_reader
    
    # RFID IN
    RFID_IN_RST_PIN = _config_instance.rfid_in.rst_pin
    RFID_IN_SDA_PIN = _config_instance.rfid_in.sda_pin
    RFID_IN_ENABLE = _config_instance.rfid_in.enabled
    
    # RFID OUT
    RFID_OUT_RST_PIN = _config_instance.rfid_out.rst_pin
    RFID_OUT_SDA_PIN = _config_instance.rfid_out.sda_pin
    RFID_OUT_ENABLE = _config_instance.rfid_out.enabled
    
    # Relè IN
    RELAY_IN_PIN = _config_instance.relay_in.pin
    RELAY_IN_ACTIVE_TIME = _config_instance.relay_in.active_time
    RELAY_IN_ACTIVE_LOW = _config_instance.relay_in.active_low
    RELAY_IN_INITIAL_STATE = _config_instance.relay_in.initial_state
    RELAY_IN_ENABLE = _config_instance.relay_in.enabled
    
    # Relè OUT
    RELAY_OUT_PIN = _config_instance.relay_out.pin
    RELAY_OUT_ACTIVE_TIME = _config_instance.relay_out.active_time
    RELAY_OUT_ACTIVE_LOW = _config_instance.relay_out.active_low
    RELAY_OUT_INITIAL_STATE = _config_instance.relay_out.initial_state
    RELAY_OUT_ENABLE = _config_instance.relay_out.enabled
    
    # Autenticazione
    AUTH_ENABLED = _config_instance.auth.enabled
    AUTH_TIMEOUT = _config_instance.auth.timeout
    AUTH_TOPIC_SUFFIX = _config_instance.auth.topic_suffix
    
    # Apertura Manuale
    MANUAL_OPEN_ENABLED = _config_instance.auth.manual_open_enabled
    MANUAL_OPEN_TOPIC_SUFFIX = _config_instance.auth.manual_open_topic_suffix
    MANUAL_OPEN_RESPONSE_TOPIC_SUFFIX = _config_instance.auth.manual_open_response_topic_suffix
    MANUAL_OPEN_TIMEOUT = _config_instance.auth.manual_open_timeout
    MANUAL_OPEN_AUTH_REQUIRED = _config_instance.auth.manual_open_auth_required
    
    # Offline
    OFFLINE_MODE_ENABLED = _config_instance.offline.enabled
    OFFLINE_ALLOW_ACCESS = _config_instance.offline.allow_access
    OFFLINE_SYNC_ENABLED = _config_instance.offline.sync_enabled
    OFFLINE_STORAGE_FILE = _config_instance.offline.storage_file
    OFFLINE_MAX_QUEUE_SIZE = _config_instance.offline.max_queue_size
    CONNECTION_CHECK_INTERVAL = _config_instance.offline.connection_check_interval
    CONNECTION_RETRY_ATTEMPTS = _config_instance.offline.connection_retry_attempts
    
    # Logging
    LOG_DIRECTORY = _config_instance.logging.directory
    LOG_LEVEL = _config_instance.logging.level
    LOG_RETENTION_DAYS = _config_instance.logging.retention_days
    ENABLE_CONSOLE_LOG = _config_instance.logging.enable_console_log
    
    # RFID Debounce
    RFID_DEBOUNCE_TIME = _config_instance.system.rfid_debounce_time
    
    # Card reading interval
    CARD_READ_INTERVAL = _config_instance.system.card_read_interval
    
    # Anti-crosstalk per dual readers
    GLOBAL_DEBOUNCE_TIME = _config_instance.system.global_debounce_time
    
    # RFID Reader Types
    RFID_IN_READER_TYPE = _config_instance.rfid_in.reader_type.value
    RFID_OUT_READER_TYPE = _config_instance.rfid_out.reader_type.value
    
    # PN532 Configuration IN
    RFID_IN_PN532_INTERFACE = _config_instance.rfid_in.pn532_interface.value
    RFID_IN_PN532_I2C_ADDRESS = _config_instance.rfid_in.pn532_i2c_address
    RFID_IN_PN532_SPI_BUS = _config_instance.rfid_in.pn532_spi_bus
    RFID_IN_PN532_SPI_DEVICE = _config_instance.rfid_in.pn532_spi_device
    RFID_IN_PN532_UART_PORT = _config_instance.rfid_in.pn532_uart_port
    RFID_IN_PN532_UART_BAUDRATE = _config_instance.rfid_in.pn532_uart_baudrate
    
    # PN532 Configuration OUT
    RFID_OUT_PN532_INTERFACE = _config_instance.rfid_out.pn532_interface.value
    RFID_OUT_PN532_I2C_ADDRESS = _config_instance.rfid_out.pn532_i2c_address
    RFID_OUT_PN532_SPI_BUS = _config_instance.rfid_out.pn532_spi_bus
    RFID_OUT_PN532_SPI_DEVICE = _config_instance.rfid_out.pn532_spi_device
    RFID_OUT_PN532_UART_PORT = _config_instance.rfid_out.pn532_uart_port
    RFID_OUT_PN532_UART_BAUDRATE = _config_instance.rfid_out.pn532_uart_baudrate
    
    # Configurazione formato UID
    UID_FORMAT_MODE = _config_instance.system.uid_format_mode.value
    UID_CHARS_COUNT = _config_instance.system.uid_chars_count
    UID_TARGET_LENGTH = _config_instance.system.uid_target_length
    UID_DEBUG_MODE = _config_instance.system.uid_debug_mode
    
    @classmethod
    def get_mqtt_topic(cls, action="badge"):
        """Mantiene compatibilità con il metodo esistente"""
        return _config_instance.get_mqtt_topic(action)
    
    @classmethod
    def get_auth_response_topic(cls):
        """Mantiene compatibilità con il metodo esistente"""
        return _config_instance.get_auth_response_topic()
    
    @classmethod
    def get_manual_open_topic(cls):
        """Mantiene compatibilità con il metodo esistente"""
        return _config_instance.get_manual_open_topic()
    
    @classmethod
    def get_manual_response_topic(cls):
        """Mantiene compatibilità con il metodo esistente"""
        return _config_instance.get_manual_response_topic()
    
    @classmethod
    def validate_config(cls):
        """Mantiene compatibilità con il metodo esistente"""
        return _config_instance.validate()


# Export per compatibilità
__all__ = [
    'Config',           # Classe compatibile esistente
    'RFIDGateConfig',   # Nuova classe type-safe
    'load_env_file',    # Funzione utile
    'ReaderType',       # Enum per i reader
    'PN532Interface',   # Enum per le interfacce
    'UIDFormatMode'     # Enum per i formati UID
]


# Test configurazione al caricamento
if __name__ == "__main__":
    print("🧪 Test nuova configurazione")
    print("=" * 40)
    
    # Test compatibilità
    print(f"Config.MQTT_BROKER: {Config.MQTT_BROKER}")
    print(f"Config.TORNELLO_ID: {Config.TORNELLO_ID}")
    print(f"Config.RELAY_IN_PIN: {Config.RELAY_IN_PIN}")
    
    # Test nuova struttura
    new_config = RFIDGateConfig.from_env()
    print(f"\nNuova struttura:")
    print(f"mqtt.broker: {new_config.mqtt.broker}")
    print(f"system.tornello_id: {new_config.system.tornello_id}")
    print(f"rfid_in.reader_type: {new_config.rfid_in.reader_type}")
    
    # Test validazione
    errors = Config.validate_config()
    if errors:
        print("\n❌ Errori:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configurazione OK")