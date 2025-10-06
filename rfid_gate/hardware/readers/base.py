#!/usr/bin/env python3
"""
🔌 Base RFID Reader - Abstract Interface
=====================================

Interfaccia unificata per tutti i tipi di lettori RFID.
Fornisce una base comune per MFRC522, PN532 e futuri lettori.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum


class ReaderStatus(str, Enum):
    """Stati possibili del lettore"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    READING = "reading"
    ERROR = "error"


@dataclass
class CardEvent:
    """Evento di lettura carta"""
    uid: str                    # UID raw della carta
    uid_formatted: str          # UID formattato secondo configurazione
    reader_id: str              # ID del lettore che ha letto
    direction: str              # "in" o "out"
    timestamp: float            # Timestamp Unix
    reader_type: str            # Tipo lettore (mfrc522, pn532)
    raw_data: Optional[bytes] = None    # Dati raw originali
    metadata: Dict[str, Any] = None     # Metadati aggiuntivi
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseRFIDReader(ABC):
    """
    Classe base astratta per tutti i lettori RFID.
    
    Implementa il pattern Template Method per:
    - Inizializzazione standardizzata
    - Gestione errori comune  
    - Formattazione UID consistente
    - Debouncing automatico
    - Status monitoring
    """
    
    def __init__(self, reader_id: str, direction: str = "in"):
        self.reader_id = reader_id
        self.direction = direction
        self.status = ReaderStatus.DISCONNECTED
        self.last_card_time = 0
        self.last_card_uid = ""
        self.debounce_time = 2.0
        self.error_count = 0
        self.read_count = 0
        self.start_time = time.time()
        
        # Callbacks
        self.on_card_read: Optional[Callable[[CardEvent], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_status_change: Optional[Callable[[ReaderStatus], None]] = None
        
        # Statistiche
        self.stats = {
            'reads_total': 0,
            'reads_valid': 0,
            'reads_debounced': 0,
            'errors_total': 0,
            'uptime_seconds': 0
        }
    
    def set_status(self, status: ReaderStatus) -> None:
        """Aggiorna status con callback"""
        if self.status != status:
            old_status = self.status
            self.status = status
            if self.on_status_change:
                try:
                    self.on_status_change(status)
                except Exception as e:
                    print(f"❌ Errore callback status change: {e}")
    
    def update_stats(self) -> None:
        """Aggiorna statistiche"""
        self.stats['uptime_seconds'] = int(time.time() - self.start_time)
    
    @abstractmethod
    async def _hardware_init(self) -> bool:
        """
        Inizializzazione hardware specifica del lettore.
        Da implementare nelle sottoclassi.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        pass
    
    @abstractmethod
    async def _hardware_read(self) -> Optional[bytes]:
        """
        Lettura hardware specifica del lettore.
        Da implementare nelle sottoclassi.
        
        Returns:
            Optional[bytes]: Dati raw della carta o None se nessuna carta
        """
        pass
    
    @abstractmethod
    async def _hardware_cleanup(self) -> None:
        """
        Cleanup hardware specifico del lettore.
        Da implementare nelle sottoclassi.
        """
        pass
    
    @abstractmethod 
    def get_reader_type(self) -> str:
        """
        Restituisce il tipo di lettore.
        Da implementare nelle sottoclassi.
        
        Returns:
            str: Tipo lettore (es. "mfrc522", "pn532")
        """
        pass
    
    def format_card_uid(self, raw_data: bytes, format_mode: str = "remove_suffix", 
                       chars_count: int = 2, target_length: int = 8) -> str:
        """
        Formatta UID della carta secondo la configurazione.
        
        Args:
            raw_data: Dati raw della carta
            format_mode: Modalità formattazione ("remove_suffix", "fixed_length", "raw")
            chars_count: Numero caratteri da rimuovere/aggiungere
            target_length: Lunghezza target per fixed_length
            
        Returns:
            str: UID formattato
        """
        if not raw_data:
            return ""
        
        # Converti in hex string maiuscolo
        hex_str = ''.join([f'{b:02X}' for b in raw_data])
        
        if format_mode == "raw":
            return hex_str
        elif format_mode == "remove_suffix":
            if len(hex_str) > chars_count:
                return hex_str[:-chars_count]
            return hex_str
        elif format_mode == "fixed_length":
            if len(hex_str) > target_length:
                return hex_str[:target_length]
            elif len(hex_str) < target_length:
                return hex_str.ljust(target_length, '0')
            return hex_str
        else:
            return hex_str
    
    def is_duplicate_read(self, uid: str, debounce_time: float = None) -> bool:
        """
        Verifica se la lettura è un duplicato (debouncing).
        
        Args:
            uid: UID della carta letta
            debounce_time: Tempo debounce (usa self.debounce_time se None)
            
        Returns:
            bool: True se è un duplicato
        """
        current_time = time.time()
        debounce = debounce_time or self.debounce_time
        
        if (uid == self.last_card_uid and 
            current_time - self.last_card_time < debounce):
            self.stats['reads_debounced'] += 1
            return True
        
        self.last_card_uid = uid
        self.last_card_time = current_time
        return False
    
    async def initialize(self) -> bool:
        """
        Inizializzazione completa del lettore.
        Template method che chiama _hardware_init.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            self.set_status(ReaderStatus.CONNECTING)
            
            success = await self._hardware_init()
            
            if success:
                self.set_status(ReaderStatus.CONNECTED)
                print(f"✅ {self.reader_id} ({self.get_reader_type()}) inizializzato")
                return True
            else:
                self.set_status(ReaderStatus.ERROR)
                print(f"❌ {self.reader_id} inizializzazione fallita")
                return False
                
        except Exception as e:
            self.set_status(ReaderStatus.ERROR)
            self.error_count += 1
            self.stats['errors_total'] += 1
            
            if self.on_error:
                self.on_error(e)
            
            print(f"❌ {self.reader_id} errore inizializzazione: {e}")
            return False
    
    async def read_card(self, timeout: float = 0.1, 
                       format_config: Optional[Dict[str, Any]] = None) -> Optional[CardEvent]:
        """
        Lettura carta con timeout e formattazione.
        Template method che chiama _hardware_read.
        
        Args:
            timeout: Timeout per la lettura
            format_config: Configurazione formattazione UID
            
        Returns:
            Optional[CardEvent]: Evento carta o None se nessuna carta/timeout
        """
        if self.status != ReaderStatus.CONNECTED:
            return None
        
        try:
            self.set_status(ReaderStatus.READING)
            self.stats['reads_total'] += 1
            
            # Leggi dati hardware con timeout
            raw_data = await asyncio.wait_for(self._hardware_read(), timeout=timeout)
            
            self.set_status(ReaderStatus.CONNECTED)
            
            if not raw_data:
                return None
            
            # Formatta UID
            uid_raw = ''.join([f'{b:02X}' for b in raw_data])
            
            if format_config:
                uid_formatted = self.format_card_uid(
                    raw_data,
                    format_config.get('mode', 'remove_suffix'),
                    format_config.get('chars_count', 2),
                    format_config.get('target_length', 8)
                )
            else:
                uid_formatted = self.format_card_uid(raw_data)
            
            # Verifica debouncing
            if self.is_duplicate_read(uid_formatted):
                return None
            
            # Crea evento
            event = CardEvent(
                uid=uid_raw,
                uid_formatted=uid_formatted,
                reader_id=self.reader_id,
                direction=self.direction,
                timestamp=time.time(),
                reader_type=self.get_reader_type(),
                raw_data=raw_data,
                metadata={
                    'read_count': self.read_count,
                    'error_count': self.error_count
                }
            )
            
            self.read_count += 1
            self.stats['reads_valid'] += 1
            
            # Callback
            if self.on_card_read:
                try:
                    self.on_card_read(event)
                except Exception as e:
                    print(f"❌ Errore callback card read: {e}")
            
            return event
            
        except asyncio.TimeoutError:
            self.set_status(ReaderStatus.CONNECTED)
            return None
        except Exception as e:
            self.set_status(ReaderStatus.ERROR)
            self.error_count += 1
            self.stats['errors_total'] += 1
            
            if self.on_error:
                try:
                    self.on_error(e)
                except Exception as callback_error:
                    print(f"❌ Errore callback error: {callback_error}")
            
            print(f"❌ {self.reader_id} errore lettura: {e}")
            return None
    
    async def cleanup(self) -> None:
        """
        Cleanup completo del lettore.
        Template method che chiama _hardware_cleanup.
        """
        try:
            await self._hardware_cleanup()
            self.set_status(ReaderStatus.DISCONNECTED)
            print(f"🧹 {self.reader_id} cleanup completato")
        except Exception as e:
            print(f"❌ {self.reader_id} errore cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche del lettore.
        
        Returns:
            Dict[str, Any]: Statistiche complete
        """
        self.update_stats()
        return {
            **self.stats,
            'reader_id': self.reader_id,
            'reader_type': self.get_reader_type(),
            'direction': self.direction,
            'status': self.status.value,
            'last_card_time': self.last_card_time,
            'last_card_uid': self.last_card_uid,
            'error_rate': self.error_count / max(self.read_count, 1)
        }
    
    def set_debounce_time(self, debounce_time: float) -> None:
        """Imposta tempo di debounce"""
        self.debounce_time = max(0.0, debounce_time)
    
    def reset_stats(self) -> None:
        """Reset statistiche"""
        self.stats = {
            'reads_total': 0,
            'reads_valid': 0,
            'reads_debounced': 0,
            'errors_total': 0,
            'uptime_seconds': 0
        }
        self.read_count = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def __str__(self) -> str:
        return f"{self.get_reader_type()}({self.reader_id}, {self.direction}, {self.status.value})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(reader_id='{self.reader_id}', "
                f"direction='{self.direction}', status='{self.status.value}')")


# Export
__all__ = [
    'BaseRFIDReader',
    'CardEvent', 
    'ReaderStatus'
]