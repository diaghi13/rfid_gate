#!/usr/bin/env python3
"""
Modulo per la gestione di lettori RFID multipli in modalità bidirezionale
"""

import threading
import time
from queue import Queue, Empty
from config import Config
from rfid_reader import RFIDReader

class RFIDManager:
    """Classe per gestire lettori RFID multipli"""
    
    def __init__(self):
        self.readers = {}
        self.reader_threads = {}
        self.card_queue = Queue()
        self.running = False
        self.is_initialized = False
    
    def initialize(self):
        """Inizializza i lettori RFID attivi"""
        try:
            print("📖 Inizializzazione RFID Manager...")
            
            # Inizializza lettore IN se abilitato
            if Config.RFID_IN_ENABLE:
                print(f"🔵 Configurazione RFID Reader IN (RST: {Config.RFID_IN_RST_PIN}, SDA: {Config.RFID_IN_SDA_PIN})")
                reader_in = RFIDReader(
                    reader_id="in",
                    rst_pin=Config.RFID_IN_RST_PIN,
                    sda_pin=Config.RFID_IN_SDA_PIN
                )
                
                if reader_in.initialize():
                    if reader_in.test_connection():
                        self.readers["in"] = reader_in
                        print("✅ RFID Reader IN inizializzato correttamente")
                    else:
                        print("❌ Test connessione RFID IN fallito")
                        return False
                else:
                    print("❌ Inizializzazione RFID IN fallita")
                    return False
            
            # Inizializza lettore OUT se abilitato e in modalità bidirezionale
            if Config.BIDIRECTIONAL_MODE and Config.RFID_OUT_ENABLE:
                print(f"🔴 Configurazione RFID Reader OUT (RST: {Config.RFID_OUT_RST_PIN}, SDA: {Config.RFID_OUT_SDA_PIN})")
                reader_out = RFIDReader(
                    reader_id="out",
                    rst_pin=Config.RFID_OUT_RST_PIN,
                    sda_pin=Config.RFID_OUT_SDA_PIN
                )
                
                if reader_out.initialize():
                    if reader_out.test_connection():
                        self.readers["out"] = reader_out
                        print("✅ RFID Reader OUT inizializzato correttamente")
                    else:
                        print("❌ Test connessione RFID OUT fallito")
                        return False
                else:
                    print("❌ Inizializzazione RFID OUT fallita")
                    return False
            
            if not self.readers:
                print("❌ Nessun lettore RFID configurato")
                return False
            
            self.is_initialized = True
            print(f"✅ RFID Manager inizializzato con {len(self.readers)} lettori")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione RFID Manager: {e}")
            return False
    
    def start_reading(self):
        """Avvia i thread di lettura per tutti i lettori attivi"""
        if not self.is_initialized:
            print("❌ RFID Manager non inizializzato")
            return False
        
        try:
            self.running = True
            
            # Avvia un thread per ogni lettore
            for direction, reader in self.readers.items():
                thread = threading.Thread(
                    target=self._reader_thread,
                    args=(direction, reader),
                    daemon=True,
                    name=f"RFID-{direction.upper()}"
                )
                thread.start()
                self.reader_threads[direction] = thread
                print(f"🚀 Thread RFID {direction.upper()} avviato")
            
            print(f"✅ Tutti i thread di lettura RFID avviati")
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio thread RFID: {e}")
            return False
    
    def stop_reading(self):
        """Ferma tutti i thread di lettura"""
        print("🛑 Fermando thread RFID...")
        self.running = False
        
        # Aspetta che tutti i thread terminino
        for direction, thread in self.reader_threads.items():
            thread.join(timeout=2)
            print(f"🔴 Thread RFID {direction.upper()} terminato")
        
        self.reader_threads.clear()
    
    def _reader_thread(self, direction, reader):
        """Thread di lettura per un singolo lettore RFID"""
        print(f"📡 Thread RFID {direction.upper()} in ascolto...")
        
        while self.running:
            try:
                # Legge una card (operazione bloccante)
                card_id, card_data = reader.read_card()
                
                if card_id is not None:
                    # Ottiene le informazioni complete della card
                    card_info = reader.get_card_info(card_id, card_data)
                    
                    # Aggiunge la direzione alle informazioni
                    card_info['direction'] = direction
                    card_info['reader_id'] = reader.reader_id
                    card_info['timestamp'] = time.time()
                    
                    # Mette la card nella coda
                    self.card_queue.put(card_info)
                    
                    print(f"📱 Card rilevata su lettore {direction.upper()}: {card_info['uid_formatted']}")
                
                # Breve pausa per evitare letture duplicate
                time.sleep(0.1)
                
            except Exception as e:
                if self.running:  # Solo se non stiamo fermando il sistema
                    print(f"⚠️ Errore nel thread RFID {direction.upper()}: {e}")
                    time.sleep(1)
    
    def get_next_card(self, timeout=None):
        """
        Ottiene la prossima card dalla coda
        Args:
            timeout (float): Timeout in secondi (None = blocca indefinitamente)
        Returns:
            dict: Informazioni della card o None se timeout
        """
        try:
            return self.card_queue.get(block=True, timeout=timeout)
        except Empty:
            return None
    
    def wait_for_card(self):
        """
        Aspetta la prossima card (modalità bloccante)
        Returns:
            dict: Informazioni della card
        """
        return self.get_next_card()
    
    def has_pending_cards(self):
        """Controlla se ci sono card in attesa nella coda"""
        return not self.card_queue.empty()
    
    def get_active_readers(self):
        """Restituisce la lista dei lettori attivi"""
        return list(self.readers.keys())
    
    def get_reader_status(self):
        """Restituisce lo status di tutti i lettori"""
        status = {
            'initialized': self.is_initialized,
            'running': self.running,
            'active_readers': len(self.readers),
            'readers': {}
        }
        
        for direction, reader in self.readers.items():
            status['readers'][direction] = {
                'reader_id': reader.reader_id,
                'initialized': reader.is_initialized,
                'thread_running': direction in self.reader_threads
            }
        
        return status
    
    def cleanup(self):
        """Pulizia delle risorse"""
        try:
            # Ferma i thread
            self.stop_reading()
            
            # Pulisce i lettori
            for direction, reader in self.readers.items():
                reader.cleanup()
                print(f"🧹 Lettore RFID {direction.upper()} pulito")
            
            self.readers.clear()
            print("🧹 RFID Manager cleanup completato")
            
        except Exception as e:
            print(f"⚠️ Errore cleanup RFID Manager: {e}")
    
    def __del__(self):
        """Destructor - pulisce automaticamente"""
        self.cleanup()