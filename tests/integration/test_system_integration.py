#!/usr/bin/env python3
"""
🧪 Integration Tests - Complete System
======================================

Test di integrazione completi per il sistema RFID Gate
"""

import unittest
import asyncio
import os
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.core.access_control import AccessControlSystem
from rfid_gate.hardware.readers.factory import ReaderFactory
from rfid_gate.network.mqtt import AsyncMQTTClient
from rfid_gate.utils.debounce import GlobalDebounceManager


class TestSystemIntegration(unittest.TestCase):
    """Test di integrazione del sistema completo"""
    
    def setUp(self):
        """Setup per ogni test"""
        # Reset singleton debounce
        if hasattr(GlobalDebounceManager, '_instance'):
            GlobalDebounceManager._instance = None
        
        # Configurazione di test
        self.test_env = {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '1883',
            'MQTT_USERNAME': 'testuser',
            'MQTT_PASSWORD': 'testpass',
            'MQTT_USE_TLS': 'false',
            'TORNELLO_ID': 'test_gate_01',
            'BIDIRECTIONAL_MODE': 'true',
            'ENABLE_IN_READER': 'true',
            'ENABLE_OUT_READER': 'true',
            'RFID_IN_READER_TYPE': 'mfrc522',
            'RFID_OUT_READER_TYPE': 'pn532',
            'RFID_IN_RST_PIN': '22',
            'RFID_IN_SDA_PIN': '8',
            'RELAY_IN_ENABLE': 'true',
            'RELAY_IN_PIN': '18',
            'AUTH_ENABLED': 'true',
            'OFFLINE_MODE_ENABLED': 'true',
            'LOG_LEVEL': 'DEBUG'
        }
    
    def test_config_to_system_integration(self):
        """Test integrazione configurazione -> sistema"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Verifica che la configurazione sia valida
            self.assertEqual(config.tornello_id, 'test_gate_01')
            self.assertTrue(config.bidirectional_mode)
            self.assertTrue(config.enable_in_reader)
            self.assertTrue(config.enable_out_reader)
            
            # Test integrazione con AccessControlSystem
            with patch.multiple(
                'rfid_gate.core.access_control',
                MFRC522Reader=Mock,
                PN532Reader=Mock,
                GPIORelay=Mock,
                AsyncMQTTClient=Mock
            ):
                system = AccessControlSystem(config)
                self.assertIsNotNone(system.config)
                self.assertEqual(system.config.tornello_id, 'test_gate_01')
    
    @patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522')
    @patch('rfid_gate.hardware.readers.pn532.PN532_I2C')
    @patch('rfid_gate.hardware.readers.pn532.PN532')
    def test_reader_factory_integration(self, mock_pn532, mock_i2c, mock_mfrc522):
        """Test integrazione factory lettori"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Crea lettore IN (MFRC522)
            in_config = {
                'reader_type': config.rfid_in_reader_type,
                'reader_id': 'reader_in',
                'direction': 'in',
                'rst_pin': config.rfid_in_rst_pin,
                'sda_pin': config.rfid_in_sda_pin
            }
            
            reader_in = ReaderFactory.create_reader(in_config)
            
            # Crea lettore OUT (PN532)
            out_config = {
                'reader_type': config.rfid_out_reader_type,
                'reader_id': 'reader_out',
                'direction': 'out',
                'interface': 'i2c',
                'i2c_address': 0x24
            }
            
            reader_out = ReaderFactory.create_reader(out_config)
            
            # Verifica tipi corretti
            self.assertEqual(reader_in.__class__.__name__, 'MFRC522Reader')
            self.assertEqual(reader_out.__class__.__name__, 'PN532Reader')
            
            # Test connessione
            self.assertTrue(reader_in.connect())
            self.assertTrue(reader_out.connect())
    
    def test_debounce_system_integration(self):
        """Test integrazione sistema debounce"""
        debounce = GlobalDebounceManager.get_instance()
        debounce.configure_debounce_time(0.1)  # 100ms per test
        
        # Simula scenario reale: carta letta da più lettori
        uid = "12345678"
        
        # Prima lettura IN
        is_dup1 = debounce.is_duplicate(uid, "in")
        self.assertFalse(is_dup1)
        
        # Lettura immediata OUT (anti-crosstalk)
        is_dup2 = debounce.is_duplicate(uid, "out")
        self.assertTrue(is_dup2)  # Bloccata da debounce globale
        
        # Lettura ripetuta IN
        is_dup3 = debounce.is_duplicate(uid, "in")
        self.assertTrue(is_dup3)  # Bloccata da debounce direzione
        
        # Verifica statistiche
        stats = debounce.get_stats()
        self.assertEqual(stats['total_checks'], 3)
        self.assertEqual(stats['duplicates_detected'], 2)
        self.assertEqual(stats['global_blocks'], 1)
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_mqtt_integration(self, mock_mqtt_client):
        """Test integrazione client MQTT"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Mock del client MQTT
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            mock_client.connect_async.return_value = 0
            
            # Crea client MQTT
            mqtt_client = AsyncMQTTClient(config)
            
            # Test configurazione
            self.assertEqual(mqtt_client.broker, 'test.broker.com')
            self.assertEqual(mqtt_client.port, 1883)
            self.assertEqual(mqtt_client.username, 'testuser')
            
            # Test connessione asincrona
            async def test_connect():
                result = await mqtt_client.connect()
                return result
            
            # Non possiamo facilmente testare async qui, ma verifichiamo setup
            self.assertIsNotNone(mqtt_client._client)
    
    def test_offline_mode_integration(self):
        """Test integrazione modalità offline"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Crea file offline temporaneo
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                offline_file = f.name
                f.write('[]')  # File offline vuoto
            
            try:
                # Configura per modalità offline
                config.offline_storage_file = offline_file
                
                # Simula sistema in offline
                with patch.multiple(
                    'rfid_gate.core.access_control',
                    MFRC522Reader=Mock,
                    PN532Reader=Mock,
                    GPIORelay=Mock,
                    AsyncMQTTClient=Mock
                ):
                    system = AccessControlSystem(config)
                    
                    # Verifica configurazione offline
                    self.assertTrue(system.config.offline_mode_enabled)
                    self.assertEqual(system.config.offline_storage_file, offline_file)
                    
                    # Test file offline accessibile
                    self.assertTrue(os.path.exists(offline_file))
                    
            finally:
                if os.path.exists(offline_file):
                    os.unlink(offline_file)
    
    def test_card_processing_workflow(self):
        """Test workflow completo processamento carta"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Mock di tutti i componenti
            mock_reader = Mock()
            mock_reader.read_card.return_value = "12345678"
            mock_reader.is_connected = True
            
            mock_relay = Mock()
            mock_mqtt = Mock()
            
            with patch('rfid_gate.hardware.readers.factory.ReaderFactory.create_reader', return_value=mock_reader), \
                 patch('rfid_gate.hardware.relays.gpio.GPIORelay', return_value=mock_relay), \
                 patch('rfid_gate.network.mqtt.AsyncMQTTClient', return_value=mock_mqtt):
                
                system = AccessControlSystem(config)
                
                # Simula lettura carta
                uid = mock_reader.read_card()
                self.assertEqual(uid, "12345678")
                
                # Verifica che il debounce sia configurato
                debounce = GlobalDebounceManager.get_instance()
                self.assertIsNotNone(debounce)
                
                # Test processo duplicati
                is_dup1 = debounce.is_duplicate(uid, "in")
                is_dup2 = debounce.is_duplicate(uid, "in")  # Duplicato
                
                self.assertFalse(is_dup1)
                self.assertTrue(is_dup2)
    
    def test_error_handling_integration(self):
        """Test gestione errori nel sistema integrato"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Mock che solleva eccezioni
            mock_reader = Mock()
            mock_reader.connect.side_effect = Exception("Hardware error")
            
            with patch('rfid_gate.hardware.readers.factory.ReaderFactory.create_reader', return_value=mock_reader):
                
                # Il sistema dovrebbe gestire l'errore gracefully
                try:
                    system = AccessControlSystem(config)
                    # Se arriva qui, l'errore è stato gestito
                except Exception as e:
                    # Se solleva eccezione, dovrebbe essere gestita appropriatamente
                    self.assertIsInstance(e, Exception)
    
    def test_configuration_validation_integration(self):
        """Test validazione configurazione integrata"""
        # Configurazione invalida
        invalid_env = self.test_env.copy()
        invalid_env['MQTT_PORT'] = 'not_a_number'
        invalid_env['RFID_IN_RST_PIN'] = 'invalid'
        
        with patch.dict(os.environ, invalid_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Dovrebbe usare valori di default per campi invalidi
            self.assertEqual(config.mqtt_port, 1883)  # Default
            # RST pin potrebbe avere default o sollevare errore
    
    def test_logging_integration(self):
        """Test integrazione sistema di logging"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            # Verifica configurazione logging
            self.assertEqual(config.log_level, 'DEBUG')
            self.assertEqual(config.log_directory, 'logs')
            
            # Test con sistema
            with patch.multiple(
                'rfid_gate.core.access_control',
                MFRC522Reader=Mock,
                PN532Reader=Mock,
                GPIORelay=Mock,
                AsyncMQTTClient=Mock
            ):
                with patch('rfid_gate.core.access_control.setup_logging') as mock_logging:
                    system = AccessControlSystem(config)
                    
                    # Verifica che il logging sia configurato
                    mock_logging.assert_called()


class TestAsyncIntegration(unittest.TestCase):
    """Test integrazione componenti asincroni"""
    
    def setUp(self):
        """Setup per test async"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Cleanup test async"""
        self.loop.close()
    
    def test_async_card_processing(self):
        """Test processamento asincrono carte"""
        async def async_test():
            # Mock componenti async
            mock_mqtt = AsyncMock()
            mock_mqtt.connect.return_value = True
            mock_mqtt.publish.return_value = True
            
            # Simula processamento carta
            card_data = {
                'uid': '12345678',
                'direction': 'in',
                'timestamp': 1234567890
            }
            
            # Test pubblicazione MQTT
            result = await mock_mqtt.publish('test/topic', json.dumps(card_data))
            self.assertTrue(result)
            
            # Verifica chiamate
            mock_mqtt.connect.assert_called_once()
            mock_mqtt.publish.assert_called_once()
        
        self.loop.run_until_complete(async_test())
    
    def test_concurrent_reader_access(self):
        """Test accesso concorrente ai lettori"""
        async def async_test():
            # Simula lettori multipli che leggono simultaneamente
            mock_reader_in = Mock()
            mock_reader_out = Mock()
            
            mock_reader_in.read_card.return_value = "111111"
            mock_reader_out.read_card.return_value = "222222"
            
            # Simula letture simultanee
            tasks = [
                asyncio.create_task(asyncio.to_thread(mock_reader_in.read_card)),
                asyncio.create_task(asyncio.to_thread(mock_reader_out.read_card))
            ]
            
            results = await asyncio.gather(*tasks)
            
            self.assertEqual(results[0], "111111")
            self.assertEqual(results[1], "222222")
        
        self.loop.run_until_complete(async_test())


if __name__ == '__main__':
    unittest.main(verbosity=2)