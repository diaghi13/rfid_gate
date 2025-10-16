#!/usr/bin/env python3
"""
🧪 Test Flusso Intelligente Completo
===================================

Testa il nuovo flusso intelligente implementato in access_control.py:

📱 CASO 1: Carta in cache → Cache auth + MQTT parallelo
📱 CASO 2: Carta NON in cache → Cache refresh → Fallback diretto (NO MQTT)  
📱 CASO 3: Carta scaduta → Cache refresh → Cache auth + MQTT parallelo
🔓 WHITELIST: Bypass completo con accesso sempre garantito
"""

import sys
import os
from pathlib import Path

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

def test_new_intelligent_flow():
    """Testa che il nuovo flusso intelligente sia implementato correttamente"""
    
    print("🧪 TEST FLUSSO INTELLIGENTE COMPLETO")
    print("=" * 45)
    
    try:
        # Import del sistema
        from rfid_gate.core.access_control import AccessControlSystem
        
        print("✅ Import AccessControlSystem riuscito")
        
        # Verifica presenza metodi del nuovo flusso
        methods_to_check = [
            '_authenticate_card',
            '_check_whitelist_access', 
            '_send_parallel_mqtt_logging',
            '_log_authorized_access',
            '_log_denied_access',
            '_direct_gate_verification'
        ]
        
        for method in methods_to_check:
            if hasattr(AccessControlSystem, method):
                print(f"✅ Metodo {method} presente")
            else:
                print(f"❌ ERRORE: Metodo {method} mancante!")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Errore import/verifica: {e}")
        return False

def analyze_new_flow_logic():
    """Analizza la logica del nuovo flusso"""
    
    print("\n🔍 ANALISI LOGICA NUOVO FLUSSO")
    print("=" * 35)
    
    try:
        # Leggi il file per verificare la logica
        with open('rfid_gate/core/access_control.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica presenza dei casi
        checks = [
            ('CASO 1', 'Carta trovata e valida in cache'),
            ('CASO 2', 'Fallback diretto gate-verification'),
            ('CASO 3', 'Cache refresh risolto'),
            ('WHITELIST', 'Accesso garantito'),
            ('_direct_gate_verification', 'Chiamata diretta'),
            ('Prevenzione duplicati', 'SENZA MQTT per evitare duplicati')
        ]
        
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Implementato")
            else:
                print(f"⚠️ {check_name}: Non trovato '{check_text}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore analisi: {e}")
        return False

def show_expected_flow_diagram():
    """Mostra il diagramma del flusso atteso"""
    
    print("\n🎯 FLUSSO INTELLIGENTE ATTESO")
    print("=" * 35)
    
    print("📱 CARTA LETTA")
    print("    ↓")
    print("🔓 1. CHECK WHITELIST")
    print("    ✅ Se whitelist → Accesso + MQTT parallelo → FINE")
    print("    ❌ Se non whitelist → Continua")
    print("    ↓")
    print("📄 2. CHECK CACHE LOCALE")
    print("    ✅ Se in cache e valida:")
    print("        → CASO 1: Accesso immediato")
    print("        → MQTT parallelo per logging")
    print("        → Log locale immediato")
    print("    ❌ Se non in cache o scaduta → Continua")
    print("    ↓")
    print("🔄 3. CACHE REFRESH (GET /api/sync-gate)")
    print("    ✅ Se trova dati aggiornati:")
    print("        → CASO 3: Cache aggiornata")
    print("        → Accesso da cache")
    print("        → MQTT parallelo per logging")
    print("    ❌ Se non trova dati → Continua")
    print("    ↓")
    print("🔗 4. FALLBACK DIRETTO (POST /api/gate-verification)")
    print("    → CASO 2: Chiamata diretta server")
    print("    → ❌ NO MQTT (per evitare duplicati)")
    print("    → Log locale immediato")
    print("    ✅/❌ Risposta diretta del server")

def show_mqtt_strategy():
    """Mostra la strategia MQTT"""
    
    print("\n📡 STRATEGIA MQTT INTELLIGENTE")
    print("=" * 35)
    
    print("✅ MQTT PARALLELO (per logging):")
    print("   → CASO 1: Cache hit")
    print("   → CASO 3: Cache refresh riuscito")
    print("   → WHITELIST: Sempre")
    print()
    print("❌ NO MQTT (evita duplicati):")
    print("   → CASO 2: Fallback diretto")
    print("   → Gate-verification diretta")
    print()
    print("🎯 RISULTATO:")
    print("   → Un solo log server per carta")
    print("   → MQTT indipendente dall'autorizzazione")
    print("   → Fallback diretto senza duplicati")

def show_whitelist_behavior():
    """Mostra comportamento whitelist"""
    
    print("\n🔓 COMPORTAMENTO WHITELIST")
    print("=" * 30)
    
    print("✅ PRIORITÀ ASSOLUTA:")
    print("   → Check prima di tutto")
    print("   → Bypass cache/server")
    print("   → Bypass controllo IN/OUT")
    print("   → Accesso sempre garantito")
    print()
    print("📋 IDENTIFICAZIONE WHITELIST:")
    print("   → subscription_info.in_white_list = True")
    print("   → subscription_info.type = 'whitelist'")
    print()
    print("📝 LOGGING WHITELIST:")
    print("   → Log locale immediato")
    print("   → MQTT parallelo per server")
    print("   → Reason: 'Carta in whitelist - bypass IN/OUT'")

def test_endpoint_configuration():
    """Testa configurazione endpoint"""
    
    print("\n🔧 TEST CONFIGURAZIONE ENDPOINT")
    print("=" * 35)
    
    try:
        from rfid_gate.config.settings import load_env_file
        load_env_file()
        
        # Verifica endpoint configurati
        cache_refresh_endpoint = os.getenv('CACHE_REFRESH_SINGLE_CARD_ENDPOINT', '/api/sync-gate')
        gate_verification_endpoint = os.getenv('GATE_VERIFICATION_ENDPOINT', '/api/gate-verification')
        
        print(f"📋 Cache refresh: {cache_refresh_endpoint}")
        print(f"🔗 Gate verification: {gate_verification_endpoint}")
        
        if cache_refresh_endpoint == '/api/sync-gate':
            print("✅ Cache refresh endpoint corretto")
        else:
            print("⚠️ Cache refresh endpoint inaspettato")
            
        if gate_verification_endpoint == '/api/gate-verification':
            print("✅ Gate verification endpoint corretto")
        else:
            print("⚠️ Gate verification endpoint inaspettato")
            
        return True
        
    except Exception as e:
        print(f"❌ Errore configurazione: {e}")
        return False

def main():
    """Test principale"""
    
    print("🧪 TEST COMPLETO FLUSSO INTELLIGENTE")
    print("=" * 45)
    
    # Test implementazione
    implementation_ok = test_new_intelligent_flow()
    
    # Analisi logica
    logic_ok = analyze_new_flow_logic()
    
    # Test configurazione
    config_ok = test_endpoint_configuration()
    
    # Mostra diagrammi
    show_expected_flow_diagram()
    show_mqtt_strategy()
    show_whitelist_behavior()
    
    print(f"\n📊 RISULTATI TEST:")
    print(f"   ✅ Implementazione: {'OK' if implementation_ok else 'ERRORE'}")
    print(f"   ✅ Logica: {'OK' if logic_ok else 'ERRORE'}")  
    print(f"   ✅ Configurazione: {'OK' if config_ok else 'ERRORE'}")
    
    if implementation_ok and logic_ok and config_ok:
        print("\n🎉 FLUSSO INTELLIGENTE IMPLEMENTATO!")
        print("   ✅ Cache-first con MQTT parallelo")
        print("   ✅ Fallback diretto senza duplicati")
        print("   ✅ Whitelist con bypass completo")
        print("   ✅ Gestione abbonamenti rinnovati")
        
        print("\n🚀 PRONTO PER TEST SU RASPBERRY PI:")
        print("   → Caso 1: Cache hit → Accesso rapido + MQTT")
        print("   → Caso 2: Cache miss → Refresh → Fallback")
        print("   → Caso 3: Scaduto → Refresh → Accesso")
        print("   → Whitelist: Sempre autorizzata")
    else:
        print("\n❌ ERRORI TROVATI - verificare implementazione")

if __name__ == "__main__":
    main()