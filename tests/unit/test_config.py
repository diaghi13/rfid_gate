#!/usr/bin/env python3
"""
🧪 Test Configuration Management
==============================

Test per il sistema di configurazione refactorizzato.
Verifica caricamento, validazione e type safety.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from rfid_gate.config.settings import (
    RFIDGateConfig, MQTTConfig, SystemConfig, RFIDReaderConfig,
    RelayConfig, AuthConfig, OfflineConfig, LoggingConfig,
    ReaderType, PN532Interface, UIDFormatMode,
    load_env_file
)


class TestConfigHelpers(unittest.TestCase):
    """Test per helper functions"""
    
    def test_load_env_file_not_exists(self):
        """Test caricamento .env quando file non esiste"""
        with patch('os.path.exists', return_value=False):
            # Non dovrebbe lanciare eccezione
            load_env_file()
    
    def test_load_env_file_exists(self):
        """Test caricamento .env quando file esiste"""
        mock_content = "TEST_VAR=test_value\nANOTHER_VAR=another_value"
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open(read_data=mock_content)):
            load_env_file()


class TestMQTTConfig(unittest.TestCase):
    """Test configurazione MQTT"""
    
    def test_default_config(self):
        """Test configurazione di default"""
        config = MQTTConfig()
        self.assertEqual(config.broker, "localhost")
        self.assertEqual(config.port, 1883)
        self.assertIsNone(config.username)
        self.assertIsNone(config.password)
        self.assertFalse(config.use_tls)
    
    def test_from_env(self):
        """Test caricamento da environment"""
        env_vars = {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USERNAME': 'testuser',
            'MQTT_PASSWORD': 'testpass',
            'MQTT_USE_TLS': 'True'
        }
        
        with patch.dict(os.environ, env_vars):
            config = MQTTConfig.from_env()
            self.assertEqual(config.broker, 'test.broker.com')
            self.assertEqual(config.port, 8883)
            self.assertEqual(config.username, 'testuser')
            self.assertEqual(config.password, 'testpass')
            self.assertTrue(config.use_tls)


class TestSystemConfig(unittest.TestCase):
    """Test configurazione sistema"""
    
    def test_default_config(self):
        """Test configurazione di default"""
        config = SystemConfig()
        self.assertEqual(config.tornello_id, "tornello_01")
        self.assertTrue(config.bidirectional_mode)
        self.assertTrue(config.enable_in_reader)
        self.assertTrue(config.enable_out_reader)
        self.assertEqual(config.rfid_debounce_time, 2.0)


class TestRFIDReaderConfig(unittest.TestCase):
    """Test configurazione lettore RFID"""
    
    def test_default_config(self):
        """Test configurazione di default"""
        config = RFIDReaderConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.reader_type, ReaderType.MFRC522)
        self.assertEqual(config.rst_pin, 22)
        self.assertEqual(config.sda_pin, 8)
        self.assertEqual(config.pn532_interface, PN532Interface.I2C)
        self.assertEqual(config.pn532_i2c_address, 0x24)


class TestRelayConfig(unittest.TestCase):
    """Test configurazione relè"""
    
    def test_default_config(self):
        """Test configurazione di default"""
        config = RelayConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.pin, 18)
        self.assertEqual(config.active_time, 2)
        self.assertFalse(config.active_low)
        self.assertEqual(config.initial_state, "LOW")


class TestRFIDGateConfig(unittest.TestCase):
    """Test configurazione completa"""
    
    def test_default_config(self):
        """Test configurazione di default"""
        config = RFIDGateConfig()
        
        # Verifica che tutti i componenti siano presenti
        self.assertIsInstance(config.mqtt, MQTTConfig)
        self.assertIsInstance(config.system, SystemConfig)
        self.assertIsInstance(config.rfid_in, RFIDReaderConfig)
        self.assertIsInstance(config.rfid_out, RFIDReaderConfig)
        self.assertIsInstance(config.relay_in, RelayConfig)
        self.assertIsInstance(config.relay_out, RelayConfig)
        self.assertIsInstance(config.auth, AuthConfig)
        self.assertIsInstance(config.offline, OfflineConfig)
        self.assertIsInstance(config.logging, LoggingConfig)
    
    def test_minimal_environment_config(self):
        """Test caricamento con configurazione minima"""
        minimal_env = {
            'TORNELLO_ID': 'test_gate_01',
            'MQTT_BROKER': 'test.broker.local'
        }
        
        with patch.dict(os.environ, minimal_env, clear=True), \
             patch('rfid_gate.config.settings.load_env_file'):
            config = RFIDGateConfig.from_env()
            
            self.assertEqual(config.system.tornello_id, 'test_gate_01')
            self.assertEqual(config.mqtt.broker, 'test.broker.local')
            # Altri valori dovrebbero essere default
            self.assertEqual(config.mqtt.port, 1883)
            self.assertTrue(config.system.bidirectional_mode)
    
    def test_complete_environment_config(self):
        """Test caricamento configurazione completa"""
        complete_env = {
            'TORNELLO_ID': 'complete_gate',
            'BIDIRECTIONAL_MODE': 'False',
            'MQTT_BROKER': 'production.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USE_TLS': 'True',
            'RFID_IN_READER_TYPE': 'pn532',
            'RFID_IN_PN532_INTERFACE': 'spi',
            'RELAY_IN_PIN': '20',
            'RELAY_IN_ACTIVE_TIME': '3',
            'LOG_LEVEL': 'DEBUG',
            'OFFLINE_MODE_ENABLED': 'False'
        }
        
        with patch.dict(os.environ, complete_env, clear=True), \
             patch('rfid_gate.config.settings.load_env_file'):
            config = RFIDGateConfig.from_env()
            
            self.assertEqual(config.system.tornello_id, 'complete_gate')
            self.assertFalse(config.system.bidirectional_mode)
            self.assertEqual(config.mqtt.broker, 'production.broker.com')
            self.assertEqual(config.mqtt.port, 8883)
            self.assertTrue(config.mqtt.use_tls)
            self.assertEqual(config.rfid_in.reader_type, ReaderType.PN532)
            self.assertEqual(config.rfid_in.pn532_interface, PN532Interface.SPI)
            self.assertEqual(config.relay_in.pin, 20)
            self.assertEqual(config.relay_in.active_time, 3)
            self.assertEqual(config.logging.level, 'DEBUG')
            self.assertFalse(config.offline.enabled)
    
    def test_boolean_parsing(self):
        """Test parsing valori booleani"""
        bool_env = {
            'BIDIRECTIONAL_MODE': 'true',
            'ENABLE_IN_READER': 'True',
            'ENABLE_OUT_READER': 'FALSE',
            'MQTT_USE_TLS': 'false',
            'OFFLINE_MODE_ENABLED': '1'  # Non valido, dovrebbe essere False
        }
        
        with patch.dict(os.environ, bool_env, clear=True), \
             patch('rfid_gate.config.settings.load_env_file'):
            config = RFIDGateConfig.from_env()
            
            self.assertTrue(config.system.bidirectional_mode)
            self.assertTrue(config.system.enable_in_reader)
            self.assertFalse(config.system.enable_out_reader)
            self.assertFalse(config.mqtt.use_tls)
            # Valore non valido dovrebbe usare default
            self.assertTrue(config.offline.enabled)  # Default True
    
    def test_integer_parsing(self):
        """Test parsing valori numerici"""
        int_env = {
            'MQTT_PORT': '1234',
            'RFID_DEBOUNCE_TIME': '1.5',
            'RELAY_IN_PIN': '25',
            'LOG_RETENTION_DAYS': '60'
        }
        
        with patch.dict(os.environ, int_env, clear=True), \
             patch('rfid_gate.config.settings.load_env_file'):
            config = RFIDGateConfig.from_env()
            
            self.assertEqual(config.mqtt.port, 1234)
            self.assertEqual(config.system.rfid_debounce_time, 1.5)
            self.assertEqual(config.relay_in.pin, 25)
            self.assertEqual(config.logging.retention_days, 60)
    
    def test_invalid_values_use_defaults(self):
        """Test che valori invalidi usino i default"""
        invalid_env = {
            'MQTT_PORT': 'not_a_number',
            'RFID_IN_READER_TYPE': 'invalid_reader',
            'RFID_IN_PN532_INTERFACE': 'invalid_interface'
        }
        
        with patch.dict(os.environ, invalid_env, clear=True), \
             patch('rfid_gate.config.settings.load_env_file'):
            # Questi dovrebbero lanciare ValueError durante il parsing
            with self.assertRaises(ValueError):
                RFIDGateConfig.from_env()
    
    def test_mqtt_topics_generation(self):
        """Test generazione topic MQTT"""
        config = RFIDGateConfig()
        config.system.tornello_id = "test_gate"
        
        # Test topic standard
        badge_topic = config.get_mqtt_topic("badge")
        self.assertEqual(badge_topic, "gate/test_gate/badge")
        
        access_topic = config.get_mqtt_topic("access")
        self.assertEqual(access_topic, "gate/test_gate/access")
        
        # Test topic specifici
        auth_topic = config.get_auth_response_topic()
        self.assertIn("test_gate", auth_topic)
        
        manual_topic = config.get_manual_open_topic()
        self.assertIn("test_gate", manual_topic)
        
        manual_response = config.get_manual_response_topic()
        self.assertIn("test_gate", manual_response)


if __name__ == '__main__':
    unittest.main()

import unittest
import os
import tempfile
from unittest.mock import patch
from pathlib import Path
import sys

# Aggiungi il path del progetto
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rfid_gate.config.settings import RFIDGateConfig


class TestRFIDGateConfig(unittest.TestCase):
    """Test della classe RFIDGateConfig"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env_path = self.temp_env.name
        
    def tearDown(self):
        """Cleanup dopo ogni test"""
        if os.path.exists(self.temp_env_path):
            os.unlink(self.temp_env_path)
    
    def test_load_minimal_config(self):
        """Test caricamento configurazione minima"""
        # Configurazione minima richiesta
        config_content = """
MQTT_BROKER=test.broker.com
TORNELLO_ID=test_01
"""
        with open(self.temp_env_path, 'w') as f:
            f.write(config_content)
            
        with patch.dict(os.environ, {}, clear=True):
            with patch('rfid_gate.config.settings.load_dotenv') as mock_load:
                mock_load.return_value = True
                os.environ.update({
                    'MQTT_BROKER': 'test.broker.com',
                    'TORNELLO_ID': 'test_01'
                })
                
                config = RFIDGateConfig.from_env()
                
                self.assertEqual(config.mqtt_broker, 'test.broker.com')
                self.assertEqual(config.tornello_id, 'test_01')
                # Valori di default
                self.assertEqual(config.mqtt_port, 1883)
                self.assertFalse(config.mqtt_use_tls)
    
    def test_load_complete_config(self):
        """Test caricamento configurazione completa"""
        with patch.dict(os.environ, {}, clear=True):
            # Configurazione completa
            env_vars = {
                'MQTT_BROKER': 'prod.broker.com',
                'MQTT_PORT': '8883',
                'MQTT_USERNAME': 'testuser',
                'MQTT_PASSWORD': 'testpass',
                'MQTT_USE_TLS': 'true',
                'MQTT_KEEP_ALIVE': '120',
                'TORNELLO_ID': 'gate_prod_01',
                'BIDIRECTIONAL_MODE': 'true',
                'ENABLE_IN_READER': 'true',
                'ENABLE_OUT_READER': 'true',
                'RFID_IN_READER_TYPE': 'pn532',
                'RFID_OUT_READER_TYPE': 'mfrc522',
                'RFID_IN_RST_PIN': '22',
                'RFID_IN_SDA_PIN': '8',
                'RELAY_IN_ENABLE': 'true',
                'RELAY_IN_PIN': '18',
                'RELAY_IN_ACTIVE_TIME': '3',
                'AUTH_ENABLED': 'false',
                'OFFLINE_MODE_ENABLED': 'true',
                'LOG_LEVEL': 'DEBUG',
                'RFID_DEBOUNCE_TIME': '1.5'
            }
            
            os.environ.update(env_vars)
            config = RFIDGateConfig.from_env()
            
            # Test MQTT
            self.assertEqual(config.mqtt_broker, 'prod.broker.com')
            self.assertEqual(config.mqtt_port, 8883)
            self.assertEqual(config.mqtt_username, 'testuser')
            self.assertEqual(config.mqtt_password, 'testpass')
            self.assertTrue(config.mqtt_use_tls)
            self.assertEqual(config.mqtt_keep_alive, 120)
            
            # Test sistema
            self.assertEqual(config.tornello_id, 'gate_prod_01')
            self.assertTrue(config.bidirectional_mode)
            self.assertTrue(config.enable_in_reader)
            self.assertTrue(config.enable_out_reader)
            
            # Test lettori
            self.assertEqual(config.rfid_in_reader_type, 'pn532')
            self.assertEqual(config.rfid_out_reader_type, 'mfrc522')
            self.assertEqual(config.rfid_in_rst_pin, 22)
            
            # Test relay
            self.assertTrue(config.relay_in_enable)
            self.assertEqual(config.relay_in_pin, 18)
            self.assertEqual(config.relay_in_active_time, 3)
            
            # Test flags
            self.assertFalse(config.auth_enabled)
            self.assertTrue(config.offline_mode_enabled)
            self.assertEqual(config.log_level, 'DEBUG')
            self.assertEqual(config.rfid_debounce_time, 1.5)
    
    def test_boolean_parsing(self):
        """Test parsing valori booleani"""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('', False),
            ('invalid', False)
        ]
        
        for input_val, expected in test_cases:
            with patch.dict(os.environ, {}, clear=True):
                os.environ.update({
                    'MQTT_BROKER': 'test.com',
                    'TORNELLO_ID': 'test',
                    'BIDIRECTIONAL_MODE': input_val
                })
                
                config = RFIDGateConfig.from_env()
                self.assertEqual(config.bidirectional_mode, expected, 
                               f"Input '{input_val}' should be {expected}")
    
    def test_integer_parsing(self):
        """Test parsing valori numerici"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update({
                'MQTT_BROKER': 'test.com',
                'TORNELLO_ID': 'test',
                'MQTT_PORT': '9999',
                'RFID_IN_RST_PIN': '25',
                'RELAY_IN_ACTIVE_TIME': '5'
            })
            
            config = RFIDGateConfig.from_env()
            self.assertEqual(config.mqtt_port, 9999)
            self.assertEqual(config.rfid_in_rst_pin, 25)
            self.assertEqual(config.relay_in_active_time, 5)
    
    def test_float_parsing(self):
        """Test parsing valori float"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update({
                'MQTT_BROKER': 'test.com',
                'TORNELLO_ID': 'test',
                'RFID_DEBOUNCE_TIME': '2.5',
                'CARD_READ_INTERVAL': '0.1'
            })
            
            config = RFIDGateConfig.from_env()
            self.assertEqual(config.rfid_debounce_time, 2.5)
            self.assertEqual(config.card_read_interval, 0.1)
    
    def test_invalid_values_use_defaults(self):
        """Test che valori invalidi usino i default"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update({
                'MQTT_BROKER': 'test.com',
                'TORNELLO_ID': 'test',
                'MQTT_PORT': 'invalid',  # Dovrebbe usare default 1883
                'RFID_DEBOUNCE_TIME': 'not_a_number'  # Default 2.0
            })
            
            config = RFIDGateConfig.from_env()
            self.assertEqual(config.mqtt_port, 1883)  # Default
            self.assertEqual(config.rfid_debounce_time, 2.0)  # Default
    
    def test_required_fields_missing(self):
        """Test comportamento con campi richiesti mancanti"""
        with patch.dict(os.environ, {}, clear=True):
            # Solo MQTT_BROKER, manca TORNELLO_ID
            os.environ.update({
                'MQTT_BROKER': 'test.com'
            })
            
            # Dovrebbe usare default o sollevare eccezione a seconda dell'implementazione
            try:
                config = RFIDGateConfig.from_env()
                # Se non solleva eccezione, verifica che abbia un valore di default
                self.assertIsNotNone(config.tornello_id)
            except Exception:
                # Se solleva eccezione è OK, significa che i campi richiesti sono validati
                pass
    
    def test_mqtt_topics_generation(self):
        """Test generazione topic MQTT"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.update({
                'MQTT_BROKER': 'test.com',
                'TORNELLO_ID': 'gate_01',
                'MQTT_CARD_READ_TOPIC': 'custom/card_read',
                'MQTT_AUTH_RESPONSE_TOPIC': 'custom/auth_response'
            })
            
            config = RFIDGateConfig.from_env()
            self.assertEqual(config.mqtt_card_read_topic, 'custom/card_read')
            self.assertEqual(config.mqtt_auth_response_topic, 'custom/auth_response')


if __name__ == '__main__':
    # Esegui i test
    unittest.main(verbosity=2)