#!/usr/bin/env python3
"""
🔧 Apply Relay Patch Runtime
============================
Applica il patch relay al sistema già in esecuzione.
"""

import sys
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

def apply_patch_runtime():
    """Applica patch al sistema runtime"""
    
    print("🔧 Applicazione Patch Relay Runtime")
    print("=" * 50)
    
    try:
        # Importa e applica patch
        from patch_independent_relay import apply_independent_relay_patch
        
        print("🚀 Applicazione patch...")
        result = apply_independent_relay_patch()
        
        if result:
            print("✅ PATCH APPLICATO CON SUCCESSO!")
            print("🎯 Il sistema ora usa thread indipendenti per relay")
            print()
            print("📋 PROSSIMI PASSI:")
            print("1. Passa una carta sul lettore")
            print("2. Verifica che nei log appaia:")
            print("   🔛 relay_in: Tentativo attivazione (target_state=True, active_low=True)")
            print("   🔧 relay_in: GPIO.output(pin=18, state=LOW)")
            print("3. Il relay dovrebbe attivarsi immediatamente")
            print()
            return True
        else:
            print("❌ PATCH FALLITO!")
            return False
            
    except Exception as e:
        print(f"❌ Errore applicazione patch: {e}")
        return False

if __name__ == "__main__":
    apply_patch_runtime()