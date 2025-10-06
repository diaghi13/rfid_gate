#!/usr/bin/env python3
"""
⏱️ Global Debounce Manager
==========================

Sistema di debounce globale per prevenire letture duplicate
tra lettori multipli e gestire anti-crosstalk.
"""

import time
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DebounceEntry:
    """Entry del sistema di debounce"""
    uid: str
    direction: str
    timestamp: float
    reader_id: Optional[str] = None


class GlobalDebounceManager:
    """
    Manager globale per debounce tra lettori multipli.
    
    Previene:
    - Letture duplicate dello stesso reader
    - Crosstalk tra reader vicini
    - Letture rapide consecutive
    """
    
    def __init__(self, global_debounce_time: float = 0.8):
        self.global_debounce_time = global_debounce_time
        self.last_reads: Dict[str, DebounceEntry] = {}  # Key: direction
        self.global_last_read: Optional[DebounceEntry] = None
        
        # Statistiche
        self.stats = {
            'total_checks': 0,
            'duplicates_detected': 0,
            'global_blocks': 0,
            'direction_blocks': 0
        }
    
    def is_duplicate(self, uid: str, direction: str, reader_id: str = None) -> bool:
        """
        Verifica se la lettura è un duplicato.
        
        Args:
            uid: UID della carta
            direction: Direzione del lettore ("in" o "out")
            reader_id: ID del lettore (opzionale)
            
        Returns:
            bool: True se è un duplicato da ignorare
        """
        current_time = time.time()
        self.stats['total_checks'] += 1
        
        # 1. Check debounce globale (anti-crosstalk)
        if self.global_last_read:
            time_diff = current_time - self.global_last_read.timestamp
            
            # Se è la stessa carta letta entro il tempo globale
            if (self.global_last_read.uid == uid and 
                time_diff < self.global_debounce_time):
                
                self.stats['duplicates_detected'] += 1
                self.stats['global_blocks'] += 1
                return True
        
        # 2. Check debounce per direzione specifica
        if direction in self.last_reads:
            last_read = self.last_reads[direction]
            time_diff = current_time - last_read.timestamp
            
            # Se è la stessa carta nella stessa direzione
            if (last_read.uid == uid and 
                time_diff < self.global_debounce_time):
                
                self.stats['duplicates_detected'] += 1
                self.stats['direction_blocks'] += 1
                return True
        
        # Non è un duplicato - registra lettura
        entry = DebounceEntry(
            uid=uid,
            direction=direction,
            timestamp=current_time,
            reader_id=reader_id
        )
        
        self.last_reads[direction] = entry
        self.global_last_read = entry
        
        return False
    
    def get_last_read(self, direction: str = None) -> Optional[DebounceEntry]:
        """
        Ottieni ultima lettura.
        
        Args:
            direction: Direzione specifica o None per globale
            
        Returns:
            Optional[DebounceEntry]: Ultima lettura o None
        """
        if direction:
            return self.last_reads.get(direction)
        else:
            return self.global_last_read
    
    def clear_direction(self, direction: str) -> None:
        """Pulisce debounce per direzione specifica"""
        self.last_reads.pop(direction, None)
    
    def clear_all(self) -> None:
        """Pulisce tutto il debounce"""
        self.last_reads.clear()
        self.global_last_read = None
    
    def get_stats(self) -> Dict[str, any]:
        """Statistiche debounce"""
        return {
            **self.stats,
            'global_debounce_time': self.global_debounce_time,
            'tracked_directions': list(self.last_reads.keys()),
            'last_global_read': {
                'uid': self.global_last_read.uid if self.global_last_read else None,
                'direction': self.global_last_read.direction if self.global_last_read else None,
                'timestamp': self.global_last_read.timestamp if self.global_last_read else None
            }
        }
    
    def set_debounce_time(self, debounce_time: float) -> None:
        """Aggiorna tempo di debounce"""
        self.global_debounce_time = max(0.1, debounce_time)
    
    def get_time_since_last_read(self, direction: str = None) -> Optional[float]:
        """
        Tempo trascorso dall'ultima lettura.
        
        Args:
            direction: Direzione specifica o None per globale
            
        Returns:
            Optional[float]: Secondi dall'ultima lettura o None
        """
        last_read = self.get_last_read(direction)
        if last_read:
            return time.time() - last_read.timestamp
        return None


# Export
__all__ = [
    'GlobalDebounceManager',
    'DebounceEntry'
]