#!/usr/bin/env python3
"""
🔌 Base Relay Controller - Abstract Interface
=============================================

Interfaccia unificata per tutti i tipi di relè.
Fornisce una base comune per GPIO relay e futuri controller.
"""

import asyncio
import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum


class RelayState(str, Enum):
    """Stati possibili del relè"""
    OFF = "off"
    ON = "on"
    ACTIVATING = "activating"
    ERROR = "error"


@dataclass
class RelayEvent:
    """Evento di attivazione relè"""
    relay_id: str              # ID del relè
    state: RelayState          # Stato corrente
    direction: str             # "in" o "out"
    timestamp: float           # Timestamp Unix
    duration: Optional[float] = None    # Durata attivazione (se ON)
    trigger_source: str = "unknown"    # Fonte che ha attivato il relè
    metadata: Dict[str, Any] = None    # Metadati aggiuntivi
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseRelayController(ABC):
    """
    Classe base astratta per tutti i controller relè.
    
    Implementa il pattern Template Method per:
    - Inizializzazione standardizzata
    - Gestione stati comune
    - Attivazione temporizzata
    - Monitoring
    """
    
    def __init__(self, relay_id: str, direction: str = "in"):
        self.relay_id = relay_id
        self.direction = direction
        self.state = RelayState.OFF
        self.last_activation_time = 0
        self.activation_count = 0
        self.total_on_time = 0
        self.start_time = time.time()
        
        # Configurazione default (Legacy System)
        self.active_time = 2.0  # Secondi
        self.active_low = True   # Legacy: relè attivo LOW (moduli con optoaccoppiatore)
        self.initial_state = "HIGH"  # Legacy: parte HIGH (relè spento)
        
        # Callbacks
        self.on_state_change: Optional[Callable[[RelayEvent], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Task attivazione corrente
        self._activation_task: Optional[asyncio.Task] = None
        
        # Thread attivazione (legacy-compatible)
        self._activation_thread: Optional[threading.Thread] = None
        self._thread_lock = threading.Lock()
        self._stop_thread = False
        
        # Statistiche
        self.stats = {
            'activations_total': 0,
            'activations_successful': 0,
            'activations_failed': 0,
            'total_on_time_seconds': 0,
            'average_on_time': 0,
            'uptime_seconds': 0
        }
    
    def set_state(self, state: RelayState, duration: Optional[float] = None, 
                  trigger_source: str = "system") -> None:
        """Aggiorna stato con callback"""
        if self.state != state:
            old_state = self.state
            self.state = state
            
            # Crea evento
            event = RelayEvent(
                relay_id=self.relay_id,
                state=state,
                direction=self.direction,
                timestamp=time.time(),
                duration=duration,
                trigger_source=trigger_source,
                metadata={
                    'previous_state': old_state.value,
                    'activation_count': self.activation_count
                }
            )
            
            if self.on_state_change:
                try:
                    self.on_state_change(event)
                except Exception as e:
                    print(f"❌ Errore callback state change: {e}")
    
    def update_stats(self) -> None:
        """Aggiorna statistiche"""
        self.stats['uptime_seconds'] = int(time.time() - self.start_time)
        if self.activation_count > 0:
            self.stats['average_on_time'] = self.total_on_time / self.activation_count
    
    @abstractmethod
    async def _hardware_init(self) -> bool:
        """
        Inizializzazione hardware specifica del relè.
        Da implementare nelle sottoclassi.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        pass
    
    @abstractmethod
    async def _hardware_set_state(self, state: bool) -> bool:
        """
        Imposta stato hardware specifico del relè.
        Da implementare nelle sottoclassi.
        
        Args:
            state: True per ON, False per OFF
            
        Returns:
            bool: True se operazione riuscita
        """
        pass
    
    @abstractmethod
    async def _hardware_cleanup(self) -> None:
        """
        Cleanup hardware specifico del relè.
        Da implementare nelle sottoclassi.
        """
        pass
    
    @abstractmethod
    def get_relay_type(self) -> str:
        """
        Restituisce il tipo di relè.
        Da implementare nelle sottoclassi.
        
        Returns:
            str: Tipo relè (es. "gpio", "i2c", "modbus")
        """
        pass
    
    def configure(self, active_time: float = None, active_low: bool = None, 
                 initial_state: str = None) -> None:
        """
        Configura parametri del relè.
        
        Args:
            active_time: Tempo attivazione in secondi
            active_low: True se relè attivo LOW
            initial_state: Stato iniziale ("LOW" o "HIGH")
        """
        if active_time is not None:
            self.active_time = max(0.1, active_time)
        if active_low is not None:
            self.active_low = active_low
        if initial_state is not None:
            self.initial_state = initial_state.upper()
        
        print(f"⚙️ {self.relay_id} configurato: {self.active_time}s, active_low={self.active_low}")
    
    async def initialize(self) -> bool:
        """
        Inizializzazione completa del relè.
        Template method che chiama _hardware_init.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            success = await self._hardware_init()
            
            if success:
                # Imposta stato iniziale
                initial_on = (self.initial_state == "HIGH")
                if self.active_low:
                    initial_on = not initial_on
                
                await self._hardware_set_state(initial_on)
                self.set_state(RelayState.ON if initial_on else RelayState.OFF, 
                             trigger_source="initialization")
                
                print(f"✅ {self.relay_id} ({self.get_relay_type()}) inizializzato")
                return True
            else:
                self.set_state(RelayState.ERROR, trigger_source="initialization")
                print(f"❌ {self.relay_id} inizializzazione fallita")
                return False
                
        except Exception as e:
            self.set_state(RelayState.ERROR, trigger_source="initialization")
            self.stats['activations_failed'] += 1
            
            if self.on_error:
                self.on_error(e)
            
            print(f"❌ {self.relay_id} errore inizializzazione: {e}")
            return False
    
    async def activate(self, duration: Optional[float] = None, 
                      trigger_source: str = "manual") -> bool:
        """
        Attiva relè per durata specificata (LEGACY-COMPATIBLE con threading).
        
        Args:
            duration: Durata attivazione (usa self.active_time se None)
            trigger_source: Fonte che ha attivato il relè
            
        Returns:
            bool: True se attivazione riuscita
        """
        if self.state == RelayState.ACTIVATING:
            print(f"⚠️ {self.relay_id} già in attivazione")
            return False
        
        duration = duration or self.active_time
        
        with self._thread_lock:
            # GESTIONE LEGACY-COMPATIBLE: Interrompi thread precedente
            if self._activation_thread and self._activation_thread.is_alive():
                print(f"🔄 {self.relay_id}: Interruzione thread precedente in corso...")
                self._stop_thread = True
                
                # Aspetta brevemente che il thread precedente si fermi
                old_thread = self._activation_thread
                self._activation_thread = None
                
                # Release lock temporaneamente per permettere al thread di terminare
                self._thread_lock.release()
                try:
                    # Breve attesa per permettere al thread di vedere _stop_thread
                    time.sleep(0.05)  # 50ms dovrebbero bastare
                    
                    # Se il thread è ancora vivo dopo il timeout, procedi comunque
                    if old_thread.is_alive():
                        print(f"⚠️ {self.relay_id}: Thread precedente ancora attivo, procedo comunque")
                    else:
                        print(f"✅ {self.relay_id}: Thread precedente terminato correttamente")
                        
                finally:
                    self._thread_lock.acquire()
            
            # Reset flag per nuovo thread
            self._stop_thread = False
            
        try:
            self.set_state(RelayState.ACTIVATING, duration, trigger_source)
            self.stats['activations_total'] += 1
            
            print(f"🧵 {self.relay_id}: Avvio nuovo thread per {duration}s...")
            
            # Crea Thread per attivazione temporizzata (COME NEL LEGACY)
            self._activation_thread = threading.Thread(
                target=self._thread_activation_worker,
                args=(duration, trigger_source),
                daemon=False  # Non daemon per garantire completamento
            )
            self._activation_thread.start()
            
            return True
            
        except Exception as e:
            self.set_state(RelayState.ERROR, trigger_source=trigger_source)
            self.stats['activations_failed'] += 1
            
            if self.on_error:
                self.on_error(e)
            
            print(f"❌ {self.relay_id} errore attivazione: {e}")
            return False
    
    def _thread_activation_worker(self, duration: float, trigger_source: str) -> None:
        """Worker thread per attivazione temporizzata (IDENTICO AL LEGACY)"""
        current_thread = threading.current_thread()
        thread_name = current_thread.name
        
        print(f"🧵 THREAD START: {self.relay_id} worker avviato (ID: {thread_name})")
        
        try:
            start_time = time.time()
            
            # Attiva relè (sincrono diretto come nel legacy)
            target_state = not self.active_low  # ON
            print(f"🔛 {self.relay_id}: Tentativo attivazione (target_state={target_state}, active_low={self.active_low})")
            
            success = self._sync_hardware_set_state(target_state)
            
            if not success:
                print(f"❌ {self.relay_id}: Fallimento attivazione hardware")
                raise Exception("Fallimento attivazione hardware")
            
            self.set_state(RelayState.ON, duration, trigger_source)
            self.last_activation_time = start_time
            self.activation_count += 1
            
            print(f"⚡ {self.relay_id}: ON per {duration}s (thread {thread_name})")
            
            # Aspetta con controlli di interruzione (COME NEL LEGACY)
            elapsed = 0
            check_count = 0
            while elapsed < duration:
                with self._thread_lock:
                    if self._stop_thread:
                        print(f"🛑 {self.relay_id}: Thread interrotto da _stop_thread")
                        return
                
                sleep_time = min(0.1, duration - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time
                check_count += 1
                
                # Log ogni secondo per debug
                if check_count % 10 == 0:
                    print(f"⏱️  {self.relay_id}: T+{elapsed:.1f}s (thread {thread_name} attivo)")
            
            print(f"⏰ {self.relay_id}: Timer completato dopo {elapsed:.2f}s - Disattivazione...")
            
            # Disattiva relè
            with self._thread_lock:
                if not self._stop_thread:
                    target_state = self.active_low  # OFF
                    print(f"🔛 {self.relay_id}: Tentativo disattivazione (target_state={target_state})")
                    
                    success = self._sync_hardware_set_state(target_state)
                    
                    if not success:
                        print(f"❌ {self.relay_id}: Fallimento disattivazione hardware")
                        raise Exception("Fallimento disattivazione hardware")
                    
                    # Aggiorna statistiche
                    actual_duration = time.time() - start_time
                    self.total_on_time += actual_duration
                    self.stats['activations_successful'] += 1
                    self.stats['total_on_time_seconds'] = self.total_on_time
                    
                    self.set_state(RelayState.OFF, trigger_source=trigger_source)
                    print(f"✅ {self.relay_id}: OFF dopo {actual_duration:.2f}s (thread {thread_name})")
                else:
                    print(f"🛑 {self.relay_id}: Disattivazione saltata - thread fermato")
            
        except Exception as e:
            print(f"💥 {self.relay_id}: EXCEPTION nel thread {thread_name}: {e}")
            with self._thread_lock:
                # Spegni in caso di errore
                try:
                    print(f"🔧 {self.relay_id}: Tentativo spegnimento di emergenza...")
                    self._sync_hardware_set_state(self.active_low)
                    print(f"✅ {self.relay_id}: Spegnimento di emergenza completato")
                except Exception as emergency_e:
                    print(f"💥 {self.relay_id}: ERRORE anche nello spegnimento di emergenza: {emergency_e}")
                
                self.set_state(RelayState.ERROR, trigger_source=trigger_source)
                self.stats['activations_failed'] += 1
                
                if self.on_error:
                    self.on_error(e)
                
                print(f"❌ {self.relay_id} errore durante attivazione thread: {e}")
        
        finally:
            print(f"🧵 THREAD END: {self.relay_id} worker terminato (ID: {thread_name})")
    
    @abstractmethod
    def _sync_hardware_set_state(self, state: bool) -> bool:
        """
        Versione sincrona per threading di _hardware_set_state.
        Da implementare nelle sottoclassi per compatibilità legacy.
        
        Args:
            state: True per ON, False per OFF
            
        Returns:
            bool: True se operazione riuscita
        """
        pass
    
    async def _timed_activation(self, duration: float, trigger_source: str) -> None:
        """Gestisce attivazione temporizzata"""
        try:
            start_time = time.time()
            
            # Attiva relè
            target_state = not self.active_low  # ON
            success = await self._hardware_set_state(target_state)
            
            if not success:
                raise Exception("Fallimento attivazione hardware")
            
            self.set_state(RelayState.ON, duration, trigger_source)
            self.last_activation_time = start_time
            self.activation_count += 1
            
            # Attendi durata
            await asyncio.sleep(duration)
            
            # Disattiva relè
            target_state = self.active_low  # OFF
            success = await self._hardware_set_state(target_state)
            
            if not success:
                raise Exception("Fallimento disattivazione hardware")
            
            # Aggiorna statistiche
            actual_duration = time.time() - start_time
            self.total_on_time += actual_duration
            self.stats['activations_successful'] += 1
            self.stats['total_on_time_seconds'] = self.total_on_time
            
            self.set_state(RelayState.OFF, trigger_source=trigger_source)
            
            print(f"✅ {self.relay_id} attivazione completata ({actual_duration:.2f}s)")
            
        except asyncio.CancelledError:
            # Attivazione cancellata, spegni relè
            try:
                await self._hardware_set_state(self.active_low)
                self.set_state(RelayState.OFF, trigger_source="cancelled")
                print(f"🚫 {self.relay_id} attivazione cancellata")
            except Exception as e:
                print(f"❌ {self.relay_id} errore durante cancellazione: {e}")
        except Exception as e:
            self.set_state(RelayState.ERROR, trigger_source=trigger_source)
            self.stats['activations_failed'] += 1
            
            if self.on_error:
                self.on_error(e)
            
            print(f"❌ {self.relay_id} errore durante attivazione: {e}")
    
    async def force_off(self) -> bool:
        """Forza spegnimento relè (legacy-compatible)"""
        try:
            # Ferma thread se attivo
            with self._thread_lock:
                if self._activation_thread and self._activation_thread.is_alive():
                    self._stop_thread = True
                    # Non fare join per evitare blocchi
            
            # Cancella anche task async se presente (backward compatibility)
            if self._activation_task and not self._activation_task.done():
                self._activation_task.cancel()
                await asyncio.sleep(0.1)  # Attendi cancellazione
            
            # Spegni hardware
            success = await self._hardware_set_state(self.active_low)
            
            if success:
                self.set_state(RelayState.OFF, trigger_source="force_off")
                print(f"🔴 {self.relay_id} forzato OFF")
                return True
            else:
                self.set_state(RelayState.ERROR, trigger_source="force_off")
                return False
                
        except Exception as e:
            self.set_state(RelayState.ERROR, trigger_source="force_off")
            
            if self.on_error:
                self.on_error(e)
            
            print(f"❌ {self.relay_id} errore force off: {e}")
            return False
    
    async def cleanup(self) -> None:
        """
        Cleanup completo del relè.
        Template method che chiama _hardware_cleanup.
        """
        try:
            # Cancella attivazioni in corso
            if self._activation_task and not self._activation_task.done():
                self._activation_task.cancel()
                try:
                    await self._activation_task
                except asyncio.CancelledError:
                    pass
            
            # Spegni relè
            await self.force_off()
            
            # Cleanup hardware
            await self._hardware_cleanup()
            
            print(f"🧹 {self.relay_id} cleanup completato")
            
        except Exception as e:
            print(f"❌ {self.relay_id} errore cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche del relè.
        
        Returns:
            Dict[str, Any]: Statistiche complete
        """
        self.update_stats()
        return {
            **self.stats,
            'relay_id': self.relay_id,
            'relay_type': self.get_relay_type(),
            'direction': self.direction,
            'state': self.state.value,
            'active_time': self.active_time,
            'active_low': self.active_low,
            'last_activation_time': self.last_activation_time,
            'is_active': self.state == RelayState.ON
        }
    
    def is_active(self) -> bool:
        """Verifica se relè è attualmente attivo"""
        return self.state == RelayState.ON
    
    async def close(self) -> None:
        """
        Chiude relè e libera risorse.
        Metodo richiesto per compatibilità con shutdown del sistema.
        """
        try:
            # Ferma thread attivo
            with self._thread_lock:
                self._stop_thread = True
            
            # Aspetta che il thread finisca (con timeout)
            if self._activation_thread and self._activation_thread.is_alive():
                self._activation_thread.join(timeout=1.0)
            
            # Spegni hardware
            await self._hardware_set_state(self.active_low)  # OFF
            
            # Cleanup hardware
            await self._hardware_cleanup()
            
            self.set_state(RelayState.OFF, trigger_source="system_shutdown")
            print(f"🔌 {self.relay_id}: Chiuso")
            
        except Exception as e:
            print(f"❌ Errore chiusura {self.relay_id}: {e}")
    
    def reset_stats(self) -> None:
        """Reset statistiche"""
        self.stats = {
            'activations_total': 0,
            'activations_successful': 0,
            'activations_failed': 0,
            'total_on_time_seconds': 0,
            'average_on_time': 0,
            'uptime_seconds': 0
        }
        self.activation_count = 0
        self.total_on_time = 0
        self.start_time = time.time()
    
    def __str__(self) -> str:
        return f"{self.get_relay_type()}({self.relay_id}, {self.direction}, {self.state.value})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(relay_id='{self.relay_id}', "
                f"direction='{self.direction}', state='{self.state.value}')")


# Export
__all__ = [
    'BaseRelayController',
    'RelayEvent',
    'RelayState'
]