#!/usr/bin/env python3
"""
🎯 Test Integrazione Completa Sistema Fallback REST
================================================

Test end-to-end del sistema di fallback REST con endpoint reale:
1. Simula scenario carta non in cache 
2. Verifica chiamata fallback REST a endpoint reale
3. Verifica cache immediato della risposta
4. Verifica performance accessi successivi
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Aggiungi path per import (ora siamo in tests/integration/)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.network.sync_manager import SyncManager

def load_env_file():
    """Carica file .env"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ File .env caricato")

class TestIntegrationFallback:
    def __init__(self):
        self.logger = logging.getLogger("test_integration")
        self.logger.setLevel(logging.INFO)
        
        # Usa configurazione reale dal .env
        load_env_file()
        self.config = RFIDGateConfig.from_env()
        
        # Cache temporaneo per test
        self.config.sync.cache_db_path = "test_integration_cache.db"
        
        self.sync_manager = SyncManager(self.config.sync, self.logger)
        
    async def setup(self):
        """Setup ambiente test"""
        print("🔧 Setup ambiente test...")
        
        # Inizializza database cache
        self.sync_manager._init_database()
        
        # Forza sistema online per test (bypassa health check)
        self.sync_manager.is_online = True
        
        print(f"📊 Configurazione fallback:")
        print(f"   Server: {self.config.sync.fallback_server_url}")
        print(f"   Endpoint: {self.config.sync.fallback_endpoint}")
        print(f"   Gate ID: {self.config.sync.gate_id}")
        print(f"   Timeout: {self.config.sync.fallback_timeout}s")
        print(f"   Status: {'🟢 Online' if self.sync_manager.is_online else '🔴 Offline'}")
        print()
        
    async def test_scenario_completo(self):
        """Test scenario completo: gap sync → fallback → cache → performance"""
        
        print("🎯 SCENARIO COMPLETO: Nuovo cliente si iscrive durante gap sync")
        print("=" * 70)
        
        test_card = "INTEGRATION_TEST_001"
        
        print(f"1️⃣ FASE 1: Cliente '{test_card}' si iscrive nel sistema centrale")
        print("   → Carta registrata nel server ma non ancora nel cache Raspberry")
        print("   → Gap di sync attivo (carta non nel cache locale)")
        print()
        
        print("2️⃣ FASE 2: Cliente prova immediatamente ad entrare...")
        
        # Test direzione IN
        result_in = await self.sync_manager.validate_card_offline(test_card, "in")
        
        print(f"   🚪 Direzione IN:")
        print(f"      Autorizzato: {result_in.get('authorized', False)}")
        print(f"      Motivo: {result_in.get('reason', 'N/A')}")
        print(f"      Customer ID: {result_in.get('customer_id', 'N/A')}")
        print(f"      Customer Name: {result_in.get('customer_name', 'N/A')}")
        print()
        
        # Test direzione OUT  
        result_out = await self.sync_manager.validate_card_offline(test_card, "out")
        
        print(f"   🚪 Direzione OUT:")
        print(f"      Autorizzato: {result_out.get('authorized', False)}")
        print(f"      Motivo: {result_out.get('reason', 'N/A')}")
        print()
        
        print("3️⃣ FASE 3: Verifica cache aggiornato immediatamente")
        
        # Verifica che la carta sia ora nel cache
        cached_result = await self.sync_manager.validate_card_offline(test_card, "in")
        print(f"   💾 Cache aggiornato: {cached_result.get('authorized', False)}")
        print(f"   📝 Fonte: {cached_result.get('reason', 'N/A')}")
        print()
        
        print("4️⃣ FASE 4: Performance - accessi successivi da cache")
        
        # Test performance: 5 accessi successivi dovrebbero essere tutti da cache
        cache_hits = 0
        for i in range(5):
            result = await self.sync_manager.validate_card_offline(test_card, "in")
            if "cache" in result.get('reason', '').lower():
                cache_hits += 1
                
        print(f"   🚀 Accessi da cache: {cache_hits}/5")
        print(f"   📈 Performance: {'✅ Ottimale' if cache_hits >= 4 else '⚠️ Da verificare'}")
        print()
        
        return result_in.get('authorized', False) and result_out.get('authorized', False)
        
    async def test_carte_multiple(self):
        """Test con multiple carte per verificare stabilità"""
        
        print("🔄 TEST CARTE MULTIPLE")
        print("=" * 30)
        
        test_cards = [
            "MULTI_TEST_001",
            "MULTI_TEST_002", 
            "MULTI_TEST_003"
        ]
        
        success_count = 0
        
        for i, card in enumerate(test_cards, 1):
            print(f"{i}️⃣ Test carta: {card}")
            
            result = await self.sync_manager.validate_card_offline(card, "in")
            authorized = result.get('authorized', False)
            
            print(f"   Risultato: {'✅ Autorizzata' if authorized else '❌ Negata'}")
            
            if authorized:
                success_count += 1
                
            # Pausa tra le carte
            await asyncio.sleep(0.5)
            
        print(f"\n📊 Risultato: {success_count}/{len(test_cards)} carte autorizzate")
        return success_count == len(test_cards)
        
    async def cleanup(self):
        """Cleanup ambiente test"""
        
        try:
            # Rimuovi cache temporaneo
            import os
            if os.path.exists(self.config.sync.cache_db_path):
                os.remove(self.config.sync.cache_db_path)
                print("🧹 Cache temporaneo rimosso")
        except Exception as e:
            print(f"⚠️ Errore cleanup: {e}")

async def main():
    """Test principale"""
    
    print("🎯 TEST INTEGRAZIONE COMPLETA SISTEMA FALLBACK REST")
    print("=" * 60)
    print()
    
    test = TestIntegrationFallback()
    
    try:
        # Setup
        await test.setup()
        
        # Test scenario completo
        scenario_ok = await test.test_scenario_completo()
        
        # Test carte multiple
        multi_ok = await test.test_carte_multiple()
        
        # Risultato finale
        print("\n" + "=" * 60)
        print("🏁 RISULTATI FINALI")
        print("=" * 60)
        print(f"✅ Scenario completo: {'PASS' if scenario_ok else 'FAIL'}")
        print(f"✅ Test carte multiple: {'PASS' if multi_ok else 'FAIL'}")
        
        if scenario_ok and multi_ok:
            print("\n🎉 TUTTI I TEST INTEGRAZIONE COMPLETATI CON SUCCESSO!")
            print("🔥 Il sistema di fallback REST è completamente funzionante!")
            print("💡 Gap di sync risolto: nuovi clienti possono accedere immediatamente!")
        else:
            print("\n⚠️ Alcuni test sono falliti, verificare la configurazione")
            
    except Exception as e:
        print(f"\n🚨 Errore durante i test: {e}")
        
    finally:
        # Cleanup
        await test.cleanup()

if __name__ == "__main__":
    # Configura logging per vedere cosa succede
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())