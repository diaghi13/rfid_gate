#!/usr/bin/env python3
"""
🧪 Test MQTT Fix - Workflow Single Topic
========================================
Test per verificare che ora venga inviato un solo topic MQTT
e che il workflow sia corretto: Card → [Auth locale + MQTT badge paralleli] → Relay
"""

import asyncio
import sys
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

async def test_mqtt_workflow():
    """Test del workflow MQTT ottimizzato"""
    print("🧪 Test MQTT Workflow - Single Topic")
    print("=" * 50)
    
    print("📋 WORKFLOW ATTESO:")
    print("1. Card letta")
    print("2. Auth locale + MQTT badge (paralleli)")
    print("3. Relay attivato se auth locale OK")
    print("4. SOLO un topic MQTT: gate/tornello_01/badge")
    print()
    
    # Simula test
    card_uid = "632D3903"
    
    print(f"📇 Card simulata: {card_uid}")
    print("🔍 Verifica che nei log del sistema reale vedrai:")
    print("   ✅ Un solo invio MQTT a gate/tornello_01/badge")
    print("   ✅ Auth locale immediata")
    print("   ✅ Relay attivato se autorizzato")
    print("   ❌ NESSUN invio a gate/tornello_01/auth_request")
    print()
    
    print("🎯 CONFRONTO PRIMA vs DOPO:")
    print()
    print("PRIMA (sbagliato):")
    print("  📤 MQTT: gate/tornello_01/badge")
    print("  📤 MQTT: gate/tornello_01/auth_request")
    print("  ⚡ Relay attivato")
    print()
    print("DOPO (corretto):")
    print("  📤 MQTT: gate/tornello_01/badge (unico)")
    print("  ⚡ Relay attivato (parallelo)")
    print()
    
    print("🚀 TESTA ORA SUL RASPBERRY PI:")
    print("Avvia il sistema e passa una card per verificare")
    print("che vedi solo un invio MQTT al topic badge!")

if __name__ == "__main__":
    asyncio.run(test_mqtt_workflow())