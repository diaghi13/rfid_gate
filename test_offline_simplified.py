#!/usr/bin/env python3
"""
Test offline mode semplificato - senza dipendenze MQTT
"""
import sys
import time
import json
import os
from datetime import datetime

# Aggiungi src al path
sys.path.insert(0, 'src')

def test_offline_mode_simplified():
    """Test offline mode senza dipendenze MQTT"""
    print("🔍 TEST OFFLINE MODE SEMPLIFICATO")
    print("=" * 50)
    
    try:
        from config import Config
        from offline_manager import OfflineManager
        from logger import AccessLogger
        
        print("✅ Import moduli base: OK")
        
        # Verifica configurazione offline
        print(f"\n📋 CONFIGURAZIONE OFFLINE:")
        print(f"   OFFLINE_MODE_ENABLED: {Config.OFFLINE_MODE_ENABLED}")
        print(f"   OFFLINE_ALLOW_ACCESS: {Config.OFFLINE_ALLOW_ACCESS}")
        print(f"   OFFLINE_SYNC_ENABLED: {Config.OFFLINE_SYNC_ENABLED}")
        
        if not Config.OFFLINE_MODE_ENABLED:
            print("❌ Modalità offline disabilitata nel .env")
            return False
        
        # Test con logger
        try:
            logger = AccessLogger(Config.LOG_DIRECTORY)
            print("✅ Logger creato")
        except Exception as e:
            print(f"⚠️ Logger error: {e}")
            logger = None
        
        # Test 1: OfflineManager senza MQTT (modalità più comune)
        print(f"\n🧪 TEST 1: OFFLINE MANAGER STANDALONE")
        
        offline_manager = OfflineManager(mqtt_client=None, logger=logger)
        
        if offline_manager.initialize():
            print("✅ OfflineManager inizializzato senza MQTT")
        else:
            print("❌ Inizializzazione fallita")
            return False
        
        # Forza stato offline
        offline_manager.is_online = False
        print("🔴 Stato: OFFLINE")
        
        # Test 2: Simulazione accesso card (scenario reale)
        print(f"\n🧪 TEST 2: ACCESSO CARD IN MODALITÀ OFFLINE")
        
        card_info = {
            'raw_id': 123456789,
            'uid_formatted': 'TESTCARD',
            'uid_hex': '0x75bcd15',
            'data': 'Test Offline',
            'data_length': 12,
            'direction': 'in',
            'reader_id': 'test_reader',
            'timestamp': time.time()
        }
        
        print(f"📱 Card simulata: {card_info['uid_formatted']}")
        
        # Questo è il punto critico - deve funzionare offline
        auth_result = offline_manager.handle_card_access(card_info)
        
        print(f"📊 RISULTATO AUTENTICAZIONE:")
        print(f"   ✅ Authorized: {auth_result.get('authorized', False)}")
        print(f"   🌐 Offline mode: {auth_result.get('offline_mode', False)}")
        print(f"   💬 Message: {auth_result.get('message', 'N/A')}")
        print(f"   🏠 Local decision: {auth_result.get('offline_decision', False)}")
        
        # Verifica comportamento atteso
        expected_auth = Config.OFFLINE_ALLOW_ACCESS
        actual_auth = auth_result.get('authorized', False)
        offline_mode = auth_result.get('offline_mode', False)
        
        success = True
        
        if not offline_mode:
            print("❌ ERRORE: Non ha rilevato modalità offline!")
            success = False
        
        if actual_auth != expected_auth:
            print(f"❌ ERRORE: Autorizzazione errata!")
            print(f"   Atteso: {expected_auth}")
            print(f"   Ottenuto: {actual_auth}")
            success = False
        
        if success:
            mode_text = "PERMISSIVO" if expected_auth else "RESTRITTIVO"
            auth_text = "AUTORIZZA" if expected_auth else "NEGA"
            print(f"✅ Modalità offline {mode_text}: {auth_text} accessi")
        
        # Test 3: Verifica persistenza
        print(f"\n🧪 TEST 3: VERIFICA PERSISTENZA DATI")
        
        queue_size = offline_manager.offline_queue.qsize()
        print(f"📊 Elementi in coda: {queue_size}")
        
        if queue_size > 0:
            print("✅ Eventi salvati per sync futura")
        else:
            print("❌ Nessun evento salvato")
            success = False
        
        # Test 4: File persistente
        queue_file = os.path.join(Config.LOG_DIRECTORY, Config.OFFLINE_STORAGE_FILE)
        
        if os.path.exists(queue_file):
            print(f"✅ File persistente creato: {queue_file}")
            try:
                with open(queue_file, 'r') as f:
                    data = json.load(f)
                print(f"📁 File contiene {data.get('queue_size', 0)} eventi")
            except Exception as e:
                print(f"⚠️ Errore lettura file: {e}")
        else:
            print(f"❌ File persistente non creato")
        
        # Test 5: Accessi multipli
        print(f"\n🧪 TEST 4: ACCESSI MULTIPLI OFFLINE")
        
        test_cards = ['CARD001', 'CARD002', 'CARD003']
        auth_count = 0
        deny_count = 0
        
        for card_uid in test_cards:
            test_card = card_info.copy()
            test_card['uid_formatted'] = card_uid
            test_card['timestamp'] = time.time()
            
            result = offline_manager.handle_card_access(test_card)
            if result.get('authorized', False):
                auth_count += 1
            else:
                deny_count += 1
            
            time.sleep(0.1)
        
        print(f"📊 Risultati accessi multipli:")
        print(f"   ✅ Autorizzati: {auth_count}")
        print(f"   ❌ Negati: {deny_count}")
        
        if Config.OFFLINE_ALLOW_ACCESS:
            if auth_count == len(test_cards):
                print("✅ Modalità permissiva: tutti autorizzati")
            else:
                print("❌ Modalità permissiva: non tutti autorizzati")
                success = False
        else:
            if deny_count == len(test_cards):
                print("✅ Modalità restrittiva: tutti negati")
            else:
                print("❌ Modalità restrittiva: non tutti negati")
                success = False
        
        # Test 6: Statistiche
        print(f"\n🧪 TEST 5: STATISTICHE")
        
        stats = offline_manager.stats
        print(f"📊 Statistiche offline:")
        print(f"   Total accesses: {stats.get('total_offline_accesses', 0)}")
        print(f"   Authorized: {stats.get('offline_authorized', 0)}")
        print(f"   Denied: {stats.get('offline_denied', 0)}")
        print(f"   Pending sync: {stats.get('pending_sync', 0)}")
        
        # Cleanup
        offline_manager.cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_scenario():
    """Test scenario reale: sistema offline con decisione locale"""
    print(f"\n🎯 TEST SCENARIO REALE")
    print("=" * 50)
    
    try:
        from config import Config
        from offline_manager import OfflineManager
        
        # Simula scenario: sistema avviato, MQTT non disponibile
        offline_manager = OfflineManager(mqtt_client=None, logger=None)
        offline_manager.initialize()
        offline_manager.is_online = False  # Simula disconnessione
        
        # Scenario: utente presenta card
        print("📱 Scenario: Utente presenta card mentre sistema è offline")
        
        card_scenario = {
            'raw_id': 2055674891,
            'uid_formatted': 'REALCARD',
            'uid_hex': '0x7a7c8c0b',
            'data': 'Real User Card',
            'data_length': 14,
            'direction': 'in',
            'reader_id': 'in',
            'timestamp': time.time()
        }
        
        # Il sistema deve decidere IMMEDIATAMENTE se aprire o no
        start_time = time.time()
        auth_result = offline_manager.handle_card_access(card_scenario)
        decision_time = (time.time() - start_time) * 1000
        
        print(f"⚡ Decisione presa in {decision_time:.1f}ms")
        
        authorized = auth_result.get('authorized', False)
        offline_mode = auth_result.get('offline_mode', False)
        message = auth_result.get('message', '')
        
        print(f"📊 RISULTATO SCENARIO REALE:")
        print(f"   Autorizzato: {'✅ SÌ' if authorized else '❌ NO'}")
        print(f"   Modalità offline: {'✅ SÌ' if offline_mode else '❌ NO'}")
        print(f"   Messaggio: {message}")
        
        # Verifica comportamento corretto
        config_mode = "PERMISSIVO" if Config.OFFLINE_ALLOW_ACCESS else "RESTRITTIVO"
        expected_auth = Config.OFFLINE_ALLOW_ACCESS
        
        print(f"\n🔧 VERIFICA COMPORTAMENTO:")
        print(f"   Configurazione: Modalità {config_mode}")
        print(f"   Atteso: {'Autorizza' if expected_auth else 'Nega'} accessi offline")
        print(f"   Ottenuto: {'Autorizzato' if authorized else 'Negato'}")
        
        if authorized == expected_auth and offline_mode:
            print("✅ COMPORTAMENTO CORRETTO")
            print("💡 Il tornello si aprirebbe IMMEDIATAMENTE")
            return True
        else:
            print("❌ COMPORTAMENTO ERRATO")
            return False
        
    except Exception as e:
        print(f"❌ Errore scenario reale: {e}")
        return False

def main():
    """Test offline completo senza dipendenze MQTT"""
    print("🔍 TEST OFFLINE MODE - VERSIONE SEMPLIFICATA")
    print("Verifica funzionamento offline senza dipendenze MQTT")
    print("=" * 60)
    
    test1_success = test_offline_mode_simplified()
    test2_success = test_real_scenario()
    
    print("\n" + "=" * 60)
    print("📋 RISULTATI FINALI:")
    print("=" * 60)
    
    print(f"🧪 Test offline semplificato: {'✅ OK' if test1_success else '❌ FALLITO'}")
    print(f"🎯 Test scenario reale: {'✅ OK' if test2_success else '❌ FALLITO'}")
    
    if test1_success and test2_success:
        print("\n🎉 OFFLINE MODE FUNZIONA CORRETTAMENTE!")
        print("💡 Il sistema può funzionare offline come previsto")
        print("🔧 PROSSIMI PASSI:")
        print("   1. Testa sul Raspberry Pi con il sistema completo")
        print("   2. Disconnetti internet per testare offline reale")
        print("   3. Verifica che il tornello si apra immediatamente")
    else:
        print("\n💔 OFFLINE MODE HA ANCORA PROBLEMI")
        print("🔧 POSSIBILI CAUSE:")
        print("   1. Configurazione .env errata")
        print("   2. Problemi inizializzazione componenti")
        print("   3. Problemi logica decisionale offline")
    
    print("=" * 60)

if __name__ == "__main__":
    main()