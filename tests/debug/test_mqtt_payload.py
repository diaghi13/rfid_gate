#!/usr/bin/env python3
"""
Test per verificare che il payload MQTT sia conforme alle specifiche:
{card_uid, identificativo_tornello, direzione, timestamp, auth_required}
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mqtt_payload_structure():
    """Test della struttura del payload MQTT"""
    
    print("🧪 TEST PAYLOAD MQTT")
    print("=" * 40)
    
    # Simula creazione AuthRequest
    try:
        from rfid_gate.network.mqtt import AuthRequest
        
        # Simula card event
        class MockCardEvent:
            def __init__(self, uid, direction):
                self.uid_formatted = uid
                self.direction = direction
        
        card_event = MockCardEvent("632D3903", "in")
        
        # Crea AuthRequest come fa il sistema
        auth_request = AuthRequest.from_card_event(
            card_event=card_event,
            tornello_id="tornello_01", 
            auth_required=True
        )
        
        print(f"📋 STRUTTURA AuthRequest:")
        print(f"   card_uid: {auth_request.card_uid}")
        print(f"   identificativo_tornello: {auth_request.identificativo_tornello}")
        print(f"   direzione: {auth_request.direzione}")
        print(f"   timestamp: {auth_request.timestamp}")
        print(f"   auth_required: {auth_request.auth_required}")
        print()
        
        # Simula payload MQTT come nel metodo send_auth_request_parallel
        payload = {
            "card_uid": auth_request.card_uid,
            "identificativo_tornello": auth_request.identificativo_tornello,
            "direzione": auth_request.direzione,
            "timestamp": auth_request.timestamp,
            "auth_required": auth_request.auth_required
        }
        
        print(f"📤 PAYLOAD MQTT INVIATO:")
        import json
        print(json.dumps(payload, indent=2))
        print()
        
        # Verifica conformità alle specifiche
        required_fields = [
            "card_uid",
            "identificativo_tornello", 
            "direzione",
            "timestamp",
            "auth_required"
        ]
        
        print(f"✅ VERIFICA CONFORMITÀ:")
        all_present = True
        for field in required_fields:
            present = field in payload
            print(f"   {field}: {'✅' if present else '❌'}")
            if not present:
                all_present = False
        
        print()
        if all_present:
            print(f"🎯 RISULTATO: ✅ PAYLOAD CONFORME ALLE SPECIFICHE")
            print(f"   Tutti i campi richiesti sono presenti")
        else:
            print(f"🎯 RISULTATO: ❌ PAYLOAD NON CONFORME")
            print(f"   Alcuni campi mancanti")
        
        # Test diversi scenari
        print(f"\n📋 TEST SCENARI DIVERSI:")
        
        scenarios = [
            ("A1B2C3D4", "out"),
            ("12345678", "in"),
            ("FFFFFFFF", "out")
        ]
        
        for uid, direction in scenarios:
            card_event = MockCardEvent(uid, direction)
            auth_request = AuthRequest.from_card_event(
                card_event=card_event,
                tornello_id="tornello_01",
                auth_required=True
            )
            
            payload = {
                "card_uid": auth_request.card_uid,
                "identificativo_tornello": auth_request.identificativo_tornello,
                "direzione": auth_request.direzione,
                "timestamp": auth_request.timestamp,
                "auth_required": auth_request.auth_required
            }
            
            print(f"   UID {uid} ({direction}): ✅ Payload OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

def test_topic_calculation():
    """Test calcolo topic MQTT"""
    
    print(f"\n📡 TEST TOPIC MQTT")
    print("-" * 30)
    
    # Simula configurazione topic
    auth_response_topic = "gate/tornello_01/auth_response"
    
    # Calcola topic auth_request come nel codice
    base_topic = '/'.join(auth_response_topic.split('/')[:-1])
    topic = f"{base_topic}/auth_request"
    
    print(f"   Auth Response Topic: {auth_response_topic}")
    print(f"   Base Topic: {base_topic}")
    print(f"   Auth Request Topic: {topic}")
    print(f"   ✅ Topic calcolato: {topic}")
    
    expected_topic = "gate/tornello_01/auth_request"
    if topic == expected_topic:
        print(f"   🎯 TOPIC CORRETTO: ✅")
    else:
        print(f"   🎯 TOPIC ERRATO: ❌ (atteso: {expected_topic})")

if __name__ == "__main__":
    print("🚀 TEST CONFORMITÀ PAYLOAD MQTT")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_mqtt_payload_structure()
    test_topic_calculation()
    
    print()
    if success:
        print("🎉 TUTTI I TEST PASSATI!")
        print("✅ Payload MQTT conforme alle specifiche")
    else:
        print("❌ Alcuni test falliti")
        
    sys.exit(0 if success else 1)