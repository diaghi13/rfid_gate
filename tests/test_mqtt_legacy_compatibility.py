#!/usr/bin/env python3
"""
🧪 Test MQTT Legacy Compatibility
================================

Test per verificare che i payload MQTT siano identici 
alla versione legacy per garantire compatibilità backend.
"""

import unittest
import json
from datetime import datetime
from rfid_gate.network.mqtt import CardReadMessage, AuthRequest
from rfid_gate.hardware.readers.base import CardEvent


class TestMQTTLegacyCompatibility(unittest.TestCase):
    """Test compatibilità payload MQTT con versione legacy"""
    
    def setUp(self):
        """Setup test data"""
        self.tornello_id = "GATE001"
        self.card_uid = "E298C6EB"
        self.direction = "in"
        self.timestamp_iso = "2024-01-15T10:30:00.123456"
        
        # Simula CardEvent
        self.card_event = CardEvent(
            uid="E298C6EB",
            uid_formatted="E298C6EB", 
            direction="in",
            reader_type="mfrc522",
            reader_id="reader_001",  # ✅ Aggiungi reader_id richiesto
            timestamp=1640995200.123,
            metadata={"test": "data"}
        )
        # Aggiungi campi extra per compatibilità
        self.card_event.uid_hex = "0xE298C6EB"
        self.card_event.raw_uid = "0xE298C6EB"
        self.card_event.data = {"sector1": "test"}
    
    def test_card_read_message_payload_structure(self):
        """Test che CardReadMessage generi payload identico al legacy"""
        
        # Crea messaggio usando factory method
        message = CardReadMessage.from_card_event(
            card_event=self.card_event,
            tornello_id=self.tornello_id,
            auth_required=True
        )
        
        # Payload atteso (identico al legacy)
        expected_payload = {
            "card_uid": "E298C6EB",
            "identificativo_tornello": "GATE001", 
            "direzione": "in",
            "timestamp": message.timestamp,  # ISO format
            "raw_id": "0xE298C6EB",
            "card_data": {"sector1": "test"},
            "hex_id": "0xE298C6EB",
            "auth_required": True,
            "reader_id": "mfrc522"
        }
        
        # Crea payload dal messaggio (come nel send_card_read)
        actual_payload = {
            "card_uid": message.card_uid,
            "identificativo_tornello": message.identificativo_tornello,
            "direzione": message.direzione,
            "timestamp": message.timestamp,
            "raw_id": message.raw_id,
            "card_data": message.card_data,
            "hex_id": message.hex_id,
            "auth_required": message.auth_required,
            "reader_id": message.reader_id
        }
        
        # Verifica struttura identica
        self.assertEqual(actual_payload.keys(), expected_payload.keys())
        self.assertEqual(actual_payload["card_uid"], expected_payload["card_uid"])
        self.assertEqual(actual_payload["identificativo_tornello"], expected_payload["identificativo_tornello"])
        self.assertEqual(actual_payload["direzione"], expected_payload["direzione"])
        self.assertEqual(actual_payload["auth_required"], expected_payload["auth_required"])
        self.assertEqual(actual_payload["reader_id"], expected_payload["reader_id"])
        
        print("✅ CardReadMessage payload structure LEGACY COMPATIBLE")
        print(f"📦 Payload: {json.dumps(actual_payload, indent=2)}")
    
    def test_auth_request_payload_structure(self):
        """Test che AuthRequest generi payload identico al legacy"""
        
        # Crea richiesta usando factory method
        request = AuthRequest.from_card_event(
            card_event=self.card_event,
            tornello_id=self.tornello_id,
            auth_required=True
        )
        
        # Payload atteso (identico al legacy)
        expected_payload = {
            "card_uid": "E298C6EB",
            "identificativo_tornello": "GATE001",
            "direzione": "in", 
            "timestamp": request.timestamp,  # ISO format
            "auth_required": True
        }
        
        # Crea payload dalla richiesta (come nel send_auth_request)
        actual_payload = {
            "card_uid": request.card_uid,
            "identificativo_tornello": request.identificativo_tornello,
            "direzione": request.direzione,
            "timestamp": request.timestamp,
            "auth_required": request.auth_required
        }
        
        # Verifica struttura identica
        self.assertEqual(actual_payload.keys(), expected_payload.keys())
        self.assertEqual(actual_payload["card_uid"], expected_payload["card_uid"])
        self.assertEqual(actual_payload["identificativo_tornello"], expected_payload["identificativo_tornello"])
        self.assertEqual(actual_payload["direzione"], expected_payload["direzione"])
        self.assertEqual(actual_payload["auth_required"], expected_payload["auth_required"])
        
        print("✅ AuthRequest payload structure LEGACY COMPATIBLE")
        print(f"📦 Payload: {json.dumps(actual_payload, indent=2)}")
    
    def test_timestamp_conversion(self):
        """Test conversione timestamp da float a ISO string"""
        
        message = CardReadMessage.from_card_event(
            card_event=self.card_event,
            tornello_id=self.tornello_id
        )
        
        # Verifica che timestamp sia ISO string (non float)
        self.assertIsInstance(message.timestamp, str)
        
        # Verifica che sia parsabile come datetime
        try:
            datetime.fromisoformat(message.timestamp.replace('Z', ''))
            print("✅ Timestamp conversion: float → ISO string")
        except ValueError:
            self.fail("Timestamp non è un ISO string valido")
    
    def test_legacy_field_names(self):
        """Test che i nomi dei campi siano identici al legacy"""
        
        message = CardReadMessage.from_card_event(
            card_event=self.card_event,
            tornello_id=self.tornello_id
        )
        
        # Verifica nomi campi legacy
        self.assertTrue(hasattr(message, 'identificativo_tornello'))
        self.assertTrue(hasattr(message, 'direzione'))
        self.assertTrue(hasattr(message, 'raw_id'))
        self.assertTrue(hasattr(message, 'hex_id'))
        self.assertTrue(hasattr(message, 'reader_id'))
        
        # Verifica valori corretti
        self.assertEqual(message.identificativo_tornello, "GATE001")
        self.assertEqual(message.direzione, "in")
        self.assertEqual(message.raw_id, "0xE298C6EB")
        self.assertEqual(message.hex_id, "0xE298C6EB")
        self.assertEqual(message.reader_id, "mfrc522")
        
        print("✅ Legacy field names preserved")
    
    def test_json_serialization(self):
        """Test che il payload sia serializzabile in JSON"""
        
        message = CardReadMessage.from_card_event(
            card_event=self.card_event,
            tornello_id=self.tornello_id
        )
        
        payload = {
            "card_uid": message.card_uid,
            "identificativo_tornello": message.identificativo_tornello,
            "direzione": message.direzione,
            "timestamp": message.timestamp,
            "raw_id": message.raw_id,
            "card_data": message.card_data,
            "hex_id": message.hex_id,
            "auth_required": message.auth_required,
            "reader_id": message.reader_id
        }
        
        # Test serializzazione JSON
        try:
            json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
            self.assertIsInstance(json_payload, str)
            print("✅ JSON serialization compatible")
            print(f"📄 JSON: {json_payload}")
        except (TypeError, ValueError) as e:
            self.fail(f"Errore serializzazione JSON: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)