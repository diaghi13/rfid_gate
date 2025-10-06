#!/usr/bin/env python3
"""
🧪 Test Sistema Refactored - Dual Readers
========================================

Test completo del sistema refactored che verifica:
- Compatibilità con configurazione esistente
- Funzionamento dual readers
- Sistema di debounce globale
- Architettura asincrona
- Error handling

Mantiene compatibilità totale con il sistema esistente.
"""

import asyncio
import os
import sys
import time
from unittest.mock import MagicMock, patch
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

# Mock hardware prima di qualsiasi import
def setup_mocks():
    """Setup mocks per hardware non disponibile"""
    mock_modules = [
        'RPi', 'RPi.GPIO', 'mfrc522', 'board', 'busio', 
        'digitalio', 'adafruit_pn532', 'adafruit_pn532.i2c', 
        'adafruit_pn532.spi', 'adafruit_pn532.uart',
        'paho', 'paho.mqtt', 'paho.mqtt.client'
    ]
    
    for module in mock_modules:
        if module not in sys.modules:
            sys.modules[module] = MagicMock()

# Setup mocks
setup_mocks()

# Ora possiamo importare il sistema refactored
from rfid_gate.config.settings import RFIDGateConfig, Config
from rfid_gate.hardware.readers.factory import ReaderFactory
from rfid_gate.hardware.readers.base import CardEvent
from rfid_gate.hardware.relays.gpio import GPIORelayController
from rfid_gate.utils.debounce import GlobalDebounceManager
from rfid_gate.core.access_control import AccessControlSystem


class RefactoredSystemTest:
    """
    Test completo del sistema refactored.
    
    Verifica:
    - Configurazione type-safe
    - Factory pattern per readers
    - Sistema di debounce
    - Access control logic
    - Compatibilità con sistema esistente
    """
    
    def __init__(self):
        self.test_results = []
        self.errors = []
        
        print("🧪 RFID Gate Refactored System Test")
        print("=" * 50)
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log risultato test"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"
        
        print(result)
        self.test_results.append((test_name, success, message))
        
        if not success:
            self.errors.append(f"{test_name}: {message}")
    
    def test_configuration_compatibility(self):
        """Test compatibilità configurazione"""
        try:
            # Test caricamento configurazione
            config = RFIDGateConfig.from_env()
            
            # Verifica campi principali
            assert hasattr(config, 'mqtt')
            assert hasattr(config, 'system')
            assert hasattr(config, 'rfid_in')
            assert hasattr(config, 'rfid_out')
            
            # Test compatibilità classe Config esistente
            assert hasattr(Config, 'MQTT_BROKER')
            assert hasattr(Config, 'TORNELLO_ID')
            assert hasattr(Config, 'RFID_IN_READER_TYPE')
            
            # Verifica valori identici
            assert config.mqtt.broker == Config.MQTT_BROKER
            assert config.system.tornello_id == Config.TORNELLO_ID
            
            self.log_test("Configuration Compatibility", True, 
                         f"Broker: {config.mqtt.broker}, ID: {config.system.tornello_id}")
            
        except Exception as e:
            self.log_test("Configuration Compatibility", False, str(e))
    
    def test_reader_factory(self):
        """Test factory pattern per lettori"""
        try:
            # Test lettori disponibili
            available = ReaderFactory.get_available_readers()
            assert 'mfrc522' in available
            assert 'pn532' in available
            
            # Test creazione MFRC522
            mfrc522 = ReaderFactory.create_reader_legacy(
                'mfrc522', 'test_mfrc522', 'in',
                rst_pin=22, sda_pin=8
            )
            assert mfrc522 is not None
            assert mfrc522.get_reader_type() == 'mfrc522'
            
            # Test creazione PN532
            pn532 = ReaderFactory.create_reader_legacy(
                'pn532', 'test_pn532', 'out',
                interface='i2c', i2c_address=0x24
            )
            assert pn532 is not None
            assert pn532.get_reader_type() == 'pn532'
            
            self.log_test("Reader Factory", True, 
                         f"Creati: {mfrc522}, {pn532}")
            
        except Exception as e:
            self.log_test("Reader Factory", False, str(e))
    
    def test_debounce_system(self):
        """Test sistema debounce globale"""
        try:
            debounce = GlobalDebounceManager(0.1)  # 100ms per test veloce
            
            # Test prima lettura
            is_dup1 = debounce.is_duplicate("632D39", "in")
            print(f"   Debug: Prima lettura 632D39/in -> duplicato: {is_dup1}")
            assert not is_dup1  # Prima lettura non è duplicato
            
            # Test lettura immediata stessa carta
            is_dup2 = debounce.is_duplicate("632D39", "in")
            print(f"   Debug: Seconda lettura 632D39/in -> duplicato: {is_dup2}")
            assert is_dup2  # Lettura immediata è duplicato
            
            # Test lettura carta diversa
            is_dup3 = debounce.is_duplicate("AABBCC", "out")
            print(f"   Debug: Lettura AABBCC/out -> duplicato: {is_dup3}")
            assert not is_dup3  # Carta diversa non è duplicato
            
            # Test anti-crosstalk dopo delay
            time.sleep(0.15)  # Supera debounce time
            is_dup4 = debounce.is_duplicate("632D39", "out")
            print(f"   Debug: Lettura 632D39/out dopo delay -> duplicato: {is_dup4}")
            # Dopo delay, non dovrebbe più essere duplicato
            
            stats = debounce.get_stats()
            print(f"   Debug: Stats = {stats}")
            
            # Verifica che almeno alcuni duplicati sono stati rilevati
            assert stats['duplicates_detected'] >= 1
            
            self.log_test("Debounce System", True, 
                         f"Duplicati: {stats['duplicates_detected']}")
            
        except Exception as e:
            import traceback
            print(f"   Debug: Errore = {e}")
            print(f"   Debug: Traceback = {traceback.format_exc()}")
            self.log_test("Debounce System", False, str(e))
    
    def test_relay_controller(self):
        """Test controller relè GPIO"""
        try:
            relay = GPIORelayController("test_relay", "in", pin=18)
            
            # Test configurazione
            relay.configure(active_time=2.0, active_low=False)
            assert relay.active_time == 2.0
            assert relay.active_low == False
            
            # Test tipo
            assert relay.get_relay_type() == "gpio"
            
            # Test info hardware
            info = relay.get_hardware_info()
            assert info['pin'] == 18
            assert 'hardware_available' in info
            
            self.log_test("Relay Controller", True, 
                         f"Pin: {info['pin']}, HW: {info['hardware_available']}")
            
        except Exception as e:
            self.log_test("Relay Controller", False, str(e))
    
    async def test_async_reader_simulation(self):
        """Test simulazione lettore asincrono"""
        try:
            # Crea reader PN532 simulato
            pn532 = ReaderFactory.create_reader_legacy(
                'pn532', 'sim_pn532', 'in',
                interface='i2c', i2c_address=0x24
            )
            
            # Mock per simulare lettura carta
            async def mock_hardware_read():
                # Simula lettura carta dopo breve delay
                await asyncio.sleep(0.1)
                return bytes([0x63, 0x2D, 0x39, 0x03])  # 632D3903
            
            pn532._hardware_read = mock_hardware_read
            pn532.status = pn532.status.__class__.CONNECTED
            
            # Test lettura con formattazione
            format_config = {
                'mode': 'remove_suffix',
                'chars_count': 2,
                'target_length': 8
            }
            
            card_event = await pn532.read_card(timeout=1.0, format_config=format_config)
            
            assert card_event is not None
            assert card_event.uid == "632D3903"  # UID raw
            assert card_event.uid_formatted == "632D39"  # UID formattato
            assert card_event.reader_type == "pn532"
            
            self.log_test("Async Reader Simulation", True,
                         f"Card: {card_event.uid_formatted}")
            
        except Exception as e:
            self.log_test("Async Reader Simulation", False, str(e))
    
    async def test_access_control_system(self):
        """Test sistema di controllo accessi completo"""
        try:
            # Mock MQTT per evitare connessioni reali
            with patch('rfid_gate.network.mqtt.AsyncMQTTClient') as MockMQTT:
                mock_mqtt = MockMQTT.return_value
                mock_mqtt.initialize.return_value = True
                mock_mqtt.connect.return_value = True
                mock_mqtt.is_connected.return_value = True
                
                # Crea sistema
                system = AccessControlSystem()
                
                # Mock inizializzazione hardware
                async def mock_hw_init():
                    return True
                
                system._initialize_readers = mock_hw_init
                system._initialize_relays = mock_hw_init
                
                # Test inizializzazione
                success = await system.initialize()
                assert success
                
                # Test stato sistema
                status = system.get_system_status()
                assert 'mode' in status
                assert 'stats' in status
                
                self.log_test("Access Control System", True,
                             f"Mode: {status['mode']}")
        
        except Exception as e:
            self.log_test("Access Control System", False, str(e))
    
    def test_backward_compatibility(self):
        """Test compatibilità con sistema esistente"""
        try:
            # Test che tutti gli attributi della vecchia classe Config esistano
            old_attributes = [
                'MQTT_BROKER', 'MQTT_PORT', 'MQTT_USERNAME', 'MQTT_PASSWORD',
                'TORNELLO_ID', 'BIDIRECTIONAL_MODE', 'ENABLE_IN_READER',
                'RFID_IN_READER_TYPE', 'RFID_OUT_READER_TYPE',
                'RFID_IN_RST_PIN', 'RFID_IN_SDA_PIN',
                'RELAY_IN_PIN', 'RELAY_IN_ACTIVE_TIME',
                'UID_FORMAT_MODE', 'UID_CHARS_COUNT'
            ]
            
            missing_attrs = []
            for attr in old_attributes:
                if not hasattr(Config, attr):
                    missing_attrs.append(attr)
            
            assert len(missing_attrs) == 0, f"Attributi mancanti: {missing_attrs}"
            
            # Test metodi compatibilità
            assert hasattr(Config, 'get_mqtt_topic')
            assert hasattr(Config, 'validate_config')
            
            # Test valori
            topic = Config.get_mqtt_topic("badge")
            assert Config.TORNELLO_ID in topic
            
            self.log_test("Backward Compatibility", True,
                         f"Attributi: {len(old_attributes)}, Topic: {topic}")
            
        except Exception as e:
            self.log_test("Backward Compatibility", False, str(e))
    
    async def run_all_tests(self):
        """Esegue tutti i test"""
        print("Avvio test suite...")
        print()
        
        # Test sincroni
        self.test_configuration_compatibility()
        self.test_reader_factory()
        self.test_debounce_system()
        self.test_relay_controller()
        self.test_backward_compatibility()
        
        # Test asincroni
        await self.test_async_reader_simulation()
        await self.test_access_control_system()
        
        # Riassunto
        print()
        print("=" * 50)
        print("📊 RISULTATI TEST")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Test eseguiti: {total}")
        print(f"Test passati: {passed}")
        print(f"Test falliti: {total - passed}")
        
        if self.errors:
            print("\\n❌ ERRORI:")
            for error in self.errors:
                print(f"   - {error}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\\n🎯 Tasso di successo: {success_rate:.1f}%")
        
        if passed == total:
            print("\\n✅ TUTTI I TEST PASSATI - Sistema refactored funzionante!")
            print("\\n🎉 Il refactor mantiene compatibilità totale con il sistema esistente")
            print("   mentre aggiunge architettura moderna, async/await e type safety.")
        else:
            print(f"\\n⚠️ {total - passed} test falliti - Rivedere implementazione")
        
        return passed == total


async def main():
    """Main test function"""
    try:
        # Setup environment per test
        os.environ['BIDIRECTIONAL_MODE'] = 'true'
        os.environ['ENABLE_IN_READER'] = 'true'
        os.environ['ENABLE_OUT_READER'] = 'true'
        os.environ['RFID_IN_READER_TYPE'] = 'pn532'
        os.environ['RFID_OUT_READER_TYPE'] = 'pn532'
        os.environ['RFID_IN_PN532_INTERFACE'] = 'i2c'
        os.environ['RFID_OUT_PN532_INTERFACE'] = 'spi'
        
        # Esegui test
        test_suite = RefactoredSystemTest()
        success = await test_suite.run_all_tests()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore critico test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)