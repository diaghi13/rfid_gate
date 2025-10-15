#!/usr/bin/env python3
"""
📡 RFID Card Reader Monitor - Live Display
========================================

Monitora e visualizza in tempo reale le letture delle card RFID
da entrambi i lettori (IN e OUT) con informazioni dettagliate.
"""

import sys
import asyncio
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RFIDCardMonitor:
    """Monitor per letture card RFID in tempo reale"""
    
    def __init__(self):
        self.is_running = False
        self.access_control = None
        self.card_count = 0
        self.total_reads = {'in': 0, 'out': 0}
        
    async def initialize(self):
        """Inizializza il sistema di controllo accessi"""
        try:
            print("🔧 Inizializzazione sistema RFID...")
            
            from rfid_gate.core.access_control import AccessControlSystem
            from rfid_gate.config.settings import RFIDGateConfig
            
            # Carica configurazione
            config = RFIDGateConfig.from_env()
            print(f"✅ Configurazione caricata: {config.system.tornello_id}")
            
            # Crea sistema controllo accessi
            self.access_control = AccessControlSystem(config)
            
            # Imposta callback per catturare eventi card
            self._setup_card_callbacks()
            
            # Inizializza sistema
            init_result = await self.access_control.initialize()
            if not init_result:
                print("❌ Errore inizializzazione sistema")
                return False
                
            print("✅ Sistema RFID inizializzato")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _setup_card_callbacks(self):
        """Imposta callback per catturare eventi di lettura card"""
        if not self.access_control:
            return
            
        # Hook nel processo card event per catturare le letture
        original_process = self.access_control._process_card_event
        
        async def monitor_card_event(card_event):
            """Wrapper per catturare e visualizzare eventi card"""
            await self._display_card_event(card_event)
            return await original_process(card_event)
        
        # Sostituisci il metodo
        self.access_control._process_card_event = monitor_card_event
    
    async def _display_card_event(self, card_event):
        """Visualizza evento di lettura card"""
        try:
            self.card_count += 1
            self.total_reads[card_event.direction] += 1
            
            # Timestamp formattato
            timestamp = datetime.fromtimestamp(card_event.timestamp)
            time_str = timestamp.strftime("%H:%M:%S")
            
            # Direzione con icona
            direction_icon = "📥" if card_event.direction == "in" else "📤"
            direction_str = f"{direction_icon} {card_event.direction.upper()}"
            
            # Reader type con icona
            reader_icon = "🔵" if card_event.reader_type == "pn532" else "🟡"
            reader_str = f"{reader_icon} {card_event.reader_type.upper()}"
            
            print("=" * 70)
            print(f"🎯 CARD #{self.card_count} - {time_str}")
            print("=" * 70)
            print(f"📇 UID Formattato: {card_event.uid_formatted}")
            print(f"🔢 UID Raw:        {card_event.uid}")
            print(f"🚪 Direzione:      {direction_str}")
            print(f"📡 Reader:         {reader_str} ({card_event.reader_id})")
            print(f"⏱️  Timestamp:      {timestamp.isoformat()}")
            
            # Metadati se disponibili
            if card_event.metadata:
                print(f"📊 Metadati:")
                for key, value in card_event.metadata.items():
                    print(f"   - {key}: {value}")
            
            # Statistiche
            total_cards = sum(self.total_reads.values())
            print(f"📈 Statistiche: IN={self.total_reads['in']}, OUT={self.total_reads['out']}, TOTALE={total_cards}")
            print("=" * 70)
            print()
            
        except Exception as e:
            print(f"❌ Errore display card: {e}")
    
    async def start_monitoring(self):
        """Avvia il monitoraggio"""
        if not self.access_control:
            print("❌ Sistema non inizializzato")
            return
            
        try:
            print("🎬 AVVIO MONITORAGGIO RFID")
            print("=" * 70)
            print("📡 Monitor RFID Card Reader attivo")
            print("💡 Avvicina le card ai lettori RFID...")
            print("⏹️  Premi Ctrl+C per uscire")
            print("=" * 70)
            print()
            
            self.is_running = True
            
            # Avvia sistema controllo accessi
            await self.access_control.start()
            
            # Mantieni il sistema in esecuzione
            while self.is_running:
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n⏹️ Interruzione richiesta dall'utente")
        except Exception as e:
            print(f"\n❌ Errore durante monitoraggio: {e}")
        finally:
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Ferma il monitoraggio"""
        try:
            print("\n🛑 Arresto monitoraggio...")
            self.is_running = False
            
            if self.access_control:
                await self.access_control.stop()
                
            print("✅ Monitoraggio fermato")
            
            # Statistiche finali
            total_cards = sum(self.total_reads.values())
            if total_cards > 0:
                print(f"\n📊 STATISTICHE FINALI:")
                print(f"   📥 Letture IN:  {self.total_reads['in']}")
                print(f"   📤 Letture OUT: {self.total_reads['out']}")
                print(f"   📇 Totale card: {total_cards}")
            
        except Exception as e:
            print(f"❌ Errore durante stop: {e}")

def setup_signal_handlers(monitor):
    """Imposta gestori segnali per arresto pulito"""
    def signal_handler(signum, frame):
        print(f"\n⚡ Ricevuto segnale {signum}")
        monitor.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Funzione principale"""
    print("📡 RFID CARD READER MONITOR")
    print("=" * 50)
    print("🎯 Monitor letture RFID in tempo reale")
    print()
    
    monitor = RFIDCardMonitor()
    setup_signal_handlers(monitor)
    
    try:
        # Inizializza
        if not await monitor.initialize():
            print("❌ Inizializzazione fallita")
            return
        
        # Avvia monitoraggio
        await monitor.start_monitoring()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Arrivederci!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programma interrotto")