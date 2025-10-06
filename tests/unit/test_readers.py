#!/usr/bin/env python3
"""
🧪 Test RFID Readers
==================

Test semplificati per i lettori RFID.
Verifica funzionalità base e factory patterns.
"""

import unittest
from unittest.mock import patch, MagicMock
from rfid_gate.hardware.readers.base import BaseRFIDReader, ReaderStatus
from rfid_gate.hardware.readers.mfrc522 import MFRC522Reader
from rfid_gate.hardware.readers.pn532 import PN532Reader
from rfid_gate.hardware.readers.factory import ReaderFactory
from rfid_gate.config.settings import RFIDReaderConfig, ReaderType, PN532Interface


class TestBaseReader(unittest.TestCase):
    """Test per classe base astratta"""
    
    def test_abstract_methods(self):
        """Test che la classe base sia astratta"""
        with self.assertRaises(TypeError):
            BaseRFIDReader("test", "in")


class TestMFRC522Reader(unittest.TestCase):
    """Test per lettore MFRC522"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.reader = MFRC522Reader('test_mfrc522', 'in', rst_pin=22, sda_pin=8)
    
    def test_initialization(self):
        """Test inizializzazione lettore"""
        self.assertEqual(self.reader.reader_id, 'test_mfrc522')
        self.assertEqual(self.reader.direction, 'in')
        self.assertEqual(self.reader.status, ReaderStatus.DISCONNECTED)
    
    def test_get_reader_type(self):
        """Test tipo lettore"""
        self.assertEqual(self.reader.get_reader_type(), "mfrc522")


class TestPN532Reader(unittest.TestCase):
    """Test per lettore PN532"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.reader = PN532Reader('test_pn532', 'out', interface='i2c')
    
    def test_initialization_i2c(self):
        """Test inizializzazione I2C"""
        self.assertEqual(self.reader.reader_id, 'test_pn532')
        self.assertEqual(self.reader.direction, 'out')
        self.assertEqual(self.reader.interface, 'i2c')
        self.assertEqual(self.reader.i2c_address, 0x24)
    
    def test_initialization_spi(self):
        """Test inizializzazione SPI"""
        spi_reader = PN532Reader('spi_reader', 'in', interface='spi', 
                                spi_bus=1, spi_device=1)
        self.assertEqual(spi_reader.interface, 'spi')
        self.assertEqual(spi_reader.spi_bus, 1)
        self.assertEqual(spi_reader.spi_device, 1)
    
    def test_get_reader_type(self):
        """Test tipo lettore"""
        self.assertEqual(self.reader.get_reader_type(), "pn532")


class TestReaderFactory(unittest.TestCase):
    """Test per factory dei lettori"""
    
    def test_create_mfrc522_reader(self):
        """Test creazione lettore MFRC522"""
        config = RFIDReaderConfig(
            enabled=True,
            reader_type=ReaderType.MFRC522,
            rst_pin=22,
            sda_pin=8
        )
        
        reader = ReaderFactory.create_reader(config, 'test_mfrc522', 'in')
        
        self.assertIsNotNone(reader)
        self.assertIsInstance(reader, MFRC522Reader)
        self.assertEqual(reader.reader_id, 'test_mfrc522')
        self.assertEqual(reader.direction, 'in')
    
    def test_create_pn532_i2c_reader(self):
        """Test creazione lettore PN532 I2C"""
        config = RFIDReaderConfig(
            enabled=True,
            reader_type=ReaderType.PN532,
            pn532_interface=PN532Interface.I2C,
            pn532_i2c_address=0x24
        )
        
        reader = ReaderFactory.create_reader(config, 'test_pn532', 'out')
        
        self.assertIsNotNone(reader)
        self.assertIsInstance(reader, PN532Reader)
        self.assertEqual(reader.reader_id, 'test_pn532')
        self.assertEqual(reader.direction, 'out')
        self.assertEqual(reader.interface, 'i2c')
    
    def test_create_pn532_spi_reader(self):
        """Test creazione lettore PN532 SPI"""
        config = RFIDReaderConfig(
            enabled=True,
            reader_type=ReaderType.PN532,
            pn532_interface=PN532Interface.SPI,
            pn532_spi_bus=1,
            pn532_spi_device=0
        )
        
        reader = ReaderFactory.create_reader(config, 'test_pn532_spi', 'in')
        
        self.assertIsNotNone(reader)
        self.assertIsInstance(reader, PN532Reader)
        self.assertEqual(reader.interface, 'spi')
        self.assertEqual(reader.spi_bus, 1)
    
    def test_disabled_reader_returns_none(self):
        """Test che lettore disabilitato restituisca None"""
        config = RFIDReaderConfig(enabled=False)
        
        reader = ReaderFactory.create_reader(config, 'disabled_reader', 'in')
        
        self.assertIsNone(reader)
    
    def test_get_available_readers(self):
        """Test lista lettori disponibili"""
        available = ReaderFactory.get_available_readers()
        
        self.assertIn('mfrc522', available)
        self.assertIn('pn532', available)
        self.assertEqual(available['mfrc522'], MFRC522Reader)
        self.assertEqual(available['pn532'], PN532Reader)


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rfid_gate.hardware.readers.factory import ReaderFactory
from rfid_gate.hardware.readers.base import BaseRFIDReader
from rfid_gate.hardware.readers.mfrc522 import MFRC522Reader
from rfid_gate.hardware.readers.pn532 import PN532Reader


class TestReaderFactory(unittest.TestCase):
    """Test della factory per i lettori RFID"""
    
    def test_create_mfrc522_reader(self):
        """Test creazione lettore MFRC522"""
        config = {
            'reader_type': 'mfrc522',
            'reader_id': 'test_reader',
            'direction': 'in',
            'rst_pin': 22,
            'sda_pin': 8
        }
        
        reader = ReaderFactory.create_reader(config)
        
        self.assertIsInstance(reader, MFRC522Reader)
        self.assertEqual(reader.reader_id, 'test_reader')
        self.assertEqual(reader.direction, 'in')
    
    def test_create_pn532_i2c_reader(self):
        """Test creazione lettore PN532 I2C"""
        config = {
            'reader_type': 'pn532',
            'reader_id': 'test_pn532',
            'direction': 'out',
            'interface': 'i2c',
            'i2c_address': 0x24
        }
        
        reader = ReaderFactory.create_reader(config)
        
        self.assertIsInstance(reader, PN532Reader)
        self.assertEqual(reader.reader_id, 'test_pn532')
        self.assertEqual(reader.direction, 'out')
        self.assertEqual(reader.interface, 'i2c')
    
    def test_create_pn532_spi_reader(self):
        """Test creazione lettore PN532 SPI"""
        config = {
            'reader_type': 'pn532',
            'reader_id': 'spi_reader',
            'direction': 'in',
            'interface': 'spi',
            'spi_bus': 0,
            'spi_device': 0
        }
        
        reader = ReaderFactory.create_reader(config)
        
        self.assertIsInstance(reader, PN532Reader)
        self.assertEqual(reader.interface, 'spi')
    
    def test_invalid_reader_type(self):
        """Test tipo lettore non valido"""
        config = {
            'reader_type': 'invalid_type',
            'reader_id': 'test',
            'direction': 'in'
        }
        
        with self.assertRaises(ValueError):
            ReaderFactory.create_reader(config)
    
    def test_missing_required_config(self):
        """Test configurazione incompleta"""
        config = {
            'reader_type': 'mfrc522',
            # Mancano reader_id e direction
        }
        
        with self.assertRaises(KeyError):
            ReaderFactory.create_reader(config)


class TestMFRC522Reader(unittest.TestCase):
    """Test del lettore MFRC522"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.reader = MFRC522Reader(
            reader_id='test_mfrc522',
            direction='in',
            rst_pin=22,
            sda_pin=8
        )
    
    def test_initialization(self):
        """Test inizializzazione lettore"""
        self.assertEqual(self.reader.reader_id, 'test_mfrc522')
        self.assertEqual(self.reader.direction, 'in')
        self.assertEqual(self.reader.rst_pin, 22)
        self.assertEqual(self.reader.sda_pin, 8)
        self.assertFalse(self.reader.is_connected)
    
    @patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522')
    def test_connect(self):
        """Test connessione al lettore"""
        mock_mfrc522 = Mock()
        
        with patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522', return_value=mock_mfrc522):
            result = self.reader.connect()
            
            self.assertTrue(result)
            self.assertTrue(self.reader.is_connected)
            self.assertIsNotNone(self.reader._device)
    
    @patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522')
    def test_connect_failure(self):
        """Test fallimento connessione"""
        with patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522', side_effect=Exception("Connection failed")):
            result = self.reader.connect()
            
            self.assertFalse(result)
            self.assertFalse(self.reader.is_connected)
    
    @patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522')
    def test_read_card_success(self):
        """Test lettura carta con successo"""
        mock_device = Mock()
        mock_device.read_id_no_block.return_value = 0x12345678
        
        with patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522', return_value=mock_device):
            self.reader.connect()
            uid = self.reader.read_card()
            
            self.assertEqual(uid, "12345678")
    
    @patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522')
    def test_read_card_no_card(self):
        """Test lettura senza carta"""
        mock_device = Mock()
        mock_device.read_id_no_block.return_value = None
        
        with patch('rfid_gate.hardware.readers.mfrc522.SimpleMFRC522', return_value=mock_device):
            self.reader.connect()
            uid = self.reader.read_card()
            
            self.assertIsNone(uid)
    
    def test_read_card_not_connected(self):
        """Test lettura senza connessione"""
        uid = self.reader.read_card()
        self.assertIsNone(uid)
    
    def test_disconnect(self):
        """Test disconnessione"""
        self.reader._device = Mock()
        self.reader.is_connected = True
        
        self.reader.disconnect()
        
        self.assertFalse(self.reader.is_connected)
        self.assertIsNone(self.reader._device)
    
    def test_status_info(self):
        """Test informazioni stato"""
        status = self.reader.get_status()
        
        expected_keys = ['reader_id', 'type', 'direction', 'is_connected', 'rst_pin', 'sda_pin']
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status['type'], 'MFRC522')
        self.assertEqual(status['reader_id'], 'test_mfrc522')


class TestPN532Reader(unittest.TestCase):
    """Test del lettore PN532"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.reader = PN532Reader(
            reader_id='test_pn532',
            direction='out',
            interface='i2c',
            i2c_address=0x24
        )
    
    def test_initialization_i2c(self):
        """Test inizializzazione I2C"""
        self.assertEqual(self.reader.reader_id, 'test_pn532')
        self.assertEqual(self.reader.direction, 'out')
        self.assertEqual(self.reader.interface, 'i2c')
        self.assertEqual(self.reader.i2c_address, 0x24)
    
    def test_initialization_spi(self):
        """Test inizializzazione SPI"""
        reader = PN532Reader(
            reader_id='spi_reader',
            direction='in',
            interface='spi',
            spi_bus=0,
            spi_device=0
        )
        
        self.assertEqual(reader.interface, 'spi')
        self.assertEqual(reader.spi_bus, 0)
        self.assertEqual(reader.spi_device, 0)
    
    def test_invalid_interface(self):
        """Test interfaccia non valida"""
        with self.assertRaises(ValueError):
            PN532Reader(
                reader_id='test',
                direction='in',
                interface='invalid_interface'
            )
    
    @patch('rfid_gate.hardware.readers.pn532.PN532_I2C')
    @patch('rfid_gate.hardware.readers.pn532.PN532')
    def test_connect_i2c(self, mock_pn532, mock_i2c):
        """Test connessione I2C"""
        mock_device = Mock()
        mock_pn532.return_value = mock_device
        mock_device.SAM_configuration.return_value = True
        
        result = self.reader.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.reader.is_connected)
    
    @patch('rfid_gate.hardware.readers.pn532.PN532_I2C')
    @patch('rfid_gate.hardware.readers.pn532.PN532')
    def test_read_card_success(self, mock_pn532, mock_i2c):
        """Test lettura carta PN532"""
        mock_device = Mock()
        mock_pn532.return_value = mock_device
        mock_device.SAM_configuration.return_value = True
        mock_device.read_passive_target.return_value = bytearray([0x12, 0x34, 0x56, 0x78])
        
        self.reader.connect()
        uid = self.reader.read_card()
        
        self.assertEqual(uid, "12345678")
    
    def test_get_status(self):
        """Test stato PN532"""
        status = self.reader.get_status()
        
        expected_keys = ['reader_id', 'type', 'direction', 'is_connected', 'interface']
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status['type'], 'PN532')
        self.assertEqual(status['interface'], 'i2c')


class TestBaseReader(unittest.TestCase):
    """Test della classe base BaseRFIDReader"""
    
    def test_abstract_methods(self):
        """Test che la classe base sia astratta"""
        with self.assertRaises(TypeError):
            BaseRFIDReader('test', 'in')
    
    def test_string_representation(self):
        """Test rappresentazione stringa dei lettori"""
        mfrc522 = MFRC522Reader('test_mfrc', 'in', 22, 8)
        pn532 = PN532Reader('test_pn532', 'out', 'i2c', 0x24)
        
        mfrc522_str = str(mfrc522)
        pn532_str = str(pn532)
        
        self.assertIn('MFRC522', mfrc522_str)
        self.assertIn('test_mfrc', mfrc522_str)
        self.assertIn('PN532', pn532_str)
        self.assertIn('I2C', pn532_str)


if __name__ == '__main__':
    unittest.main(verbosity=2)