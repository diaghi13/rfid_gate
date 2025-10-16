#!/usr/bin/env python3
"""
🧪 Test Debug - Nuova Carta Appena Registrata
Verifica flusso completo per carta non presente nella cache locale
"""

import asyncio
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from rfid_gate.core.access_control import AccessControlSystem, SystemMode
from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.hardware.readers.base import CardEvent

class NewCardTester:
    def __init__(self):
        # Carica configurazione
        self.config = RFIDGateConfig.load_from_env()
        
        # Inizializza sistema di controllo accessi  
        self.access_system = AccessControlSystem()
    
    async def setup(self):
        """Setup sistema"""
        await self.access_system.initialize()
        print("🚀 Sistema inizializzato")
    
    def remove_card_from_cache(self, card_uid: str):
        """Rimuove carta dalla cache locale per simulare carta nuova"""
        cache_db_path = "cache/local_cache.db"
        
        try:
            conn = sqlite3.connect(cache_db_path)
            cursor = conn.cursor()
            
            # Controlla se carta esiste
            cursor.execute("SELECT customer_name FROM synced_cards WHERE card_uid = ?", (card_uid,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"📋 Carta {card_uid} trovata in cache: {existing[0]}")
                
                # Rimuovi dalla cache
                cursor.execute("DELETE FROM synced_cards WHERE card_uid = ?", (card_uid,))
                conn.commit()
                
                print(f"🗑️ Carta {card_uid} rimossa dalla cache locale")
                return True
            else:
                print(f"❌ Carta {card_uid} non trovata in cache locale")
                return False
                
        except Exception as e:
            print(f"⚠️ Errore rimozione cache: {e}")
            return False
        finally:
            conn.close()
    
    async def test_new_card_flow(self, card_uid: str):
        """Testa flusso completa per carta nuova"""
        print(f"\n🧪 === TEST NUOVA CARTA: {card_uid} ===")
        
        # 1. Rimuovi carta dalla cache (simula carta nuova)
        removed = self.remove_card_from_cache(card_uid)
        if not removed:
            print("⚠️ ATTENZIONE: Carta non era in cache (forse è davvero nuova)")
        
        # 2. Simula lettura carta
        import time
        card_event = CardEvent(
            uid=card_uid,
            uid_formatted=card_uid, 
            reader_id="test_reader",
            direction="in",
            timestamp=time.time(),
            reader_type="mfrc522",
            metadata={"test": "new_card_flow"}
        )
        
        print(f"\n📱 Simulazione lettura carta: {card_uid}")
        print("🔍 Flusso atteso:")
        print("   1️⃣ Cache miss (carta non in cache)")
        print("   2️⃣ Cache refresh: GET /api/sync-gate")
        print("   3️⃣ Se trovata → aggiorna cache + autorizza")
        print("   4️⃣ Se non trovata → fallback diretto: POST /api/gate-verification")
        
        # 3. Esegui autenticazione
        try:
            result = await self.access_system._authenticate_card(card_event)
            
            print(f"\n✅ Risultato autenticazione: {result}")
            
            if result.name == "GRANT":
                print("🎉 SUCCESSO: Carta nuova autorizzata!")
            else:
                print("❌ PROBLEMA: Carta nuova NEGATA!")
                
        except Exception as e:
            print(f"💥 ERRORE durante autenticazione: {e}")
            import traceback
            traceback.print_exc()
    
    async def cleanup(self):
        """Cleanup"""
        await self.access_system.cleanup()
        print("🧹 Cleanup completato")

async def main():
    """Test principale"""
    tester = NewCardTester()
    
    try:
        await tester.setup()
        
        # Test con carta che dovrebbe esistere sul server ma non in cache
        # Usa una carta di un cliente esistente
        test_cards = [
            "44FB1DE5",  # Carta che potrebbe essere sul server
            "E22532EC",  # Altra carta test
            "F24FC4EB",  # PIETRO SALERNO
        ]
        
        for card_uid in test_cards:
            await tester.test_new_card_flow(card_uid)
            print("\n" + "="*60)
            
        print("\n🎯 CONCLUSIONI:")
        print("Se le carte sono state NEGATE nonostante dovrebbero esistere sul server,")
        print("il problema è nel flusso cache refresh o gate-verification.")
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())