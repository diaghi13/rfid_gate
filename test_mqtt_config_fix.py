#!/usr/bin/env python3
"""
🧪 Test MQTT Configuration Fix
===============================
Verifica che i topic MQTT vengano letti correttamente dal .env
invece di usare valori hardcoded.
"""

import os
import sys

# Aggiungi il path per import
sys.path.insert(0, '/Users/davidedonghi/Apps/_micro services/rfid_gate')

def test_mqtt_config_loading():
    """Test caricamento configurazione MQTT dal .env"""
    
    print("🧪 Test MQTT Configuration Loading")
    print("=" * 50)
    
    try:
        from rfid_gate.config.settings import _config_instance
        
        # Usa l'istanza di configurazione
        config = _config_instance
        
        print(f"📡 MQTT Configuration:")
        print(f"   Card Read Topic: {config.mqtt.card_read_topic}")
        print(f"   Auth Response Topic: {config.mqtt.auth_response_topic}")
        print(f"   Manual Open Topic: {config.mqtt.manual_open_topic}")
        print(f"   Tornello ID: {config.system.tornello_id}")
        
        # Verifica che i topic usino l'ID tornello
        expected_card_read = "gate/tornello_01/badge"
        expected_auth_response = "gate/tornello_01/auth_response"
        
        print(f"\n✅ Verifiche:")
        print(f"   Card Read Topic == '{expected_card_read}': {config.mqtt.card_read_topic == expected_card_read}")
        print(f"   Auth Response Topic == '{expected_auth_response}': {config.mqtt.auth_response_topic == expected_auth_response}")
        
        return config
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return None

def test_mqtt_topic_construction():
    """Test costruzione dinamica topic MQTT"""
    
    print(f"\n🔧 Test MQTT Topic Construction")
    print("=" * 50)
    
    try:
        from rfid_gate.config.settings import _config_instance
        
        config = _config_instance
        
        # Simula costruzione topic per auth_request
        auth_response_topic = config.mqtt.auth_response_topic
        base_topic = '/'.join(auth_response_topic.split('/')[:-1])
        auth_request_topic = f"{base_topic}/auth_request"
        
        print(f"📤 Topic Construction:")
        print(f"   Auth Response Topic: {auth_response_topic}")
        print(f"   Base Topic: {base_topic}")
        print(f"   Auth Request Topic: {auth_request_topic}")
        
        expected_auth_request = "gate/tornello_01/auth_request"
        
        print(f"\n✅ Verifica:")
        print(f"   Auth Request Topic == '{expected_auth_request}': {auth_request_topic == expected_auth_request}")
        
        return auth_request_topic == expected_auth_request
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 MQTT Configuration Fix Test")
    print("=" * 50)
    print("Verifica che i topic MQTT usino configurazione .env")
    print("invece di valori hardcoded.")
    print()
    
    # Test 1: Caricamento configurazione
    config = test_mqtt_config_loading()
    
    if config is None:
        print("\n❌ Test fallito: impossibile caricare configurazione")
        return
    
    # Test 2: Costruzione topic dinamica
    topic_ok = test_mqtt_topic_construction()
    
    print(f"\n🎯 RISULTATO FINALE:")
    print("=" * 50)
    
    if topic_ok:
        print("✅ MQTT Configuration Fix: SUCCESSO")
        print("   I topic MQTT ora usano correttamente la configurazione .env")
        print("   invece di valori hardcoded.")
    else:
        print("❌ MQTT Configuration Fix: FALLITO")
        print("   Ci sono ancora problemi nella costruzione dei topic.")
    
    print(f"\n📋 Configurazione Attiva:")
    print(f"   Card Read: {config.mqtt.card_read_topic}")
    print(f"   Auth Response: {config.mqtt.auth_response_topic}")
    print(f"   Manual Open: {config.mqtt.manual_open_topic}")

if __name__ == "__main__":
    main()