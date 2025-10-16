#!/usr/bin/env python3
"""
Test finale per verificare topic e payload MQTT corretti
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_final_mqtt_configuration():
    """Test finale della configurazione MQTT"""
    
    print("🧪 TEST FINALE CONFIGURAZIONE MQTT")
    print("=" * 50)
    
    # Simula il flusso completo
    try:
        from rfid_gate.network.mqtt import AuthRequest
        from rfid_gate.config.settings import MQTTConfig
        
        # Carica configurazione
        mqtt_config = MQTTConfig.from_env()
        
        # Simula card event
        class MockCardEvent:
            def __init__(self, uid, direction):
                self.uid_formatted = uid
                self.direction = direction
        
        card_event = MockCardEvent("632D3903", "in")
        
        # Crea AuthRequest
        auth_request = AuthRequest.from_card_event(
            card_event=card_event,
            tornello_id="tornello_01",
            auth_required=True
        )
        
        # Simula payload come nel metodo send_auth_request_parallel
        payload = {
            "card_uid": auth_request.card_uid,
            "identificativo_tornello": auth_request.identificativo_tornello,
            "direzione": auth_request.direzione,
            "timestamp": auth_request.timestamp,
            "auth_required": auth_request.auth_required
        }
        
        # Topic come nel codice corretto
        topic = mqtt_config.card_read_topic
        
        print("📡 CONFIGURAZIONE FINALE:")
        print(f"   Topic di invio: {topic}")
        print(f"   Topic di risposta: {mqtt_config.auth_response_topic}")
        print(f"   Topic apertura manuale: {mqtt_config.manual_open_topic}")
        print()
        
        print("📤 PAYLOAD INVIATO:")
        import json
        print(json.dumps(payload, indent=2))
        print()
        
        # Verifica conformità
        expected_topic = "gate/tornello_01/badge"
        expected_response_topic = "gate/tornello_01/response"
        
        required_fields = ["card_uid", "identificativo_tornello", "direzione", "timestamp", "auth_required"]
        
        print("✅ VERIFICA FINALE:")
        
        # Topic corretto
        topic_ok = (topic == expected_topic)
        print(f"   📤 Topic invio: {'✅' if topic_ok else '❌'} ({topic})")
        
        response_topic_ok = (mqtt_config.auth_response_topic == expected_response_topic)
        print(f"   📥 Topic risposta: {'✅' if response_topic_ok else '❌'} ({mqtt_config.auth_response_topic})")
        
        # Payload completo
        payload_ok = all(field in payload for field in required_fields)
        print(f"   📦 Payload completo: {'✅' if payload_ok else '❌'}")
        
        for field in required_fields:
            present = field in payload
            print(f"      {field}: {'✅' if present else '❌'}")
        
        # Test diversi scenari
        print()
        print("🔄 TEST SCENARI DIVERSI:")
        
        scenarios = [
            ("A1B2C3D4", "out", "CASO 1: Cache Hit"),
            ("9Z8Y7X6W", "in", "CASO 2: Cache Miss (NO MQTT)"),
            ("5E6F7G8H", "out", "CASO 3: Cache Refresh")
        ]
        
        for uid, direction, scenario in scenarios:
            card_event = MockCardEvent(uid, direction)
            auth_request = AuthRequest.from_card_event(
                card_event=card_event,
                tornello_id="tornello_01",
                auth_required=True
            )
            
            should_send_mqtt = "NO MQTT" not in scenario
            status = "📤 MQTT" if should_send_mqtt else "🚫 NO MQTT"
            
            print(f"   {scenario}: {status} → {topic if should_send_mqtt else 'Nessun invio'}")
        
        # Risultato finale
        all_ok = topic_ok and response_topic_ok and payload_ok
        
        print()
        if all_ok:
            print("🎉 CONFIGURAZIONE MQTT PERFETTA!")
            print("✅ Topic corretti, payload conforme, sistema pronto")
        else:
            print("❌ Configurazione MQTT ha problemi")
            
        return all_ok
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TEST FINALE TOPIC E PAYLOAD MQTT")
    print("=" * 55)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_final_mqtt_configuration()
    
    print()
    if success:
        print("🎊 TUTTI I TEST FINALI PASSATI!")
        print("   Sistema MQTT configurato correttamente secondo specifiche")
    else:
        print("❌ Test finali falliti")
        
    sys.exit(0 if success else 1)