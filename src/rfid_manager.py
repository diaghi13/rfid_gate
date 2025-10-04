#!/usr/bin/env python3
"""
RFID Manager - Gestione dual readers con anti-crosstalk
"""

import threading
import time
from queue import Queue, Empty
from config import Config
from rfid_readers.reader_factory import RFIDReaderFactory

class RFIDManager:
    """Manager per dual readers con debounce cross-reader."""
    
    def __init__(self):
        self.readers = {}
        self.reader_threads = {}
        self.card_queue = Queue()
        self.running = False
        self.is_initialized = False
        
        # Anti-crosstalk: debounce globale tra lettori
        self.global_debounce = {}  # {card_id: {"time": timestamp, "reader": reader_id}}
        self.global_debounce_time = getattr(Config, 'GLOBAL_DEBOUNCE_TIME', 0.8)  # Configurabile
        self.debounce_lock = threading.Lock()
    
    def initialize(self):
        """Inizializza lettori usando factory pattern."""
        try:
            print("📖 Inizializzazione RFID Manager (Dual Reader)...")
            
            # Lettore IN
            if Config.ENABLE_IN_READER:
                print(f"🔵 Configurazione RFID Reader IN ({Config.RFID_IN_READER_TYPE.upper()})")
                
                reader_in = RFIDReaderFactory.create_reader(
                    reader_type=Config.RFID_IN_READER_TYPE,
                    reader_id="in",
                    interface=getattr(Config, 'RFID_IN_PN532_INTERFACE', 'i2c'),
                    i2c_address=getattr(Config, 'RFID_IN_PN532_I2C_ADDRESS', 0x24),
                    spi_bus=getattr(Config, 'RFID_IN_PN532_SPI_BUS', 0),
                    spi_device=getattr(Config, 'RFID_IN_PN532_SPI_DEVICE', 0),
                    rst_pin=getattr(Config, 'RFID_IN_RST_PIN', 22),
                    sda_pin=getattr(Config, 'RFID_IN_SDA_PIN', 8)
                )
                
                if reader_in.initialize():
                    if reader_in.test_connection():
                        self.readers["in"] = reader_in
                        print("✅ RFID Reader IN inizializzato")
                    else:
                        print("⚠️ Test connessione IN limitato (continuiamo)")
                        self.readers["in"] = reader_in  # Usa comunque il reader
                else:
                    print("❌ Inizializzazione RFID IN fallita")
                    return False
            
            # Lettore OUT
            if Config.ENABLE_OUT_READER:
                print(f"🟡 Configurazione RFID Reader OUT ({Config.RFID_OUT_READER_TYPE.upper()})")
                
                reader_out = RFIDReaderFactory.create_reader(
                    reader_type=Config.RFID_OUT_READER_TYPE,
                    reader_id="out", 
                    interface=getattr(Config, 'RFID_OUT_PN532_INTERFACE', 'spi'),
                    i2c_address=getattr(Config, 'RFID_OUT_PN532_I2C_ADDRESS', 0x25),
                    spi_bus=getattr(Config, 'RFID_OUT_PN532_SPI_BUS', 0),
                    spi_device=getattr(Config, 'RFID_OUT_PN532_SPI_DEVICE', 0),
                    rst_pin=getattr(Config, 'RFID_OUT_RST_PIN', 25),
                    sda_pin=getattr(Config, 'RFID_OUT_SDA_PIN', 7)
                )
                
                if reader_out.initialize():
                    if reader_out.test_connection():
                        self.readers["out"] = reader_out
                        print("✅ RFID Reader OUT inizializzato")
                    else:
                        print("⚠️ Test connessione OUT limitato (continuiamo)")
                        self.readers["out"] = reader_out  # Usa comunque il reader
                else:
                    print("❌ Inizializzazione RFID OUT fallita")
                    return False
            
            if not self.readers:
                print("❌ Nessun lettore configurato")
                return False
            
            self.is_initialized = True
            print(f"✅ RFID Manager inizializzato - {len(self.readers)} lettori attivi")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione RFID Manager: {e}")
            return False
    
    def apply_global_debounce(self, card_id, reader_id):
        """
        Debounce globale per evitare letture multiple tra lettori diversi.
        Previene che la stessa card sia letta contemporaneamente su IN e OUT.
        """
        with self.debounce_lock:
            current_time = time.time()
            card_str = str(card_id)
            
            if card_str in self.global_debounce:
                last_read = self.global_debounce[card_str]
                time_diff = current_time - last_read["time"]
                
                # Se la stessa card è stata letta di recente
                if time_diff < self.global_debounce_time:
                    # Se è lo stesso lettore, permetti (debounce locale gestisce)
                    if last_read["reader"] == reader_id:
                        return True
                    # Se è lettore diverso, blocca per evitare crosstalk
                    else:
                        print(f"🚫 Crosstalk bloccato: card {card_id} letta {time_diff:.2f}s fa su {last_read['reader']}, ora su {reader_id}")
                        return False
            
            # Aggiorna debounce globale
            self.global_debounce[card_str] = {
                "time": current_time,
                "reader": reader_id
            }
            
            # Cleanup vecchi record (oltre 10 secondi)
            to_remove = []
            for card, data in self.global_debounce.items():
                if current_time - data["time"] > 10.0:
                    to_remove.append(card)
            
            for card in to_remove:
                del self.global_debounce[card]
            
            return True
    
    def start(self):
        """Avvia threads di lettura per ogni lettore."""
        if not self.is_initialized:
            print("❌ RFID Manager non inizializzato")
            return False
        
        self.running = True
        
        for reader_id, reader in self.readers.items():
            thread = threading.Thread(
                target=self._reader_loop,
                args=(reader_id, reader),
                name=f"RFIDThread_{reader_id}"
            )
            thread.daemon = True
            thread.start()
            self.reader_threads[reader_id] = thread
            print(f"🚀 Thread avviato per lettore {reader_id}")
        
        print("✅ RFID Manager avviato")
        return True
    
    def start_reading(self):
        """Alias per start() - compatibilità"""
        return self.start()
    
    def get_active_readers(self):
        """Restituisce lista dei lettori attivi"""
        return list(self.readers.keys())
    
    def wait_for_card(self, timeout=None):
        """Alias per get_next_card() - compatibilità"""
        return self.get_next_card(timeout)
    
    def _reader_loop(self, reader_id, reader):
        """Loop di lettura per singolo lettore."""
        print(f"🔄 Loop lettura avviato per {reader_id}")
        
        while self.running:
            try:
                result = reader.read_card()
                
                if result and result[0]:  # Card rilevata
                    card_id, card_data = result
                    
                    # Applica debounce globale anti-crosstalk
                    if self.apply_global_debounce(card_id, reader_id):
                        # Aggiungi reader_id ai dati
                        if isinstance(card_data, dict):
                            card_data['reader_id'] = reader_id
                        
                        # Invia a queue per processamento
                        self.card_queue.put({
                            'reader_id': reader_id,
                            'card_id': card_id,
                            'card_data': card_data,
                            'timestamp': time.time()
                        })
                        
                        print(f"📇 {reader_id} - Carta: {card_id} (PN532-4byte)")
                
                time.sleep(Config.CARD_READ_INTERVAL)
                
            except Exception as e:
                print(f"❌ Errore lettura {reader_id}: {e}")
                time.sleep(0.5)  # Pausa dopo errore
    
    def get_next_card(self, timeout=0.1):
        """Ottiene prossima card dalla queue."""
        try:
            return self.card_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def stop(self):
        """Ferma il manager."""
        print("🛑 Arresto RFID Manager...")
        self.running = False
        
        # Attendi threads
        for reader_id, thread in self.reader_threads.items():
            if thread.is_alive():
                thread.join(timeout=2.0)
                print(f"🏁 Thread {reader_id} terminato")
        
        self.reader_threads.clear()
        print("✅ RFID Manager arrestato")
    
    def cleanup(self):
        """Cleanup completo."""
        self.stop()
        
        for reader_id, reader in self.readers.items():
            try:
                reader.cleanup()
                print(f"🧹 Cleanup {reader_id} completato")
            except Exception as e:
                print(f"⚠️ Errore cleanup {reader_id}: {e}")
        
        self.readers.clear()
        self.is_initialized = False
        print("🧹 RFID Manager cleanup completato")
    
    def get_reader_info(self):
        """Info sui lettori attivi."""
        info = {}
        for reader_id, reader in self.readers.items():
            try:
                info[reader_id] = reader.get_reader_info()
            except:
                info[reader_id] = {"status": "error"}
        return info