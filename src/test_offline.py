#!/usr/bin/env python3
"""
Script di test per verificare il funzionamento del sistema offline
"""

import sys
import os
import time

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from offline_manager import OfflineManager
from mqtt_client import MQTTClient
from logger import AccessLogger

def test_offline_system():
    """Test completo del sistema offline"""
    print("🧪 TEST SISTEMA OFFLINE")
    print("=" * 50)
    
    # Inizializza componenti
    print("1️⃣ Inizializzazione componenti...")
    logger = AccessLogger(Config.LOG_DIRECTORY)
    
    # Test con MQTT (se disponibile)
    mqtt_client = None
    try:
        mqtt_client = MQTTClient()
        mqtt_client.initialize()
        if mqtt_client.connect():
            print("✅ MQTT Client: Connesso")
        else:
            print("⚠️ MQTT Client: Non connesso")
    except Exception as e:
        print(f"⚠️ MQTT Client: Errore - {e}")
    
    # Inizializza Offline Manager
    print("\n2️⃣ Test Offline Manager...")
    offline_manager = OfflineManager(mqtt_client, logger)
    
    if offline_manager.initialize():
        print("✅ Offline Manager: Inizializzato")
    else:
        print("❌ Offline Manager: Errore inizializzazione")
        return
    
    # Mostra status
    print("\n3️⃣ Status sistema:")
    status = offline_manager.get_status()
    print(f"   🌐 Online: {status['online']}")
    print(f"   🔧 Abilitato: {status['enabled']}")
    print(f"   🚪 Accesso offline: {status['allow_offline_access']}")
    print(f"   📦 Coda: {status['queue_size']} elementi")
    
    # Test accesso simulato
    print("\n4️⃣ Test accesso card simulata...")
    fake_card_info = {
        'uid_formatted': 'TEST1234',
        'direction': 'in',
        'raw_id': 123456789,
        'data': 'Test Card',
        'data_length': 9,
        'uid_hex': '0x75BCD15'
    }
    
    print(f"📱 Card simulata: {fake_card_info['uid_formatted']}")
    
    # Test autenticazione
    auth_result = offline_manager.handle_card_access(fake_card_info)
    
    print(f"📋 Risultato autenticazione:")
    print(f"   ✅ Autorizzato: {auth_result.get('authorized', False)}")
    print(f"   🌐 Modalità: {'Offline' if auth_result.get('offline_mode', False) else 'Online'}")
    print(f"   💬 Messaggio: {auth_result.get('message', 'N/A')}")
    
    if auth_result.get('error'):
        print(f"   ❌ Errore: {auth_result.get('error')}")
    
    # Verifica coda se offline
    if auth_result.get('offline_mode', False):
        new_status = offline_manager.get_status()
        print(f"\n📦 Elementi in coda dopo test: {new_status['queue_size']}")
    
    # Test connessione
    print("\n5️⃣ Test controllo connessione...")
    connection_result = offline_manager.check_connection()
    print(f"🔌 Risultato test connessione: {'✅ Online' if connection_result else '🔴 Offline'}")
    
    # Cleanup
    print("\n6️⃣ Cleanup...")
    offline_manager.cleanup()
    if mqtt_client:
        mqtt_client.disconnect()
    
    print("\n✅ Test completato!")

def test_config():
    """Test configurazioni"""
    print("🔧 TEST CONFIGURAZIONI")
    print("=" * 30)
    
    print(f"OFFLINE_MODE_ENABLED: {Config.OFFLINE_MODE_ENABLED}")
    print(f"OFFLINE_ALLOW_ACCESS: {Config.OFFLINE_ALLOW_ACCESS}")
    print(f"OFFLINE_SYNC_ENABLED: {Config.OFFLINE_SYNC_ENABLED}")
    print(f"OFFLINE_MAX_QUEUE_SIZE: {Config.OFFLINE_MAX_QUEUE_SIZE}")
    print(f"CONNECTION_CHECK_INTERVAL: {Config.CONNECTION_CHECK_INTERVAL}")
    
    # Valida configurazione
    errors = Config.validate_config()
    if errors:
        print("\n❌ Errori configurazione:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("\n✅ Configurazione valida")

def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Sistema Offline")
    parser.add_argument("--config", action="store_true", help="Testa solo configurazioni")
    parser.add_argument("--full", action="store_true", help="Test completo sistema")
    
    args = parser.parse_args()
    
    if args.config:
        test_config()
    elif args.full:
        test_offline_system()
    else:
        print("🧪 MENU TEST SISTEMA OFFLINE")
        print("=" * 40)
        print("1. Test configurazioni")
        print("2. Test sistema completo")
        print()
        
        choice = input("Scegli opzione (1-2): ").strip()
        
        if choice == "1":
            test_config()
        elif choice == "2":
            test_offline_system()
        else:
            print("❌ Opzione non valida")

if __name__ == "__main__":
    main()