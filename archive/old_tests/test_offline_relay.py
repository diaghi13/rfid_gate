#!/usr/bin/env python3
"""
Test integrazione Offline + Relè
Verifica che il relè scatti quando il sistema è offline
"""
import sys
import time
from datetime import datetime

# Aggiungi src al path
sys.path.insert(0, 'src')

def test_offline_relay_integration():
    """Test integrazione offline manager + relay manager"""
    print("🔗 TEST INTEGRAZIONE OFFLINE + RELÈ")
    print("=" * 50)
    
    try:
        from config import Config
        from offline_manager import OfflineManager
        from relay_manager import RelayManager
        from logger import AccessLogger
        
        print("✅ Import moduli: OK")
        
        # Verifica configurazione
        print(f"\n📋 CONFIGURAZIONE:")
        print(f"   OFFLINE_MODE_ENABLED: {Config.OFFLINE_MODE_ENABLED}")
        print(f"   OFFLINE_ALLOW_ACCESS: {Config.OFFLINE_ALLOW_ACCESS}")
        print(f"   RELAY_IN_ENABLE: {Config.RELAY_IN_ENABLE}")
        print(f"   RELAY_IN_PIN: {Config.RELAY_IN_PIN}")
        
        if not Config.OFFLINE_MODE_ENABLED:
            print("❌ Modalità offline disabilitata")
            return False
        
        if not Config.RELAY_IN_ENABLE:
            print("❌ Relè IN disabilitato")
            return False
        
        # Inizializza componenti
        logger = AccessLogger(Config.LOG_DIRECTORY)
        
        # Test 1: Offline Manager
        print(f"\n🧪 TEST 1: INIZIALIZZAZIONE OFFLINE MANAGER")
        offline_manager = OfflineManager(mqtt_client=None, logger=logger)
        
        if offline_manager.initialize():
            print("✅ Offline Manager inizializzato")
        else:
            print("❌ Inizializzazione Offline Manager fallita")
            return False
        
        # Forza stato offline
        offline_manager.is_online = False
        print("🔴 Stato forzato: OFFLINE")
        
        # Test 2: Relay Manager
        print(f"\n🧪 TEST 2: INIZIALIZZAZIONE RELAY MANAGER")
        relay_manager = RelayManager()
        
        if relay_manager.initialize():
            print("✅ Relay Manager inizializzato")
        else:
            print("❌ Inizializzazione Relay Manager fallita")
            return False
        
        active_relays = relay_manager.get_active_relays()
        print(f"⚡ Relè attivi: {active_relays}")
        
        if not active_relays:
            print("❌ Nessun relè attivo")
            return False
        
        # Test 3: Simulazione card offline
        print(f"\n🧪 TEST 3: SIMULAZIONE CARD OFFLINE")
        
        card_info = {
            'raw_id': 123456789,
            'uid_formatted': 'TESTOFFLINE',
            'uid_hex': '0x75bcd15',
            'data': 'Test Offline Relay',
            'data_length': 18,
            'direction': 'in',
            'reader_id': 'test_reader',
            'timestamp': time.time()
        }
        
        print(f"📱 Card simulata: {card_info['uid_formatted']}")
        
        # PASSO CRITICO: Autenticazione offline
        print(f"\n🔐 AUTENTICAZIONE OFFLINE...")
        auth_start = time.time()
        auth_result = offline_manager.handle_card_access(card_info)
        auth_time = int((time.time() - auth_start) * 1000)
        
        authorized = auth_result.get('authorized', False)
        offline_mode = auth_result.get('offline_mode', False)
        message = auth_result.get('message', '')
        
        print(f"📊 RISULTATO AUTENTICAZIONE:")
        print(f"   Autorizzato: {'✅ SÌ' if authorized else '❌ NO'}")
        print(f"   Modalità offline: {'✅ SÌ' if offline_mode else '❌ NO'}")
        print(f"   Tempo auth: {auth_time}ms")
        print(f"   Messaggio: {message}")
        
        # Verifica autorizzazione
        if not authorized:
            print("❌ Card non autorizzata - relè non dovrebbe scattare")
            if Config.OFFLINE_ALLOW_ACCESS:
                print("⚠️ PROBLEMA: OFFLINE_ALLOW_ACCESS=True ma card non autorizzata!")
                return False
            else:
                print("✅ Comportamento corretto per modalità restrittiva")
                return True
        
        print("✅ Card autorizzata - procedo con attivazione relè")
        
        # PASSO CRITICO: Attivazione relè (come nel main.py)
        print(f"\n⚡ ATTIVAZIONE RELÈ...")
        
        direction_key = card_info.get('direction', 'in')
        available_relays = relay_manager.get_active_relays()
        
        print(f"🎯 Direzione richiesta: {direction_key}")
        print(f"🔌 Relè disponibili: {available_relays}")
        
        relay_success = False
        
        if direction_key in available_relays:
            print(f"🎯 Attivazione relè {direction_key.upper()}...")
            relay_success = relay_manager.activate_relay(direction_key)
            if relay_success:
                print(f"✅ Relè {direction_key.upper()} attivato con successo!")
            else:
                print(f"❌ Errore attivazione relè {direction_key.upper()}")
        elif available_relays:
            # Usa primo relè disponibile
            relay_key = available_relays[0]
            print(f"🔄 Uso primo relè disponibile: {relay_key.upper()}")
            relay_success = relay_manager.activate_relay(relay_key)
            if relay_success:
                print(f"✅ Relè {relay_key.upper()} attivato con successo!")
            else:
                print(f"❌ Errore attivazione relè {relay_key.upper()}")
        else:
            print("❌ Nessun relè disponibile")
        
        # Test 4: Verifica finale
        print(f"\n📊 RISULTATO FINALE:")
        print(f"   🔐 Autenticazione: {'✅ OK' if authorized else '❌ FALLITA'}")
        print(f"   ⚡ Relè: {'✅ ATTIVATO' if relay_success else '❌ NON ATTIVATO'}")
        print(f"   🌐 Modalità: {'OFFLINE' if offline_mode else 'ONLINE'}")
        
        # Cleanup
        relay_manager.reset_all_to_initial_state()
        relay_manager.cleanup()
        offline_manager.cleanup()
        
        # Verifica successo completo
        success = authorized and relay_success and offline_mode
        
        if success:
            print("\n🎉 INTEGRAZIONE OFFLINE + RELÈ: SUCCESSO!")
            print("💡 Il sistema funziona correttamente offline")
        else:
            print("\n💔 INTEGRAZIONE OFFLINE + RELÈ: PROBLEMI")
            print("🔧 Analisi problemi:")
            if not authorized:
                print("   - ❌ Autorizzazione fallita")
            if not relay_success:
                print("   - ❌ Attivazione relè fallita")
            if not offline_mode:
                print("   - ❌ Modalità offline non rilevata")
        
        return success
        
    except Exception as e:
        print(f"❌ Errore test integrazione: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relay_offline_scenario():
    """Test scenario specifico: relè in modalità offline"""
    print(f"\n🎯 TEST SCENARIO RELÈ OFFLINE")
    print("=" * 50)
    
    try:
        from config import Config
        from relay_manager import RelayManager
        
        print("📱 Scenario: Sistema offline, card autorizzata localmente")
        
        # Test solo relay manager
        relay_manager = RelayManager()
        
        if not relay_manager.initialize():
            print("❌ Relay Manager non inizializzato")
            return False
        
        print("✅ Relay Manager inizializzato")
        
        active_relays = relay_manager.get_active_relays()
        print(f"⚡ Relè attivi: {active_relays}")
        
        if not active_relays:
            print("❌ Nessun relè configurato")
            return False
        
        # Test attivazione diretta
        test_relay = active_relays[0]
        print(f"\n🧪 Test attivazione diretta relè {test_relay.upper()}")
        
        success = relay_manager.activate_relay(test_relay)
        
        if success:
            print(f"✅ Relè {test_relay.upper()} attivato direttamente")
            
            # Aspetta tempo attivazione
            wait_time = Config.RELAY_IN_ACTIVE_TIME if test_relay == 'in' else 2
            print(f"⏳ Attesa {wait_time}s (tempo attivazione)...")
            time.sleep(wait_time + 0.5)
            
            print("✅ Test relè completato")
        else:
            print(f"❌ Errore attivazione diretta relè {test_relay.upper()}")
        
        # Cleanup
        relay_manager.reset_all_to_initial_state()
        relay_manager.cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore test relay: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test completo integrazione offline + relè"""
    print("🔗 TEST INTEGRAZIONE OFFLINE + RELÈ")
    print("Verifica che il relè scatti quando il sistema è offline")
    print("=" * 60)
    
    # Test 1: Integrazione completa
    test1_success = test_offline_relay_integration()
    
    # Test 2: Scenario specifico relè
    test2_success = test_relay_offline_scenario()
    
    print("\n" + "=" * 60)
    print("📋 RISULTATI FINALI:")
    print("=" * 60)
    
    print(f"🔗 Test integrazione completa: {'✅ OK' if test1_success else '❌ FALLITO'}")
    print(f"⚡ Test relè diretto: {'✅ OK' if test2_success else '❌ FALLITO'}")
    
    if test1_success and test2_success:
        print("\n🎉 TUTTO FUNZIONA!")
        print("💡 L'integrazione offline + relè è corretta")
        print("🔧 Se il relè non scatta nel sistema reale:")
        print("   1. Verifica log del sistema durante test offline")
        print("   2. Controlla se l'autorizzazione è True")
        print("   3. Verifica connessioni hardware relè")
    else:
        print("\n💔 PROBLEMI IDENTIFICATI")
        if not test1_success:
            print("🔧 Problema integrazione offline-relè:")
            print("   - Verifica configurazione OFFLINE_ALLOW_ACCESS")
            print("   - Controlla inizializzazione relay manager")
            print("   - Verifica autorizzazione offline")
        if not test2_success:
            print("🔧 Problema relè hardware:")
            print("   - Verifica pin configurazione")
            print("   - Controlla connessioni fisiche")
            print("   - Testa con multimetro")
    
    print("=" * 60)

if __name__ == "__main__":
    main()