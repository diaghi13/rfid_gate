#!/usr/bin/env python3
"""
Test specifico per l'Offline Mode
Identifica problemi nella modalità offline
"""
import sys
import time
import json
import os
from datetime import datetime

# Aggiungi src al path
sys.path.insert(0, 'src')

def test_offline_mode():
    """Test completo della modalità offline"""
    print("🔍 TEST MODALITÀ OFFLINE")
    print("=" * 50)
    
    try:
        from config import Config
        from offline_manager import OfflineManager
        from logger import AccessLogger
        
        print("✅ Import moduli: OK")
        
        # Verifica configurazione
        print(f"\n📋 CONFIGURAZIONE OFFLINE:")
        print(f"   OFFLINE_MODE_ENABLED: {Config.OFFLINE_MODE_ENABLED}")
        print(f"   OFFLINE_ALLOW_ACCESS: {Config.OFFLINE_ALLOW_ACCESS}")
        print(f"   OFFLINE_SYNC_ENABLED: {Config.OFFLINE_SYNC_ENABLED}")
        print(f"   OFFLINE_STORAGE_FILE: {Config.OFFLINE_STORAGE_FILE}")
        print(f"   OFFLINE_MAX_QUEUE_SIZE: {Config.OFFLINE_MAX_QUEUE_SIZE}")
        print(f"   CONNECTION_CHECK_INTERVAL: {Config.CONNECTION_CHECK_INTERVAL}")
        
        if not Config.OFFLINE_MODE_ENABLED:
            print("❌ OFFLINE_MODE_ENABLED è False - modalità offline disabilitata")
            return False
        
        # Test 1: Inizializzazione OfflineManager
        print(f"\n🧪 TEST 1: INIZIALIZZAZIONE OFFLINE MANAGER")
        
        # Crea logger fittizio
        try:
            logger = AccessLogger(Config.LOG_DIRECTORY)
            print("✅ Logger creato")
        except Exception as e:
            print(f"⚠️ Errore logger: {e}")
            logger = None
        
        # Crea OfflineManager senza MQTT (simula offline)
        offline_manager = OfflineManager(mqtt_client=None, logger=logger)
        
        if offline_manager.initialize():
            print("✅ OfflineManager inizializzato")
        else:
            print("❌ Inizializzazione OfflineManager fallita")
            return False
        
        # Test 2: Controllo connessione
        print(f"\n🧪 TEST 2: CONTROLLO CONNESSIONE")
        
        # Forza stato offline per test
        offline_manager.is_online = False
        print("🔴 Simulazione stato offline")
        
        # Test 3: Simulazione accesso card offline
        print(f"\n🧪 TEST 3: SIMULAZIONE ACCESSO CARD OFFLINE")
        
        # Simula dati card
        fake_card_info = {
            'raw_id': 123456789,
            'uid_formatted': 'ABCDEF12',
            'uid_hex': '0x75bcd15',
            'data': 'Test Card',
            'data_length': 9,
            'direction': 'in',
            'reader_id': 'test_reader',
            'timestamp': time.time()
        }
        
        print(f"📱 Simulazione card: {fake_card_info['uid_formatted']}")
        
        # Test accesso offline
        auth_result = offline_manager.handle_card_access(fake_card_info)
        
        print(f"📊 RISULTATO AUTENTICAZIONE OFFLINE:")
        print(f"   authorized: {auth_result.get('authorized', 'N/A')}")
        print(f"   message: {auth_result.get('message', 'N/A')}")
        print(f"   offline_mode: {auth_result.get('offline_mode', 'N/A')}")
        print(f"   offline_decision: {auth_result.get('offline_decision', 'N/A')}")
        print(f"   access_type: {auth_result.get('access_type', 'N/A')}")
        
        # Verifica logica decisione
        expected_authorized = Config.OFFLINE_ALLOW_ACCESS
        actual_authorized = auth_result.get('authorized', False)
        
        if actual_authorized == expected_authorized:
            print(f"✅ Decisione offline corretta: {'AUTORIZZATO' if actual_authorized else 'NEGATO'}")
        else:
            print(f"❌ Decisione offline errata!")
            print(f"   Atteso: {expected_authorized}")
            print(f"   Ottenuto: {actual_authorized}")
            return False
        
        # Test 4: Verifica coda offline
        print(f"\n🧪 TEST 4: VERIFICA CODA OFFLINE")
        
        queue_size = offline_manager.offline_queue.qsize()
        print(f"📊 Elementi in coda: {queue_size}")
        
        if queue_size > 0:
            print("✅ Evento salvato in coda offline")
        else:
            print("❌ Nessun evento salvato in coda")
            return False
        
        # Test 5: Verifica file persistente
        print(f"\n🧪 TEST 5: VERIFICA FILE PERSISTENTE")
        
        queue_file = os.path.join(Config.LOG_DIRECTORY, Config.OFFLINE_STORAGE_FILE)
        
        if os.path.exists(queue_file):
            print(f"✅ File coda offline esistente: {queue_file}")
            try:
                with open(queue_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Dati file coda:")
                print(f"   saved_at: {data.get('saved_at', 'N/A')}")
                print(f"   queue_size: {data.get('queue_size', 'N/A')}")
                
                queue_data = data.get('queue_data', [])
                if queue_data:
                    last_entry = queue_data[-1]
                    print(f"   ultimo_evento: {last_entry.get('timestamp', 'N/A')}")
                    print(f"   offline_authorized: {last_entry.get('offline_authorized', 'N/A')}")
                
            except Exception as e:
                print(f"⚠️ Errore lettura file coda: {e}")
        else:
            print(f"❌ File coda offline non trovato: {queue_file}")
        
        # Test 6: Test con múltiple card
        print(f"\n🧪 TEST 6: ACCESSI MULTIPLI OFFLINE")
        
        test_cards = [
            {'uid_formatted': 'CARD0001', 'direction': 'in'},
            {'uid_formatted': 'CARD0002', 'direction': 'out'},
            {'uid_formatted': 'CARD0003', 'direction': 'in'},
        ]
        
        for i, test_card in enumerate(test_cards, 1):
            card_info = fake_card_info.copy()
            card_info.update(test_card)
            card_info['timestamp'] = time.time()
            
            result = offline_manager.handle_card_access(card_info)
            auth_status = "✅ AUTORIZZATO" if result.get('authorized') else "❌ NEGATO"
            print(f"   Card {i}: {test_card['uid_formatted']} → {auth_status}")
            
            time.sleep(0.1)
        
        final_queue_size = offline_manager.offline_queue.qsize()
        print(f"📊 Coda finale: {final_queue_size} elementi")
        
        # Test 7: Statistiche offline
        print(f"\n🧪 TEST 7: STATISTICHE OFFLINE")
        
        stats = offline_manager.stats
        print(f"📊 STATISTICHE:")
        print(f"   total_offline_accesses: {stats.get('total_offline_accesses', 0)}")
        print(f"   offline_authorized: {stats.get('offline_authorized', 0)}")
        print(f"   offline_denied: {stats.get('offline_denied', 0)}")
        print(f"   pending_sync: {stats.get('pending_sync', 0)}")
        
        # Test 8: Status manager
        print(f"\n🧪 TEST 8: STATUS MANAGER")
        
        status = offline_manager.get_status()
        print(f"📊 STATUS:")
        print(f"   enabled: {status.get('enabled', 'N/A')}")
        print(f"   online: {status.get('online', 'N/A')}")
        print(f"   allow_offline_access: {status.get('allow_offline_access', 'N/A')}")
        print(f"   sync_enabled: {status.get('sync_enabled', 'N/A')}")
        print(f"   queue_size: {status.get('queue_size', 'N/A')}")
        
        # Cleanup
        offline_manager.cleanup()
        
        print(f"\n✅ TUTTI I TEST OFFLINE COMPLETATI CON SUCCESSO")
        return True
        
    except Exception as e:
        print(f"❌ Errore test offline: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_offline_integration():
    """Test integrazione offline con sistema principale"""
    print(f"\n🔗 TEST INTEGRAZIONE OFFLINE")
    print("=" * 50)
    
    try:
        from config import Config
        from offline_manager import OfflineManager
        from mqtt_client import MQTTClient
        from logger import AccessLogger
        
        # Simula inizializzazione come nel main.py
        logger = AccessLogger(Config.LOG_DIRECTORY)
        
        # Crea MQTT client ma non connettere (simula offline)
        mqtt_client = MQTTClient()
        mqtt_client.initialize()
        # Non chiamiamo connect() per simulare stato offline
        
        # Crea offline manager con mqtt_client
        offline_manager = OfflineManager(mqtt_client, logger)
        
        if offline_manager.initialize():
            print("✅ Integrazione inizializzata")
        else:
            print("❌ Integrazione fallita")
            return False
        
        # Simula card come nel main.py
        card_info = {
            'raw_id': 987654321,
            'uid_formatted': 'INTEGRATION',
            'uid_hex': '0x3ade68b1',
            'data': 'Integration Test',
            'data_length': 16,
            'direction': 'in',
            'reader_id': 'integration_test',
            'timestamp': time.time()
        }
        
        # Test come viene chiamato nel main.py
        print("🧪 Test handle_card_access...")
        auth_result = offline_manager.handle_card_access(card_info)
        
        print(f"📊 RISULTATO INTEGRAZIONE:")
        for key, value in auth_result.items():
            print(f"   {key}: {value}")
        
        # Verifica che sia stato processato correttamente
        expected_behavior = Config.OFFLINE_ALLOW_ACCESS
        actual_result = auth_result.get('authorized', False)
        
        if actual_result == expected_behavior:
            print("✅ Integrazione funziona correttamente")
            return True
        else:
            print("❌ Integrazione non funziona come atteso")
            return False
        
    except Exception as e:
        print(f"❌ Errore test integrazione: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test completo offline mode"""
    print("🔍 TEST COMPLETO MODALITÀ OFFLINE")
    print("Identifica problemi nell'offline mode")
    print("=" * 60)
    
    # Test standalone
    test1_success = test_offline_mode()
    
    # Test integrazione
    test2_success = test_offline_integration()
    
    print("\n" + "=" * 60)
    print("📋 RISULTATI FINALI:")
    print("=" * 60)
    
    print(f"🧪 Test standalone offline: {'✅ OK' if test1_success else '❌ FALLITO'}")
    print(f"🔗 Test integrazione offline: {'✅ OK' if test2_success else '❌ FALLITO'}")
    
    if test1_success and test2_success:
        print("\n🎉 OFFLINE MODE FUNZIONA CORRETTAMENTE!")
        print("💡 Se hai problemi nel sistema reale:")
        print("   1. Verifica che MQTT sia davvero disconnesso")
        print("   2. Controlla i log per errori specifici")
        print("   3. Verifica permessi file offline_queue.json")
    else:
        print("\n💔 OFFLINE MODE HA PROBLEMI")
        print("🔧 Controlla gli errori sopra e:")
        print("   1. Verifica configurazione .env")
        print("   2. Controlla permessi directory logs/")
        print("   3. Verifica inizializzazione componenti")
    
    print("=" * 60)

if __name__ == "__main__":
    main()