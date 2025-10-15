#!/usr/bin/env python3
"""
🔄 Sync Manager - Sistema di sincronizzazione offline-first
=========================================================

Sistema di sincronizzazione che gestisce:
- Cache locale delle carte autorizzate
- Sincronizzazione giornaliera
- Log degli accessi con retry
- Validazione offline-first

Mantiene la nomenclatura esistente per compatibilità.
"""

import asyncio
import json
import sqlite3
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from ..config.settings import SyncConfig

# Import condizionali per dipendenze esterne
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    # Mock per development
    class aiohttp:
        class ClientSession:
            def __init__(self, timeout=None): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def get(self, url, params=None): return MockResponse()
            async def post(self, url, json=None): return MockResponse()
        
        class ClientTimeout:
            def __init__(self, total=None): pass

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class MockResponse:
    status = 200
    async def json(self): return []
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass


@dataclass
class CardData:
    """Struttura dati carta sincronizzata (mantiene nomenclatura API)"""
    card_uid: str
    customer_id: Optional[int]  # Può essere null per carte whitelist
    customer_name: str
    in_white_list: bool
    active_subscriptions: List[Dict[str, Any]]
    
    def __post_init__(self):
        # Assicura che active_subscriptions sia una lista
        if not isinstance(self.active_subscriptions, list):
            self.active_subscriptions = []


@dataclass
class AccessLog:
    """Log di accesso da sincronizzare"""
    timestamp: str  # ISO format
    card_uid: str
    tornello_id: str
    direction: str  # "in" o "out"
    result: str     # "authorized", "denied", "manual"
    reason: str
    customer_name: Optional[str] = None
    reader_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SyncManager:
    """
    Manager per sincronizzazione offline-first.
    
    Gestisce:
    - Cache locale SQLite delle carte
    - Validazione offline con cache
    - Sincronizzazione periodica con server
    - Queue log per invio al server
    """
    
    def __init__(self, config: SyncConfig, tornello_id: str):
        self.config = config
        self.tornello_id = tornello_id
        self.logger = logging.getLogger(__name__)
        
        # Crea directory cache se non esiste
        self.cache_dir = Path(config.sync.cache_db_path).parent
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = config.sync.cache_db_path
        self.is_online = False
        self.last_sync = None
        self.background_task: Optional[asyncio.Task] = None
        
        # Inizializza database
        self._init_database()
        
        self.logger.info(f"🔄 SyncManager inizializzato per {tornello_id}")
    
    def _init_database(self):
        """Inizializza database SQLite per cache locale"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella carte sincronizzate (mantiene struttura API)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synced_cards (
                card_uid TEXT PRIMARY KEY,
                customer_id INTEGER,  -- Può essere NULL per carte whitelist
                customer_name TEXT,
                in_white_list BOOLEAN DEFAULT 0,
                active_subscriptions TEXT,  -- JSON delle subscriptions
                last_sync TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabella log in attesa di sincronizzazione
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                card_uid TEXT,
                tornello_id TEXT,
                direction TEXT,
                result TEXT,
                reason TEXT,
                customer_id TEXT,  -- ✨ NUOVO: ID cliente per analytics
                customer_name TEXT,
                reader_type TEXT,
                metadata TEXT,  -- JSON
                synced BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella stato sincronizzazione
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY,
                last_full_sync TIMESTAMP,
                last_log_sync TIMESTAMP,
                last_updates_check TIMESTAMP,
                sync_errors INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"📁 Database cache inizializzato: {self.db_path}")
    
    async def validate_card_offline(self, card_uid: str, direction: str = "in") -> Dict[str, Any]:
        """
        Valida carta usando cache locale.
        
        Returns:
            Dict con struttura compatibile con risposta MQTT:
            {
                'authorized': bool,
                'customer_name': str,
                'reason': str,
                'subscription_info': dict,
                'offline_mode': True
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT customer_id, customer_name, in_white_list, active_subscriptions 
                FROM synced_cards 
                WHERE card_uid = ? AND is_active = 1
            ''', (card_uid,))
            
            result = cursor.fetchone()
            
            if not result:
                return {
                    'authorized': False,
                    'customer_id': None,         # ✨ NUOVO: ID cliente
                    'customer_name': None,
                    'reason': 'Carta non trovata nella cache locale',
                    'subscription_info': None,
                    'offline_mode': True
                }
            
            customer_id, customer_name, in_white_list, subscriptions_json = result
            
            # 🎯 WHITELIST: Se la carta è in whitelist, accesso sempre autorizzato
            if in_white_list:
                return {
                    'authorized': True,
                    'customer_id': customer_id,  # ✨ NUOVO: ID cliente (può essere None per whitelist)
                    'customer_name': customer_name,
                    'reason': 'Carta in whitelist - accesso sempre autorizzato',
                    'subscription_info': {'type': 'whitelist', 'in_white_list': True},
                    'offline_mode': True
                }
            
            # Altrimenti verifica abbonamenti normalmente
            active_subscriptions = json.loads(subscriptions_json)
            
            # Verifica abbonamenti attivi
            valid_subscription = None
            now = datetime.now()
            
            for subscription in active_subscriptions:
                if not subscription.get('is_active', True):
                    continue
                
                sub_type = subscription.get('type', '')
                
                if sub_type == 'time_based':
                    expiry_str = subscription.get('expiry_date')
                    if expiry_str:
                        try:
                            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
                            if expiry_date >= now:
                                valid_subscription = subscription
                                break
                        except ValueError:
                            continue
                
                elif sub_type == 'single_entrance':
                    remaining = subscription.get('remaining_entrances', 0)
                    if remaining and remaining > 0:
                        valid_subscription = subscription
                        # Aggiorna contatore localmente
                        self._update_subscription_usage(card_uid, subscription)
                        break
            
            if valid_subscription:
                return {
                    'authorized': True,
                    'customer_id': customer_id,  # ✨ NUOVO: ID cliente
                    'customer_name': customer_name,
                    'reason': 'Accesso autorizzato (modalità offline)',
                    'subscription_info': valid_subscription,
                    'offline_mode': True
                }
            else:
                return {
                    'authorized': False,
                    'customer_id': customer_id,  # ✨ NUOVO: ID cliente
                    'customer_name': customer_name,
                    'reason': 'Nessun abbonamento valido',
                    'subscription_info': None,
                    'offline_mode': True
                }
                
        except Exception as e:
            self.logger.error(f"Errore validazione offline: {e}")
            return {
                'authorized': False,
                'customer_id': None,         # ✨ NUOVO: ID cliente
                'customer_name': None,
                'reason': f'Errore validazione: {e}',
                'subscription_info': None,
                'offline_mode': True
            }
        finally:
            conn.close()
    
    def _update_subscription_usage(self, card_uid: str, subscription: Dict[str, Any]):
        """Aggiorna uso abbonamento nel cache locale"""
        if subscription.get('type') != 'single_entrance':
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Recupera abbonamenti attuali
            cursor.execute('SELECT active_subscriptions FROM synced_cards WHERE card_uid = ?', (card_uid,))
            result = cursor.fetchone()
            
            if result:
                active_subscriptions = json.loads(result[0])
                
                # Trova e aggiorna l'abbonamento specifico
                for sub in active_subscriptions:
                    if (sub.get('type') == 'single_entrance' and 
                        sub.get('remaining_entrances') == subscription.get('remaining_entrances')):
                        sub['remaining_entrances'] = max(0, sub['remaining_entrances'] - 1)
                        break
                
                # Salva aggiornamenti
                cursor.execute(
                    'UPDATE synced_cards SET active_subscriptions = ? WHERE card_uid = ?',
                    (json.dumps(active_subscriptions), card_uid)
                )
                conn.commit()
                
                self.logger.info(f"Aggiornato uso abbonamento per carta {card_uid}")
                
        except Exception as e:
            self.logger.error(f"Errore aggiornamento abbonamento: {e}")
        finally:
            conn.close()
    
    async def log_access(self, card_uid: str, direction: str, result: str, reason: str, 
                        customer_id: Optional[int] = None,  # ✨ NUOVO: ID cliente
                        customer_name: Optional[str] = None, reader_type: Optional[str] = None,
                        metadata: Dict[str, Any] = None):
        """
        Registra log di accesso per sincronizzazione.
        
        Args:
            card_uid: UID della carta
            direction: "in" o "out" 
            result: "authorized", "denied", "manual"
            reason: Motivo del risultato
            customer_id: ID cliente univoco (✨ NUOVO per analytics)
            customer_name: Nome cliente (se disponibile)
            reader_type: Tipo lettore (mfrc522, pn532)
            metadata: Dati aggiuntivi
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            timestamp = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO pending_logs 
                (timestamp, card_uid, tornello_id, direction, result, reason, 
                 customer_id, customer_name, reader_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                card_uid,
                self.tornello_id,
                direction,
                result,
                reason,
                customer_id,  # ✨ NUOVO campo
                customer_name,
                reader_type,
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            
            # Log migliorato con customer info
            customer_info = f" (customer_id: {customer_id})" if customer_id else ""
            self.logger.info(f"📝 Log registrato: {card_uid} - {result}{customer_info}")
            
            # Prova sync immediato se online
            if self.is_online:
                await self._sync_logs()
                
        except Exception as e:
            self.logger.error(f"Errore registrazione log: {e}")
        finally:
            conn.close()
    
    async def daily_sync(self) -> bool:
        """Sincronizzazione giornaliera completa delle carte"""
        try:
            self.logger.info("🔄 Avvio sincronizzazione giornaliera...")
            
            url = f"{self.config.server_url}{self.config.sync_endpoint}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.connection_timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        cards_data = await response.json()
                        self._update_local_cache(cards_data)
                        self.last_sync = datetime.now()
                        self.is_online = True
                        
                        self.logger.info(f"✅ Sincronizzazione completata: {len(cards_data)} carte aggiornate")
                        return True
                    else:
                        self.logger.error(f"❌ Errore sincronizzazione: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Errore connessione durante sync: {e}")
            self.is_online = False
            return False
    
    def _update_local_cache(self, cards_data: List[Dict[str, Any]]):
        """Aggiorna cache locale con dati dal server"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Disattiva tutte le carte esistenti
            cursor.execute("UPDATE synced_cards SET is_active = 0")
            
            # Inserisci/aggiorna carte sincronizzate
            for card_data in cards_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO synced_cards 
                    (card_uid, customer_id, customer_name, in_white_list, active_subscriptions, last_sync, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (
                    card_data['card_uid'],
                    card_data.get('customer_id'),  # Può essere None/null
                    card_data['customer_name'],
                    card_data.get('in_white_list', False),
                    json.dumps(card_data['active_subscriptions']),
                    datetime.now()
                ))
            
            # Aggiorna stato sincronizzazione
            cursor.execute('''
                INSERT OR REPLACE INTO sync_status (id, last_full_sync)
                VALUES (1, ?)
            ''', (datetime.now(),))
            
            conn.commit()
            self.logger.info(f"📁 Cache aggiornata con {len(cards_data)} carte")
            
        except Exception as e:
            self.logger.error(f"Errore aggiornamento cache: {e}")
        finally:
            conn.close()
    
    async def _sync_logs(self) -> bool:
        """Sincronizza log pendenti con server"""
        if not self.is_online:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Recupera log da sincronizzare
            cursor.execute('''
                SELECT id, timestamp, card_uid, tornello_id, direction, result, reason,
                       customer_id, customer_name, reader_type, metadata
                FROM pending_logs 
                WHERE synced = 0
                ORDER BY timestamp
                LIMIT 100
            ''')
            
            pending = cursor.fetchall()
            
            if not pending:
                return True
            
            # Prepara dati per invio
            logs_to_send = []
            for log in pending:
                logs_to_send.append({
                    'timestamp': log[1],
                    'card_uid': log[2],
                    'tornello_id': log[3],
                    'direction': log[4],
                    'result': log[5],
                    'reason': log[6],
                    'customer_id': log[7],        # ✨ NUOVO: ID cliente per analytics
                    'customer_name': log[8],
                    'reader_type': log[9],
                    'metadata': json.loads(log[10] or '{}')
                })
            
            # Invia al server
            url = f"{self.config.server_url}{self.config.logs_endpoint}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.post(url, json={'logs': logs_to_send}) as response:
                    if response.status == 200:
                        # Marca come sincronizzati
                        log_ids = [log[0] for log in pending]
                        placeholders = ','.join(['?' for _ in log_ids])
                        cursor.execute(
                            f"UPDATE pending_logs SET synced = 1 WHERE id IN ({placeholders})",
                            log_ids
                        )
                        conn.commit()
                        
                        self.logger.info(f"📤 Sincronizzati {len(pending)} log")
                        return True
                    else:
                        self.logger.error(f"Errore sync log: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Errore sync log: {e}")
            self.is_online = False
            return False
        finally:
            conn.close()
    
    async def check_for_updates(self) -> bool:
        """Controlla aggiornamenti carte dal server"""
        try:
            params = {}
            if self.last_sync:
                params['since'] = self.last_sync.isoformat()
            
            url = f"{self.config.server_url}{self.config.updates_endpoint}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        updates = await response.json()
                        if updates:
                            self.logger.info(f"📥 Ricevuti {len(updates)} aggiornamenti")
                            self._apply_updates(updates)
                        self.is_online = True
                        return True
                    else:
                        return False
                        
        except Exception as e:
            self.logger.error(f"Errore check updates: {e}")
            self.is_online = False
            return False
    
    def _apply_updates(self, updates: List[Dict[str, Any]]):
        """Applica aggiornamenti incrementali delle carte"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for update in updates:
                action = update.get('action', 'update')
                
                if action == 'update':
                    card_data = update['card_data']
                    cursor.execute('''
                        INSERT OR REPLACE INTO synced_cards 
                        (card_uid, customer_id, customer_name, in_white_list, active_subscriptions, last_sync, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    ''', (
                        card_data['card_uid'],
                        card_data.get('customer_id'),  # Può essere None/null
                        card_data['customer_name'],
                        card_data.get('in_white_list', False),
                        json.dumps(card_data['active_subscriptions']),
                        datetime.now()
                    ))
                elif action == 'delete':
                    cursor.execute(
                        'UPDATE synced_cards SET is_active = 0 WHERE card_uid = ?',
                        (update['card_uid'],)
                    )
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Errore applicazione updates: {e}")
        finally:
            conn.close()
    
    async def check_connectivity(self) -> bool:
        """Verifica connettività con server"""
        try:
            url = f"{self.config.server_url}{self.config.health_endpoint}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as response:
                    self.is_online = response.status == 200
                    return self.is_online
                    
        except Exception:
            self.is_online = False
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Restituisce stato sincronizzazione"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Conta carte attive
            cursor.execute('SELECT COUNT(*) FROM synced_cards WHERE is_active = 1')
            active_cards = cursor.fetchone()[0]
            
            # Conta log in attesa
            cursor.execute('SELECT COUNT(*) FROM pending_logs WHERE synced = 0')
            pending_logs = cursor.fetchone()[0]
            
            # Ultima sincronizzazione
            cursor.execute('SELECT last_full_sync FROM sync_status WHERE id = 1')
            result = cursor.fetchone()
            last_sync = result[0] if result else None
            
            return {
                'active_cards': active_cards,
                'pending_logs': pending_logs,
                'last_sync': last_sync,
                'is_online': self.is_online,
                'tornello_id': self.tornello_id
            }
            
        except Exception as e:
            self.logger.error(f"Errore get status: {e}")
            return {
                'active_cards': 0,
                'pending_logs': 0,
                'last_sync': None,
                'is_online': False,
                'tornello_id': self.tornello_id
            }
        finally:
            conn.close()
    
    async def start_background_sync(self):
        """Avvia sincronizzazioni in background"""
        if self.background_task:
            return
        
        self.background_task = asyncio.create_task(self._background_worker())
        self.logger.info("🔄 Background sync avviato")
    
    async def stop_background_sync(self):
        """Ferma sincronizzazioni in background"""
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
            self.background_task = None
            self.logger.info("⏹️ Background sync fermato")
    
    async def _background_worker(self):
        """Worker per sincronizzazioni periodiche"""
        last_updates_check = datetime.min
        last_logs_sync = datetime.min
        
        while True:
            try:
                now = datetime.now()
                
                # Check connettività ogni minuto
                await self.check_connectivity()
                
                # Sync log ogni 5 minuti se online
                if (now - last_logs_sync).total_seconds() >= self.config.logs_sync_interval * 60:
                    if self.is_online:
                        await self._sync_logs()
                    last_logs_sync = now
                
                # Check updates ogni 15 minuti se online
                if (now - last_updates_check).total_seconds() >= self.config.updates_check_interval * 60:
                    if self.is_online:
                        await self.check_for_updates()
                    last_updates_check = now
                
                # Sync completa giornaliera
                sync_time = datetime.strptime(self.config.daily_sync_time, "%H:%M").time()
                if (now.time().hour == sync_time.hour and 
                    now.time().minute == sync_time.minute and
                    self.is_online):
                    await self.daily_sync()
                
                await asyncio.sleep(60)  # Check ogni minuto
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Errore background worker: {e}")
                await asyncio.sleep(60)


class MockResponse:
    status = 200
    async def json(self): return []
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass