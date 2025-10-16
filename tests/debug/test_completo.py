#!/usr/bin/env python3
"""
🧪 Test Completo Sistema RFID Gate
================================
Test completo delle funzionalità: relay, cache refresh, logging
"""

import sys
import os
import time
from pathlib import Path

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

def test_import_system():
    """Test import del sistema"""
    
    print("🧪 Test Import Sistema")
    print("=" * 30)
    
    try:
        # Test import core
        from rfid_gate.core.access_control import AccessControlSystem
        print("✅ AccessControlSystem importato")
        
        from rfid_gate.network.cache_refresh_strategy import CacheRefreshManager
        print("✅ CacheRefreshManager importato")
        
        from rfid_gate.hardware.relays.base import BaseRelayController
        print("✅ BaseRelayController importato")
        
        from rfid_gate.config.settings import RFIDGateConfig
        print("✅ RFIDGateConfig importato")
        
        return True
        
    except Exception as e:
        print(f"❌ Import fallito: {e}")
        return False

def test_settings_loading():
    """Test caricamento configurazioni"""
    
    print("\n📋 Test Configurazioni")
    print("=" * 30)
    
    try:
        from rfid_gate.config.settings import RFIDGateConfig
        
        config = RFIDGateConfig()
        settings = config
        
        # Test configurazioni critiche
        print(f"📡 MQTT Broker: {settings.mqtt.broker}")
        print(f"🔄 Bidirezionale: {settings.bidirectional.enabled}")
        print(f"🔄 Offline Access: {settings.offline.allow_access}")
        print(f"🔄 Cache Refresh: {settings.cache_refresh.enabled}")
        print(f"📁 Log Directory: {settings.logging.directory}")
        
        # Test relay settings
        print(f"⚡ Relay Pin: {settings.gpio.relay_pin}")
        print(f"⚡ Relay Active Low: {settings.gpio.relay_active_low}")
        print(f"⚡ Relay Duration: {settings.timing.relay_duration}")
        
        return settings
        
    except Exception as e:
        print(f"❌ Settings fallito: {e}")
        return None

def test_cache_refresh_conditions(settings):
    """Test condizioni cache refresh"""
    
    print("\n🔄 Test Cache Refresh Conditions")
    print("=" * 40)
    
    # Simula scenario cache refresh
    print("🧪 Scenario: Carta non trovata in cache locale")
    
    # Condizioni per cache refresh
    cache_enabled = settings.cache_refresh.enabled
    offline_access = settings.offline.allow_access
    
    print(f"   Cache Refresh Abilitato: {cache_enabled}")
    print(f"   Offline Access Abilitato: {offline_access}")
    
    if cache_enabled and not offline_access:
        print("✅ Cache refresh si attiverà (carta sconosciuta + no offline)")
    elif cache_enabled and offline_access:
        print("⚠️ Cache refresh potrebbe non attivarsi (offline access permesso)")
        print("    Il sistema darà accesso senza controllare il server")
    else:
        print("❌ Cache refresh disabilitato")
    
    # Test endpoint
    endpoint = settings.cache_refresh.single_card_endpoint
    print(f"🌐 Endpoint Cache Refresh: {endpoint}")
    
    return cache_enabled

def test_relay_logic():
    """Test logica relay"""
    
    print("\n⚡ Test Logica Relay")
    print("=" * 25)
    
    try:
        # Test senza hardware (mock)
        from rfid_gate.hardware.relays.base import BaseRelayController
        
        # Simula relay controller
        class MockRelayController(BaseRelayController):
            def __init__(self):
                super().__init__(relay_id="test", pin=18, active_low=True)
                self.activated = False
                
            def _physical_activate(self):
                print("   🔧 Mock: GPIO -> LOW (relay attivato)")
                self.activated = True
                
            def _physical_deactivate(self):
                print("   🔧 Mock: GPIO -> HIGH (relay disattivato)")
                self.activated = False
        
        # Test relay
        relay = MockRelayController()
        
        print("🧪 Test attivazione relay:")
        relay.activate()
        print(f"   Stato: {'ATTIVO' if relay.activated else 'INATTIVO'}")
        
        time.sleep(0.1)  # Simula durata
        
        print("🧪 Test disattivazione relay:")
        relay.deactivate()
        print(f"   Stato: {'ATTIVO' if relay.activated else 'INATTIVO'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test relay fallito: {e}")
        return False

def test_log_monitoring():
    """Monitora log in tempo reale per il test"""
    
    print("\n👀 Monitoraggio Log Attivo")
    print("=" * 30)
    print("(Premi Ctrl+C per fermare)")
    
    log_file = Path("logs/system.log")
    
    if not log_file.exists():
        print("❌ File di log non trovato!")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # Va alla fine del file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    line = line.strip()
                    
                    # Filtra eventi interessanti
                    if any(word in line.upper() for word in ['AUTORIZZATO', 'NEGATO', 'CACHE', 'REFRESH', 'ERROR']):
                        if "AUTORIZZATO" in line:
                            print(f"✅ {line}")
                        elif "NEGATO" in line:
                            print(f"❌ {line}")
                        elif "CACHE" in line or "REFRESH" in line:
                            print(f"🔄 {line}")
                        elif "ERROR" in line:
                            print(f"🚨 {line}")
                        else:
                            print(f"📋 {line}")
                else:
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\n👋 Monitoraggio fermato.")

def main():
    """Test completo del sistema"""
    
    print("🧪 TEST COMPLETO SISTEMA RFID GATE")
    print("=" * 50)
    
    # Test 1: Import sistema
    if not test_import_system():
        print("\n❌ Test import fallito - impossibile continuare")
        return
    
    # Test 2: Settings
    settings = test_settings_loading()
    if not settings:
        print("\n❌ Test settings fallito - impossibile continuare")
        return
    
    # Test 3: Cache refresh conditions
    cache_enabled = test_cache_refresh_conditions(settings)
    
    # Test 4: Relay logic
    relay_ok = test_relay_logic()
    
    # Riassunto
    print("\n📊 RIASSUNTO TEST")
    print("=" * 20)
    print(f"✅ Import Sistema: OK")
    print(f"✅ Settings: OK")
    print(f"{'✅' if cache_enabled else '❌'} Cache Refresh: {'Abilitato' if cache_enabled else 'Disabilitato'}")
    print(f"{'✅' if relay_ok else '❌'} Relay Logic: {'OK' if relay_ok else 'ERRORE'}")
    
    # Raccomandazioni
    print("\n💡 RACCOMANDAZIONI")
    print("=" * 20)
    
    if settings.offline.allow_access and cache_enabled:
        print("⚠️ OFFLINE_ALLOW_ACCESS=True potrebbe impedire cache refresh")
        print("   Soluzione: Impostare OFFLINE_ALLOW_ACCESS=False per testare")
    
    if relay_ok:
        print("✅ Relay logic corretta - problema probabilmente risolto")
    
    print("\n🎯 Per monitorare il sistema in tempo reale:")
    print("   python test_completo.py monitor")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        test_log_monitoring()
    else:
        main()