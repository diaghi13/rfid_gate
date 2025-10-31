#!/usr/bin/env python3
"""
🌐 MQTT Client - Refactored Version
==================================

Client MQTT moderno con:
- Async/await support
- Auto-reconnection  
- Message queuing
- Type-safe configuration
- Comprehensive error handling

🔄 COMPATIBILITÀ LEGACY:
Questa versione mantiene compatibilità completa con il payload legacy per garantire
che il backend esistente continui a funzionare senza modifiche.

✨ CAMPI FUTURI:
I campi per la versione moderna dell'API sono commentati nelle dataclass.
Per abilitarli in futuro:
1. Decommentare i campi futuri nelle dataclass
2. Aggiornare i metodi send_* per usare i nuovi campi
3. Implementare backward compatibility nel backend
4. Testare con entrambi i formati
5. Migrare gradualmente

📝 ROADMAP:
- v1.0: Legacy compatibility (current)
- v2.0: Hybrid mode (legacy + modern fields)
- v3.0: Modern API only
"""

import asyncio
import json
import ssl
import time
from typing import Optional, Dict, Any, Callable, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import condizionale MQTT
try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    # Mock per development
    class mqtt:
        class Client:
            def __init__(self): pass
            def username_pw_set(self, user, pwd): pass
            def tls_set_context(self, ctx): pass
            def on_connect(self, func): pass
            def on_message(self, func): pass
            def connect_async(self, host, port): pass
            def loop_start(self): pass
            def publish(self, topic, payload): return (0, 0)
            def subscribe(self, topic): return (0, 0)
            def disconnect(self): pass


class ConnectionState(str, Enum):
    """Stati connessione MQTT"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MQTTMessage:
    """Messaggio MQTT standardizzato"""
    topic: str
    payload: Dict[str, Any]
    qos: int = 0
    retain: bool = False
    timestamp: float = None
    message_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())[:8]


@dataclass
class CardReadMessage:
    """Messaggio lettura carta - COMPATIBILE CON LEGACY"""
    # ========================================
    # 🔄 CAMPI LEGACY (MANTENUTI PER COMPATIBILITÀ)
    # ========================================
    card_uid: str                           # UID carta formattato (legacy: uid_formatted)
    identificativo_tornello: str            # ID tornello (legacy: identificativo_tornello)
    direzione: str                          # "in" o "out" (legacy: direzione)
    timestamp: str                          # ISO timestamp (legacy: timestamp)
    raw_id: str                            # Raw ID carta (legacy: raw_id)
    card_data: Optional[Dict[str, Any]] = None  # Dati carta completi (legacy: card_data)
    hex_id: Optional[str] = None           # UID in hex (legacy: hex_id)
    auth_required: bool = True             # Flag auth richiesta (legacy: auth_required)
    reader_id: str = "unknown"             # ID reader (legacy: reader_id)
    
    # ========================================
    # ✨ CAMPI FUTURI (COMMENTATI PER USO FUTURO)
    # ========================================
    # Quando sarà il momento di modernizzare l'API, decommentare questi campi:
    # 
    # tornello_id: str = None              # ✨ FUTURO: Nome moderno per identificativo_tornello
    # direction: str = None                # ✨ FUTURO: Nome moderno per direzione  
    # reader_type: str = None              # ✨ FUTURO: Tipo specifico reader ("mfrc522", "pn532")
    # raw_uid: Optional[str] = None        # ✨ FUTURO: Nome moderno per raw_id
    # uid_hex: Optional[str] = None        # ✨ FUTURO: Nome moderno per hex_id
    # metadata: Dict[str, Any] = None      # ✨ FUTURO: Metadata aggiuntivi strutturati
    # message_id: str = None               # ✨ FUTURO: ID messaggio univoco per tracking
    # retry_count: int = 0                 # ✨ FUTURO: Contatore retry per resilienza
    # priority: int = 0                    # ✨ FUTURO: Priorità messaggio (0=normale, 1=alta)
    # source_version: str = "2.0"          # ✨ FUTURO: Versione protocollo per compatibilità
    
    def __post_init__(self):
        # Converte timestamp float a ISO string se necessario
        if isinstance(self.timestamp, (int, float)):
            from datetime import datetime
            self.timestamp = datetime.fromtimestamp(self.timestamp).isoformat()
        
        # Assicura che raw_id sia stringa
        if self.raw_id is not None:
            self.raw_id = str(self.raw_id)
    
    @classmethod
    def from_card_event(cls, card_event, tornello_id: str, auth_required: bool = True):
        """Crea CardReadMessage da CardEvent mantenendo compatibilità legacy"""
        from datetime import datetime
        
        return cls(
            card_uid=card_event.uid_formatted,
            identificativo_tornello=tornello_id,
            direzione=card_event.direction,
            timestamp=datetime.now().isoformat(),
            raw_id=str(getattr(card_event, 'raw_uid', card_event.uid_formatted)),
            card_data=getattr(card_event, 'data', None),
            hex_id=getattr(card_event, 'uid_hex', card_event.uid_formatted),
            auth_required=auth_required,
            reader_id=getattr(card_event, 'reader_type', 'unknown')
        )
    
    # ========================================
    # ✨ METODI FUTURI (COMMENTATI)
    # ========================================
    # def to_modern_format(self) -> Dict[str, Any]:
    #     """Converte al formato moderno per API v2"""
    #     return {
    #         "card_uid": self.card_uid,
    #         "tornello_id": self.identificativo_tornello,  # Nome moderno
    #         "direction": self.direzione,                  # Nome moderno
    #         "reader_type": self.reader_id,
    #         "timestamp": self.timestamp,
    #         "raw_uid": self.raw_id,
    #         "metadata": self.card_data or {}
    #     }
    # 
    # @property
    # def is_legacy_compatible(self) -> bool:
    #     """Verifica se il messaggio è compatibile con legacy"""
    #     required_fields = ['card_uid', 'identificativo_tornello', 'direzione']
    #     return all(hasattr(self, field) for field in required_fields)


@dataclass
class AuthRequest:
    """Richiesta autenticazione - COMPATIBILE CON LEGACY"""
    # ========================================
    # 🔄 CAMPI LEGACY (MANTENUTI PER COMPATIBILITÀ)
    # ========================================
    card_uid: str                          # UID carta (compatibile con legacy)
    identificativo_tornello: str           # ID tornello (legacy: identificativo_tornello)
    direzione: str                         # Direzione (legacy: direzione)
    timestamp: str                         # ISO timestamp (legacy: timestamp)
    auth_required: bool = True             # Flag auth (legacy: auth_required)
    fallback_mode: bool = False            # 🔥 NUOVO: Flag per richieste di fallback real-time
    
    # ========================================
    # ✨ CAMPI FUTURI (COMMENTATI PER USO FUTURO)
    # ========================================
    # Quando sarà il momento di modernizzare l'API, decommentare questi campi:
    # 
    # tornello_id: str = None              # ✨ FUTURO: Nome moderno per identificativo_tornello
    # direction: str = None                # ✨ FUTURO: Nome moderno per direzione
    # request_id: str = None               # ✨ FUTURO: ID richiesta univoco per tracking
    # timeout: int = 30                    # ✨ FUTURO: Timeout specifico per questa richiesta
    # priority: int = 0                    # ✨ FUTURO: Priorità richiesta (0=normale, 1=alta)
    # retry_count: int = 0                 # ✨ FUTURO: Contatore retry
    # correlation_id: str = None           # ✨ FUTURO: ID correlazione per tracing distribuito
    # client_version: str = "2.0"          # ✨ FUTURO: Versione client per compatibilità
    # auth_method: str = "default"         # ✨ FUTURO: Metodo auth ("default", "biometric", "pin")
    # metadata: Dict[str, Any] = None      # ✨ FUTURO: Metadata aggiuntivi per context
    
    def __post_init__(self):
        # Converte timestamp float a ISO string se necessario
        if isinstance(self.timestamp, (int, float)):
            from datetime import datetime
            self.timestamp = datetime.fromtimestamp(self.timestamp).isoformat()
    
    @classmethod
    def from_card_event(cls, card_event, tornello_id: str, auth_required: bool = True):
        """Crea AuthRequest da CardEvent mantenendo compatibilità legacy"""
        from datetime import datetime
        
        return cls(
            card_uid=card_event.uid_formatted,
            identificativo_tornello=tornello_id,
            direzione=card_event.direction,
            timestamp=datetime.now().isoformat(),
            auth_required=auth_required
        )
    
    # ========================================
    # ✨ METODI FUTURI (COMMENTATI)
    # ========================================
    # def to_modern_format(self) -> Dict[str, Any]:
    #     """Converte al formato moderno per API v2"""
    #     return {
    #         "card_uid": self.card_uid,
    #         "tornello_id": self.identificativo_tornello,
    #         "direction": self.direzione,
    #         "timestamp": self.timestamp,
    #         "request_id": str(uuid.uuid4())[:8],
    #         "auth_required": self.auth_required
    #     }
    # 
    # def generate_request_id(self) -> str:
    #     """Genera ID richiesta univoco per tracking"""
    #     return f"{self.card_uid}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    # 
    # @property
    # def is_expired(self, timeout: int = 30) -> bool:
    #     """Verifica se la richiesta è scaduta"""
    #     from datetime import datetime
    #     request_time = datetime.fromisoformat(self.timestamp)
    #     return (datetime.now() - request_time).total_seconds() > timeout


class AsyncMQTTClient:
    """
    Client MQTT asincrono con features avanzate.
    
    Features:
    - Auto-reconnection
    - Message queuing offline
    - Type-safe messaging
    - Event callbacks
    - Connection monitoring
    """
    
    def __init__(self, config_mqtt):
        self.config = config_mqtt
        self.client: Optional[mqtt.Client] = None
        self.state = ConnectionState.DISCONNECTED
        self.connection_attempts = 0
        self.max_retries = 10  # 🔧 Aumentato da 3 a 10
        self.reconnect_delay = 2.0  # 🔧 Ridotto da 5.0 a 2.0
        self.last_connection_time = 0  # 🔧 Timestamp ultima connessione
        self.connection_reset_interval = 300  # 🔧 Reset tentativi ogni 5 minuti
        
        # Message queuing
        self.message_queue: List[MQTTMessage] = []
        self.max_queue_size = 1000
        
        # ✨ Queue retry per messaggi falliti
        self.retry_queue: List[MQTTMessage] = []
        self.max_retry_queue_size = getattr(config_mqtt, 'max_retry_queue_size', 1000)
        self.retry_interval = getattr(config_mqtt, 'retry_interval', 30)
        
        # Auth system
        self.auth_responses: Dict[str, Dict[str, Any]] = {}
        self.pending_auths: Dict[str, AuthRequest] = {}
        self.auth_timeout = 5.0
        
        # Callbacks
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_message: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.on_auth_response: Optional[Callable[[str, Dict[str, Any]], None]] = None
        
        # Tasks and event loop
        self._reconnect_task: Optional[asyncio.Task] = None
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._retry_processor_task: Optional[Union[asyncio.Task, asyncio.Future]] = None  # ✨ Task o Future retry
        self._heartbeat_task: Optional[asyncio.Task] = None  # 🔧 NUOVO: Task heartbeat
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None  # ✨ Riferimento al loop
        
        # Health check and ping
        self.heartbeat_interval = 30.0  # 🔧 NUOVO: ping ogni 30 secondi
        self.last_ping_time = 0
        self.ping_timeout = 10.0  # 🔧 NUOVO: timeout ping
        self.missed_pings = 0
        self.max_missed_pings = 3  # 🔧 NUOVO: max ping mancati prima disconnessione
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_queued': 0,
            'connection_attempts': 0,
            'reconnections': 0,
            'auth_requests': 0,
            'auth_responses': 0
        }
    
    async def initialize(self) -> bool:
        """
        Inizializza client MQTT.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        if not HAS_MQTT:
            print("❌ Libreria paho-mqtt non disponibile")
            return False
        
        try:
            print("🌐 Inizializzazione client MQTT...")
            
            # 🔧 NUOVO: Cattura event loop corrente per thread-safety
            self._event_loop = asyncio.get_running_loop()
            
            # Crea client
            self.client = mqtt.Client()
            
            # Configura autenticazione
            if self.config.username and self.config.password:
                self.client.username_pw_set(self.config.username, self.config.password)
                print(f"🔐 Autenticazione configurata: {self.config.username}")
            
            # Configura TLS
            if self.config.use_tls:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.client.tls_set_context(context)
                print("🔒 TLS configurato")
            
            # Imposta callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            
            # Avvia task per processing coda
            self._queue_processor_task = asyncio.create_task(self._process_queue())
            
            # 🔧 NUOVO: Avvia heartbeat monitor
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            print("✅ Client MQTT inizializzato")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione MQTT: {e}")
            return False
    
    async def connect(self) -> bool:
        """
        Connette al broker MQTT.
        
        Returns:
            bool: True se connessione riuscita
        """
        if not self.client:
            print("❌ Client MQTT non inizializzato")
            return False
        
        try:
            self.state = ConnectionState.CONNECTING
            self.connection_attempts += 1
            self.stats['connection_attempts'] += 1
            
            print(f"🔌 Connessione a {self.config.broker}:{self.config.port}...")
            
            # Salva riferimento al loop per callback
            self._event_loop = asyncio.get_event_loop()
            
            # Connessione asincrona
            loop = self._event_loop
            
            def _connect():
                return self.client.connect_async(self.config.broker, self.config.port, self.config.keep_alive)
            
            result = await loop.run_in_executor(None, _connect)
            
            # Avvia loop MQTT
            self.client.loop_start()
            
            # Attendi connessione con timeout
            for _ in range(50):  # 5 secondi max
                if self.state == ConnectionState.CONNECTED:
                    # 🔧 NUOVO: Verifica e forza subscription dopo connessione
                    await asyncio.sleep(0.5)  # Pausa per stabilizzare connessione
                    await self._ensure_subscriptions_active()
                    return True
                await asyncio.sleep(0.1)
            
            print("⚠️ Timeout connessione MQTT")
            return False
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            print(f"❌ Errore connessione MQTT: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback connessione MQTT"""
        if rc == 0:
            self.state = ConnectionState.CONNECTED
            self.connection_attempts = 0
            self.last_connection_time = time.time()  # 🔧 Registra timestamp connessione
            print("✅ MQTT connesso")
            
            # 🔧 NUOVO: Esegui subscription sempre dopo connessione
            self._setup_subscriptions()
            
            # ✨ Avvia retry processor se abilitato e non già attivo
            if (getattr(self.config, 'enable_retry_queue', True) and 
                (not self._retry_processor_task or self._retry_processor_task.done())):
                
                # Usa run_coroutine_threadsafe per eseguire da thread diverso
                if self._event_loop and self._event_loop.is_running():
                    self._retry_processor_task = asyncio.run_coroutine_threadsafe(
                        self._process_retry_queue(), self._event_loop
                    )
                else:
                    print("⚠️ Event loop non disponibile per retry processor")
            
            # Callback utente
            if self.on_connected:
                try:
                    self.on_connected()
                except Exception as e:
                    print(f"❌ Errore callback connected: {e}")
        else:
            self.state = ConnectionState.ERROR
            print(f"❌ Connessione MQTT fallita: {rc}")
    
    def _setup_subscriptions(self):
        """🔧 NUOVO: Configura subscription MQTT (chiamato sempre dopo connessione)"""
        try:
            if not self.client:
                print("⚠️ Client MQTT non disponibile per subscription")
                return
            
            # Topic per auth response
            if self.config.auth_response_topic:
                auth_topic = f"gate/+/{self.config.auth_response_topic.split('/')[-1]}"
                result = self.client.subscribe(auth_topic)
                print(f"📧 Subscribe auth_response: {auth_topic} (rc: {result[0]})")
            
            # Topic per manual open
            manual_topic = f"gate/+/manual_open"
            result = self.client.subscribe(manual_topic)
            print(f"📧 Subscribe manual_open: {manual_topic} (rc: {result[0]})")
            
            # 🔧 NUOVO: Subscribe anche al nostro topic heartbeat per debug
            heartbeat_topic = "rfid_gate/heartbeat"
            result = self.client.subscribe(heartbeat_topic)
            print(f"📧 Subscribe heartbeat: {heartbeat_topic} (rc: {result[0]})")
            
            print("✅ Subscription configurate")
            
        except Exception as e:
            print(f"❌ Errore configurazione subscription: {e}")
    
    async def _ensure_subscriptions_active(self):
        """🔧 NUOVO: Assicura che le subscription siano attive dopo riconnessione"""
        try:
            if not self.client or not self.is_connected():
                print("⚠️ Client non connesso per verifica subscription")
                return
            
            print("🔍 Verifica subscription post-connessione...")
            
            # Aspetta un po' per stabilizzare la connessione
            await asyncio.sleep(1)
            
            # Forza re-subscription (in caso il callback _on_connect non sia stato chiamato)
            if hasattr(self.client, '_subscriptions'):
                current_subs = self.client._subscriptions or {}
                print(f"📊 Subscription attive: {len(current_subs)}")
                
                if len(current_subs) == 0:
                    print("⚠️ Nessuna subscription attiva! Forzo re-subscription...")
                    self._setup_subscriptions()
                else:
                    print("✅ Subscription presenti:")
                    for topic in current_subs.keys():
                        print(f"   - {topic}")
            else:
                print("⚠️ Impossibile verificare subscription, forzo setup...")
                self._setup_subscriptions()
                
        except Exception as e:
            print(f"❌ Errore verifica subscription: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback disconnessione MQTT"""
        self.state = ConnectionState.DISCONNECTED
        print(f"🔌 MQTT disconnesso (rc: {rc})")
        
        # 🔧 FIX: Avvia riconnessione automatica in modo thread-safe
        if self._event_loop and not self._event_loop.is_closed():
            # Siamo in un thread diverso, quindi usiamo call_soon_threadsafe
            if not self._reconnect_task or self._reconnect_task.done():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self._auto_reconnect(), 
                        self._event_loop
                    )
                    self._reconnect_task = future
                    print("🔄 Riconnessione automatica avviata (thread-safe)")
                except Exception as e:
                    print(f"❌ Errore avvio riconnessione thread-safe: {e}")
        else:
            print("⚠️ Event loop non disponibile per riconnessione automatica")
        
        # Callback utente
        if self.on_disconnected:
            try:
                self.on_disconnected()
            except Exception as e:
                print(f"❌ Errore callback disconnected: {e}")
    
    def _on_message(self, client, userdata, msg):
        """Callback messaggio ricevuto"""
        try:
            self.stats['messages_received'] += 1
            
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"📨 MQTT ricevuto: {topic}")
            
            # Gestione auth response - controllo più flessibile
            if ('response' in topic or 'auth_response' in topic) and 'tornello' in topic:
                print(f"🔐 AUTH RESPONSE rilevata: {topic}")
                self._handle_auth_response(payload)
                if self.on_auth_response:
                    try:
                        self.on_auth_response(topic, payload)
                    except Exception as e:
                        print(f"❌ Errore callback auth_response: {e}")
            
            # Callback utente
            if self.on_message:
                try:
                    self.on_message(topic, payload)
                except Exception as e:
                    print(f"❌ Errore callback message: {e}")
                    
        except Exception as e:
            print(f"❌ Errore processing messaggio: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback pubblicazione completata"""
        self.stats['messages_sent'] += 1
    
    def _handle_auth_response(self, payload: Dict[str, Any]):
        """Gestisce risposta autenticazione"""
        try:
            request_id = payload.get('request_id')
            if request_id and request_id in self.pending_auths:
                self.auth_responses[request_id] = payload
                del self.pending_auths[request_id]
                self.stats['auth_responses'] += 1
                
                if self.on_auth_response:
                    self.on_auth_response(request_id, payload)
                    
        except Exception as e:
            print(f"❌ Errore gestione auth response: {e}")
    
    async def _auto_reconnect(self):
        """Riconnessione automatica migliorata - Thread-safe"""
        try:
            while self.state == ConnectionState.DISCONNECTED:
                try:
                    await asyncio.sleep(self.reconnect_delay)
                    
                    # 🔧 Reset tentativi se sono passati più di 5 minuti dall'ultima connessione
                    if (time.time() - self.last_connection_time) > self.connection_reset_interval:
                        if self.connection_attempts >= self.max_retries:
                            print(f"🔄 Reset tentativi riconnessione dopo {self.connection_reset_interval}s")
                            self.connection_attempts = 0
                    
                    if self.connection_attempts < self.max_retries:
                        print(f"🔄 Tentativo riconnessione #{self.connection_attempts + 1}/{self.max_retries}")
                        success = await self.connect()
                        
                        if success:
                            self.stats['reconnections'] += 1
                            print("✅ Riconnessione automatica riuscita!")
                            break
                    else:
                        print(f"❌ Max tentativi riconnessione raggiunti ({self.max_retries})")
                        print(f"⏱️ Attendo {self.connection_reset_interval}s prima del reset...")
                        await asyncio.sleep(self.connection_reset_interval)
                        self.connection_attempts = 0  # 🔧 Reset per riprovare
                        print("🔄 Reset tentativi completato, riprovo...")
                        
                except Exception as e:
                    print(f"❌ Errore riconnessione: {e}")
                    await asyncio.sleep(self.reconnect_delay)
                    
        except asyncio.CancelledError:
            print("🛑 Riconnessione automatica cancellata")
        except Exception as e:
            print(f"❌ Errore critico riconnessione automatica: {e}")
    
    async def _heartbeat_monitor(self):
        """
        🔧 NUOVO: Monitor heartbeat per rilevare connessioni passive morte.
        Invia ping periodico e rileva se la connessione è ancora attiva.
        """
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.state == ConnectionState.CONNECTED and self.client:
                    current_time = time.time()
                    
                    # Controlla se è il momento di inviare un ping
                    if (current_time - self.last_ping_time) >= self.heartbeat_interval:
                        print(f"💓 MQTT ping check...")
                        
                        # Invia un ping (publish su topic speciale o usa keep-alive interno)
                        try:
                            # Usa metodo interno per verificare se socket è ancora attivo
                            if hasattr(self.client, '_sock') and self.client._sock:
                                # Test connessione con un piccolo publish
                                test_payload = {"ping": current_time, "from": "rfid_gate"}
                                result = self.client.publish("rfid_gate/heartbeat", json.dumps(test_payload), qos=0)
                                
                                if result.rc == 0:
                                    self.last_ping_time = current_time
                                    self.missed_pings = 0
                                    print(f"💓 MQTT ping OK")
                                else:
                                    self.missed_pings += 1
                                    print(f"⚠️ MQTT ping fallito: rc={result.rc} (missed: {self.missed_pings}/{self.max_missed_pings})")
                            else:
                                # Socket non disponibile
                                self.missed_pings += 1
                                print(f"⚠️ MQTT socket non disponibile (missed: {self.missed_pings}/{self.max_missed_pings})")
                        
                        except Exception as ping_error:
                            self.missed_pings += 1
                            print(f"❌ MQTT ping error: {ping_error} (missed: {self.missed_pings}/{self.max_missed_pings})")
                        
                        # Se troppi ping mancati, forza disconnessione
                        if self.missed_pings >= self.max_missed_pings:
                            print(f"💔 MQTT connessione morta rilevata! Forzo disconnessione...")
                            self.state = ConnectionState.DISCONNECTED
                            
                            # Forza disconnessione del client
                            if self.client:
                                try:
                                    self.client.disconnect()
                                except:
                                    pass
                            
                            # Avvia riconnessione se non già attiva
                            if not self._reconnect_task or self._reconnect_task.done():
                                self._reconnect_task = asyncio.create_task(self._auto_reconnect())
                                
            except asyncio.CancelledError:
                print("🛑 Heartbeat monitor fermato")
                break
            except Exception as e:
                print(f"❌ Errore heartbeat monitor: {e}")
                await asyncio.sleep(5)  # Breve pausa in caso di errore
    
    async def _process_queue(self):
        """Processore coda messaggi"""
        while True:
            try:
                if (self.state == ConnectionState.CONNECTED and 
                    self.message_queue and self.client):
                    
                    # Processa messaggi in coda
                    messages_to_send = self.message_queue[:10]  # Max 10 alla volta
                    self.message_queue = self.message_queue[10:]
                    
                    for msg in messages_to_send:
                        try:
                            payload_str = json.dumps(msg.payload)
                            result = self.client.publish(msg.topic, payload_str, msg.qos, msg.retain)
                            
                            if result.rc == 0:
                                print(f"📤 MQTT inviato: {msg.topic}")
                            else:
                                print(f"❌ MQTT invio fallito: {result.rc}")
                                
                        except Exception as e:
                            print(f"❌ Errore invio messaggio: {e}")
                
                await asyncio.sleep(0.1)  # 100ms delay
                
            except Exception as e:
                print(f"❌ Errore processore coda: {e}")
                await asyncio.sleep(1)
    
    async def _process_retry_queue(self):
        """✨ Processore coda retry per messaggi falliti"""
        while True:
            try:
                if (self.state == ConnectionState.CONNECTED and 
                    self.retry_queue and self.client):
                    
                    print(f"🔄 Processing retry queue: {len(self.retry_queue)} messaggi")
                    
                    # Processa messaggi retry
                    messages_to_retry = self.retry_queue[:5]  # Max 5 alla volta
                    self.retry_queue = self.retry_queue[5:]
                    
                    for msg in messages_to_retry:
                        try:
                            payload_str = json.dumps(msg.payload)
                            result = self.client.publish(msg.topic, payload_str, msg.qos, msg.retain)
                            
                            if result.rc == 0:
                                print(f"✅ MQTT retry riuscito: {msg.topic}")
                            else:
                                print(f"❌ MQTT retry fallito: {result.rc}")
                                # Rimetti in coda se c'è spazio
                                if len(self.retry_queue) < self.max_retry_queue_size:
                                    self.retry_queue.append(msg)
                                    
                        except Exception as e:
                            print(f"❌ Errore retry messaggio: {e}")
                            # Rimetti in coda se c'è spazio
                            if len(self.retry_queue) < self.max_retry_queue_size:
                                self.retry_queue.append(msg)
                
                # Attesa basata sull'intervallo configurato
                await asyncio.sleep(self.retry_interval)
                
            except Exception as e:
                print(f"❌ Errore processore retry: {e}")
                await asyncio.sleep(self.retry_interval)
    
    async def send_card_read(self, card_message: CardReadMessage) -> bool:
        """
        Invia messaggio lettura carta con payload LEGACY compatibile.
        
        Args:
            card_message: Messaggio carta letta
            
        Returns:
            bool: True se inviato/accodato con successo
        """
        try:
            # ========================================
            # 🔄 PAYLOAD LEGACY COMPATIBILE
            # ========================================
            payload = {
                "card_uid": card_message.card_uid,
                "identificativo_tornello": card_message.identificativo_tornello,
                "direzione": card_message.direzione,
                "timestamp": card_message.timestamp,
                "raw_id": card_message.raw_id,
                "card_data": card_message.card_data,
                "hex_id": card_message.hex_id,
                "auth_required": card_message.auth_required,
                "reader_id": card_message.reader_id
            }
            
            # Topic dinamico usando configurazione .env
            topic = self.config.card_read_topic
            
            # Crea messaggio MQTT
            mqtt_msg = MQTTMessage(
                topic=topic,
                payload=payload,
                qos=1  # QoS 1 come nel legacy
            )
            
            success = await self._send_message(mqtt_msg)
            
            if success:
                print(f"✅ Card read inviato (legacy compatible): {card_message.card_uid}")
                print(f"📍 Topic: {topic}")
            else:
                print(f"❌ Errore invio card read: {card_message.card_uid}")
            
            return success
            
        except Exception as e:
            print(f"❌ Errore send_card_read: {e}")
            return False
    
    async def send_auth_request(self, auth_request: AuthRequest) -> Optional[str]:
        """
        Invia richiesta autenticazione con payload LEGACY compatibile.
        
        Args:
            auth_request: Richiesta autenticazione
            
        Returns:
            Optional[str]: Request ID se inviato, None se errore
        """
        try:
            # Genera request_id per tracking (anche se non nel payload legacy)
            request_id = str(uuid.uuid4())[:8]
            
            # ========================================
            # 🔄 PAYLOAD LEGACY COMPATIBILE
            # ========================================
            payload = {
                "card_uid": auth_request.card_uid,
                "identificativo_tornello": auth_request.identificativo_tornello,
                "direzione": auth_request.direzione,
                "timestamp": auth_request.timestamp,
                "auth_required": auth_request.auth_required
            }
            
            # Topic dinamico basato su auth_response_topic configurato
            base_topic = '/'.join(self.config.auth_response_topic.split('/')[:-1])
            topic = f"{base_topic}/auth_request"
            
            # Registra richiesta pending per tracking interno
            self.pending_auths[request_id] = auth_request
            self.stats['auth_requests'] += 1
            
            # Crea messaggio MQTT
            mqtt_msg = MQTTMessage(
                topic=topic,
                payload=payload,
                qos=1  # QoS 1 come nel legacy
            )
            
            success = await self._send_message(mqtt_msg)
            
            if success:
                print(f"✅ Auth request inviato (legacy compatible): {auth_request.card_uid}")
                print(f"📍 Topic: {topic}")
                return request_id
            else:
                print(f"❌ Errore invio auth request: {auth_request.card_uid}")
                # Rimuovi dalla pending se fallisce
                self.pending_auths.pop(request_id, None)
                return None
                
        except Exception as e:
            print(f"❌ Errore send_auth_request: {e}")
            return None
    
    async def send_auth_request_parallel(self, auth_request: AuthRequest) -> bool:
        """
        ✨ Invia richiesta autenticazione in modalità parallela (fire-and-forget).
        Non attende risposta, utile per notificare il server senza bloccare.
        
        Args:
            auth_request: Richiesta autenticazione
            
        Returns:
            bool: True se inviato/accodato, False se errore
        """
        try:
            # ========================================
            # 🔄 PAYLOAD LEGACY COMPATIBILE
            # ========================================
            payload = {
                "card_uid": auth_request.card_uid,
                "identificativo_tornello": auth_request.identificativo_tornello,
                "direzione": auth_request.direzione,
                "timestamp": auth_request.timestamp,
                "auth_required": auth_request.auth_required
            }
            
            # Topic per invio badge (card_read_topic è il topic giusto per inviare)
            topic = self.config.card_read_topic
            
            # Crea messaggio MQTT
            mqtt_msg = MQTTMessage(
                topic=topic,
                payload=payload,
                qos=1  # QoS 1 per affidabilità
            )
            
            success = await self._send_message(mqtt_msg)
            
            if success:
                print(f"🚀 Auth request parallelo inviato: {auth_request.card_uid}")
                return True
            else:
                print(f"⚠️ Auth request parallelo accodato/retry: {auth_request.card_uid}")
                return False  # In realtà potrebbe essere in retry queue
                
        except Exception as e:
            print(f"❌ Errore send_auth_request_parallel: {e}")
            return False
            print(f"❌ Errore invio auth request: {e}")
            return None
    
    async def wait_auth_response(self, request_id: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """
        Attende risposta autenticazione.
        
        Args:
            request_id: ID richiesta
            timeout: Timeout in secondi
            
        Returns:
            Optional[Dict[str, Any]]: Risposta auth o None se timeout
        """
        timeout = timeout or self.auth_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if request_id in self.auth_responses:
                response = self.auth_responses.pop(request_id)
                return response
            
            await asyncio.sleep(0.1)
        
        # Timeout - rimuovi da pending
        self.pending_auths.pop(request_id, None)
        return None
    
    async def _send_message(self, message: MQTTMessage) -> bool:
        """
        Invia messaggio (diretto o accodato) in modo VERAMENTE asincrono.
        
        Args:
            message: Messaggio da inviare
            
        Returns:
            bool: True se inviato/accodato con successo
        """
        if self.state == ConnectionState.CONNECTED and self.client:
            # Invio diretto ASINCRONO per evitare blocchi
            try:
                payload_str = json.dumps(message.payload)
                
                # ✨ USA THREAD POOL per evitare blocchi del publish sincrono
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,  # ThreadPoolExecutor default
                    lambda: self.client.publish(message.topic, payload_str, message.qos, message.retain)
                )
                
                if result.rc == 0:
                    print(f"📤 MQTT inviato (async): {message.topic}")
                    return True
                else:
                    print(f"❌ MQTT invio fallito: {result.rc}")
                    # ✨ Aggiungi alla retry queue se abilitata
                    self._add_to_retry_queue(message)
                    return False
                    
            except Exception as e:
                print(f"❌ Errore invio asincrono: {e}")
                # ✨ Aggiungi alla retry queue se abilitata
                self._add_to_retry_queue(message)
                return False
        else:
            # Accoda per invio successivo
            if len(self.message_queue) < self.max_queue_size:
                self.message_queue.append(message)
                self.stats['messages_queued'] += 1
                print(f"📥 MQTT accodato: {message.topic} (coda: {len(self.message_queue)})")
                return True
            else:
                print(f"❌ Coda MQTT piena ({self.max_queue_size})")
                # ✨ Prova retry queue come fallback
                return self._add_to_retry_queue(message)
    
    def _add_to_retry_queue(self, message: MQTTMessage) -> bool:
        """✨ Aggiunge messaggio alla retry queue"""
        if (getattr(self.config, 'enable_retry_queue', True) and 
            len(self.retry_queue) < self.max_retry_queue_size):
            self.retry_queue.append(message)
            print(f"♻️ MQTT aggiunto a retry queue: {message.topic} (retry: {len(self.retry_queue)})")
            return True
        else:
            print(f"❌ Retry queue piena o disabilitata ({len(self.retry_queue)}/{self.max_retry_queue_size})")
            return False
    
    def is_connected(self) -> bool:
        """Verifica se connesso"""
        return self.state == ConnectionState.CONNECTED
    
    def get_queue_size(self) -> int:
        """Dimensione coda messaggi"""
        return len(self.message_queue)
    
    def get_retry_queue_size(self) -> int:
        """✨ Dimensione retry queue"""
        return len(self.retry_queue)
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiche client"""
        return {
            **self.stats,
            'state': self.state.value,
            'connection_attempts': self.connection_attempts,
            'queue_size': len(self.message_queue),
            'retry_queue_size': len(self.retry_queue),  # ✨ Nuovo
            'pending_auths': len(self.pending_auths)
        }
    
    async def cleanup(self):
        """Cleanup client MQTT"""
        try:
            # Cancella tasks
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
            
            if self._queue_processor_task and not self._queue_processor_task.done():
                self._queue_processor_task.cancel()
            
            # ✨ Cancella retry processor task
            if self._retry_processor_task and not self._retry_processor_task.done():
                self._retry_processor_task.cancel()
            
            # 🔧 NUOVO: Cancella heartbeat task
            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
            
            # Disconnetti client
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            
            print("🧹 MQTT client cleanup completato")
            
        except Exception as e:
            print(f"❌ Errore cleanup MQTT: {e}")
    
    async def disconnect(self):
        """Disconnette il client MQTT (alias per cleanup)"""
        await self.cleanup()


# Export
__all__ = [
    'AsyncMQTTClient',
    'MQTTMessage',
    'CardReadMessage', 
    'AuthRequest',
    'ConnectionState'
]