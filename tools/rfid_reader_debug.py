#!/usr/bin/env python3
"""
🔍 RFID Reader Debug - Lettura diretta
=====================================

Tool di debug per testare i lettori RFID direttamente,
senza il sistema completo di controllo accessi.
"""

import sys
import asyncio
import signal
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SimpleRFIDDebug:
    """Debug semplice lettori RFID"""
    
    def __init__(self):
        self.is_running = False
        self.readers = {}
        self.card_count = 0
        
    async def initialize(self):
        """Inizializza i lettori RFID"""
        try:
            print("🔧 Inizializzazione lettori RFID...")
            
            from rfid_gate.config.settings import RFIDGateConfig
            
            # Carica configurazione
            config = RFIDGateConfig.from_env()
            print(f"✅ Configurazione caricata: {config.system.tornello_id}")
            
            # Inizializza lettore IN
            if config.system.enable_in_reader and config.rfid_in.enabled:
                reader_in = await self._create_reader(config.rfid_in, "in")
                if reader_in:
                    self.readers["in"] = reader_in
                    print(f"✅ Lettore IN inizializzato: {config.rfid_in.reader_type}")
            
            # Inizializza lettore OUT (se bidirezionale)
            if config.system.bidirectional_mode and config.system.enable_out_reader and config.rfid_out.enabled:
                reader_out = await self._create_reader(config.rfid_out, "out")  
                if reader_out:
                    self.readers["out"] = reader_out
                    print(f"✅ Lettore OUT inizializzato: {config.rfid_out.reader_type}")
            
            if not self.readers:
                print("❌ Nessun lettore inizializzato")
                return False
                
            print(f"✅ {len(self.readers)} lettore/i pronti")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _create_reader(self, reader_config, direction):
        """Crea e inizializza un lettore specifico"""
        try:
            reader = None
            
            if reader_config.reader_type.value == "pn532":
                from rfid_gate.hardware.readers.pn532 import PN532Reader
                
                # Crea PN532Reader con configurazione integrata
                kwargs = {
                    'interface': reader_config.pn532_interface.value
                }
                
                # Aggiungi parametri specifici per interfaccia
                if reader_config.pn532_interface.value == "i2c":
                    kwargs['i2c_address'] = reader_config.pn532_i2c_address
                elif reader_config.pn532_interface.value == "spi":
                    kwargs['spi_bus'] = reader_config.pn532_spi_bus
                    kwargs['spi_device'] = reader_config.pn532_spi_device
                elif reader_config.pn532_interface.value == "uart":
                    kwargs['uart_port'] = reader_config.pn532_uart_port
                    kwargs['uart_baudrate'] = reader_config.pn532_uart_baudrate
                
                reader = PN532Reader(
                    reader_id=f"reader_{direction}",
                    direction=direction,
                    **kwargs
                )
                    
            elif reader_config.reader_type.value == "mfrc522":
                from rfid_gate.hardware.readers.mfrc522 import MFRC522Reader
                reader = MFRC522Reader(
                    reader_id=f"reader_{direction}",
                    direction=direction,
                    rst_pin=reader_config.rst_pin,
                    sda_pin=reader_config.sda_pin
                )
            
            if reader:
                # Inizializza reader
                init_result = await reader.initialize()
                if init_result:
                    return reader
                else:
                    print(f"❌ Inizializzazione reader {direction} fallita")
            
            return None
            
        except Exception as e:
            print(f"❌ Errore creazione reader {direction}: {e}")
            return None
    
    async def start_debug(self):
        """Avvia il debug dei lettori"""
        if not self.readers:
            print("❌ Nessun lettore disponibile")
            return
            
        try:
            print("\n🎬 AVVIO DEBUG LETTORI RFID")
            print("=" * 60)
            print(f"📡 {len(self.readers)} lettore/i attivi: {list(self.readers.keys())}")
            print("💡 Avvicina le card ai lettori...")
            print("⏹️  Premi Ctrl+C per uscire")
            print("=" * 60)
            print()
            
            self.is_running = True
            
            # Avvia task per ogni lettore
            tasks = []
            for direction, reader in self.readers.items():
                task = asyncio.create_task(self._reader_loop(reader, direction))
                tasks.append(task)
            
            # Aspetta che tutti i task finiscano
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            print("\n⏹️ Interruzione richiesta dall'utente")
        except Exception as e:
            print(f"\n❌ Errore durante debug: {e}")
        finally:
            await self.stop_debug()
    
    async def _reader_loop(self, reader, direction):
        """Loop di lettura per un singolo lettore"""
        print(f"🔄 Avvio loop lettore {direction}")
        
        while self.is_running:
            try:
                # Leggi carta con timeout breve
                card_event = await reader.read_card(timeout=0.1)
                
                if card_event:
                    await self._display_card_read(card_event, direction)
                
                # Pausa breve per evitare sovraccarico CPU
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Errore lettore {direction}: {e}")
                await asyncio.sleep(1)  # Pausa più lunga in caso di errore
    
    async def _display_card_read(self, card_event, direction):
        """Mostra dettagli lettura carta"""
        try:
            self.card_count += 1
            
            # Timestamp
            timestamp = datetime.fromtimestamp(card_event.timestamp)
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]  # Con millisecondi
            
            # Icone per direzione
            direction_icon = "📥" if direction == "in" else "📤"
            reader_icon = "🔵" if card_event.reader_type == "pn532" else "🟡"
            
            print("─" * 50)
            print(f"🎯 CARD #{self.card_count} - {time_str}")
            print("─" * 50)
            print(f"📇 UID:       {card_event.uid_formatted}")
            print(f"🔢 UID Raw:   {card_event.uid}")
            print(f"🚪 Reader:    {direction_icon} {direction.upper()}")
            print(f"📡 Type:      {reader_icon} {card_event.reader_type}")
            print(f"🆔 Reader ID: {card_event.reader_id}")
            
            # Dati raw se disponibili
            if card_event.raw_data:
                hex_data = ' '.join([f'{b:02X}' for b in card_event.raw_data])
                print(f"🔬 Raw Data:  {hex_data}")
            
            # Statistiche lettore
            if hasattr(card_event, 'metadata') and card_event.metadata:
                read_count = card_event.metadata.get('read_count', 'N/A')
                print(f"📊 Read #:    {read_count}")
            
            print("─" * 50)
            print()
            
        except Exception as e:
            print(f"❌ Errore display: {e}")
    
    async def stop_debug(self):
        """Ferma il debug"""
        try:
            print("\n🛑 Arresto lettori...")
            self.is_running = False
            
            # Cleanup lettori
            for direction, reader in self.readers.items():
                try:
                    await reader.cleanup()
                    print(f"✅ Lettore {direction} fermato")
                except Exception as e:
                    print(f"⚠️ Errore stop lettore {direction}: {e}")
            
            print(f"📊 Totale card lette: {self.card_count}")
            
        except Exception as e:
            print(f"❌ Errore durante stop: {e}")

def setup_signal_handlers(debug):
    """Imposta gestori segnali"""
    def signal_handler(signum, frame):
        print(f"\n⚡ Ricevuto segnale {signum}")
        debug.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Funzione principale"""
    print("🔍 RFID READER DEBUG")
    print("=" * 40)
    print("🎯 Test diretto lettori RFID")
    print()
    
    debug = SimpleRFIDDebug()
    setup_signal_handlers(debug)
    
    try:
        # Inizializza
        if not await debug.initialize():
            print("❌ Inizializzazione fallita")
            return
        
        # Avvia debug
        await debug.start_debug()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Debug terminato!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programma interrotto")