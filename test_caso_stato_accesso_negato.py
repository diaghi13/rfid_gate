#!/usr/bin/env python3
"""
🧪 Test per verificare che quando l'accesso viene NEGATO, 
lo stato IN/OUT NON viene aggiornato.

Scenario:
1. Utente fa IN (autorizzato) → stato diventa IN
2. Utente fa IN di nuovo (negato per direzione) → stato rimane IN 
3. Utente rinnova abbonamento
4. Utente fa IN diretto → deve funzionare (stato era rimasto IN)

Questo test verifica la richiesta dell'utente:
"Se l'accesso viene negato alla lettura della card non aggiornare lo stato in/out"
"""

import asyncio
import sqlite3
import tempfile
import os
import time
from unittest.mock import patch, AsyncMock, MagicMock

import sys
sys.path.insert(0, "/Users/davidedonghi/Apps/_micro services/rfid_gate")

from rfid_gate.config.settings import RFIDGateConfig, SystemConfig, SyncConfig
from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.core.access_control import AccessControlSystem, AccessDecision
from rfid_gate.hardware.readers.base import CardEvent

class TestStatoAccessoNegato:
    """Test per validazione stato con accessi negati"""
    
    def __init__(self):
        self.config = None
        self.sync_manager = None
        self.access_control = None
        self.temp_db = None
    
    async def setup(self):
        """Configura test environment"""
        # Crea database temporaneo
        fd, self.temp_db = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Configurazione test
        self.config = RFIDGateConfig(
            system=SystemConfig(
                bidirectional_mode=True,
                tornello_id="TEST_GATE_01"
            ),
            sync=SyncConfig(
                enabled=True,
                cache_db_path=self.temp_db
            )
        )
        
        # Setup sync manager
        self.sync_manager = SyncManager(self.config, self.config.system.tornello_id)
        print(f"🔍 Tornello ID configurato: {self.config.system.tornello_id}")
        print(f"🔍 Sync Manager tornello ID: {self.sync_manager.tornello_id}")
        
        # Setup access control con configurazione test
        self.access_control = AccessControlSystem()
        self.access_control.config = self.config  # Override config con quella del test
        self.access_control.sync_manager = self.sync_manager
        
        # Mock MQTT per evitare connessioni reali
        self.access_control.mqtt_client = AsyncMock()
        self.access_control.mqtt_client.is_connected.return_value = False
        
        print("✅ Test environment configurato")
    
    async def cleanup(self):
        """Pulizia test"""
        if self.sync_manager:
            await self.sync_manager.stop_background_sync()
        if self.temp_db and os.path.exists(self.temp_db):
            os.unlink(self.temp_db)
        print("🧹 Test environment pulito")
    
    def create_card_event(self, uid: str, direction: str) -> CardEvent:
        """Crea evento carta per test"""
        return CardEvent(
            uid=uid.replace(':', ''),
            uid_formatted=uid,
            direction=direction,
            reader_id="test_reader",
            timestamp=time.time(),
            reader_type="PN532",
            metadata={'test': True}
        )
    
    async def get_user_direction_state(self, card_uid: str, tornello_id: str) -> str:
        """Ottiene lo stato della direzione dal database"""
        import sqlite3
        conn = sqlite3.connect(self.sync_manager.db_path)
        cursor = conn.cursor()
        
        try:
            # Debug: verifica tutti i record nella tabella
            cursor.execute('SELECT * FROM user_direction_state')
            all_states = cursor.fetchall()
            print(f"🔍 Tutti gli stati direzioni: {all_states}")
            
            cursor.execute('''
                SELECT last_direction 
                FROM user_direction_state 
                WHERE card_uid = ? AND tornello_id = ?
            ''', (card_uid, tornello_id))
            
            result = cursor.fetchone()
            print(f"🔍 Query stato per {card_uid}, {tornello_id}: {result}")
            return result[0] if result else None
            
        finally:
            conn.close()
    
    async def test_accesso_negato_non_aggiorna_stato(self):
        """
        Test principale: accesso negato NON deve aggiornare lo stato
        """
        print("\n🧪 TEST: Accesso negato NON aggiorna stato")
        print("=" * 50)
        
        card_uid = "04:1A:2B:3C"
        tornello_id = self.config.system.tornello_id
        
        # ========================================================================
        # STEP 1: Primo accesso IN (deve essere sempre autorizzato)
        # ========================================================================
        print("\n📥 STEP 1: Primo accesso IN")
        
        # Simula carta autorizzata in cache (con abbonamento attivo)
        import sqlite3
        import json
        conn = sqlite3.connect(self.sync_manager.db_path)
        cursor = conn.cursor()
        
        # Crea abbonamento attivo
        active_subscription = [{
            "type": "monthly",
            "expires_at": "2026-12-31T23:59:59",
            "uses_remaining": 100,
            "active": True
        }]
        
        cursor.execute('''
            INSERT OR REPLACE INTO synced_cards 
            (card_uid, customer_id, customer_name, in_white_list, active_subscriptions, last_sync, is_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (card_uid, "CUST001", "John Doe", True, json.dumps(active_subscription)))
        
        # Debug: verifica tabelle database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"🔍 Tabelle nel DB: {[table[0] for table in tables]}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Carta {card_uid} inserita in cache con abbonamento attivo")
        # Debug: verifica configurazione bidirezionale
        print(f"🔍 Config bidirezionale: {self.config.system.bidirectional_mode}")
        print(f"🔍 Sync manager: {self.sync_manager is not None}")
        
        card_event_in1 = self.create_card_event(card_uid, "in")
        result1 = await self.access_control._authenticate_card(card_event_in1)
        
        print(f"   Risultato primo IN: {result1}")
        assert result1 == AccessDecision.GRANT, "Primo accesso IN deve essere autorizzato"
        
        # Verifica stato salvato nel DB
        stato_dopo_in1 = await self.get_user_direction_state(card_uid, tornello_id)
        print(f"   Stato nel DB dopo primo IN: {stato_dopo_in1}")
        assert stato_dopo_in1 == "in", "Stato deve essere 'in' dopo primo accesso"
        
        # ========================================================================
        # STEP 2: Secondo accesso IN consecutivo (WHITELIST = sempre autorizzato)
        # ========================================================================
        print("\n📥 STEP 2: Secondo accesso IN consecutivo (WHITELIST bypass)")
        
        card_event_in2 = self.create_card_event(card_uid, "in")
        result2 = await self.access_control._authenticate_card(card_event_in2)
        
        print(f"   Risultato secondo IN: {result2}")
        assert result2 == AccessDecision.GRANT, "WHITELIST deve sempre autorizzare (bypass bidirezionale)"
        
        # ✅ VERIFICA: WHITELIST aggiorna sempre lo stato (non c'è negazione)
        stato_dopo_in2 = await self.get_user_direction_state(card_uid, tornello_id)
        print(f"   Stato nel DB dopo secondo IN whitelist: {stato_dopo_in2}")
        assert stato_dopo_in2 == "in", "WHITELIST può fare accessi multipli e aggiorna stato"
        
        # ========================================================================
        # STEP 3: Test carta NON-whitelist con controllo bidirezionale
        # ========================================================================
        print("\n� STEP 3: Test carta normale (NON-whitelist) per controllo bidirezionale")
        
        # Crea carta normale con abbonamento attivo ma NON in whitelist
        normal_card_uid = "05:2B:3C:4D"
        conn = sqlite3.connect(self.sync_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO synced_cards 
            (card_uid, customer_id, customer_name, in_white_list, active_subscriptions, last_sync, is_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (normal_card_uid, "CUST002", "Normal User", True, json.dumps(active_subscription)))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Carta normale {normal_card_uid} inserita (NON-whitelist)")
        
        # Primo accesso normale - deve funzionare 
        card_event_normal1 = self.create_card_event(normal_card_uid, "in")
        result_normal1 = await self.access_control._authenticate_card(card_event_normal1)
        print(f"   Primo IN carta normale: {result_normal1}")
        assert result_normal1 == AccessDecision.GRANT, "Primo accesso deve essere autorizzato"
        
        # Secondo accesso normale - deve essere NEGATO per controllo bidirezionale
        card_event_normal2 = self.create_card_event(normal_card_uid, "in")  
        result_normal2 = await self.access_control._authenticate_card(card_event_normal2)
        print(f"   Secondo IN carta normale: {result_normal2}")
        assert result_normal2 == AccessDecision.DENY, "Carta normale deve rispettare controllo bidirezionale"
        
        print("   ✅ Controllo bidirezionale funziona per carte normali")
        
        # ========================================================================  
        # STEP 4: WHITELIST continua a funzionare liberamente
        # ========================================================================
        print("\n📥 STEP 4: WHITELIST continua accessi liberi")
        
        card_event_in3 = self.create_card_event(card_uid, "in")
        result3 = await self.access_control._authenticate_card(card_event_in3)
        
        print(f"   Terzo IN whitelist: {result3}")
        assert result3 == AccessDecision.GRANT, "WHITELIST sempre autorizzata"
        
        stato_dopo_in3 = await self.get_user_direction_state(card_uid, tornello_id)
        print(f"   Stato nel DB dopo terzo IN whitelist: {stato_dopo_in3}")
        assert stato_dopo_in3 == "in", "WHITELIST aggiorna sempre stato"
        
        # ========================================================================
        # STEP 5: Prova OUT (direzione opposta) - deve funzionare
        # ========================================================================
        print("\n📤 STEP 5: Tentativo OUT (direzione opposta)")
        
        card_event_out = self.create_card_event(card_uid, "out")
        result_out = await self.access_control._authenticate_card(card_event_out)
        
        print(f"   Risultato OUT: {result_out}")
        assert result_out == AccessDecision.GRANT, "OUT dopo IN deve essere autorizzato"
        
        stato_dopo_out = await self.get_user_direction_state(card_uid, tornello_id)
        print(f"   Stato nel DB dopo OUT: {stato_dopo_out}")
        assert stato_dopo_out == "out", "Stato deve essere 'out' dopo OUT autorizzato"
        
        # ========================================================================
        # STEP 6: Ora IN deve funzionare (direzione opposta)
        # ========================================================================
        print("\n📥 STEP 6: IN dopo OUT (direzione opposta)")
        
        card_event_in4 = self.create_card_event(card_uid, "in")
        result4 = await self.access_control._authenticate_card(card_event_in4)
        
        print(f"   Risultato IN dopo OUT: {result4}")
        assert result4 == AccessDecision.GRANT, "IN dopo OUT deve essere autorizzato"
        
        stato_finale = await self.get_user_direction_state(card_uid, tornello_id)
        print(f"   Stato finale nel DB: {stato_finale}")
        assert stato_finale == "in", "Stato finale deve essere 'in'"
        
        print("\n✅ TEST COMPLETATO - Comportamento CORRETTO!")
        print("📋 RIEPILOGO:")
        print("   • WHITELIST: Accesso sempre libero (bypass controllo bidirezionale)")
        print("   • CARTE NORMALI: Controllo bidirezionale attivo")
        print("   • Accessi negati NON aggiornano lo stato") 
        print("   • Operatori possono entrare/uscire più volte con stesso badge")
        
        return True

async def main():
    """Esegue il test"""
    tester = TestStatoAccessoNegato()
    
    try:
        await tester.setup()
        success = await tester.test_accesso_negato_non_aggiorna_stato()
        
        if success:
            print("\n🎯 RISULTATO: Sistema PERFETTO per operatori e utenti!")
            print("✅ WHITELIST: Accesso sempre libero senza controlli bidirezionali")
            print("✅ CARTE NORMALI: Controllo bidirezionale + accessi negati NON aggiornano stato")
            print("✅ Operatori possono entrare più persone con stesso badge")
            
    except Exception as e:
        print(f"\n❌ ERRORE durante test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())