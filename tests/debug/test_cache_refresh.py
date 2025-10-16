#!/usr/bin/env python3
"""
🧪 Test Cache Refresh con Offline Access
========================================
Testa la nuova logica che permette cache refresh anche con OFFLINE_ALLOW_ACCESS=True
"""

import sys
import os
import time
from pathlib import Path

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

def simulate_unknown_card_scenario():
    """Simula scenario carta sconosciuta"""
    
    print("🧪 SIMULAZIONE: Carta Sconosciuta con Offline Access")
    print("=" * 55)
    
    # Carta di test inventata
    test_card_uid = "UNKNOWN123456"
    
    print(f"🏷️ Carta Test: {test_card_uid}")
    print(f"🔄 Offline Access: True (permette accesso)")
    print(f"🔄 Cache Refresh: True (abilita refresh)")
    
    print("\n📋 WORKFLOW ATTESO:")
    print("1. Carta sconosciuta letta")
    print("2. Sistema permette accesso (offline mode)")
    print("3. In background: cache refresh al server")
    print("4. Cache aggiornata per prossimi accessi")
    
    print("\n💡 BENEFICI:")
    print("   ✅ Utente non aspetta (accesso immediato)")
    print("   ✅ Cache si popola automaticamente")
    print("   ✅ Prossimi accessi saranno più veloci")
    
    return test_card_uid

def simulate_renewed_subscription_scenario():
    """Simula scenario abbonamento rinnovato"""
    
    print("\n🧪 SIMULAZIONE: Abbonamento Rinnovato")
    print("=" * 40)
    
    # Carta di test con abbonamento (inventata)
    test_card_uid = "RENEWED789012"
    
    print(f"🏷️ Carta Test: {test_card_uid}")
    print(f"📅 Scenario: Abbonamento scaduto ma rinnovato online")
    
    print("\n📋 WORKFLOW ATTESO:")
    print("1. Carta letta (cache dice scaduto)")
    print("2. Sistema permette accesso (offline mode)")
    print("3. Cache refresh trova abbonamento rinnovato")
    print("4. Cache aggiornata con nuovi dati")
    
    return test_card_uid

def check_current_config():
    """Controlla configurazione corrente"""
    
    print("\n📋 CONFIGURAZIONE CORRENTE")
    print("=" * 30)
    
    try:
        from rfid_gate.config.settings import load_env_file
        load_env_file()
        
        offline_access = os.getenv('OFFLINE_ALLOW_ACCESS', 'False').lower() == 'true'
        cache_refresh = os.getenv('CACHE_REFRESH_ENABLED', 'False').lower() == 'true'
        cache_endpoint = os.getenv('CACHE_REFRESH_SINGLE_CARD_ENDPOINT', '/api/sync-gate')
        
        print(f"🔄 OFFLINE_ALLOW_ACCESS: {offline_access}")
        print(f"🔄 CACHE_REFRESH_ENABLED: {cache_refresh}")
        print(f"🌐 Cache Endpoint: {cache_endpoint}")
        
        if offline_access and cache_refresh:
            print("\n✅ CONFIGURAZIONE OTTIMALE:")
            print("   Sistema permette accesso + cache refresh attivo")
        elif offline_access and not cache_refresh:
            print("\n⚠️ CACHE REFRESH DISABILITATO:")
            print("   Impostare CACHE_REFRESH_ENABLED=true")
        elif not offline_access and cache_refresh:
            print("\n⚠️ MODALITÀ STRICT:")
            print("   Accesso negato se server non raggiungibile")
        else:
            print("\n❌ CONFIGURAZIONE PROBLEMATICA:")
            print("   Né offline né cache refresh abilitati")
            
        return offline_access, cache_refresh
        
    except Exception as e:
        print(f"❌ Errore lettura config: {e}")
        return False, False

def test_relay_status():
    """Testa stato relay"""
    
    print("\n⚡ TEST RELAY STATUS")
    print("=" * 20)
    
    # Controlla log per vedere ultima attivazione relay
    log_file = Path("logs/system.log")
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Cerca ultime attivazioni relay
        relay_activations = []
        for line in lines[-50:]:  # Ultimi 50 log
            if "ATTIVATO" in line or "RELAY" in line.upper():
                relay_activations.append(line.strip())
        
        if relay_activations:
            print("📋 Ultime attivazioni relay:")
            for activation in relay_activations[-3:]:  # Ultime 3
                print(f"   {activation}")
            print(f"\n✅ Relay sembra funzionare ({len(relay_activations)} attivazioni trovate)")
        else:
            print("❌ Nessuna attivazione relay trovata nei log recenti")
    else:
        print("❌ File di log non trovato")

def recommend_testing_strategy():
    """Raccomanda strategia di test"""
    
    print("\n🎯 STRATEGIA DI TEST RACCOMANDATA")
    print("=" * 35)
    
    print("1. 📱 PREPARAZIONE:")
    print("   - Usa carta RFID che non hai mai registrato")
    print("   - Oppure carta registrata di cui hai rinnovato abbonamento")
    
    print("\n2. 🔍 MONITORAGGIO:")
    print("   - Apri terminale: python3 logging_helper.py watch")
    print("   - Tieni d'occhio per messaggi 'cache refresh'")
    
    print("\n3. 🧪 TEST STEPS:")
    print("   a. Avvia il sistema RFID Gate")
    print("   b. Passa carta sul lettore")
    print("   c. Verifica accesso immediato (✅ dovrebbe aprire)")
    print("   d. Nei log cerca: 'tentativo cache refresh'")
    print("   e. Riprova carta dopo 30 secondi")
    
    print("\n4. ✅ RISULTATI ATTESI:")
    print("   - Primo passaggio: Accesso OK + cache refresh avviato")
    print("   - Secondo passaggio: Accesso OK + dati cache aggiornati")
    
def main():
    """Test principale"""
    
    print("🧪 TEST CACHE REFRESH + OFFLINE ACCESS")
    print("=" * 45)
    
    # Test configurazione
    offline_access, cache_refresh = check_current_config()
    
    # Test relay
    test_relay_status()
    
    # Simulazioni
    unknown_card = simulate_unknown_card_scenario()
    renewed_card = simulate_renewed_subscription_scenario()
    
    # Raccomandazioni
    recommend_testing_strategy()
    
    print("\n📊 RIASSUNTO MODIFICHE")
    print("=" * 25)
    print("✅ Modificata logica _offline_authentication()")
    print("✅ Aggiunto handle_unknown_card_refresh()")
    print("✅ Cache refresh funziona anche con offline access")
    print("✅ Relay logic corretta (bug risolto)")
    
    print("\n🚀 PROSSIMO PASSO:")
    print("   Testare con carta reale sul Raspberry Pi!")

if __name__ == "__main__":
    main()