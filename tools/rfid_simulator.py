#!/usr/bin/env python3
"""
🔍 RFID Reader Simulator - Test su macOS
======================================

Simula le letture RFID per test su macOS/development environment
senza hardware reale.
"""

import sys
import asyncio
import signal
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MockRFIDReader:
    """Mock reader per simulare letture RFID"""
    
    def __init__(self, reader_id: str, direction: str, reader_type: str = "pn532"):
        self.reader_id = reader_id
        self.direction = direction
        self.reader_type = reader_type
        self.is_initialized = False
        self.read_count = 0
        
        # Card simulate database
        self.test_cards = [
            "632D3903",  # Card test 1
            "AB123456",  # Card test 2  
            "12345678",  # Card test 3
            "DEADBEEF",  # Card test 4
            "CAFEBABE",  # Card test 5
        ]
        
        print(f"📡 Mock {reader_type.upper()} Reader {reader_id} creato - {direction}")
    
    async def initialize(self):
        """Simula inizializzazione"""
        print(f"🔄 Inizializzazione mock {self.reader_id}...")
        await asyncio.sleep(0.5)  # Simula tempo inizializzazione
        self.is_initialized = True
        print(f"✅ Mock {self.reader_id} inizializzato")
        return True
    
    async def read_card(self, timeout=0.1):
        """Simula lettura carta"""
        if not self.is_initialized:
            return None
        
        # Simula chance di lettura (5% ogni tentativo)
        if random.random() < 0.05:
            await asyncio.sleep(0.1)  # Simula tempo lettura
            
            # Scegli carta random
            uid_formatted = random.choice(self.test_cards)
            uid_raw = uid_formatted + "FF"  # Simula suffix
            
            self.read_count += 1
            
            # Crea mock CardEvent
            from rfid_gate.hardware.readers.base import CardEvent
            import time
            
            return CardEvent(
                uid=uid_raw,
                uid_formatted=uid_formatted,
                reader_id=self.reader_id,
                direction=self.direction,
                timestamp=time.time(),
                reader_type=self.reader_type,
                raw_data=bytes.fromhex(uid_raw),
                metadata={
                    'read_count': self.read_count,
                    'mock': True,
                    'test_mode': True
                }
            )
        
        return None
    
    async def cleanup(self):
        """Simula cleanup"""
        print(f"🧹 Mock {self.reader_id} cleanup")
        self.is_initialized = False

class RFIDSimulator:
    """Simulatore RFID per test su macOS"""
    
    def __init__(self):
        self.is_running = False
        self.readers = {}
        self.card_count = 0
        
    async def initialize(self):
        """Inizializza simulatori"""
        try:
            print("🔧 Inizializzazione simulatori RFID...")
            
            from rfid_gate.config.settings import RFIDGateConfig
            import time as time_module
            
            # Carica configurazione
            config = RFIDGateConfig.from_env()
            print(f"✅ Configurazione caricata: {config.system.tornello_id}")
            
            # Crea mock readers
            if config.system.enable_in_reader and config.rfid_in.enabled:
                reader_in = MockRFIDReader("reader_in", "in", config.rfid_in.reader_type.value)
                await reader_in.initialize()
                self.readers["in"] = reader_in
                print(f"✅ Mock Reader IN inizializzato")
            
            if config.system.bidirectional_mode and config.system.enable_out_reader and config.rfid_out.enabled:
                reader_out = MockRFIDReader("reader_out", "out", config.rfid_out.reader_type.value)
                await reader_out.initialize()
                self.readers["out"] = reader_out
                print(f"✅ Mock Reader OUT inizializzato")
            
            if not self.readers:
                print("❌ Nessun reader simulato")
                return False
                
            print(f"✅ {len(self.readers)} simulatore/i pronti")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione simulatore: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def start_simulation(self):
        """Avvia simulazione"""
        if not self.readers:
            print("❌ Nessun simulatore disponibile")
            return
            
        try:
            print("\n🎬 AVVIO SIMULAZIONE RFID")
            print("=" * 60)
            print(f"🎭 {len(self.readers)} simulatore/i attivi: {list(self.readers.keys())}")
            print("💡 Simulazione automatica di letture card...")
            print("📊 Frequenza letture: ~5% per ciclo (~1 card ogni 2-3 secondi)")
            print("⏹️  Premi Ctrl+C per uscire")
            print("=" * 60)
            print()
            
            self.is_running = True
            
            # Avvia task per ogni reader
            tasks = []
            for direction, reader in self.readers.items():
                task = asyncio.create_task(self._reader_loop(reader, direction))
                tasks.append(task)
            
            # Aggiungi task per statistiche periodiche
            stats_task = asyncio.create_task(self._stats_loop())
            tasks.append(stats_task)
            
            # Aspetta che tutti i task finiscano
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            print("\n⏹️ Interruzione richiesta dall'utente")
        except Exception as e:
            print(f"\n❌ Errore durante simulazione: {e}")
        finally:
            await self.stop_simulation()
    
    async def _reader_loop(self, reader, direction):
        """Loop di lettura per un reader simulato"""
        print(f"🔄 Avvio simulazione reader {direction}")
        
        while self.is_running:
            try:
                # Simula lettura
                card_event = await reader.read_card(timeout=0.1)
                
                if card_event:
                    await self._display_card_read(card_event, direction)
                
                # Pausa tra tentativi
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Errore simulatore {direction}: {e}")
                await asyncio.sleep(1)
    
    async def _stats_loop(self):
        """Loop statistiche periodiche"""
        while self.is_running:
            await asyncio.sleep(10)  # Ogni 10 secondi
            if self.card_count > 0:
                print(f"📊 [INFO] Totale card simulate: {self.card_count}")
    
    async def _display_card_read(self, card_event, direction):
        """Mostra lettura carta simulata"""
        try:
            self.card_count += 1
            
            # Timestamp
            timestamp = datetime.fromtimestamp(card_event.timestamp)
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]
            
            # Icone
            direction_icon = "📥" if direction == "in" else "📤"
            reader_icon = "🎭"  # Mock icon
            
            print("─" * 50)
            print(f"🎯 MOCK CARD #{self.card_count} - {time_str}")
            print("─" * 50)
            print(f"📇 UID:       {card_event.uid_formatted}")
            print(f"🔢 UID Raw:   {card_event.uid}")
            print(f"🚪 Reader:    {direction_icon} {direction.upper()}")
            print(f"📡 Type:      {reader_icon} {card_event.reader_type} (MOCK)")
            print(f"🆔 Reader ID: {card_event.reader_id}")
            print(f"🎭 Mock Mode: Test card simulation")
            
            # Statistiche
            read_count = card_event.metadata.get('read_count', 'N/A')
            print(f"📊 Read #:    {read_count}")
            
            print("─" * 50)
            print()
            
        except Exception as e:
            print(f"❌ Errore display simulazione: {e}")
    
    async def stop_simulation(self):
        """Ferma simulazione"""
        try:
            print("\n🛑 Arresto simulatori...")
            self.is_running = False
            
            # Cleanup simulatori
            for direction, reader in self.readers.items():
                try:
                    await reader.cleanup()
                    print(f"✅ Simulatore {direction} fermato")
                except Exception as e:
                    print(f"⚠️ Errore stop simulatore {direction}: {e}")
            
            print(f"📊 Totale card simulate: {self.card_count}")
            
        except Exception as e:
            print(f"❌ Errore durante stop: {e}")

def setup_signal_handlers(simulator):
    """Imposta gestori segnali"""
    def signal_handler(signum, frame):
        print(f"\n⚡ Ricevuto segnale {signum}")
        simulator.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Funzione principale"""
    print("🎭 RFID SIMULATOR - Development Mode")
    print("=" * 50)
    print("🎯 Simulazione lettori RFID per test su macOS")
    print()
    
    simulator = RFIDSimulator()
    setup_signal_handlers(simulator)
    
    try:
        # Inizializza
        if not await simulator.initialize():
            print("❌ Inizializzazione fallita")
            return
        
        # Avvia simulazione
        await simulator.start_simulation()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Simulazione terminata!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programma interrotto")