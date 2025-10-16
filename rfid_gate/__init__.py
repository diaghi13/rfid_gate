"""
RFID Gate System - Modular Architecture
======================================

Sistema modulare per controllo accessi con lettori RFID.

Modules:
    - core: Business logic principale
    - hardware: Astrazione hardware (lettori, relè)
    - network: Comunicazione (MQTT, offline)
    - config: Gestione configurazione
    - utils: Utilità generiche
    - logging: Sistema logging avanzato
"""

__version__ = "2.0.0"

from rfid_gate.core.access_control import AccessControlSystem
from rfid_gate.config.settings import RFIDGateConfig

__all__ = [
    'AccessControlSystem',
    'RFIDGateConfig'
]