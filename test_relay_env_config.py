#!/usr/bin/env python3
"""
🧪 Test Configurazione Relay dal .env
====================================

Verifica che i relay prendano correttamente i valori dal .env
e che i default siano allineati al sistema legacy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_relay_config_from_env():
    """Test caricamento configurazione relay da .env"""
    print("🔧 TEST CARICAMENTO CONFIGURAZIONE RELAY DA .env")
    print("="*60)
    
    try:
        from rfid_gate.config.settings import RFIDGateConfig
        
        print("\n📁 Test 1: Caricamento da .env")
        print("-" * 40)
        
        # Carica configurazione da .env
        config = RFIDGateConfig.from_env()
        
        print(f"Relay IN configurazione:")
        print(f"  - enabled: {config.relay_in.enabled}")
        print(f"  - pin: {config.relay_in.pin}")
        print(f"  - active_time: {config.relay_in.active_time}")
        print(f"  - active_low: {config.relay_in.active_low}")
        print(f"  - initial_state: {config.relay_in.initial_state}")
        
        print(f"\nRelay OUT configurazione:")
        print(f"  - enabled: {config.relay_out.enabled}")
        print(f"  - pin: {config.relay_out.pin}")
        print(f"  - active_time: {config.relay_out.active_time}")
        print(f"  - active_low: {config.relay_out.active_low}")
        print(f"  - initial_state: {config.relay_out.initial_state}")
        
        # Verifica valori attesi dal .env
        print(f"\n📋 Test 2: Verifica Valori .env")
        print("-" * 40)
        
        # Valori attesi dal .env
        expected_relay_in = {
            'pin': 18,
            'active_time': 1,
            'active_low': True,
            'initial_state': 'HIGH',
            'enabled': True
        }
        
        expected_relay_out = {
            'pin': 19,
            'active_time': 1,
            'active_low': True,
            'initial_state': 'HIGH',
            'enabled': True
        }
        
        # Verifica relay IN
        relay_in_ok = (
            config.relay_in.pin == expected_relay_in['pin'] and
            config.relay_in.active_time == expected_relay_in['active_time'] and
            config.relay_in.active_low == expected_relay_in['active_low'] and
            config.relay_in.initial_state == expected_relay_in['initial_state'] and
            config.relay_in.enabled == expected_relay_in['enabled']
        )
        
        # Verifica relay OUT  
        relay_out_ok = (
            config.relay_out.pin == expected_relay_out['pin'] and
            config.relay_out.active_time == expected_relay_out['active_time'] and
            config.relay_out.active_low == expected_relay_out['active_low'] and
            config.relay_out.initial_state == expected_relay_out['initial_state'] and
            config.relay_out.enabled == expected_relay_out['enabled']
        )
        
        status_in = "✅" if relay_in_ok else "❌"
        status_out = "✅" if relay_out_ok else "❌"
        
        print(f"{status_in} Relay IN: Valori dal .env corretti")
        print(f"{status_out} Relay OUT: Valori dal .env corretti")
        
        print(f"\n🧪 Test 3: Logica Legacy")
        print("-" * 40)
        
        legacy_correct = (
            config.relay_in.active_low == True and
            config.relay_in.initial_state == "HIGH" and
            config.relay_out.active_low == True and
            config.relay_out.initial_state == "HIGH"
        )
        
        if legacy_correct:
            print("✅ LEGACY LOGIC: Configurazione corretta")
            print("✅ active_low = True (moduli optoaccoppiatore)")
            print("✅ initial_state = HIGH (relè partono spenti)")
        else:
            print("❌ LEGACY LOGIC: Problemi configurazione")
            
        return relay_in_ok and relay_out_ok and legacy_correct
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relay_defaults():
    """Test che i default siano corretti anche senza .env"""
    print(f"\n🧪 Test 4: Default Settings (Simulazione .env mancante)")
    print("-" * 40)
    
    try:
        import os
        
        # Salva environment originale
        original_env = dict(os.environ)
        
        # Rimuovi variabili RELAY dal environment per testare i default
        relay_vars = [k for k in os.environ.keys() if k.startswith('RELAY_')]
        for var in relay_vars:
            del os.environ[var]
            
        print(f"Rimosso {len(relay_vars)} variabili RELAY_ dall'environment")
        
        # Test default (dopo la correzione)
        from rfid_gate.config.settings import RFIDGateConfig
        config = RFIDGateConfig.from_env()
        
        print(f"Default relay IN:")
        print(f"  - active_low: {config.relay_in.active_low} (should be True)")
        print(f"  - initial_state: {config.relay_in.initial_state} (should be HIGH)")
        
        defaults_ok = (
            config.relay_in.active_low == True and
            config.relay_in.initial_state == "HIGH"
        )
        
        status = "✅" if defaults_ok else "❌"
        print(f"{status} Default values: {'CORRETTI' if defaults_ok else 'SBAGLIATI'}")
        
        # Ripristina environment
        os.environ.clear()
        os.environ.update(original_env)
        
        return defaults_ok
        
    except Exception as e:
        print(f"❌ Errore test default: {e}")
        return False

def main():
    """Test principale completo"""
    success1 = test_relay_config_from_env()
    success2 = test_relay_defaults()
    
    print(f"\n🎯 RISULTATO TEST CONFIGURAZIONE:")
    print("="*60)
    
    if success1 and success2:
        print("✅ CONFIGURAZIONE RELAY: PERFETTA")
        print("📁 Caricamento da .env: FUNZIONANTE")
        print("🔧 Default settings: CORRETTI") 
        print("🎯 I relay ora usano correttamente i valori dal .env!")
    else:
        print("❌ PROBLEMI CONFIGURAZIONE")
        if not success1:
            print("❌ Caricamento da .env fallito")
        if not success2:
            print("❌ Default settings sbagliati")
    
    return success1 and success2

if __name__ == "__main__":
    main()