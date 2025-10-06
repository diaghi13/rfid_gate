#!/usr/bin/env python3
"""
🧪 Test Suite Semplificata
=========================

Test base per validare l'architettura refactorizzata.
Focus sui componenti core senza mock complessi.
"""

import sys
import os
import unittest

# Aggiungi il path del progetto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rfid_gate.config.settings import (
    RFIDGateConfig, MQTTConfig, SystemConfig, RFIDReaderConfig,
    ReaderType, PN532Interface, UIDFormatMode
)
from rfid_gate.utils.debounce import GlobalDebounceManager, DebounceEntry
from rfid_gate.hardware.readers.factory import ReaderFactory


class TestBasicConfig(unittest.TestCase):
    """Test configurazione base"""
    
    def test_config_creation(self):
        """Test creazione configurazione"""
        config = RFIDGateConfig()
        
        # Verifica struttura base
        self.assertIsInstance(config.mqtt, MQTTConfig)
        self.assertIsInstance(config.system, SystemConfig)
        self.assertIsInstance(config.rfid_in, RFIDReaderConfig)
        self.assertIsInstance(config.rfid_out, RFIDReaderConfig)
    
    def test_mqtt_config_defaults(self):
        """Test default MQTT"""
        mqtt = MQTTConfig()
        self.assertEqual(mqtt.port, 1883)
        self.assertFalse(mqtt.use_tls)
    
    def test_system_config_defaults(self):
        """Test default sistema"""
        system = SystemConfig()
        self.assertEqual(system.tornello_id, "tornello_01")
        self.assertTrue(system.bidirectional_mode)
        self.assertEqual(system.rfid_debounce_time, 2.0)
    
    def test_reader_config_defaults(self):
        """Test default lettore"""
        reader = RFIDReaderConfig()
        self.assertTrue(reader.enabled)
        self.assertEqual(reader.reader_type, ReaderType.MFRC522)
        self.assertEqual(reader.rst_pin, 22)
        self.assertEqual(reader.pn532_interface, PN532Interface.I2C)


class TestDebounceManager(unittest.TestCase):
    """Test debounce semplificato"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.debounce = GlobalDebounceManager(global_debounce_time=0.1)
    
    def test_creation(self):
        """Test creazione manager"""
        self.assertEqual(self.debounce.global_debounce_time, 0.1)
        self.assertEqual(len(self.debounce.last_reads), 0)
    
    def test_first_read_accepted(self):
        """Test prima lettura accettata"""
        result = self.debounce.is_duplicate("123456", "in", "reader1")
        self.assertFalse(result)
        self.assertEqual(self.debounce.stats['total_checks'], 1)
    
    def test_immediate_duplicate_blocked(self):
        """Test duplicato immediato bloccato"""
        # Prima lettura
        self.debounce.is_duplicate("123456", "in", "reader1")
        
        # Seconda lettura immediata - dovrebbe essere bloccata
        result = self.debounce.is_duplicate("123456", "in", "reader1")
        self.assertTrue(result)
    
    def test_different_uids_accepted(self):
        """Test UID diversi accettati"""
        result1 = self.debounce.is_duplicate("123456", "in", "reader1")
        result2 = self.debounce.is_duplicate("789012", "in", "reader1")
        
        self.assertFalse(result1)
        self.assertFalse(result2)
    
    def test_stats_tracking(self):
        """Test tracciamento statistiche"""
        self.debounce.is_duplicate("123456", "in", "reader1")
        self.debounce.is_duplicate("123456", "in", "reader1")  # Duplicate
        
        stats = self.debounce.get_stats()
        self.assertEqual(stats['total_checks'], 2)
        self.assertEqual(stats['duplicates_detected'], 1)
    
    def test_stats_reset(self):
        """Test reset statistiche"""
        self.debounce.is_duplicate("123456", "in", "reader1")
        self.debounce.reset_stats()
        
        stats = self.debounce.get_stats()
        self.assertEqual(stats['total_checks'], 0)
        self.assertEqual(stats['duplicates_detected'], 0)


class TestReaderFactory(unittest.TestCase):
    """Test factory lettori"""
    
    def test_available_readers(self):
        """Test lettori disponibili"""
        readers = ReaderFactory.get_available_readers()
        
        self.assertIn('mfrc522', readers)
        self.assertIn('pn532', readers)
        self.assertEqual(len(readers), 2)
    
    def test_disabled_reader_returns_none(self):
        """Test lettore disabilitato"""
        config = RFIDReaderConfig(enabled=False)
        reader = ReaderFactory.create_reader(config, 'test', 'in')
        
        self.assertIsNone(reader)
    
    def test_create_mfrc522_reader(self):
        """Test creazione MFRC522"""
        config = RFIDReaderConfig(
            enabled=True,
            reader_type=ReaderType.MFRC522,
            rst_pin=22,
            sda_pin=8
        )
        
        reader = ReaderFactory.create_reader(config, 'test_mfrc522', 'in')
        
        self.assertIsNotNone(reader)
        self.assertEqual(reader.reader_id, 'test_mfrc522')
        self.assertEqual(reader.direction, 'in')
        self.assertEqual(reader.get_reader_type(), 'mfrc522')
    
    def test_create_pn532_reader(self):
        """Test creazione PN532"""
        config = RFIDReaderConfig(
            enabled=True,
            reader_type=ReaderType.PN532,
            pn532_interface=PN532Interface.I2C
        )
        
        reader = ReaderFactory.create_reader(config, 'test_pn532', 'out')
        
        self.assertIsNotNone(reader)
        self.assertEqual(reader.reader_id, 'test_pn532')
        self.assertEqual(reader.direction, 'out')
        self.assertEqual(reader.get_reader_type(), 'pn532')
        self.assertEqual(reader.interface, 'i2c')


class TestEnumTypes(unittest.TestCase):
    """Test tipi enum"""
    
    def test_reader_types(self):
        """Test tipi lettore"""
        self.assertEqual(ReaderType.MFRC522, "mfrc522")
        self.assertEqual(ReaderType.PN532, "pn532")
    
    def test_pn532_interfaces(self):
        """Test interfacce PN532"""
        self.assertEqual(PN532Interface.I2C, "i2c")
        self.assertEqual(PN532Interface.SPI, "spi")
        self.assertEqual(PN532Interface.UART, "uart")
    
    def test_uid_format_modes(self):
        """Test modalità formattazione UID"""
        self.assertEqual(UIDFormatMode.REMOVE_SUFFIX, "remove_suffix")
        self.assertEqual(UIDFormatMode.FIXED_LENGTH, "fixed_length")
        self.assertEqual(UIDFormatMode.RAW, "raw")


class TestArchitectureIntegrity(unittest.TestCase):
    """Test integrità architettura"""
    
    def test_package_imports(self):
        """Test import pacchetti principali"""
        # Test che tutti i moduli principali siano importabili
        try:
            from rfid_gate.config import settings
            from rfid_gate.core import access_control
            from rfid_gate.hardware.readers import factory
            from rfid_gate.hardware.relays import gpio
            from rfid_gate.network import mqtt
            from rfid_gate.utils import debounce
            success = True
        except ImportError:
            success = False
        
        self.assertTrue(success, "Tutti i moduli principali devono essere importabili")
    
    def test_config_completeness(self):
        """Test completezza configurazione"""
        config = RFIDGateConfig()
        
        # Verifica che tutti i componenti necessari siano presenti
        required_components = [
            'mqtt', 'system', 'rfid_in', 'rfid_out', 
            'relay_in', 'relay_out', 'auth', 'offline', 'logging'
        ]
        
        for component in required_components:
            self.assertTrue(hasattr(config, component), 
                          f"Configurazione deve avere componente {component}")
    
    def test_topic_generation(self):
        """Test generazione topic MQTT"""
        config = RFIDGateConfig()
        config.system.tornello_id = "test_gate"
        
        topic = config.get_mqtt_topic("access")
        self.assertEqual(topic, "gate/test_gate/access")
        
        auth_topic = config.get_auth_response_topic()
        self.assertIn("test_gate", auth_topic)


if __name__ == '__main__':
    # Esegui solo questi test semplificati
    unittest.main()