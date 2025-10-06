#!/usr/bin/env python3
"""
🎯 Access Control System - Core Business Logic
=============================================

Sistema centrale di controllo accessi che coordina:
- Lettori RFID (in/out)
- Relè di controllo
- Autenticazione MQTT
- Modalità offline
- Logging eventi
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from rfid_gate.config.settings import RFIDGateConfig
from rfid_gate.hardware.readers.factory import ReaderFactory
from rfid_gate.hardware.readers.base import BaseRFIDReader, CardEvent
from rfid_gate.hardware.relays.gpio import GPIORelayController
from rfid_gate.hardware.relays.base import BaseRelayController, RelayEvent
from rfid_gate.network.mqtt import AsyncMQTTClient, CardReadMessage, AuthRequest
from rfid_gate.utils.debounce import GlobalDebounceManager


class AccessDecision(str, Enum):
    """Decisioni di accesso possibili"""
    GRANT = "grant"          # Accesso autorizzato
    DENY = "deny"            # Accesso negato
    PENDING = "pending"      # In attesa autenticazione
    OFFLINE = "offline"      # Modalità offline attiva
    ERROR = "error"          # Errore sistema


class SystemMode(str, Enum):
    """Modalità operative sistema"""
    ONLINE = "online"        # Modalità online normale
    OFFLINE = "offline"      # Modalità offline
    MAINTENANCE = "maintenance"  # Modalità manutenzione
    ERROR = "error"          # Modalità errore


@dataclass
class AccessEvent:
    """Evento di controllo accesso"""
    card_uid: str
    direction: str
    decision: AccessDecision
    timestamp: float
    reader_type: str
    auth_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AccessControlSystem:
    """
    Sistema centrale di controllo accessi.
    
    Coordina tutti i componenti del sistema:
    - Gestione lettori RFID multipli
    - Controllo relè per apertura
    - Autenticazione via MQTT
    - Modalità offline con cache locale
    - Logging e monitoring
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Carica configurazione
        self.config = RFIDGateConfig.from_env()
        
        # Componenti sistema
        self.readers: Dict[str, BaseRFIDReader] = {}
        self.relays: Dict[str, BaseRelayController] = {}
        self.mqtt_client: Optional[AsyncMQTTClient] = None
        self.debounce_manager = GlobalDebounceManager(self.config.system.global_debounce_time)
        
        # Stato sistema
        self.mode = SystemMode.OFFLINE
        self.is_running = False
        self.start_time = 0
        
        # Cache autenticazioni (modalità offline)
        self.auth_cache: Dict[str, Dict[str, Any]] = {}
        self.access_log: List[AccessEvent] = []
        
        # Tasks
        self._reader_tasks: List[asyncio.Task] = []
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_access_event: Optional[callable] = None
        self.on_mode_change: Optional[callable] = None
        
        # Statistiche
        self.stats = {
            'access_events': 0,
            'access_granted': 0,
            'access_denied': 0,
            'offline_events': 0,
            'errors': 0,
            'uptime_seconds': 0
        }
        
        print(f"🎯 AccessControlSystem inizializzato")
        print(f"   Modalità bidirezionale: {self.config.system.bidirectional_mode}")
        print(f"   Lettore IN: {self.config.rfid_in.reader_type.value if self.config.rfid_in.enabled else 'disabilitato'}")
        print(f"   Lettore OUT: {self.config.rfid_out.reader_type.value if self.config.rfid_out.enabled else 'disabilitato'}")
    
    async def initialize(self) -> bool:
        """
        Inizializza tutti i componenti del sistema.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            print("🚀 Inizializzazione sistema controllo accessi...")
            
            # 1. Valida configurazione
            errors = self.config.validate()
            if errors:
                print("❌ Errori configurazione:")
                for error in errors:
                    print(f"   - {error}")
                return False
            
            # 2. Inizializza lettori RFID
            success = await self._initialize_readers()
            if not success:
                print("❌ Inizializzazione lettori fallita")
                return False
            
            # 3. Inizializza relè
            success = await self._initialize_relays()
            if not success:
                print("❌ Inizializzazione relè fallita")
                return False
            
            # 4. Inizializza MQTT client
            success = await self._initialize_mqtt()
            if not success:
                print("⚠️ MQTT non disponibile, modalità offline")
                self.mode = SystemMode.OFFLINE
            else:
                self.mode = SystemMode.ONLINE
            
            # 5. Setup callbacks
            self._setup_callbacks()
            
            # 6. Avvia monitoring
            self._monitor_task = asyncio.create_task(self._system_monitor())
            
            self.start_time = time.time()
            print("✅ Sistema inizializzato correttamente")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione sistema: {e}")
            return False
    
    async def _initialize_readers(self) -> bool:
        """Inizializza lettori RFID"""
        try:
            print("📡 Inizializzazione lettori RFID...")
            
            # Crea lettori basati su configurazione
            readers_config = ReaderFactory.create_dual_readers(
                self.config.rfid_in,
                self.config.rfid_out
            )
            
            # Inizializza lettori attivi
            for direction, reader in readers_config.items():
                if reader:
                    success = await reader.initialize()
                    if success:
                        self.readers[direction] = reader
                        print(f"   ✅ Lettore {direction}: {reader}")
                    else:
                        print(f"   ❌ Lettore {direction} inizializzazione fallita")
                        return False
            
            if not self.readers:
                print("❌ Nessun lettore attivo")
                return False
            
            print(f"✅ {len(self.readers)} lettori inizializzati")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione lettori: {e}")
            return False
    
    async def _initialize_relays(self) -> bool:
        """Inizializza relè di controllo"""
        try:
            print("⚡ Inizializzazione relè...")
            
            # Relè IN
            if self.config.relay_in.enabled:
                relay_in = GPIORelayController(
                    relay_id="relay_in",
                    direction="in",
                    pin=self.config.relay_in.pin
                )
                relay_in.configure(
                    active_time=self.config.relay_in.active_time,
                    active_low=self.config.relay_in.active_low,
                    initial_state=self.config.relay_in.initial_state
                )
                
                success = await relay_in.initialize()
                if success:
                    self.relays["in"] = relay_in
                    print(f"   ✅ Relè IN: pin {self.config.relay_in.pin}")
                else:
                    print(f"   ❌ Relè IN inizializzazione fallita")
                    return False
            
            # Relè OUT
            if self.config.relay_out.enabled:
                relay_out = GPIORelayController(
                    relay_id="relay_out",
                    direction="out",
                    pin=self.config.relay_out.pin
                )
                relay_out.configure(
                    active_time=self.config.relay_out.active_time,
                    active_low=self.config.relay_out.active_low,
                    initial_state=self.config.relay_out.initial_state
                )
                
                success = await relay_out.initialize()
                if success:
                    self.relays["out"] = relay_out
                    print(f"   ✅ Relè OUT: pin {self.config.relay_out.pin}")
                else:
                    print(f"   ❌ Relè OUT inizializzazione fallita")
                    return False
            
            if not self.relays:
                print("❌ Nessun relè attivo")
                return False
            
            print(f"✅ {len(self.relays)} relè inizializzati")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione relè: {e}")
            return False
    
    async def _initialize_mqtt(self) -> bool:
        """Inizializza client MQTT"""
        try:
            print("🌐 Inizializzazione MQTT...")
            
            self.mqtt_client = AsyncMQTTClient(self.config.mqtt)
            
            success = await self.mqtt_client.initialize()
            if not success:
                return False
            
            success = await self.mqtt_client.connect()
            if not success:
                return False
            
            print("✅ MQTT client connesso")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione MQTT: {e}")
            return False
    
    def _setup_callbacks(self):
        """Configura callbacks componenti"""
        # Callbacks lettori
        for reader in self.readers.values():
            reader.on_card_read = self._on_card_read
            reader.on_error = self._on_reader_error
        
        # Callbacks relè
        for relay in self.relays.values():
            relay.on_state_change = self._on_relay_state_change
            relay.on_error = self._on_relay_error
        
        # Callbacks MQTT
        if self.mqtt_client:
            self.mqtt_client.on_connected = self._on_mqtt_connected
            self.mqtt_client.on_disconnected = self._on_mqtt_disconnected
            self.mqtt_client.on_auth_response = self._on_auth_response
    
    async def run(self):
        """
        Avvia il sistema di controllo accessi.
        Main loop principale.
        """
        if not await self.initialize():
            print("❌ Inizializzazione fallita, impossibile avviare")
            return False
        
        try:
            self.is_running = True
            print("🎯 Sistema di controllo accessi AVVIATO")
            print("=" * 50)
            
            # Avvia tasks lettori
            for direction, reader in self.readers.items():
                task = asyncio.create_task(self._reader_loop(reader))
                self._reader_tasks.append(task)
            
            # Attendi interruzione
            while self.is_running:
                await asyncio.sleep(1)
                self._update_stats()
            
        except KeyboardInterrupt:
            print("\\n🛑 Interruzione utente")
        except Exception as e:
            print(f"❌ Errore sistema: {e}")
        finally:
            await self.shutdown()
    
    async def _reader_loop(self, reader: BaseRFIDReader):
        """Loop di lettura per singolo lettore"""
        format_config = {
            'mode': self.config.system.uid_format_mode.value,
            'chars_count': self.config.system.uid_chars_count,
            'target_length': self.config.system.uid_target_length
        }
        
        while self.is_running:
            try:
                # Leggi carta con configurazione formattazione
                card_event = await reader.read_card(
                    timeout=self.config.system.card_read_interval,
                    format_config=format_config
                )
                
                if card_event:
                    # Verifica debounce globale
                    if not self.debounce_manager.is_duplicate(
                        card_event.uid_formatted,
                        card_event.direction
                    ):
                        await self._process_card_event(card_event)
                
                # Piccola pausa per evitare sovraccarico CPU
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Errore reader loop {reader.reader_id}: {e}")
                await asyncio.sleep(1)  # Pausa più lunga in caso di errore
    
    async def _process_card_event(self, card_event: CardEvent):
        """Processa evento lettura carta"""
        try:
            print(f"📇 {card_event.direction} - Carta: {card_event.uid_formatted} ({card_event.reader_type})")
            
            # Invia dati via MQTT (se online)
            if self.mode == SystemMode.ONLINE and self.mqtt_client:
                await self._send_card_data(card_event)
            
            # Processa autenticazione
            decision = await self._authenticate_card(card_event)
            
            # Crea evento accesso
            access_event = AccessEvent(
                card_uid=card_event.uid_formatted,
                direction=card_event.direction,
                decision=decision,
                timestamp=card_event.timestamp,
                reader_type=card_event.reader_type,
                metadata={
                    'raw_uid': card_event.uid,
                    'reader_id': card_event.reader_id,
                    'mode': self.mode.value
                }
            )
            
            # Registra evento
            await self._log_access_event(access_event)
            
            # Attiva relè se accesso autorizzato
            if decision == AccessDecision.GRANT:
                await self._activate_relay(card_event.direction)
            
            # Callback utente
            if self.on_access_event:
                try:
                    self.on_access_event(access_event)
                except Exception as e:
                    print(f"❌ Errore callback access event: {e}")
            
        except Exception as e:
            print(f"❌ Errore processing card event: {e}")
    
    async def _send_card_data(self, card_event: CardEvent):
        """Invia dati carta via MQTT"""
        try:
            message = CardReadMessage(
                tornello_id=self.config.system.tornello_id,
                card_uid=card_event.uid_formatted,
                direction=card_event.direction,
                reader_type=card_event.reader_type,
                timestamp=card_event.timestamp,
                raw_uid=card_event.uid,
                metadata=card_event.metadata
            )
            
            await self.mqtt_client.send_card_read(message)
            
        except Exception as e:
            print(f"❌ Errore invio dati MQTT: {e}")
    
    async def _authenticate_card(self, card_event: CardEvent) -> AccessDecision:
        """Autentica carta e restituisce decisione"""
        try:
            if self.mode == SystemMode.OFFLINE:
                # Modalità offline - usa cache locale
                return self._offline_authentication(card_event.uid_formatted)
            
            elif self.mode == SystemMode.ONLINE and self.config.auth.enabled:
                # Modalità online - autentica via MQTT
                return await self._online_authentication(card_event)
            
            else:
                # Accesso sempre consentito se auth disabilitata
                return AccessDecision.GRANT
                
        except Exception as e:
            print(f"❌ Errore autenticazione: {e}")
            return AccessDecision.ERROR
    
    def _offline_authentication(self, card_uid: str) -> AccessDecision:
        """Autenticazione offline usando cache"""
        if self.config.offline.allow_access:
            # In modalità offline permetti sempre l'accesso
            self.stats['offline_events'] += 1
            return AccessDecision.OFFLINE
        else:
            # Verifica cache se disponibile
            if card_uid in self.auth_cache:
                cache_entry = self.auth_cache[card_uid]
                if cache_entry.get('authorized', False):
                    return AccessDecision.GRANT
            
            return AccessDecision.DENY
    
    async def _online_authentication(self, card_event: CardEvent) -> AccessDecision:
        """Autenticazione online via MQTT"""
        try:
            if not self.mqtt_client or not self.mqtt_client.is_connected():
                # Fallback a modalità offline
                return self._offline_authentication(card_event.uid_formatted)
            
            # Crea richiesta autenticazione
            auth_request = AuthRequest(
                card_uid=card_event.uid_formatted,
                tornello_id=self.config.system.tornello_id,
                direction=card_event.direction,
                timestamp=card_event.timestamp
            )
            
            # Invia richiesta
            request_id = await self.mqtt_client.send_auth_request(auth_request)
            if not request_id:
                return AccessDecision.ERROR
            
            # Attendi risposta
            response = await self.mqtt_client.wait_auth_response(
                request_id, 
                self.config.auth.timeout
            )
            
            if response:
                authorized = response.get('authorized', False)
                
                # Aggiorna cache per uso offline futuro
                self.auth_cache[card_event.uid_formatted] = {
                    'authorized': authorized,
                    'timestamp': time.time(),
                    'response': response
                }
                
                return AccessDecision.GRANT if authorized else AccessDecision.DENY
            else:
                # Timeout - usa fallback offline
                return self._offline_authentication(card_event.uid_formatted)
                
        except Exception as e:
            print(f"❌ Errore auth online: {e}")
            return AccessDecision.ERROR
    
    async def _activate_relay(self, direction: str):
        """Attiva relè per direzione specificata"""
        try:
            relay = self.relays.get(direction)
            if relay:
                success = await relay.activate(trigger_source="card_auth")
                if success:
                    print(f"🚪 Apertura {direction} attivata")
                else:
                    print(f"❌ Errore attivazione relè {direction}")
            else:
                print(f"⚠️ Relè {direction} non configurato")
                
        except Exception as e:
            print(f"❌ Errore attivazione relè: {e}")
    
    async def _log_access_event(self, event: AccessEvent):
        """Registra evento di accesso"""
        try:
            self.access_log.append(event)
            self.stats['access_events'] += 1
            
            if event.decision == AccessDecision.GRANT:
                self.stats['access_granted'] += 1
                status_emoji = "✅"
            elif event.decision == AccessDecision.DENY:
                self.stats['access_denied'] += 1
                status_emoji = "❌"
            elif event.decision == AccessDecision.OFFLINE:
                self.stats['offline_events'] += 1
                status_emoji = "📴"
            else:
                self.stats['errors'] += 1
                status_emoji = "⚠️"
            
            print(f"{status_emoji} Accesso {event.decision.value}: {event.card_uid} ({event.direction})")
            
            # Mantieni log limitato in memoria
            if len(self.access_log) > 1000:
                self.access_log = self.access_log[-500:]  # Tieni ultimi 500
                
        except Exception as e:
            print(f"❌ Errore logging evento: {e}")
    
    async def _system_monitor(self):
        """Monitor sistema per health check"""
        while self.is_running:
            try:
                # Check connessione MQTT
                if self.mqtt_client and not self.mqtt_client.is_connected():
                    if self.mode == SystemMode.ONLINE:
                        print("⚠️ Connessione MQTT persa, passaggio a modalità offline")
                        await self._set_mode(SystemMode.OFFLINE)
                
                # Check stato lettori
                for direction, reader in self.readers.items():
                    if reader.status.value == "error":
                        print(f"⚠️ Lettore {direction} in errore")
                
                # Check stato relè
                for direction, relay in self.relays.items():
                    if relay.state.value == "error":
                        print(f"⚠️ Relè {direction} in errore")
                
                await asyncio.sleep(30)  # Check ogni 30 secondi
                
            except Exception as e:
                print(f"❌ Errore system monitor: {e}")
                await asyncio.sleep(60)
    
    async def _set_mode(self, new_mode: SystemMode):
        """Cambia modalità sistema"""
        if self.mode != new_mode:
            old_mode = self.mode
            self.mode = new_mode
            
            print(f"🔄 Modalità sistema: {old_mode.value} → {new_mode.value}")
            
            if self.on_mode_change:
                try:
                    self.on_mode_change(old_mode, new_mode)
                except Exception as e:
                    print(f"❌ Errore callback mode change: {e}")
    
    def _update_stats(self):
        """Aggiorna statistiche sistema"""
        if self.start_time > 0:
            self.stats['uptime_seconds'] = int(time.time() - self.start_time)
    
    # Callback handlers
    def _on_card_read(self, card_event: CardEvent):
        """Callback lettura carta"""
        pass  # Gestito da _reader_loop
    
    def _on_reader_error(self, error: Exception):
        """Callback errore lettore"""
        print(f"📡❌ Errore lettore: {error}")
    
    def _on_relay_state_change(self, relay_event: RelayEvent):
        """Callback cambio stato relè"""
        print(f"⚡ Relè {relay_event.relay_id}: {relay_event.state.value}")
    
    def _on_relay_error(self, error: Exception):
        """Callback errore relè"""
        print(f"⚡❌ Errore relè: {error}")
    
    def _on_mqtt_connected(self):
        """Callback MQTT connesso"""
        asyncio.create_task(self._set_mode(SystemMode.ONLINE))
    
    def _on_mqtt_disconnected(self):
        """Callback MQTT disconnesso"""
        asyncio.create_task(self._set_mode(SystemMode.OFFLINE))
    
    def _on_auth_response(self, request_id: str, response: Dict[str, Any]):
        """Callback risposta autenticazione"""
        print(f"🔐 Auth response ricevuta: {request_id}")
    
    # API pubbliche
    def get_system_status(self) -> Dict[str, Any]:
        """Stato completo del sistema"""
        self._update_stats()
        
        return {
            'mode': self.mode.value,
            'is_running': self.is_running,
            'stats': self.stats,
            'readers': {
                direction: reader.get_stats() 
                for direction, reader in self.readers.items()
            },
            'relays': {
                direction: relay.get_stats() 
                for direction, relay in self.relays.items()
            },
            'mqtt': self.mqtt_client.get_stats() if self.mqtt_client else None,
            'auth_cache_size': len(self.auth_cache),
            'access_log_size': len(self.access_log)
        }
    
    async def manual_open(self, direction: str, duration: Optional[float] = None) -> bool:
        """Apertura manuale relè"""
        try:
            relay = self.relays.get(direction)
            if not relay:
                print(f"❌ Relè {direction} non trovato")
                return False
            
            success = await relay.activate(duration, trigger_source="manual")
            if success:
                print(f"🔓 Apertura manuale {direction} attivata")
            
            return success
            
        except Exception as e:
            print(f"❌ Errore apertura manuale: {e}")
            return False
    
    async def shutdown(self):
        """Spegnimento sistema"""
        try:
            print("🛑 Spegnimento sistema...")
            self.is_running = False
            
            # Cancella tasks
            for task in self._reader_tasks:
                if not task.done():
                    task.cancel()
            
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
            
            # Cleanup componenti
            for reader in self.readers.values():
                await reader.cleanup()
            
            for relay in self.relays.values():
                await relay.cleanup()
            
            if self.mqtt_client:
                await self.mqtt_client.cleanup()
            
            print("✅ Sistema spento correttamente")
            
        except Exception as e:
            print(f"❌ Errore durante spegnimento: {e}")


# Export
__all__ = [
    'AccessControlSystem',
    'AccessEvent',
    'AccessDecision',
    'SystemMode'
]