#!/usr/bin/env python3
"""
🔄 Cache Refresh Strategy - Gestione Aggiornamenti Abbonamenti
============================================================

Strategia per gestire il caso critico:
Cliente con carta in cache (expired) che rinnova abbonamento

WORKFLOW CORRETTO:
1. Cache refresh SOLO aggiorna cache locale
2. NON chiama gate-verification direttamente  
3. Sistema ricontrolla cache aggiornata
4. Se cache OK → MQTT → broker → gate-verification → decisione finale
"""

import asyncio
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


class CacheRefreshManager:
    """Gestisce refresh intelligente cache per abbonamenti rinnovati"""
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.cache_path = Path("cache/local_cache.db")
        
        # Carica parametri da .env per cache refresh
        import os
        self.enabled = os.getenv('CACHE_REFRESH_ENABLED', 'true').lower() == 'true'
        self.timeout_ms = int(os.getenv('CACHE_REFRESH_TIMEOUT', '5000'))
        self.cooldown_sec = int(os.getenv('CACHE_REFRESH_COOLDOWN', '300'))
        self.single_card_endpoint = os.getenv('CACHE_REFRESH_SINGLE_CARD_ENDPOINT', '/api/sync-gate')
        self.max_retries = int(os.getenv('CACHE_REFRESH_MAX_RETRIES', '2'))
        self.retry_delay_ms = int(os.getenv('CACHE_REFRESH_RETRY_DELAY', '1000'))
        
        print(f"📋 Cache Refresh Config:")
        print(f"   Enabled: {self.enabled}")
        print(f"   Timeout: {self.timeout_ms}ms")
        print(f"   Cooldown: {self.cooldown_sec}s")
        print(f"   Endpoint: {self.single_card_endpoint}")
    
    async def handle_denied_card_refresh(self, card_uid: str) -> bool:
        """
        Gestisce refresh cache per carta negata dalla cache locale.
        
        IMPORTANTE: Questo metodo SOLO aggiorna la cache locale con dati freschi.
        NON decide l'autorizzazione finale (quello è compito del workflow MQTT).
        
        Returns:
            bool: True se cache è stata aggiornata con successo, False altrimenti
        """
        # Controllo se cache refresh è abilitato
        if not self.enabled:
            print(f"⏸️  Cache refresh disabilitato - skip per {card_uid}")
            return False
            
        print(f"🔄 Cache refresh per carta negata: {card_uid}")
        
        try:
            # 1. Verifica se carta è stata controllata recentemente (evita spam)
            if await self._is_recently_refreshed(card_uid):
                print(f"   ⏱️ Carta già controllata recentemente - skip refresh")
                return False
            
            # 2. Scarica dati aggiornati dal server
            server_data = await self._check_single_card_server(card_uid)
            
            if server_data and server_data.get('found'):
                # 3. Aggiorna cache locale con dati freschi
                await self._update_single_card_cache(card_uid, server_data)
                
                print(f"   ✅ Cache refresh completato per {card_uid}")
                print(f"   📋 Il sistema ora rivaluterà la cache aggiornata")
                print(f"   📡 Se cache OK → MQTT → broker → gate-verification → decisione finale")
                
                return True  # Cache refreshed successfully
            else:
                # 4. Carta non trovata su server - marca come controllata
                await self._mark_card_checked(card_uid)
                print(f"   📭 Carta {card_uid} non trovata su server")
                return False
                
        except Exception as e:
            print(f"   ⚠️ Errore durante cache refresh per {card_uid}: {e}")
            return False
    
    async def _is_recently_refreshed(self, card_uid: str) -> bool:
        """Controlla se carta è stata controllata recentemente"""
        try:
            conn = sqlite3.connect(str(self.cache_path))
            cursor = conn.cursor()
            
            # Usa cooldown configurabile da .env
            cooldown_minutes = self.cooldown_sec // 60 if self.cooldown_sec >= 60 else 5
            
            # Cerca ultimo check per questa carta
            cursor.execute("""
                SELECT last_server_check FROM synced_cards 
                WHERE card_uid = ? AND last_server_check > datetime('now', '-{} minutes')
            """.format(cooldown_minutes), (card_uid,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                print(f"   ⏱️ Carta controllata recentemente (cooldown {cooldown_minutes}min)")
                return True
            return False
            
        except Exception:
            return False
    
    async def _check_single_card_server(self, card_uid: str) -> dict:
        """Scarica dati aggiornati carta da server (SOLO per aggiornare cache)"""
        try:
            # Usa SOLO sync endpoint per scaricare dati aggiornati
            # NON chiama gate-verification (quello è compito del broker via MQTT)
            return await self._try_sync_endpoint(card_uid)
            
        except Exception as e:
            print(f"   ⚠️ Errore server check: {e}")
            return None
    
    async def _try_sync_endpoint(self, card_uid: str) -> dict:
        """Scarica dati aggiornati da sync endpoint con retry configurabile"""
        
        for attempt in range(self.max_retries + 1):
            try:
                # Usa endpoint configurabile per singola carta
                url = f"{self.sync_manager.config.server_url}{self.single_card_endpoint}"
                params = {
                    'card_uid': card_uid,
                    'gate_id': getattr(self.sync_manager, 'tornello_id', 'tornello_01'),
                    'refresh': 'true'
                }
                
                if attempt > 0:
                    print(f"   🔄 Retry {attempt}/{self.max_retries}: {card_uid}")
                else:
                    print(f"   🔄 Sync refresh: {card_uid}")
                
                # Usa timeout configurabile
                timeout_sec = self.timeout_ms / 1000.0
                
                async with self.sync_manager._create_aiohttp_session(timeout_sec) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('success') and data.get('data'):
                                card_data = data['data']
                                
                                # Verifica che sia la carta richiesta (endpoint singola carta)
                                if card_data.get('card_uid') == card_uid:
                                    print(f"   ✅ Dati aggiornati scaricati da server (attempt {attempt + 1})")
                                    
                                    # IMPORTANTE: Restituisce SOLO dati per cache update
                                    # NON decide autorizzazione (quello è compito del workflow MQTT)
                                    return {
                                        'found': True,
                                        'customer_name': card_data.get('customer_name', 'Unknown'),
                                        'customer_id': card_data.get('customer_id'),
                                        'has_active_subscriptions': len(card_data.get('active_subscriptions', [])) > 0,
                                        'in_white_list': card_data.get('in_white_list', False),
                                        'source': 'sync_endpoint_refresh'
                                    }
                                else:
                                    print(f"   ⚠️ Server restituì carta diversa: {card_data.get('card_uid')} != {card_uid}")
                                    return {'found': False, 'source': 'sync_endpoint_refresh'}
                            else:
                                print(f"   📭 Carta {card_uid} non trovata su server")
                                return {'found': False, 'source': 'sync_endpoint_refresh'}
                        else:
                            print(f"   ⚠️ Server response HTTP {response.status}")
                            if attempt < self.max_retries:
                                await asyncio.sleep(self.retry_delay_ms / 1000.0)
                                continue
                            return None
                            
            except Exception as e:
                print(f"   ⚠️ Errore sync endpoint (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_ms / 1000.0)
                    continue
                return None
        
        return None
    
    async def _update_single_card_cache(self, card_uid: str, server_data: dict):
        """Aggiorna singola carta in cache con dati freschi da server"""
        try:
            if not server_data.get('found'):
                print(f"   📭 Carta {card_uid} non trovata su server - nessun update cache")
                return
            
            conn = sqlite3.connect(str(self.cache_path))
            cursor = conn.cursor()
            
            # Determina se carta dovrebbe essere attiva in base ai dati server
            # NOTA: Questo è per la cache locale, NON per autorizzazione finale
            should_be_active = (
                server_data.get('in_white_list', False) or 
                server_data.get('has_active_subscriptions', False)
            )
            
            # Aggiorna carta con dati server freschi
            cursor.execute("""
                INSERT OR REPLACE INTO synced_cards 
                (card_uid, is_active, customer_name, customer_id, last_sync, last_server_check)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                card_uid,
                1 if should_be_active else 0,  # Cache locale aggiornata
                server_data.get('customer_name', 'Unknown'),
                server_data.get('customer_id')
            ))
            
            conn.commit()
            conn.close()
            
            status = "ATTIVA" if should_be_active else "INATTIVA"
            print(f"   💾 Cache aggiornata: {card_uid} → {status}")
            
        except Exception as e:
            print(f"   ⚠️ Errore aggiornamento cache: {e}")
    
    async def _mark_card_checked(self, card_uid: str):
        """Marca carta come controllata recentemente"""
        try:
            conn = sqlite3.connect(str(self.cache_path))
            cursor = conn.cursor()
            
            # Aggiorna timestamp per evitare check ripetuti
            cursor.execute("""
                INSERT OR REPLACE INTO synced_cards 
                (card_uid, is_active, customer_name, customer_id, last_sync, last_server_check)
                VALUES (?, 0, 'Not Found', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (card_uid,))
            
            conn.commit()
            conn.close()
            
            print(f"   🕒 Carta {card_uid} marcata come controllata")
            
        except Exception as e:
            print(f"   ⚠️ Errore marcatura carta: {e}")
    
    async def refresh_cache_for_renewed_subscription(self, card_uid: str) -> bool:
        """
        Metodo pubblico per refresh abbonamento rinnovato
        
        Scenario: Cliente con abbonamento scaduto rinnova, ma cache locale ha ancora 
        dati vecchi. Questo metodo forza update con dati server freschi.
        """
        print(f"🔄 Refresh abbonamento rinnovato: {card_uid}")
        
        try:
            # Forza refresh ignorando timestamp recenti
            server_data = await self._check_single_card_server(card_uid)
            
            if server_data and server_data.get('found'):
                await self._update_single_card_cache(card_uid, server_data)
                print(f"✅ Abbonamento rinnovato aggiornato in cache per {card_uid}")
                return True
            else:
                print(f"❌ Dati abbonamento rinnovato non trovati per {card_uid}")
                return False
                
        except Exception as e:
            print(f"⚠️ Errore refresh abbonamento rinnovato: {e}")
            return False
    
    async def handle_unknown_card_refresh(self, card_uid: str) -> bool:
        """
        Gestisce refresh cache per carta sconosciuta (non in cache locale).
        
        Scenario: Cliente ha carta nuova o cache è stata svuotata.
        Controlla server per vedere se è una carta valida.
        """
        print(f"🔄 Cache refresh per carta sconosciuta: {card_uid}")
        
        if not self.enabled:
            print("❌ Cache refresh disabilitato")
            return False
            
        # Controlla se dobbiamo aspettare cooldown (stesso di handle_denied_card_refresh)
        if not await self._check_cooldown(card_uid):
            return False
        
        try:
            # Controlla server per carta sconosciuta
            server_data = await self._check_single_card_server(card_uid)
            
            if server_data and server_data.get('found'):
                await self._update_single_card_cache(card_uid, server_data)
                print(f"✅ Carta sconosciuta aggiunta alla cache: {card_uid}")
                return True
            else:
                print(f"📭 Carta sconosciuta non trovata nel server: {card_uid}")
                # Registra il tentativo per cooldown
                await self._update_refresh_timestamp(card_uid)
                return False
                
        except Exception as e:
            print(f"⚠️ Errore refresh carta sconosciuta: {e}")
            return False