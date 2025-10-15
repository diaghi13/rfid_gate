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
import ssl
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
            def __init__(self, timeout=None, connector=None): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def get(self, url, params=None): return MockResponse()
            async def post(self, url, json=None): return MockResponse()
        
        class ClientTimeout:
            def __init__(self, total=None): pass
            
        class TCPConnector:
            def __init__(self, ssl=None): pass

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
    
    def __init__(self, config, tornello_id: str):
        # Supporta sia SyncConfig che RFIDGateConfig per compatibilità test
        if hasattr(config, 'sync'):  # È RFIDGateConfig
            self.config = config.sync
            self.system_config = config.system
        else:  # È SyncConfig
            self.config = config
            self.system_config = None  # Fallback per test legacy
            
        self.tornello_id = tornello_id
        self.logger = logging.getLogger(__name__)
        
        # Crea directory cache se non esiste
        self.cache_dir = Path(self.config.cache_db_path).parent
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.config.cache_db_path
        self.is_online = False
        self.last_sync = None
        self.background_task: Optional[asyncio.Task] = None
        
        # Inizializza database
        self._init_database()
        
        # Scheduler per sync automatiche
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        
        self.logger.info(f"🔄 SyncManager inizializzato per {tornello_id}")
    
    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Crea SSL context per gestire certificati self-signed o non verificabili"""
        if not HAS_AIOHTTP:
            return None
            
        try:
            # Crea context SSL che non verifica i certificati
            # NOTA: Questo è per development/testing - in produzione usare certificati validi
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            self.logger.debug("🔒 SSL context configurato (verificazione disabilitata)")
            return ssl_context
        except Exception as e:
            self.logger.warning(f"⚠️ Errore creazione SSL context: {e}")
            return None
    
    def _create_aiohttp_session(self, timeout_seconds: int) -> 'aiohttp.ClientSession':
        """Crea una sessione aiohttp con configurazione SSL appropriata"""
        if not HAS_AIOHTTP:
            return aiohttp.ClientSession()
            
        try:
            # Crea SSL context
            ssl_context = self._create_ssl_context()
            
            # Crea connector con SSL context
            connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
            
            # Crea timeout
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            
            # Crea sessione
            if connector:
                return aiohttp.ClientSession(timeout=timeout, connector=connector)
            else:
                return aiohttp.ClientSession(timeout=timeout)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Errore creazione sessione aiohttp: {e}")
            # Fallback a sessione standard
            return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_seconds))
    
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
        
        # Tabella stato direzioni utenti (per tornelli bidirezionali)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_direction_state (
                card_uid TEXT PRIMARY KEY,
                last_direction TEXT NOT NULL,
                last_access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tornello_id TEXT,
                customer_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"📁 Database cache inizializzato: {self.db_path}")
    
    async def check_bidirectional_access(self, card_uid: str, direction: str, tornello_id: str) -> Dict[str, Any]:
        """
        Controlla se l'accesso è valido per tornelli bidirezionali con timeout.
        
        Args:
            card_uid: UID della carta
            direction: Direzione richiesta ('in' o 'out')
            tornello_id: ID del tornello
            
        Returns:
            Dict con:
            - valid: bool - Se l'accesso è valido
            - reason: str - Motivo del rifiuto se non valido
            - last_direction: str - Ultima direzione registrata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Cerca ultima direzione per questa carta su questo tornello
            cursor.execute('''
                SELECT last_direction, last_access_time, tornello_id 
                FROM user_direction_state 
                WHERE card_uid = ? AND tornello_id = ?
            ''', (card_uid, tornello_id))
            
            result = cursor.fetchone()
            
            if not result:
                # Prima volta che vediamo questa carta - permetti qualsiasi direzione
                return {
                    'valid': True,
                    'reason': 'Prima lettura carta',
                    'last_direction': None
                }
            
            last_direction, last_access_time, last_tornello = result
            
            # 🕐 CONTROLLO TIMEOUT - Se passato troppo tempo, resetta stato
            from datetime import datetime, timedelta
            
            # Parsing del timestamp (formato SQLite)
            try:
                if '.' in last_access_time:
                    # Formato con microsecondi: "2025-01-15 10:30:00.123456"
                    last_time = datetime.strptime(last_access_time, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    # Formato senza microsecondi: "2025-01-15 10:30:00"
                    last_time = datetime.strptime(last_access_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Se c'è un errore nel parsing, considera scaduto
                self.logger.warning(f"⚠️  Formato timestamp non valido per {card_uid}: {last_access_time}")
                return {
                    'valid': True,
                    'reason': 'Timestamp non valido - stato resettato',
                    'last_direction': None
                }
            
            # Calcola se il timeout è scaduto
            if self.system_config:
                timeout_hours = self.system_config.bidirectional_timeout_hours
            else:
                timeout_hours = 24.0  # Default fallback
                
            timeout_delta = timedelta(hours=timeout_hours)
            current_time = datetime.now()
            
            if current_time - last_time > timeout_delta:
                # Timeout scaduto - permetti qualsiasi direzione e logga
                self.logger.info(f"🕐 Timeout scaduto per {card_uid} ({timeout_hours}h). Stato resettato.")
                return {
                    'valid': True,
                    'reason': f'Timeout scaduto ({timeout_hours}h) - stato resettato',
                    'last_direction': last_direction  # Per info, ma stato considerato resettato
                }
            
            # Se è lo stesso tornello e stessa direzione -> NON VALIDO
            if last_tornello == tornello_id and last_direction == direction:
                time_since_last = current_time - last_time
                return {
                    'valid': False,
                    'reason': f'Accesso consecutivo stesso tipo: {direction}. Ultima direzione: {last_direction} ({time_since_last})',
                    'last_direction': last_direction
                }
            
            # Accesso valido (direzione opposta o tornello diverso)
            time_since_last = current_time - last_time
            return {
                'valid': True,
                'reason': f'Accesso valido. Precedente: {last_direction} -> Richiesto: {direction} ({time_since_last})',
                'last_direction': last_direction
            }
            
        finally:
            conn.close()
    
    async def update_user_direction(self, card_uid: str, direction: str, tornello_id: str, customer_id: str = None):
        """
        Aggiorna lo stato della direzione per un utente.
        
        Args:
            card_uid: UID della carta
            direction: Direzione ('in' o 'out')
            tornello_id: ID del tornello
            customer_id: ID del cliente (opzionale)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO user_direction_state 
                (card_uid, last_direction, last_access_time, tornello_id, customer_id)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
            ''', (card_uid, direction, tornello_id, customer_id))
            
            conn.commit()
            self.logger.debug(f"🔄 Aggiornato stato direzione: {card_uid} -> {direction}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore update_user_direction: {e}")
            raise
        finally:
            conn.close()
    
    async def cleanup_expired_direction_states(self) -> int:
        """
        Rimuove stati direzioni scaduti dal database per mantenerlo pulito.
        
        Returns:
            int: Numero di record rimossi
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calcola timestamp di cutoff
            from datetime import datetime, timedelta
            if self.system_config:
                timeout_hours = self.system_config.bidirectional_timeout_hours
            else:
                timeout_hours = 24.0  # Default fallback
                
            cutoff_time = datetime.now() - timedelta(hours=timeout_hours)
            cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Conta record da rimuovere per logging
            cursor.execute('''
                SELECT COUNT(*) FROM user_direction_state 
                WHERE last_access_time < ?
            ''', (cutoff_str,))
            
            count_to_remove = cursor.fetchone()[0]
            
            if count_to_remove > 0:
                # Rimuovi record scaduti
                cursor.execute('''
                    DELETE FROM user_direction_state 
                    WHERE last_access_time < ?
                ''', (cutoff_str,))
                
                conn.commit()
                self.logger.info(f"🧹 Cleanup: rimossi {count_to_remove} stati direzioni scaduti (>{timeout_hours}h)")
            
            return count_to_remove
            
        except Exception as e:
            self.logger.error(f"❌ Errore cleanup stati direzioni: {e}")
            return 0
        finally:
            conn.close()

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
            
            async with self._create_aiohttp_session(self.config.connection_timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        try:
                            response_data = await response.json()
                            
                            # Supporta diversi formati di risposta dal server:
                            if isinstance(response_data, dict):
                                if 'data' in response_data:
                                    # Formato principale: {"success": true, "data": [...]}
                                    if not response_data.get('success', False):
                                        self.logger.error(f"❌ Errore sincronizzazione: server ha restituito success=false")
                                        return False
                                    cards_data = response_data['data']
                                elif 'card_data' in response_data:
                                    # Formato updates: {"action": "update", "card_data": [...]}
                                    action = response_data.get('action', 'unknown')
                                    self.logger.debug(f"🔄 Azione ricevuta dal server: {action}")
                                    cards_data = response_data['card_data']
                                else:
                                    self.logger.error(f"❌ Errore sincronizzazione: formato risposta non riconosciuto: {type(response_data)}")
                                    self.logger.debug(f"Contenuto ricevuto: {str(response_data)[:200]}...")
                                    return False
                            elif isinstance(response_data, list):
                                # Backward compatibility: array diretto
                                cards_data = response_data
                            else:
                                self.logger.error(f"❌ Errore sincronizzazione: formato risposta non riconosciuto: {type(response_data)}")
                                self.logger.debug(f"Contenuto ricevuto: {str(response_data)[:200]}...")
                                return False
                            
                            # Validate that cards_data is a list
                            if not isinstance(cards_data, list):
                                self.logger.error(f"❌ Errore sincronizzazione: card_data non è una lista, ricevuto: {type(cards_data)}")
                                return False
                            
                            # Validate that each item is a dict with required fields
                            for i, card in enumerate(cards_data):
                                if not isinstance(card, dict):
                                    self.logger.error(f"❌ Errore sincronizzazione: carta {i} non è un dict, ricevuto: {type(card)}")
                                    return False
                                
                                # Check required fields
                                required_fields = ['card_uid', 'customer_name', 'in_white_list']
                                for field in required_fields:
                                    if field not in card:
                                        self.logger.error(f"❌ Errore sincronizzazione: carta {i} manca campo '{field}'")
                                        return False
                            
                            self._update_local_cache(cards_data)
                            self.last_sync = datetime.now()
                            self.is_online = True
                            
                            self.logger.info(f"✅ Sincronizzazione completata: {len(cards_data)} carte aggiornate")
                            return True
                        except json.JSONDecodeError as e:
                            self.logger.error(f"❌ Errore parsing JSON sincronizzazione: {e}")
                            return False
                        except Exception as e:
                            self.logger.error(f"❌ Errore processing sincronizzazione: {e}")
                            return False
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
            # Validate input
            if not isinstance(cards_data, list):
                raise ValueError(f"cards_data deve essere una lista, ricevuto: {type(cards_data)}")
            
            # Disattiva tutte le carte esistenti
            cursor.execute("UPDATE synced_cards SET is_active = 0")
            
            # Inserisci/aggiorna carte sincronizzate
            for i, card_data in enumerate(cards_data):
                if not isinstance(card_data, dict):
                    self.logger.error(f"Carta {i} non è un dict: {type(card_data)}")
                    continue
                
                cursor.execute('''
                    INSERT OR REPLACE INTO synced_cards 
                    (card_uid, customer_id, customer_name, in_white_list, active_subscriptions, last_sync, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (
                    card_data.get('card_uid'),
                    card_data.get('customer_id'),  # Può essere None/null
                    card_data.get('customer_name'),
                    card_data.get('in_white_list', False),
                    json.dumps(card_data.get('active_subscriptions', [])),
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
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
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
            
            async with self._create_aiohttp_session(15) as session:
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
                params['last_update'] = self.last_sync.isoformat()
            
            url = f"{self.config.server_url}{self.config.updates_endpoint}"
            
            async with self._create_aiohttp_session(10) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        try:
                            response_data = await response.json()
                            
                            # Supporta il nuovo formato: {"action": "update", "card_data": [...]}
                            if isinstance(response_data, dict) and 'card_data' in response_data:
                                action = response_data.get('action', 'update')
                                self.logger.debug(f"🔄 Azione ricevuta: {action}")
                                updates = response_data['card_data']
                            elif isinstance(response_data, list):
                                # Backward compatibility: array diretto
                                updates = response_data
                            else:
                                self.logger.error(f"❌ Errore updates: formato risposta non riconosciuto: {type(response_data)}")
                                return False
                            
                            # Validate that updates is a list
                            if not isinstance(updates, list):
                                self.logger.error(f"❌ Errore updates: card_data non è una lista, ricevuto: {type(updates)}")
                                return False
                            
                            if updates:
                                # Validate that each update is a dict
                                for i, update in enumerate(updates):
                                    if not isinstance(update, dict):
                                        self.logger.error(f"❌ Errore update {i}: non è un dict, ricevuto: {type(update)}")
                                        return False
                                
                                self.logger.info(f"📥 Ricevuti {len(updates)} aggiornamenti")
                                
                                # Trasforma il formato per _apply_updates se necessario
                                if isinstance(response_data, dict) and 'card_data' in response_data:
                                    # Formato: {"action": "update", "card_data": [...]}
                                    # Trasforma ogni carta in un update con action
                                    action = response_data.get('action', 'update')
                                    formatted_updates = []
                                    for card in updates:
                                        formatted_updates.append({
                                            'action': action,
                                            'card_data': card
                                        })
                                    self._apply_updates(formatted_updates)
                                else:
                                    # Formato legacy: array di updates già formattati
                                    self._apply_updates(updates)
                                
                                self.last_sync = datetime.now()
                            else:
                                self.logger.info("📥 Nessun aggiornamento disponibile")
                            
                            self.is_online = True
                            return True
                        except json.JSONDecodeError as e:
                            self.logger.error(f"❌ Errore parsing JSON updates: {e}")
                            return False
                        except Exception as e:
                            self.logger.error(f"❌ Errore processing updates: {e}")
                            return False
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
            for i, update in enumerate(updates):
                # Validate update is a dict
                if not isinstance(update, dict):
                    self.logger.error(f"Update {i} non è un dict: {type(update)}")
                    continue
                
                action = update.get('action', 'update')
                self.logger.debug(f"🔄 Applicando azione: {action} per update {i}")
                
                if action == 'update':
                    card_data = update.get('card_data')
                    if not isinstance(card_data, dict):
                        self.logger.error(f"card_data nell'update {i} non è un dict: {type(card_data)}")
                        continue
                    
                    card_uid = card_data.get('card_uid')
                    if not card_uid:
                        self.logger.error(f"Update {i} manca card_uid")
                        continue
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO synced_cards 
                        (card_uid, customer_id, customer_name, in_white_list, active_subscriptions, last_sync, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    ''', (
                        card_uid,
                        card_data.get('customer_id'),  # Può essere None/null
                        card_data.get('customer_name'),
                        card_data.get('in_white_list', False),
                        json.dumps(card_data.get('active_subscriptions', [])),
                        datetime.now()
                    ))
                    self.logger.debug(f"✅ Aggiornata carta: {card_uid}")
                    
                elif action == 'delete':
                    # Può essere card_uid diretto nell'update o dentro card_data
                    card_uid = update.get('card_uid')
                    if not card_uid and 'card_data' in update:
                        card_uid = update['card_data'].get('card_uid')
                    
                    if card_uid:
                        cursor.execute(
                            'UPDATE synced_cards SET is_active = 0 WHERE card_uid = ?',
                            (card_uid,)
                        )
                        self.logger.debug(f"🗑️ Disattivata carta: {card_uid}")
                    else:
                        self.logger.error(f"Update delete {i} manca card_uid")
                else:
                    self.logger.warning(f"⚠️ Azione sconosciuta nell'update {i}: {action}")
            
            conn.commit()
            self.logger.info(f"✅ Applicati {len(updates)} aggiornamenti al database locale")
            
        except Exception as e:
            self.logger.error(f"Errore applicazione updates: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            conn.close()
    
    async def check_connectivity(self) -> bool:
        """Verifica connettività con server"""
        try:
            url = f"{self.config.server_url}{self.config.health_endpoint}"
            
            async with self._create_aiohttp_session(5) as session:
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
        last_cleanup = datetime.min
        
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
                
                # Cleanup stati direzioni scaduti ogni 4 ore
                if (now - last_cleanup).total_seconds() >= 4 * 60 * 60:  # 4 ore
                    await self.cleanup_expired_direction_states()
                    last_cleanup = now
                
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