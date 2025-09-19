#!/usr/bin/env python3
"""
Diagnostica completa sistema offline
"""

import sys
import os
import socket
import argparse

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from offline_manager import OfflineManager
from mqtt_client import MQTTClient
from logger import AccessLogger
from relay_manager import RelayManager

def check_offline_config():
    """Controlla configurazione modalità offline"""
    
    print("🔧 CONTROLLO CONFIGURAZIONE OFFLINE")
    print("="*50)
    
    # Controlla configurazioni chiave
    configs = {
        'OFFLINE_MODE_ENABLED': Config.OFFLINE_MODE_ENABLED,
        'OFFLINE_ALLOW_ACCESS': Config.OFFLINE_ALLOW_ACCESS,
        'OFFLINE_SYNC_ENABLED': Config.OFFLINE_SYNC_ENABLED,
        'MQTT_BROKER': Config.MQTT_BROKER,
        'RELAY_IN_ENABLE': Config.RELAY_IN_ENABLE,
    }
    
    warnings = []
    errors = []
    
    for key, value in configs.items():
        status = "✅" if value else "❌"
        print(f"   {key}: {status} {value}")
        
        # Analisi problemi
        if key == 'OFFLINE_MODE_ENABLED' and not value:
            warnings.append("Modalità offline disabilitata - sistema non funzionerà senza internet")
        elif key == 'OFFLINE_ALLOW_ACCESS' and not value and Config.OFFLINE_MODE_ENABLED:
            errors.append("CRITICO: OFFLINE_MODE_ENABLED=True ma OFFLINE_ALLOW_ACCESS=False!")
        elif key == 'RELAY_IN_ENABLE' and not value:
            errors.append("CRITICO: Nessun relè abilitato - tornello non si aprirà mai")
    
    print()
    
    if errors:
        print("🚨 ERRORI CRITICI:")
        for error in errors:
            print(f"   ❌ {error}")
        print()
    
    if warnings:
        print("⚠️ AVVERTIMENTI:")
        for warning in warnings:
            print(f"   ⚠️ {warning}")
        print()
    
    # Raccomandazioni
    print("💡 CONFIGURAZIONE RACCOMANDATA PER OFFLINE:")
    print("   OFFLINE_MODE_ENABLED=True")
    print("   OFFLINE_ALLOW_ACCESS=True")
    print("   OFFLINE_SYNC_ENABLED=True")
    print("   RELAY_IN_ENABLE=True")
    
    return len(errors) == 0

def test_offline_simulation():
    """Simula accesso offline completo"""
    
    print("\n🧪 SIMULAZIONE ACCESSO OFFLINE")
    print("="*50)
    
    try:
        # Inizializza componenti
        logger = AccessLogger(Config.LOG_DIRECTORY)
        
        # Offline manager senza MQTT (simula offline)
        offline_manager = OfflineManager(None, logger)
        offline_manager.is_online = False  # Forza offline
        
        # Relay manager
        relay_manager = RelayManager()
        if not relay_manager.initialize():
            print("❌ Impossibile inizializzare relay manager")
            return False
        
        # Simula card
        test_card = {
            'uid_formatted': 'TEST1234',
            'raw_id': 123456,
            'direction': 'in',
            'data': 'Test Offline',
            'uid_hex': '0x1E240',
            'reader_id': 'in'
        }
        
        print(f"📱 Simulazione card: {test_card['uid_formatted']}")
        
        # Test autenticazione offline
        auth_result = offline_manager._handle_offline_access(test_card)
        
        print(f"🔐 Risultato autenticazione:")
        print(f"   Autorizzato: {auth_result['authorized']}")
        print(f"   Messaggio: {auth_result['message']}")
        print(f"   Offline mode: {auth_result['offline_mode']}")
        
        # Test relè se autorizzato
        relay_success = False
        if auth_result['authorized']:
            available_relays = relay_manager.get_active_relays()
            print(f"⚡ Relè disponibili: {available_relays}")
            
            if available_relays:
                relay_key = available_relays[0]
                print(f"🔄 Test attivazione relè {relay_key}...")
                relay_success = relay_manager.activate_relay(relay_key, 1)  # 1 secondo
                
                if relay_success:
                    print(f"✅ Relè {relay_key} attivato con successo!")
                else:
                    print(f"❌ Errore attivazione relè {relay_key}")
            else:
                print("❌ Nessun relè disponibile")
        
        # Cleanup
        relay_manager.cleanup()
        offline_manager.cleanup()
        
        # Risultato finale
        success = auth_result['authorized'] and (relay_success if auth_result['authorized'] else True)
        
        print(f"\n📊 RISULTATO SIMULAZIONE:")
        print(f"   Autorizzazione: {'✅' if auth_result['authorized'] else '❌'}")
        print(f"   Relè: {'✅' if relay_success or not auth_result['authorized'] else '❌'}")
        print(f"   Successo complessivo: {'✅' if success else '❌'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Errore simulazione: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connectivity():
    """Testa connettività di rete"""
    
    print("\n🌐 TEST CONNETTIVITÀ")
    print("="*30)
    
    tests = [
        ('Internet generico', '8.8.8.8', 53),
        ('MQTT Broker', Config.MQTT_BROKER, Config.MQTT_PORT),
    ]
    
    results = {}
    
    for name, host, port in tests:
        try:
            socket.create_connection((host, port), timeout=5)
            print(f"✅ {name}: OK")
            results[name] = True
        except Exception as e:
            print(f"❌ {name}: FALLITO ({e})")
            results[name] = False
    
    return results

def fix_offline_config():
    """Fix automatico configurazione offline"""
    
    print("\n🔧 FIX CONFIGURAZIONE OFFLINE")
    print("="*40)
    
    env_file = '.env'
    if not os.path.exists(env_file):
        env_file = '../.env'
    
    if not os.path.exists(env_file):
        print("❌ File .env non trovato!")
        return False
    
    # Leggi contenuto attuale
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Configurazione ottimale offline
    optimal_config = {
        'OFFLINE_MODE_ENABLED': 'True',
        'OFFLINE_ALLOW_ACCESS': 'True',  # CHIAVE CRITICA
        'OFFLINE_SYNC_ENABLED': 'True',
        'RELAY_IN_ENABLE': 'True',
        'CONNECTION_CHECK_INTERVAL': '30',
        'CONNECTION_RETRY_ATTEMPTS': '3'
    }
    
    # Aggiorna configurazioni
    new_lines = []
    found_keys = set()
    
    for line in lines:
        if line.strip() and '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in optimal_config:
                new_lines.append(f"{key}={optimal_config[key]}\n")
                found_keys.add(key)
                print(f"   ✅ Aggiornato: {key}={optimal_config[key]}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Aggiungi chiavi mancanti
    added_keys = []
    for key, value in optimal_config.items():
        if key not in found_keys:
            new_lines.append(f"{key}={value}\n")
            added_keys.append(f"{key}={value}")
            print(f"   ➕ Aggiunto: {key}={value}")
    
    # Scrivi file aggiornato
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    if found_keys or added_keys:
        print(f"\n✅ Configurazione offline ottimizzata!")
        print("🔄 Riavvia servizio: sudo systemctl restart rfid-gate")
        return True
    else:
        print("ℹ️ Configurazione già ottimale")
        return True

def main():
    parser = argparse.ArgumentParser(description="Diagnostica Sistema Offline")
    parser.add_argument("--check", "-c", action="store_true",
                       help="Controlla configurazione offline")
    parser.add_argument("--test", "-t", action="store_true",
                       help="Simula accesso offline completo")
    parser.add_argument("--connectivity", action="store_true",
                       help="Testa connettività di rete")
    parser.add_argument("--fix", action="store_true",
                       help="Fix automatico configurazione")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Esegue tutti i test")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        args.all = True  # Default a tutti i test
    
    success = True
    
    if args.all or args.check:
        if not check_offline_config():
            success = False
    
    if args.all or args.connectivity:
        connectivity = test_connectivity()
        if not all(connectivity.values()):
            print("⚠️ Problemi di connettività rilevati - modalità offline necessaria")
    
    if args.all or args.test:
        if os.geteuid() != 0:
            print("⚠️ Test relè richiede sudo")
        else:
            if not test_offline_simulation():
                success = False
    
    if args.fix:
        fix_offline_config()
    
    print(f"\n{'='*50}")
    if success:
        print("✅ SISTEMA OFFLINE: FUNZIONANTE")
    else:
        print("❌ SISTEMA OFFLINE: PROBLEMI RILEVATI")
        print("💡 Usa --fix per correggere automaticamente")

if __name__ == "__main__":
    main()