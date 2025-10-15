#!/usr/bin/env python3
"""
🕐 Test per il timeout del controllo bidirezionale

Testa che lo stato delle direzioni venga resettato automaticamente
dopo il timeout configurato.
"""

import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta

from rfid_gate.network.sync_manager import SyncManager
from rfid_gate.config.settings import RFIDGateConfig, SystemConfig

class TestBidirectionalTimeout:
    """Test timeout controllo bidirezionale"""
    
    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup per ogni test"""
        # Crea database temporaneo
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)
        
        # Configurazione con timeout molto breve per test
        self.config = RFIDGateConfig()
        self.config.system = SystemConfig(
            tornello_id='test_tornello',
            bidirectional_mode=True,
            bidirectional_timeout_hours=100.0  # 100 ore per test (non scade mai nel test)
        )
        
        # Configura il sync con il database temporaneo
        from rfid_gate.config.settings import SyncConfig
        self.config.sync = SyncConfig(
            cache_db_path=self.db_path,
            server_url='http://test',
            enabled=True
        )
        
        # Crea SyncManager con config completa
        self.sync_manager = SyncManager(self.config, 'test_tornello')
        
        # Inizializza il database con le tabelle necessarie
        # Non serve più - SyncManager le crea automaticamente
        
        yield
        
        # Cleanup dopo ogni test
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @pytest.mark.asyncio
    async def test_timeout_resets_state(self):
        """Test: Timeout resetta lo stato"""
        # Per questo test specifico, creiamo un sync manager con timeout breve
        from rfid_gate.config.settings import SyncConfig
        temp_config = RFIDGateConfig()
        temp_config.system = SystemConfig(
            tornello_id='test_tornello',
            bidirectional_mode=True,
            bidirectional_timeout_hours=1.0  # 1 ora per questo test
        )
        temp_config.sync = SyncConfig(
            cache_db_path=self.db_path,
            server_url='http://test',
            enabled=True
        )
        temp_sync_manager = SyncManager(temp_config, 'test_tornello')
        
        card_uid = "TEST123"
        
        # Simula accesso IN nel passato
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Inserisci stato con timestamp passato (2 ore fa)
        past_time = datetime.now() - timedelta(hours=2)
        past_time_str = past_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', (card_uid, 'in', past_time_str, 'test_tornello'))
        
        conn.commit()
        conn.close()
        
        # Prova nuovo accesso IN - dovrebbe essere permesso per timeout
        result = await temp_sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        assert result['valid']
        assert 'Timeout scaduto' in result['reason']
        assert result['last_direction'] == 'in'  # Info mantenuta
    
    @pytest.mark.asyncio
    async def test_no_timeout_blocks_access(self):
        """Test: Senza timeout blocca accesso consecutivo"""
        card_uid = "TEST123"
        
        # Accesso IN recente
        await self.sync_manager.update_user_direction(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        # Tentativo accesso IN immediato - dovrebbe essere bloccato
        result = await self.sync_manager.check_bidirectional_access(
            card_uid=card_uid,
            direction="in",
            tornello_id="test_tornello"
        )
        
        assert not result['valid']
        assert 'Accesso consecutivo stesso tipo' in result['reason']
    
    @pytest.mark.asyncio
    async def test_cleanup_removes_expired_states(self):
        """Test: Cleanup rimuove stati scaduti"""
        # Per questo test specifico, creiamo un sync manager con timeout breve
        from rfid_gate.config.settings import SyncConfig
        temp_config = RFIDGateConfig()
        temp_config.system = SystemConfig(
            tornello_id='test_tornello',
            bidirectional_mode=True,
            bidirectional_timeout_hours=1.0  # 1 ora per questo test
        )
        temp_config.sync = SyncConfig(
            cache_db_path=self.db_path,
            server_url='http://test',
            enabled=True
        )
        temp_sync_manager = SyncManager(temp_config, 'test_tornello')
        
        # Inserisci alcuni stati - alcuni scaduti, altri no
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Stato scaduto (2 ore fa, timeout è 1 ora)
        expired_time = now - timedelta(hours=2)
        expired_str = expired_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Stato valido (30 minuti fa)
        valid_time = now - timedelta(minutes=30)
        valid_str = valid_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', ('EXPIRED1', 'in', expired_str, 'test_tornello'))
        
        cursor.execute('''
            INSERT INTO user_direction_state 
            (card_uid, last_direction, last_access_time, tornello_id)
            VALUES (?, ?, ?, ?)
        ''', ('VALID1', 'out', valid_str, 'test_tornello'))
        
        conn.commit()
        
        # Verifica che ci siano 2 record
        cursor.execute('SELECT COUNT(*) FROM user_direction_state')
        initial_count = cursor.fetchone()[0]
        assert initial_count == 2
        
        conn.close()
        
        # Esegui cleanup con il sync manager che ha timeout di 1 ora
        removed_count = await temp_sync_manager.cleanup_expired_direction_states()
        
        # Verifica che sia stato rimosso 1 record (quello scaduto)
        assert removed_count == 1
        
        # Verifica che rimanga solo 1 record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_direction_state')
        final_count = cursor.fetchone()[0]
        assert final_count == 1
        
        # Verifica che sia rimasto quello valido
        cursor.execute('SELECT card_uid FROM user_direction_state')
        remaining_card = cursor.fetchone()[0]
        assert remaining_card == 'VALID1'
        
        conn.close()

if __name__ == '__main__':
    # Esegui i test
    pytest.main([__file__, '-v'])