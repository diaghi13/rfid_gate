#!/usr/bin/env python3
"""
🚀 RFID Gate System - Main Entry Point (Refactored)
==================================================

Entry point principale del sistema refactored con:
- Compatibilità totale con il sistema esistente
- Architettura modulare moderna
- Async/await support
- Configurazione type-safe
- Graceful shutdown

Mantiene tutti i comportamenti del sistema originale.
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Aggiungi il path del modulo rfid_gate
sys.path.insert(0, str(Path(__file__).parent))

# Import del nuovo sistema
from rfid_gate import AccessControlSystem, RFIDGateConfig
from rfid_gate.config.settings import Config  # Compatibilità


class RFIDGateApplication:
    """
    Applicazione principale RFID Gate.
    
    Wrapper che mantiene compatibilità con l'interfaccia esistente
    ma usa internamente l'architettura refactored.
    """
    
    def __init__(self):
        self.system: AccessControlSystem = None
        self.shutdown_event = asyncio.Event()
        self.is_running = False
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        print("🎯 RFID Gate Application inizializzata")
    
    def _setup_signal_handlers(self):
        """Configura gestione segnali per shutdown graceful"""
        def signal_handler(signum, frame):
            print(f"\\n🛑 Ricevuto segnale {signum}")
            if self.is_running:
                asyncio.create_task(self._graceful_shutdown())
        
        # Registra handlers per SIGINT e SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _graceful_shutdown(self):
        """Shutdown graceful del sistema"""
        print("🛑 Avvio shutdown graceful...")
        self.is_running = False
        self.shutdown_event.set()
        
        if self.system:
            # Ferma il sistema (questo fermerà i loop di lettura)
            self.system.is_running = False
            await self.system.stop()
    
    async def run(self):
        """
        Avvia l'applicazione RFID Gate.
        
        Metodo principale che:
        1. Inizializza il sistema
        2. Avvia il loop principale
        3. Gestisce shutdown graceful
        """
        try:
            print("🚀 Avvio RFID Gate System")
            print("=" * 50)
            
            # Mostra configurazione (compatibilità)
            self._print_configuration()
            
            # Crea e inizializza sistema
            self.system = AccessControlSystem()
            
            # Setup callbacks per logging compatibile
            self.system.on_access_event = self._on_access_event
            self.system.on_mode_change = self._on_mode_change
            
            # Inizializza e avvia sistema (questo include il loop di lettura)
            self.is_running = True
            success = await self.system.run()
            
            return success
            
        except KeyboardInterrupt:
            print("\\n🛑 Interruzione da tastiera")
            await self._graceful_shutdown()
            return True
        except Exception as e:
            print(f"❌ Errore applicazione: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.system:
                await self.system.stop()
    
    def _print_configuration(self):
        """Stampa configurazione sistema (compatibilità)"""
        print("📄 Configurazione Sistema:")
        print(f"   MQTT Broker: {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
        print(f"   Tornello ID: {Config.TORNELLO_ID}")
        print(f"   Modalità Bidirezionale: {Config.BIDIRECTIONAL_MODE}")
        
        if Config.ENABLE_IN_READER:
            print(f"   Lettore IN: {Config.RFID_IN_READER_TYPE.upper()}")
            if Config.RFID_IN_READER_TYPE == 'pn532':
                print(f"      Interfaccia: {Config.RFID_IN_PN532_INTERFACE.upper()}")
        
        if Config.ENABLE_OUT_READER:
            print(f"   Lettore OUT: {Config.RFID_OUT_READER_TYPE.upper()}")
            if Config.RFID_OUT_READER_TYPE == 'pn532':
                print(f"      Interfaccia: {Config.RFID_OUT_PN532_INTERFACE.upper()}")
        
        if Config.RELAY_IN_ENABLE:
            print(f"   Relè IN: Pin {Config.RELAY_IN_PIN} ({Config.RELAY_IN_ACTIVE_TIME}s)")
        
        if Config.RELAY_OUT_ENABLE:
            print(f"   Relè OUT: Pin {Config.RELAY_OUT_PIN} ({Config.RELAY_OUT_ACTIVE_TIME}s)")
        
        print(f"   Formato UID: {Config.UID_FORMAT_MODE} (chars: {Config.UID_CHARS_COUNT})")
        print()
    
    def _on_access_event(self, event):
        """Callback evento accesso (compatibilità con logging esistente)"""
        # Mantiene il formato di logging esistente
        timestamp_str = f"{event.timestamp:.2f}"
        
        if event.decision.value == "grant":
            print(f"✅ [{timestamp_str}] ACCESSO AUTORIZZATO: {event.card_uid} ({event.direction})")
        elif event.decision.value == "deny":
            print(f"❌ [{timestamp_str}] ACCESSO NEGATO: {event.card_uid} ({event.direction})")
        elif event.decision.value == "offline":
            print(f"📴 [{timestamp_str}] ACCESSO OFFLINE: {event.card_uid} ({event.direction})")
        else:
            print(f"⚠️ [{timestamp_str}] ERRORE ACCESSO: {event.card_uid} ({event.direction})")
    
    def _on_mode_change(self, old_mode, new_mode):
        """Callback cambio modalità sistema"""
        print(f"🔄 MODALITÀ SISTEMA: {old_mode.value.upper()} → {new_mode.value.upper()}")


# Funzioni di compatibilità con il sistema esistente
def main():
    """
    Funzione main per compatibilità.
    Identica all'interfaccia del main.py originale.
    """
    print("🎯 RFID Gate System - Versione Refactored")
    print("Compatibilità totale con sistema esistente")
    print("=" * 50)
    
    # Verifica Python version
    if sys.version_info < (3, 7):
        print("❌ Richiesto Python 3.7 o superiore")
        sys.exit(1)
    
    try:
        # Crea e avvia applicazione
        app = RFIDGateApplication()
        
        # Avvia loop asincrono
        result = asyncio.run(app.run())
        
        if result:
            print("✅ Sistema terminato correttamente")
            sys.exit(0)
        else:
            print("❌ Sistema terminato con errori")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Errore critico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()