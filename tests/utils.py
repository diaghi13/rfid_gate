#!/usr/bin/env python3
"""
🧪 Test Utilities
================

Utilities e mock objects per il testing del sistema RFID Gate
"""

import time
import json
import tempfile
import os
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, MagicMock
from pathlib import Path


class TestUtilities:
    """Utility class per test comuni"""
    
    @staticmethod
    def create_temp_env_file(config: Dict[str, str]) -> str:
        """Crea un file .env temporaneo per i test"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
            return f.name
    
    @staticmethod  
    def create_temp_config(minimal: bool = True) -> Dict[str, str]:
        """Crea configurazione temporanea per test"""
        if minimal:
            return {
                'MQTT_BROKER': 'test.broker.com',
                'TORNELLO_ID': 'test_gate'
            }
        else:
            return {
                'MQTT_BROKER': 'test.broker.com',
                'MQTT_PORT': '1883',
                'MQTT_USERNAME': 'testuser',
                'MQTT_PASSWORD': 'testpass',
                'MQTT_USE_TLS': 'false',
                'TORNELLO_ID': 'test_gate_full',
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
                'OFFLINE_MODE_ENABLED': 'true'
            }
    
    @staticmethod
    def cleanup_temp_file(filepath: str):
        """Rimuove file temporaneo"""
        if os.path.exists(filepath):
            os.unlink(filepath)
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Misura tempo di esecuzione di una funzione"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # ms
        return result, execution_time
    
    @staticmethod
    def generate_test_uids(count: int, prefix: str = "TEST") -> List[str]:
        """Genera UIDs di test"""
        return [f"{prefix}{i:06d}" for i in range(count)]
    
    @staticmethod
    def create_mock_mqtt_message(topic: str, payload: Dict[str, Any]) -> Mock:
        """Crea mock message MQTT"""
        mock_msg = Mock()
        mock_msg.topic = topic
        mock_msg.payload = json.dumps(payload).encode('utf-8')
        mock_msg.qos = 0
        mock_msg.retain = False
        return mock_msg


class MockRFIDReader:
    """Mock reader RFID per test"""
    
    def __init__(self, reader_id: str, direction: str, reader_type: str = "mock"):
        self.reader_id = reader_id
        self.direction = direction
        self.reader_type = reader_type
        self.is_connected = False
        self._device = None
        self._read_responses = []
        self._read_index = 0
    
    def set_read_responses(self, responses: List[Optional[str]]):
        """Imposta sequenza di risposte per read_card()"""
        self._read_responses = responses
        self._read_index = 0
    
    def connect(self) -> bool:
        """Simula connessione"""
        self.is_connected = True
        self._device = Mock()
        return True
    
    def disconnect(self):
        """Simula disconnessione"""
        self.is_connected = False
        self._device = None
    
    def read_card(self) -> Optional[str]:
        """Simula lettura carta"""
        if not self.is_connected:
            return None
        
        if not self._read_responses:
            return None
        
        if self._read_index >= len(self._read_responses):
            return None
        
        response = self._read_responses[self._read_index]
        self._read_index += 1
        return response
    
    def get_status(self) -> Dict[str, Any]:
        """Restituisce stato mock"""
        return {
            'reader_id': self.reader_id,
            'type': self.reader_type.upper(),
            'direction': self.direction,
            'is_connected': self.is_connected
        }
    
    def __str__(self) -> str:
        return f"MockReader({self.reader_id}, {self.reader_type.upper()}, {self.direction}, {'connected' if self.is_connected else 'disconnected'})"


class MockGPIORelay:
    """Mock relè GPIO per test"""
    
    def __init__(self, relay_id: str, pin: int, active_time: float = 2.0, 
                 active_low: bool = True, initial_state: str = 'LOW'):
        self.relay_id = relay_id
        self.pin = pin
        self.active_time = active_time
        self.active_low = active_low
        self.initial_state = initial_state
        self.is_active = False
        self.is_setup = False
        self._activation_count = 0
    
    def setup(self) -> bool:
        """Simula setup GPIO"""
        self.is_setup = True
        return True
    
    def activate(self) -> bool:
        """Simula attivazione relè"""
        if not self.is_setup:
            return False
        
        self.is_active = True
        self._activation_count += 1
        return True
    
    def deactivate(self) -> bool:
        """Simula disattivazione relè"""
        if not self.is_setup:
            return False
        
        self.is_active = False
        return True
    
    def pulse(self) -> bool:
        """Simula pulse relè"""
        if not self.setup():
            return False
        
        self.activate()
        # In un test reale, qui ci sarebbe un timer
        # Per i test, si può chiamare deactivate() manualmente
        return True
    
    def cleanup(self):
        """Simula cleanup GPIO"""
        self.is_setup = False
        self.is_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Restituisce stato mock"""
        return {
            'relay_id': self.relay_id,
            'pin': self.pin,
            'is_active': self.is_active,
            'is_setup': self.is_setup,
            'active_low': self.active_low,
            'active_time': self.active_time,
            'activation_count': self._activation_count
        }
    
    def __str__(self) -> str:
        return f"MockRelay({self.relay_id}, pin={self.pin}, {'active' if self.is_active else 'inactive'})"


class MockAsyncMQTTClient:
    """Mock client MQTT asincrono per test"""
    
    def __init__(self, config):
        self.config = config
        self.broker = config.mqtt_broker
        self.port = config.mqtt_port
        self.is_connected = False
        self.published_messages = []
        self.subscriptions = []
        self._message_callback = None
    
    async def connect(self) -> bool:
        """Simula connessione asincrona"""
        self.is_connected = True
        return True
    
    async def disconnect(self):
        """Simula disconnessione"""
        self.is_connected = False
    
    async def publish(self, topic: str, payload: str, qos: int = 0) -> bool:
        """Simula pubblicazione messaggio"""
        if not self.is_connected:
            return False
        
        message = {
            'topic': topic,
            'payload': payload,
            'qos': qos,
            'timestamp': time.time()
        }
        self.published_messages.append(message)
        return True
    
    async def publish_card_read(self, uid: str, direction: str) -> bool:
        """Simula pubblicazione lettura carta"""
        topic = self.config.mqtt_card_read_topic
        payload = json.dumps({
            'uid': uid,
            'direction': direction,
            'timestamp': time.time(),
            'tornello_id': self.config.tornello_id
        })
        return await self.publish(topic, payload)
    
    def subscribe(self, topic: str, qos: int = 0):
        """Simula sottoscrizione"""
        self.subscriptions.append({'topic': topic, 'qos': qos})
    
    def set_message_callback(self, callback):
        """Imposta callback per messaggi ricevuti"""
        self._message_callback = callback
    
    def simulate_received_message(self, topic: str, payload: Dict[str, Any]):
        """Simula ricezione messaggio (per test)"""
        if self._message_callback:
            mock_msg = TestUtilities.create_mock_mqtt_message(topic, payload)
            self._message_callback(mock_msg)
    
    def get_published_messages(self, topic_filter: Optional[str] = None) -> List[Dict]:
        """Restituisce messaggi pubblicati, opzionalmente filtrati per topic"""
        if topic_filter:
            return [msg for msg in self.published_messages if msg['topic'] == topic_filter]
        return self.published_messages.copy()
    
    def clear_published_messages(self):
        """Pulisce la lista dei messaggi pubblicati"""
        self.published_messages.clear()


class TestDataGenerator:
    """Generatore di dati di test"""
    
    @staticmethod
    def generate_card_read_scenarios() -> List[Dict[str, Any]]:
        """Genera scenari di lettura carte per test"""
        return [
            # Scenario normale
            {
                'name': 'normal_read',
                'uid': '12345678',
                'direction': 'in',
                'expected_duplicate': False
            },
            # Scenario duplicato immediato
            {
                'name': 'immediate_duplicate',
                'uid': '12345678',
                'direction': 'in',
                'expected_duplicate': True
            },
            # Scenario crosstalk
            {
                'name': 'crosstalk',
                'uid': '12345678',
                'direction': 'out',
                'expected_duplicate': True  # Bloccato da debounce globale
            },
            # Nuovo UID
            {
                'name': 'new_uid',
                'uid': 'ABCDEF12',
                'direction': 'in',
                'expected_duplicate': False
            }
        ]
    
    @staticmethod
    def generate_stress_test_data(count: int) -> List[Dict[str, str]]:
        """Genera dati per stress test"""
        data = []
        for i in range(count):
            data.append({
                'uid': f"STRESS{i:08d}",
                'direction': 'in' if i % 2 == 0 else 'out',
                'timestamp': str(time.time() + i * 0.001)  # 1ms intervals
            })
        return data


# Alias per compatibilità
MockReader = MockRFIDReader
MockRelay = MockGPIORelay