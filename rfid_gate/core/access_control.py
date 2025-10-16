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
import os
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
from rfid_gate.network.sync_manager import SyncManager
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
        self.sync_manager: Optional[SyncManager] = None
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
            
            # 4. Inizializza SyncManager (se abilitato)
            if self.config.sync.enabled:
                success = await self._initialize_sync_manager()
                if not success:
                    print("⚠️ SyncManager non disponibile")
            
            # 5. Inizializza MQTT client
            success = await self._initialize_mqtt()
            if not success:
                print("⚠️ MQTT non disponibile, modalità offline")
                self.mode = SystemMode.OFFLINE
            else:
                self.mode = SystemMode.ONLINE
            
            # 6. Setup callbacks
            self._setup_callbacks()
            
            # 7. Avvia monitoring
            self._monitor_task = asyncio.create_task(self._system_monitor())
            
            self.start_time = time.time()
            print("✅ Sistema inizializzato correttamente")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione sistema: {e}")
            return False
    
    async def start(self) -> bool:
        """Avvia il sistema (alias per initialize per compatibilità con monitor tools)"""
        return await self.initialize()
    
    async def stop(self) -> None:
        """Ferma il sistema e libera le risorse"""
        try:
            print("🛑 Arresto sistema di controllo accessi...")
            
            # Ferma task di monitoring
            if hasattr(self, '_monitor_task') and self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                print("   ✅ Monitor task fermato")
            
            # Ferma lettori RFID
            for direction, reader in self.readers.items():
                if reader:
                    try:
                        await reader.cleanup()
                        print(f"   ✅ Lettore {direction} fermato")
                    except Exception as e:
                        print(f"   ⚠️ Errore arresto lettore {direction}: {e}")
            
            # Ferma relè (resetta a stato chiuso)
            for direction, relay in self.relays.items():
                if relay:
                    try:
                        await relay.close()
                        print(f"   ✅ Relè {direction} chiuso")
                    except Exception as e:
                        print(f"   ⚠️ Errore chiusura relè {direction}: {e}")
            
            # Disconnetti MQTT
            if self.mqtt_client:
                try:
                    await self.mqtt_client.disconnect()
                    print("   ✅ MQTT disconnesso")
                except Exception as e:
                    print(f"   ⚠️ Errore disconnessione MQTT: {e}")
            
            # Ferma sync manager
            if hasattr(self, 'sync_manager') and self.sync_manager:
                try:
                    await self.sync_manager.stop()
                    print("   ✅ Sync manager fermato")
                except Exception as e:
                    print(f"   ⚠️ Errore arresto sync manager: {e}")
            
            print("✅ Sistema arrestato correttamente")
            
        except Exception as e:
            print(f"❌ Errore durante arresto sistema: {e}")
    
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
    
    async def _initialize_sync_manager(self) -> bool:
        """Inizializza SyncManager per cache offline"""
        try:
            print("🔄 Inizializzazione SyncManager...")
            
            self.sync_manager = SyncManager(
                config=self.config.sync,
                tornello_id=self.config.system.tornello_id
            )
            
            # Avvia background sync
            await self.sync_manager.start_background_sync()
            
            # Prova una sync iniziale se online
            connectivity = await self.sync_manager.check_connectivity()
            if connectivity:
                await self.sync_manager.daily_sync()
                print("✅ SyncManager inizializzato e sincronizzato")
            else:
                print("✅ SyncManager inizializzato (modalità offline)")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione SyncManager: {e}")
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
            
            # 🚀 MQTT Fix: Rimuoviamo invio duplicato qui
            # L'invio MQTT ora avviene DENTRO _authenticate_card() in parallelo
            # if self.mode == SystemMode.ONLINE and self.mqtt_client:
            #     await self._send_card_data(card_event)
            
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
        """Invia dati carta via MQTT con payload LEGACY compatibile"""
        try:
            # ========================================
            # 🔄 USA FACTORY METHOD LEGACY COMPATIBLE
            # ========================================
            message = CardReadMessage.from_card_event(
                card_event=card_event,
                tornello_id=self.config.system.tornello_id,
                auth_required=self.config.auth.enabled
            )
            
            await self.mqtt_client.send_card_read(message)
            
        except Exception as e:
            print(f"❌ Errore invio dati MQTT: {e}")
    
    async def _authenticate_card(self, card_event: CardEvent) -> AccessDecision:
        """
        🎯 NUOVO FLUSSO INTELLIGENTE - Cache First con MQTT Parallelo e Fallback Diretto
        ================================================================================
        
        📱 CASO 1: Carta in cache
           → Carta letta → autenticazione cache → apertura relè
           → Log: UNA entry di autorizzazione
           → In parallelo dopo validazione cache: MQTT → broker → gate-verification (non uso risposta)

        📱 CASO 2: Carta NON in cache  
           → Carta letta → carta non trovata
           → Cache refresh: GET /api/sync-gate?card_uid=XXX
           → Se trova dati → autenticazione cache e aggiorna dati → MQTT parallelo
           → Se ancora non trova: chiamata /api/gate-verification (senza MQTT parallelo)
           → Log: UNA entry di autorizzazione finale

        📱 CASO 3: Carta con abbonamento scaduto
           → Carta letta → abbonamento scaduto o non esistente  
           → Cache refresh: GET /api/sync-gate?card_uid=XXX
           → Se trova rinnovo → autenticazione cache → aggiorna cache
           → Log: UNA entry con nuovo abbonamento
           → In parallelo dopo autenticazione cache: MQTT → broker (non uso risposta)
           
        🔐 WHITELIST: Sempre autorizzata con bypass IN/OUT
        """
        try:
            print(f"🎯 Flusso intelligente per carta: {card_event.uid_formatted}")
            
            # ============================================================================
            # � CONTROLLO BIDIREZIONALE (se abilitato) - PRIMA PRIORITÀ
            # ============================================================================
            # ============================================================================
            # 🔐 WHITELIST CHECK - PRIORITÀ MASSIMA (bypass controlli bidirezionali)
            # ============================================================================
            if self.sync_manager and self.config.sync.enabled:
                # Controlla se la carta è in whitelist
                whitelist_result = await self._check_whitelist_access(card_event)
                if whitelist_result['authorized']:
                    print(f"🔓 WHITELIST: Accesso libero per {card_event.uid_formatted} (bypass controlli bidirezionali)")
                    
                    # WHITELIST: Aggiorna stato ma NON fa controlli preventivi 
                    # (operatori possono entrare/uscire liberamente)
                    if self.config.system.bidirectional_mode:
                        await self.sync_manager.update_user_direction(
                            card_uid=card_event.uid_formatted,
                            direction=card_event.direction,
                            tornello_id=self.config.system.tornello_id,
                            customer_id=whitelist_result.get('customer_id')
                        )
                    
                    # Log immediato whitelist
                    await self.sync_manager.log_access(
                        card_uid=card_event.uid_formatted,
                        direction=card_event.direction,
                        result="authorized",
                        reason=whitelist_result['reason'],
                        customer_id=whitelist_result.get('customer_id'),
                        customer_name=whitelist_result.get('customer_name'),
                        reader_type=card_event.reader_type,
                        metadata=card_event.metadata
                    )
                    
                    # WHITELIST: MQTT parallelo solo per logging (non per autorizzazione)
                    if (self.mode == SystemMode.ONLINE and self.config.auth.enabled and 
                        self.mqtt_client and self.mqtt_client.is_connected()):
                        await self._send_parallel_mqtt_logging(card_event)
                    
                    return AccessDecision.GRANT
                    
            # ============================================================================
            # 🔄 CONTROLLO BIDIREZIONALE (solo per carte NON-whitelist)
            # ============================================================================
            if self.config.system.bidirectional_mode and self.sync_manager:
                bidirectional_check = await self.sync_manager.check_bidirectional_access(
                    card_uid=card_event.uid_formatted,
                    direction=card_event.direction,
                    tornello_id=self.config.system.tornello_id
                )
                
                if not bidirectional_check['valid']:
                    await self._log_denied_access(
                        card_event, 
                        f"Controllo bidirezionale: {bidirectional_check['reason']}"
                    )
                    return AccessDecision.DENY
            
            # ============================================================================
            # 📱 CASO 1: Controlla Cache Locale
            # ============================================================================
            if self.sync_manager and self.config.sync.enabled:
                cache_result = await self.sync_manager.validate_card_offline(
                    card_event.uid_formatted, 
                    card_event.direction
                )
                
                if cache_result['authorized']:
                    # ✅ CASO 1: Carta trovata e valida in cache
                    print(f"✅ CASO 1: Carta {card_event.uid_formatted} autorizzata da cache")
                    
                    # Update bidirezionale se necessario
                    if self.config.system.bidirectional_mode:
                        await self.sync_manager.update_user_direction(
                            card_uid=card_event.uid_formatted,
                            direction=card_event.direction,
                            tornello_id=self.config.system.tornello_id,
                            customer_id=cache_result.get('customer_id')
                        )
                    
                    # Log immediato locale
                    await self._log_authorized_access(card_event, cache_result)
                    
                    # MQTT parallelo per logging server
                    if (self.mode == SystemMode.ONLINE and self.config.auth.enabled and 
                        self.mqtt_client and self.mqtt_client.is_connected()):
                        await self._send_parallel_mqtt_logging(card_event)
                    
                    return AccessDecision.GRANT
                
                # ============================================================================
                # 📱 CASO 2 & 3: Cache Miss o Scaduta - Prova Cache Refresh
                # ============================================================================
                elif self.mode == SystemMode.ONLINE:
                    print(f"🔄 CASO 2/3: Cache miss/scaduta per {card_event.uid_formatted} - tentativo refresh")
                    
                    try:
                        from rfid_gate.network.cache_refresh_strategy import CacheRefreshManager
                        refresh_mgr = CacheRefreshManager(self.sync_manager)
                        
                        # Cache refresh: GET /api/sync-gate
                        cache_updated = await refresh_mgr.handle_denied_card_refresh(card_event.uid_formatted)
                        
                        if cache_updated:
                            # Cache aggiornata - ricontrolla
                            print(f"💾 Cache aggiornata per {card_event.uid_formatted} - ricontrollo...")
                            
                            refreshed_result = await self.sync_manager.validate_card_offline(
                                card_event.uid_formatted, 
                                card_event.direction
                            )
                            
                            if refreshed_result['authorized']:
                                # ✅ CASO 3: Cache refresh ha risolto (es. abbonamento rinnovato/scaduto)
                                print(f"✅ CASO 3: Cache refresh risolto per {card_event.uid_formatted} - CON MQTT parallelo")
                                
                                # Update bidirezionale
                                if self.config.system.bidirectional_mode:
                                    await self.sync_manager.update_user_direction(
                                        card_uid=card_event.uid_formatted,
                                        direction=card_event.direction,
                                        tornello_id=self.config.system.tornello_id,
                                        customer_id=refreshed_result.get('customer_id')
                                    )
                                
                                # Log immediato con nuovo abbonamento
                                await self._log_authorized_access(card_event, refreshed_result, source="cache_refresh")
                                
                                # ✅ CASO 3: MQTT parallelo per logging dopo trovata carta in cache refresh
                                if (self.config.auth.enabled and self.mqtt_client and 
                                    self.mqtt_client.is_connected()):
                                    await self._send_parallel_mqtt_logging(card_event)
                                
                                return AccessDecision.GRANT
                        
                        # ============================================================================
                        # 📱 CASO 2: Cache refresh non ha trovato la carta - FALLBACK DIRETTO
                        # ============================================================================
                        print(f"🔗 CASO 2: Fallback diretto gate-verification per {card_event.uid_formatted}")
                        
                        # Chiamata diretta /api/gate-verification (SENZA MQTT per evitare duplicati)
                        direct_result = await self._direct_gate_verification(
                            card_event.uid_formatted, 
                            card_event.direction
                        )
                        
                        if direct_result['authorized']:
                            print(f"✅ CASO 2: Gate-verification autorizza {card_event.uid_formatted} (NO MQTT parallelo)")
                            
                            # Update bidirezionale se necessario
                            if self.config.system.bidirectional_mode:
                                await self.sync_manager.update_user_direction(
                                    card_uid=card_event.uid_formatted,
                                    direction=card_event.direction,
                                    tornello_id=self.config.system.tornello_id,
                                    customer_id=direct_result.get('customer_id')
                                )
                            
                            # Log immediato fallback - IMPORTANTE: NO MQTT parallelo per CASO 2
                            await self._log_authorized_access(card_event, direct_result, source="fallback")
                            
                            return AccessDecision.GRANT
                        else:
                            print(f"❌ CASO 2: Gate-verification nega {card_event.uid_formatted}")
                            await self._log_denied_access(card_event, direct_result['reason'], source="fallback")
                            return AccessDecision.DENY
                            
                    except Exception as e:
                        print(f"⚠️ Errore durante cache refresh/fallback per {card_event.uid_formatted}: {e}")
                        # Continua con cache result originale
                        await self._log_denied_access(card_event, cache_result['reason'])
                        return AccessDecision.DENY
                
                # Modalità offline - usa solo cache
                else:
                    await self._log_denied_access(card_event, cache_result['reason'])
                    return AccessDecision.DENY
            
            # ============================================================================
            # 💽 Fallback Offline Mode (legacy)
            # ============================================================================
            elif self.mode == SystemMode.OFFLINE:
                decision = self._offline_authentication(card_event.uid_formatted)
                result_str = "authorized" if decision == AccessDecision.GRANT else "denied"
                reason = "Offline auth | Local"
                
                if self.sync_manager:
                    await self.sync_manager.log_access(
                        card_uid=card_event.uid_formatted,
                        direction=card_event.direction,
                        result=result_str,
                        reason=reason,
                        customer_id=None,
                        reader_type=card_event.reader_type,
                        metadata=card_event.metadata
                    )
                
                return decision
            
            # Nessuna autenticazione disponibile
            else:
                return AccessDecision.DENY
                
        except Exception as e:
            print(f"❌ Errore autenticazione: {e}")
            return AccessDecision.ERROR
    
    async def _check_whitelist_access(self, card_event: CardEvent) -> Dict[str, Any]:
        """Controlla se la carta è in whitelist (accesso sempre autorizzato)"""
        try:
            # Usa la logica esistente di validate_card_offline ma controlla specificamente whitelist
            cache_result = await self.sync_manager.validate_card_offline(
                card_event.uid_formatted, 
                card_event.direction
            )
            
            # Verifica che cache_result non sia None
            if not cache_result:
                return {
                    'authorized': False,
                    'reason': 'Carta non trovata - non in whitelist',
                    'source': 'whitelist_check'
                }
            
            # Controlla se è whitelist dalla subscription_info
            subscription_info = cache_result.get('subscription_info', {})
            is_whitelist = subscription_info.get('in_white_list', False) or subscription_info.get('type') == 'whitelist'
            
            if is_whitelist:
                return {
                    'authorized': True,
                    'reason': 'Carta in whitelist - accesso sempre autorizzato (bypass IN/OUT)',
                    'customer_id': cache_result.get('customer_id'),
                    'customer_name': cache_result.get('customer_name'),
                    'subscription_info': subscription_info,
                    'source': 'whitelist'
                }
            else:
                return {
                    'authorized': False,
                    'reason': 'Non in whitelist',
                    'source': 'whitelist_check'
                }
                
        except Exception as e:
            print(f"❌ Errore controllo whitelist per {card_event.uid_formatted}: {e}")
            return {
                'authorized': False,
                'reason': f'Errore whitelist check: {str(e)}',
                'source': 'whitelist_check'
            }
    
    async def _send_parallel_mqtt_logging(self, card_event: CardEvent):
        """Invia MQTT in parallelo solo per logging (non per autorizzazione)"""
        try:
            auth_request = AuthRequest.from_card_event(
                card_event=card_event,
                tornello_id=self.config.system.tornello_id,
                auth_required=self.config.auth.enabled
            )
            
            mqtt_success = await self.mqtt_client.send_auth_request_parallel(auth_request)
            print(f"📡 MQTT logging parallelo {'✅' if mqtt_success else '⚠️'}: {card_event.uid_formatted}")
            
        except Exception as e:
            print(f"⚠️ Errore MQTT parallelo per {card_event.uid_formatted}: {e}")
    
    async def _log_authorized_access(self, card_event: CardEvent, result: Dict[str, Any], source: str = "cache"):
        """Log per accesso autorizzato"""
        if not self.sync_manager:
            return
            
        try:
            reason_suffix = " | Cache" if source == "cache" else " | Fallback"
            
            await self.sync_manager.log_access(
                card_uid=card_event.uid_formatted,
                direction=card_event.direction,
                result="authorized",
                reason=f"{result['reason']}{reason_suffix}",
                customer_id=result.get('customer_id'),
                customer_name=result.get('customer_name'),
                reader_type=card_event.reader_type,
                metadata=card_event.metadata
            )
            print(f"📝 Log autorizzato: {card_event.uid_formatted} ({source})")
            
        except Exception as e:
            print(f"❌ Errore logging autorizzato per {card_event.uid_formatted}: {e}")
    
    async def _log_denied_access(self, card_event: CardEvent, reason: str, source: str = "cache"):
        """Log per accesso negato"""
        if not self.sync_manager:
            return
            
        try:
            reason_suffix = " | Cache" if source == "cache" else " | Fallback"
            
            await self.sync_manager.log_access(
                card_uid=card_event.uid_formatted,
                direction=card_event.direction,
                result="denied",
                reason=f"{reason}{reason_suffix}",
                customer_id=None,
                reader_type=card_event.reader_type,
                metadata=card_event.metadata
            )
            print(f"📝 Log negato: {card_event.uid_formatted} ({source}) - {reason}")
            
        except Exception as e:
            print(f"❌ Errore logging negato per {card_event.uid_formatted}: {e}")
    
    def _check_internet_connectivity(self) -> bool:
        """Controlla velocemente se internet è disponibile"""
        try:
            import socket
            # Test veloce a DNS Google (timeout 3 secondi)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def _offline_authentication(self, card_uid: str) -> AccessDecision:
        """Autenticazione fallback quando server non raggiungibile"""
        if self.config.offline.allow_access:
            # FALLBACK STRATEGY: Permetti accesso se server non raggiungibile
            self.stats['offline_events'] += 1
            
            # 🔄 SMART CACHE REFRESH: Solo se connessione internet disponibile
            if card_uid not in self.auth_cache:
                print(f"🔄 Carta {card_uid} sconosciuta - controllo connettività per cache refresh...")
                
                # Controlla se connessione internet disponibile per tentare cache refresh
                if self._check_internet_connectivity():
                    print(f"🌐 Internet disponibile - tentativo cache refresh al server...")
                    try:
                        # Importa e usa cache refresh manager
                        from rfid_gate.network.cache_refresh_strategy import CacheRefreshManager
                        refresh_mgr = CacheRefreshManager(self.sync_manager)
                        
                        # Prova refresh per carta sconosciuta in background (non-bloccante)
                        import asyncio
                        if hasattr(asyncio, '_get_running_loop'):
                            try:
                                loop = asyncio.get_running_loop()
                                task = loop.create_task(refresh_mgr.handle_unknown_card_refresh(card_uid))
                                print(f"📡 Cache refresh avviato in background per {card_uid}")
                            except RuntimeError:
                                print(f"📡 Cache refresh non disponibile (no event loop)")
                        else:
                            print(f"📡 Cache refresh non disponibile (asyncio non supportato)")
                            
                    except Exception as e:
                        print(f"⚠️ Errore avvio cache refresh per {card_uid}: {e}")
                else:
                    print(f"❌ Internet non disponibile - cache refresh saltato")
                    print(f"💾 Fallback: accesso permesso usando solo cache locale per {card_uid}")
            
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
            
            # ========================================
            # 🔄 USA FACTORY METHOD LEGACY COMPATIBLE
            # ========================================
            auth_request = AuthRequest.from_card_event(
                card_event=card_event,
                tornello_id=self.config.system.tornello_id,
                auth_required=self.config.auth.enabled
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
            
            # Cleanup SyncManager
            if self.sync_manager:
                await self.sync_manager.stop_background_sync()
                # Ultima sync log se possibile
                if self.sync_manager.is_online:
                    await self.sync_manager._sync_logs()
            
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
    
    async def _direct_gate_verification(self, card_uid: str, direction: str) -> Dict[str, Any]:
        """
        Chiamata diretta a /api/gate-verification quando cache refresh fallisce.
        Questa è l'ultima risorsa quando la carta non è in cache e non è stata trovata dal sync.
        
        Returns:
            Dict con 'authorized', 'reason', 'card_data', etc.
        """
        try:
            import aiohttp
            import asyncio
            
            # URL endpoint dal config
            server_url = self.config.sync.cache_sync_server_url
            endpoint = os.getenv('GATE_VERIFICATION_ENDPOINT', '/api/gate-verification')
            url = f"{server_url}{endpoint}"
            
            # Payload per gate-verification (come da specifiche)
            payload = {
                "uid": card_uid,
                "direction": direction,
                "gate_id": self.config.system.tornello_id
            }
            
            print(f"🔗 Chiamata diretta gate-verification: {url}")
            print(f"📤 Payload: {payload}")
            
            timeout = aiohttp.ClientTimeout(total=self.config.sync.cache_sync_timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Estrai risultato
                        authorized = data.get('authorized', False)
                        message = data.get('message', 'Risposta gate-verification')
                        card_data = data.get('card_data', {})
                        
                        print(f"✅ Gate-verification risposta: authorized={authorized}, message='{message}'")
                        
                        return {
                            'authorized': authorized,
                            'reason': f"Gate-verification: {message}",
                            'card_data': card_data,
                            'customer_id': card_data.get('customer_id'),
                            'customer_name': card_data.get('customer_name'),
                            'subscription_info': card_data.get('subscription_info', {}),
                            'source': 'direct_gate_verification'
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ Gate-verification error {response.status}: {error_text}")
                        return {
                            'authorized': False,
                            'reason': f"Gate-verification error: HTTP {response.status}",
                            'source': 'direct_gate_verification'
                        }
                        
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout chiamata gate-verification per {card_uid}")
            return {
                'authorized': False,
                'reason': 'Gate-verification timeout',
                'source': 'direct_gate_verification'
            }
        except Exception as e:
            print(f"❌ Errore gate-verification per {card_uid}: {e}")
            return {
                'authorized': False,
                'reason': f'Gate-verification error: {str(e)}',
                'source': 'direct_gate_verification'
            }


# Export
__all__ = [
    'AccessControlSystem',
    'AccessEvent',
    'AccessDecision',
    'SystemMode'
]