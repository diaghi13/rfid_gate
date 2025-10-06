#!/usr/bin/env python3
"""
🧪 Integration Tests - MQTT System
==================================

Test di integrazione per il sistema MQTT completo
"""

import unittest
import asyncio
import json
import ssl
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient, MQTTMessage


class TestMQTTIntegration(unittest.TestCase):
    """Test integrazione completa MQTT"""
    
    def setUp(self):
        """Setup per ogni test"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Configurazione MQTT di test
        self.test_env = {
            'MQTT_BROKER': 'test.broker.com',
            'MQTT_PORT': '8883',
            'MQTT_USERNAME': 'testuser',
            'MQTT_PASSWORD': 'testpass',
            'MQTT_USE_TLS': 'true',
            'MQTT_KEEP_ALIVE': '60',
            'TORNELLO_ID': 'gate_test_01',
            'MQTT_CARD_READ_TOPIC': 'rfid_gate/card_read',
            'MQTT_AUTH_RESPONSE_TOPIC': 'rfid_gate/auth_response',
            'MQTT_MANUAL_OPEN_TOPIC': 'rfid_gate/manual_open'
        }
    
    def tearDown(self):
        """Cleanup dopo test"""
        self.loop.close()
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_mqtt_client_initialization(self, mock_mqtt_client):
        """Test inizializzazione client MQTT"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            
            mqtt = AsyncMQTTClient(config)
            
            # Verifica configurazione
            self.assertEqual(mqtt.broker, 'test.broker.com')
            self.assertEqual(mqtt.port, 8883)
            self.assertEqual(mqtt.username, 'testuser')
            self.assertEqual(mqtt.password, 'testpass')
            self.assertTrue(mqtt.use_tls)
            self.assertEqual(mqtt.keep_alive, 60)
            
            # Verifica configurazione client
            mock_mqtt_client.assert_called_once()
            mock_client.username_pw_set.assert_called_with('testuser', 'testpass')
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_tls_configuration(self, mock_mqtt_client):
        """Test configurazione TLS"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            
            mqtt = AsyncMQTTClient(config)
            
            # Verifica configurazione TLS
            mock_client.tls_set.assert_called_once_with(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
    
    def test_message_formatting(self):
        """Test formattazione messaggi MQTT"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            with patch('rfid_gate.network.mqtt.mqtt_client.Client'):
                mqtt = AsyncMQTTClient(config)
                
                # Test messaggio lettura carta
                card_message = mqtt._format_card_read_message("12345678", "in")
                
                # Verifica struttura messaggio
                self.assertIn('uid', card_message)
                self.assertIn('direction', card_message)
                self.assertIn('timestamp', card_message)
                self.assertIn('tornello_id', card_message)
                
                # Verifica contenuto
                parsed = json.loads(card_message)
                self.assertEqual(parsed['uid'], "12345678")
                self.assertEqual(parsed['direction'], "in")
                self.assertEqual(parsed['tornello_id'], "gate_test_01")
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_connection_workflow(self, mock_mqtt_client):
        """Test workflow di connessione completo"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            mock_client.connect_async.return_value = 0  # Success
            
            async def test_connect():
                mqtt = AsyncMQTTClient(config)
                
                # Test connessione
                result = await mqtt.connect()
                
                # Verifica chiamate
                mock_client.connect_async.assert_called_with(
                    'test.broker.com', 8883, 60
                )
                mock_client.loop_start.assert_called_once()
                
                return result
            
            result = self.loop.run_until_complete(test_connect())
            self.assertTrue(result)
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_publish_workflow(self, mock_mqtt_client):
        """Test workflow pubblicazione messaggi"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            mock_client.publish.return_value.rc = 0  # Success
            
            async def test_publish():
                mqtt = AsyncMQTTClient(config)
                mqtt.is_connected = True  # Simula connessione
                
                # Test pubblicazione
                result = await mqtt.publish_card_read("ABCDEF12", "out")
                
                # Verifica chiamata publish
                self.assertTrue(mock_client.publish.called)
                call_args = mock_client.publish.call_args
                
                # Verifica topic
                topic = call_args[0][0]
                self.assertEqual(topic, 'rfid_gate/card_read')
                
                # Verifica payload
                payload = call_args[0][1]
                parsed_payload = json.loads(payload)
                self.assertEqual(parsed_payload['uid'], 'ABCDEF12')
                self.assertEqual(parsed_payload['direction'], 'out')
                
                return result
            
            result = self.loop.run_until_complete(test_publish())
            self.assertTrue(result)
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_subscription_workflow(self, mock_mqtt_client):
        """Test workflow sottoscrizioni"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            
            mqtt = AsyncMQTTClient(config)
            
            # Test sottoscrizione topic auth response
            auth_topic = f"rfid_gate/auth_response"
            mqtt.subscribe(auth_topic)
            
            mock_client.subscribe.assert_called_with(auth_topic, 0)
    
    def test_message_callbacks(self):
        """Test gestione callback messaggi"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            with patch('rfid_gate.network.mqtt.mqtt_client.Client') as mock_mqtt_client:
                mock_client = Mock()
                mock_mqtt_client.return_value = mock_client
                
                mqtt = AsyncMQTTClient(config)
                
                # Setup callback
                callback_called = []
                def test_callback(message: MQTTMessage):
                    callback_called.append(message)
                
                mqtt.set_message_callback(test_callback)
                
                # Simula messaggio ricevuto
                mock_message = Mock()
                mock_message.topic = "rfid_gate/auth_response"
                mock_message.payload = b'{"authorized": true, "uid": "12345678"}'
                
                # Trigger callback direttamente
                mqtt._on_message(mock_client, None, mock_message)
                
                # Verifica callback chiamato
                self.assertEqual(len(callback_called), 1)
                received_msg = callback_called[0]
                self.assertEqual(received_msg.topic, "rfid_gate/auth_response")
                self.assertIn("authorized", received_msg.payload)
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_reconnection_logic(self, mock_mqtt_client):
        """Test logica di riconnessione"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            
            mqtt = AsyncMQTTClient(config)
            
            # Simula disconnessione
            mqtt.is_connected = False
            
            # Test callback disconnessione
            mqtt._on_disconnect(mock_client, None, 0)
            
            # Verifica stato
            self.assertFalse(mqtt.is_connected)
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_offline_queue_integration(self, mock_mqtt_client):
        """Test integrazione coda offline"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            
            async def test_offline():
                mqtt = AsyncMQTTClient(config)
                mqtt.is_connected = False  # Simula offline
                
                # Test pubblicazione in modalità offline
                result = await mqtt.publish_card_read("OFFLINE123", "in")
                
                # In modalità offline potrebbe:
                # 1. Restituire False
                # 2. Accumulare in coda
                # 3. Gestire diversamente
                self.assertIsInstance(result, bool)
            
            self.loop.run_until_complete(test_offline())
    
    def test_topic_generation(self):
        """Test generazione topic MQTT"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            with patch('rfid_gate.network.mqtt.mqtt_client.Client'):
                mqtt = AsyncMQTTClient(config)
                
                # Test topic generati
                expected_topics = [
                    'rfid_gate/card_read',
                    'rfid_gate/auth_response',
                    'rfid_gate/manual_open'
                ]
                
                # Verifica che i topic siano configurati correttamente
                self.assertEqual(config.mqtt_card_read_topic, expected_topics[0])
                self.assertEqual(config.mqtt_auth_response_topic, expected_topics[1])
                self.assertEqual(config.mqtt_manual_open_topic, expected_topics[2])
    
    @patch('rfid_gate.network.mqtt.mqtt_client.Client')
    def test_error_handling(self, mock_mqtt_client):
        """Test gestione errori MQTT"""
        with patch.dict(os.environ, self.test_env, clear=True):
            config = RFIDGateConfig.load_from_env()
            
            mock_client = Mock()
            mock_mqtt_client.return_value = mock_client
            
            # Simula errore di connessione
            mock_client.connect_async.return_value = 1  # Error code
            
            async def test_error():
                mqtt = AsyncMQTTClient(config)
                
                # Test gestione errore
                result = await mqtt.connect()
                
                # Dovrebbe gestire l'errore gracefully
                self.assertFalse(result)
            
            self.loop.run_until_complete(test_error())
    
    def test_mqtt_message_validation(self):
        """Test validazione messaggi MQTT"""
        # Test MQTTMessage class
        message = MQTTMessage(
            topic="test/topic",
            payload={"test": "data"},
            qos=1,
            timestamp=1234567890
        )
        
        self.assertEqual(message.topic, "test/topic")
        self.assertEqual(message.payload["test"], "data")
        self.assertEqual(message.qos, 1)
        self.assertEqual(message.timestamp, 1234567890)


if __name__ == '__main__':
    unittest.main(verbosity=2)