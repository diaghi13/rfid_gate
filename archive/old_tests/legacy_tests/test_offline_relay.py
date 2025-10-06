#!/usr/bin/env python3
"""
Test specifico per verificare modalità offline e relè
"""
import sys
import os
sys.path.insert(0, 'src')

from config import Config
from offline_manager import OfflineManager
from relay_manager import RelayManager
from logger import AccessLogger

def test_offline_relay():
    print("🧪 TEST MODALITÀ OFFLINE E RELÈ")
    print("="*50)
    
    # 1. Verifica configurazione
    print("📋 Configurazione attuale:")
    print(f"   TORNELLO_ID: {Config.TORNELLO_ID}")
    print(f"   OFFLINE_MODE_ENABLED: {Config.OFFLINE_MODE_ENABLED}")
    print(f"   OFFLINE_ALLOW_ACCESS: {Config.OFFLINE_ALLOW_ACCESS}")
    print(f"   RELAY_IN_ENABLE: {Config.RELAY_IN_ENABLE}")
    print(f"   RELAY_IN_PIN: {Config.RELAY_IN_PIN}")
    
    # 2. Test Relay Manager
    print("\n⚡ Test Relay Manager...")
    relay_manager = RelayManager()
    if not relay_manager.initialize():
        print("❌ Relay Manager fallito")
        return False
    
    active_relays = relay_manager.get_active_relays()
    print(f"✅ Relè attivi: {active_relays}")
    
    # 3. Test attivazione relè diretto
    print("\n🔧 Test attivazione relè diretta...")
    if active_relays:
        relay_key = active_relays[0]
        success = relay_manager.activate_relay(relay_key, 1)  # 1 secondo
        if success:
            print(f"✅ Relè {relay_key} attivato con successo!")
        else:
            print(f"❌ Errore attivazione relè {relay_key}")
    
    # 4. Test Offline Manager
    print("\n🌐 Test Offline Manager...")
    logger = AccessLogger(Config.LOG_DIRECTORY)
    offline_manager = OfflineManager(None, logger)  # Senza MQTT = offline
    
    if not offline_manager.initialize():
        print("❌ Offline Manager fallito")
        return False
    
    # Forza modalità offline
    offline_manager.is_online = False
    print("🔴 Modalità offline forzata")
    
    # 5. Simula card in modalità offline
    print("\n📱 Simulazione card offline...")
    
    card_info = {
        'uid_formatted': 'TEST1234',
        'raw_id': 123456,
        'direction': 'in',
        'data': 'Test Card',
        'uid_hex': '0x1E240',
        'reader_id': 'in'
    }
    
    # Test decisione offline
    auth_result = offline_manager._handle_offline_access(card_info)
    
    print(f"📊 Risultato autenticazione offline:")
    print(f"   Autorizzato: {auth_result['authorized']}")
    print(f"   Messaggio: {auth_result['message']}")
    print(f"   Offline mode: {auth_result['offline_mode']}")
    
    # 6. Test completo con relè
    if auth_result['authorized'] and active_relays:
        print("\n⚡ Test attivazione relè post-auth...")
        direction = card_info.get('direction', 'in')
        
        if direction in active_relays:
            relay_success = relay_manager.activate_relay(direction, 2)
        else:
            relay_success = relay_manager.activate_relay(active_relays[0], 2)
        
        if relay_success:
            print("✅ SUCCESSO: Modalità offline + relè funzionante!")
        else:
            print("❌ ERRORE: Relè non attivato")
    
    # Cleanup
    relay_manager.cleanup()
    offline_manager.cleanup()
    
    return True

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("❌ Eseguire con sudo")
        print("💡 sudo python3 test_offline_relay.py")
        sys.exit(1)
    
    test_offline_relay()