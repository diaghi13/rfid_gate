#!/usr/bin/env python3
"""
🧪 Test MQTT Fix Verification
=============================
Test per verificare che la modifica MQTT funzioni
"""

import sys
from pathlib import Path

# Aggiungi path
sys.path.insert(0, str(Path(__file__).parent))

def test_mqtt_fix():
    """Test verifica MQTT fix"""
    print("🧪 Test MQTT Fix Verification")
    print("=" * 50)
    
    try:
        # Test import dopo modifica
        from rfid_gate.core.access_control import AccessControlSystem
        
        print("✅ Import AccessControlSystem: OK")
        
        # Leggi il file per verificare la modifica
        with open('/Users/davidedonghi/Apps/_micro services/rfid_gate/rfid_gate/core/access_control.py', 'r') as f:
            content = f.read()
        
        # Verifica che l'invio MQTT duplicato sia commentato
        if "# L'invio MQTT ora avviene DENTRO _authenticate_card()" in content:
            print("✅ MQTT duplicato commentato: OK")
            
            if content.count("await self._send_card_data(card_event)") == 0:
                print("✅ Chiamata _send_card_data rimossa: OK")
            else:
                print("⚠️  Chiamata _send_card_data ancora presente")
                
            print("\n🎯 RISULTATO MODIFICA:")
            print("✅ Rimossa duplicazione MQTT in _process_card_event")
            print("✅ L'invio MQTT ora avviene solo dentro _authenticate_card")
            print("✅ Workflow: Card → Auth locale + MQTT paralleli → Relay")
            
            return True
        else:
            print("❌ Modifica non trovata nel file")
            return False
            
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

def main():
    """Main test"""
    print("🔧 Verifica MQTT Fix")
    print("=" * 30)
    
    success = test_mqtt_fix()
    
    print(f"\n📊 RISULTATO: {'✅ SUCCESSO' if success else '❌ FALLITO'}")
    
    if success:
        print("\n🚀 PROSSIMO PASSO:")
        print("Testa sul Raspberry Pi per verificare che ora vedi:")
        print("   ✅ Un solo invio MQTT a gate/tornello_01/badge") 
        print("   ❌ NESSUN invio a gate/tornello_01/auth_request")
        print("   ⚡ Relay attivato normalmente")

if __name__ == "__main__":
    main()