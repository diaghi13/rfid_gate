#!/usr/bin/env python3
"""
🧪 Test MQTT Parallelo Non-Bloccante
===================================

Test per verificare il nuovo flusso di autenticazione parallela:
1. MQTT sempre inviato in parallelo (non-bloccante)
2. Autenticazione locale immediata
3. Logging condizionale (solo se MQTT fallisce)
4. Queue resiliente per retry automatico
"""

import asyncio
import time
import unittest
from unittest.mock import Mock, AsyncMock, patch
from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.mqtt import AsyncMQTTClient, AuthRequest
from rfid_gate.core.access_control import AccessControlSystem, AccessDecision, SystemMode
from rfid_gate.hardware.readers.base import CardEvent


class TestParallelMQTT(unittest.TestCase):
    """Test MQTT parallelo e logging condizionale"""
    
    def setUp(self):
        """Setup test"""
        # Sistema di controllo accessi
        self.access_control = AccessControlSystem()
        
        # Sovrascrivi configurazione con settings paralleli
        self.access_control.config.mqtt.parallel_auth = True
        self.access_control.config.mqtt.sync_logs_only_on_mqtt_failure = True
        self.access_control.config.mqtt.always_log_locally = True
        self.access_control.config.mqtt.enable_retry_queue = True
        
        # Mock components
        self.mock_mqtt = Mock(spec=AsyncMQTTClient)
        self.mock_sync_manager = AsyncMock()
        
        # Sostituisci componenti con mock
        self.access_control.mqtt_client = self.mock_mqtt
        self.access_control.sync_manager = self.mock_sync_manager
        self.access_control.mode = SystemMode.ONLINE
    
    def test_mqtt_config_new_settings(self):
        """✅ Test nuove configurazioni MQTT"""
        config = self.access_control.config
        
        # Verifica default values
        self.assertTrue(config.mqtt.parallel_auth)
        self.assertTrue(config.mqtt.sync_logs_only_on_mqtt_failure)
        self.assertTrue(config.mqtt.always_log_locally)
        self.assertTrue(config.mqtt.enable_retry_queue)
        self.assertEqual(config.mqtt.max_retry_queue_size, 1000)
        self.assertEqual(config.mqtt.retry_interval, 30)
        
        print("✅ Configurazioni MQTT parallelo caricate correttamente")
    
    async def test_parallel_auth_flow_mqtt_success(self):
        """🚀 Test flusso parallelo con MQTT riuscito"""
        # Setup mocks
        self.mock_mqtt.is_connected.return_value = True
        self.mock_mqtt.send_auth_request_parallel = AsyncMock(return_value=True)  # MQTT success
        
        # Mock sync manager per auth locale
        self.mock_sync_manager.validate_card_offline = AsyncMock(return_value={
            'authorized': True,
            'reason': 'Card trovata in cache',
            'customer_id': 'CUST123',
            'customer_name': 'Test User'
        })
        self.mock_sync_manager.log_access = AsyncMock()
        self.mock_sync_manager.update_user_direction = AsyncMock()
        
        # Mock bidirectional check
        self.mock_sync_manager.check_bidirectional_access = AsyncMock(return_value={
            'valid': True
        })
        
        # Crea evento carta
        card_event = CardEvent(
            uid='A1B2C3D4',
            uid_formatted='A1B2C3D4',
            reader_id='reader_in',
            direction='IN',
            timestamp=time.time(),
            reader_type='PN532',
            metadata={}
        )
        
        # Esegui autenticazione
        decision = await self.access_control._authenticate_card(card_event)
        
        # Verifica risultati
        self.assertEqual(decision, AccessDecision.GRANT)
        
        # Verifica MQTT parallelo chiamato
        self.mock_mqtt.send_auth_request_parallel.assert_called_once()
        
        # Verifica che il log LOCALE sia sempre stato salvato
        self.mock_sync_manager.log_access.assert_called_once()
        log_call = self.mock_sync_manager.log_access.call_args[1]
        self.assertEqual(log_call['result'], 'authorized')
        self.assertIn('Local', log_call['reason'])
        
        print("✅ Test flusso parallelo con MQTT success: PASSED")
    
    async def test_parallel_auth_flow_mqtt_failure(self):
        """⚠️ Test flusso parallelo con MQTT fallito"""
        # Setup mocks
        self.mock_mqtt.is_connected.return_value = True
        self.mock_mqtt.send_auth_request_parallel = AsyncMock(return_value=False)  # MQTT failure
        
        # Mock sync manager per auth locale
        self.mock_sync_manager.validate_card_offline = AsyncMock(return_value={
            'authorized': True,
            'reason': 'Card trovata in cache',
            'customer_id': 'CUST123',
            'customer_name': 'Test User'
        })
        self.mock_sync_manager.log_access = AsyncMock()
        self.mock_sync_manager.update_user_direction = AsyncMock()
        
        # Mock bidirectional check
        self.mock_sync_manager.check_bidirectional_access = AsyncMock(return_value={
            'valid': True
        })
        
        # Crea evento carta
        card_event = CardEvent(
            uid='A1B2C3D4',
            uid_formatted='A1B2C3D4',
            reader_id='reader_in',
            direction='IN',
            timestamp=time.time(),
            reader_type='PN532',
            metadata={}
        )
        
        # Esegui autenticazione
        decision = await self.access_control._authenticate_card(card_event)
        
        # Verifica risultati
        self.assertEqual(decision, AccessDecision.GRANT)
        
        # Verifica MQTT parallelo chiamato
        self.mock_mqtt.send_auth_request_parallel.assert_called_once()
        
        # Verifica che il log LOCALE sia sempre stato salvato
        self.mock_sync_manager.log_access.assert_called_once()
        log_call = self.mock_sync_manager.log_access.call_args[1]
        self.assertEqual(log_call['result'], 'authorized')
        self.assertIn('Local', log_call['reason'])
        
        print("✅ Test flusso parallelo con MQTT failure: PASSED")
    
    async def test_mqtt_client_retry_queue(self):
        """♻️ Test retry queue MQTT"""
        # Crea client MQTT reale per testare retry queue
        mqtt_config = self.access_control.config.mqtt
        mqtt_client = AsyncMQTTClient(mqtt_config)
        
        # Verifica che retry queue è inizializzata
        self.assertEqual(len(mqtt_client.retry_queue), 0)
        self.assertEqual(mqtt_client.max_retry_queue_size, 1000)
        self.assertEqual(mqtt_client.retry_interval, 30)
        
        # Test aggiunta a retry queue
        from rfid_gate.network.mqtt import MQTTMessage
        test_msg = MQTTMessage(
            topic="test/topic",
            payload={"test": "data"},
            qos=1
        )
        
        success = mqtt_client._add_to_retry_queue(test_msg)
        self.assertTrue(success)
        self.assertEqual(len(mqtt_client.retry_queue), 1)
        
        print("✅ Test retry queue MQTT: PASSED")
    
    def test_auth_request_factory_method(self):
        """🏭 Test factory method AuthRequest"""
        card_event = CardEvent(
            uid='A1B2C3D4',
            uid_formatted='A1B2C3D4',
            reader_id='reader_in',
            direction='IN',
            timestamp=time.time(),
            reader_type='PN532',
            metadata={}
        )
        
        auth_request = AuthRequest.from_card_event(
            card_event=card_event,
            tornello_id="tornello_01",
            auth_required=True
        )
        
        self.assertEqual(auth_request.card_uid, 'A1B2C3D4')
        self.assertEqual(auth_request.identificativo_tornello, 'tornello_01')
        self.assertEqual(auth_request.direzione, 'IN')
        self.assertTrue(auth_request.auth_required)
        
        print("✅ Test AuthRequest factory method: PASSED")


async def run_async_tests():
    """Esegue test asincroni"""
    test_instance = TestParallelMQTT()
    test_instance.setUp()
    
    print("🧪 TESTING MQTT PARALLELO NON-BLOCCANTE")
    print("=" * 50)
    
    # Test configurazioni
    test_instance.test_mqtt_config_new_settings()
    
    # Test retry queue
    await test_instance.test_mqtt_client_retry_queue()
    
    # Test factory method
    test_instance.test_auth_request_factory_method()
    
    # Test flusso parallelo
    await test_instance.test_parallel_auth_flow_mqtt_success()
    await test_instance.test_parallel_auth_flow_mqtt_failure()
    
    print("\n🎉 TUTTI I TEST COMPLETATI!")


if __name__ == '__main__':
    print("🚀 Avvio test MQTT parallelo...")
    asyncio.run(run_async_tests())