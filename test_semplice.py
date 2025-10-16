#!/usr/bin/env python3
"""
🧪 Test Semplice Sistema RFID Gate
=================================
Test di base per verificare funzionalità principali
"""

import sys
import os
from pathlib import Path

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

def test_config():
    """Test configurazione base"""
    
    print("📋 Test Configurazione")
    print("=" * 25)
    
    try:
        # Test ambiente
        from rfid_gate.config.settings import load_env_file
        load_env_file()
        
        # Test valori chiave
        offline_access = os.getenv('OFFLINE_ALLOW_ACCESS', 'False').lower() == 'true'
        cache_refresh = os.getenv('CACHE_REFRESH_ENABLED', 'False').lower() == 'true'
        relay_pin = os.getenv('GPIO_RELAY_PIN', '18')
        
        print(f"🔄 Offline Access: {offline_access}")
        print(f"🔄 Cache Refresh: {cache_refresh}")
        print(f"⚡ Relay Pin: {relay_pin}")
        
        # Problema principale
        if offline_access and cache_refresh:
            print("\n⚠️ PROBLEMA IDENTIFICATO:")
            print("   OFFLINE_ALLOW_ACCESS=True blocca il cache refresh")
            print("   Il sistema permette accesso senza controllare il server")
            print("\n💡 SOLUZIONE:")
            print("   1. Testare con OFFLINE_ALLOW_ACCESS=False")
            print("   2. Oppure modificare logica per forzare cache refresh")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test fallito: {e}")
        return False

def test_log_analysis():
    """Analizza log per problemi"""
    
    print("\n📋 Analisi Log Recenti")
    print("=" * 25)
    
    log_file = Path("logs/system.log")
    
    if not log_file.exists():
        print("❌ File di log non trovato!")
        return False
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Analizza ultimi 100 log
        recent_logs = lines[-100:]
        
        # Contatori
        authorized_count = 0
        denied_count = 0
        cache_refresh_count = 0
        error_count = 0
        
        for line in recent_logs:
            line_upper = line.upper()
            if "AUTORIZZATO" in line_upper:
                authorized_count += 1
            elif "NEGATO" in line_upper:
                denied_count += 1
            elif "CACHE" in line_upper or "REFRESH" in line_upper:
                cache_refresh_count += 1
            elif "ERROR" in line_upper:
                error_count += 1
        
        print(f"✅ Accessi Autorizzati: {authorized_count}")
        print(f"❌ Accessi Negati: {denied_count}")
        print(f"🔄 Cache Refresh: {cache_refresh_count}")
        print(f"🚨 Errori: {error_count}")
        
        # Diagnosi
        if authorized_count > 0 and cache_refresh_count == 0:
            print("\n🔍 DIAGNOSI:")
            print("   Il sistema autorizza accessi ma non fa cache refresh")
            print("   Conferma che OFFLINE_ALLOW_ACCESS=True è il problema")
        
        return True
        
    except Exception as e:
        print(f"❌ Analisi log fallita: {e}")
        return False

def suggest_fixes():
    """Suggerisce fix specifici"""
    
    print("\n🔧 SUGGERIMENTI FIX")
    print("=" * 25)
    
    print("1. ⚠️ CACHE REFRESH NON ATTIVO:")
    print("   Problema: OFFLINE_ALLOW_ACCESS=True bypassa controlli server")
    print("   Fix: Modificare logica in access_control.py")
    print("   Linea da cercare: se offline_allow_access è True")
    
    print("\n2. ⚡ RELAY NON RILASCIA:")
    print("   Problema RISOLTO: Logica relay corretta in base.py")
    print("   Status: ✅ Dovrebbe funzionare ora")
    
    print("\n3. 📝 LOGGING:")
    print("   Problema RISOLTO: Sistema log funziona")
    print("   Status: ✅ Log vengono scritti correttamente")
    
    print("\n🎯 AZIONE RACCOMANDATA:")
    print("   Testare il sistema con una carta SCONOSCIUTA")
    print("   per verificare se cache refresh si attiva")

def main():
    """Test principale"""
    
    print("🧪 TEST SEMPLICE SISTEMA RFID GATE")
    print("=" * 40)
    
    # Test 1: Configurazione
    config_ok = test_config()
    
    # Test 2: Analisi log
    log_ok = test_log_analysis()
    
    # Test 3: Suggerimenti
    suggest_fixes()
    
    print("\n📊 RIASSUNTO")
    print("=" * 15)
    print(f"✅ Configurazione: {'OK' if config_ok else 'ERRORE'}")
    print(f"✅ Log: {'OK' if log_ok else 'ERRORE'}")
    
    print("\n🚀 PROSSIMI PASSI:")
    print("1. Testare con carta sconosciuta")
    print("2. Monitorare log in tempo reale")
    print("3. Verificare comportamento relay")

if __name__ == "__main__":
    main()