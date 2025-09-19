#!/usr/bin/env python3
"""
Modulo per la gestione di lettori RFID multipli in modalità bidirezionale - VERSIONE CORRETTA
"""

import threading
import time
from queue import Queue, Empty
import RPi.GPIO as GPIO
from config import Config
from rfid_reader import RFIDReader

class RFIDManager:
    """Classe per gestire lettori RFID multipli - VERSIONE CORRETTA"""
    
    def __init__(self):
        self.readers = {}
        self.reader_threads = {}
        self.card_queue = Queue()
        self.running = False
        self.is_initialized = False
        self._gpio_initialized = False
    
    def initialize(self):
        """Inizializza i lettori RFID attivi"""
        try:
            print("📖 Inizializzazione RFID Manager...")
            
            # CRITICO: Inizializza GPIO una sola volta per tutti i lettori
            if not self._gpio_initialized:
                print("⚙️ Configurazione GPIO globale...")
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                self._gpio_initialized = True
                print("✅ GPIO configurato in modalità BCM")
            
            # Verifica configurazione doppio RFID
            if Config.RFID_IN_ENABLE and Config.RFID_OUT_ENABLE:
                print("🔄 Modalità DOPPIO RFID rilevata")
                
                # Verifica che i pin siano diversi
                if Config.RFID_IN_SDA_PIN == Config.RFID_OUT_SDA_PIN:
                    print("❌ ERRORE: RFID_IN_SDA_PIN e RFID_OUT_SDA_PIN devono essere diversi!")
                    print(f"   Attuale: IN={Config.RFID_IN_SDA_PIN}, OUT={Config.RFID_OUT_SDA_PIN}")
                    print("💡 Configura pin diversi nel file .env")
                    return False
                
                if Config.RFID_IN_RST_PIN == Config.RFID_OUT_RST_PIN:
                    print("❌ ERRORE: RFID_IN_RST_PIN e RFID_OUT_RST_PIN devono essere diversi!")
                    print(f"   Attuale: IN={Config.RFID_IN_RST_PIN}, OUT={Config.RFID_OUT_RST_PIN}")
                    print("💡 Configura pin diversi nel file .env")
                    return False
                
                print(f"✅ Pin configurati correttamente:")
                print(f"   IN:  RST={Config.RFID_IN_RST_PIN}, SDA={Config.RFID_IN_SDA_PIN}")
                print(f"   OUT: RST={Config.RFID_OUT_RST_PIN}, SDA={Config.RFID_OUT_SDA_PIN}")
            
            # Inizializza lettore IN se abilitato
            if Config.RFID_IN_ENABLE:
                print(f"🔵 Configurazione RFID Reader IN")
                reader_in = RFIDReader(
                    reader_id="in",
                    rst_pin=Config.RFID_IN_RST_PIN,
                    sda_pin=Config.RFID_IN_SDA_PIN
                )
                
                if reader_in.initialize():
                    if reader_in.test_connection():
                        self.readers["in"] = reader_in
                        print("✅ RFID Reader IN inizializzato e testato")
                    else:
                        print("❌ Test connessione RFID IN fallito")
                        return False
                else:
                    print("❌ Inizializzazione RFID IN fallita")
                    return False
            
            # Inizializza lettore OUT se abilitato e in modalità bidirezionale
            if Config.BIDIRECTIONAL_MODE and Config.RFID_OUT_ENABLE:
                print(f"🔴 Configurazione RFID Reader OUT")
                
                # Piccola pausa tra inizializzazioni per stabilità
                time.sleep(0.5)
                
                reader_out = RFIDReader(
                    reader_id="out",
                    rst_pin=Config.RFID_OUT_RST_PIN,
                    sda_pin=Config.RFID_OUT_SDA_PIN
                )
                
                if reader_out.initialize():
                    if reader_out.test_connection():
                        self.readers["out"] = reader_out
                        print("✅ RFID Reader OUT inizializzato e testato")
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
            
            # Stampa riepilogo configurazione
            self._print_config_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione RFID Manager: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_config_summary(self):
        """Stampa riepilogo configurazione"""
        print("\n📋 RIEPILOGO CONFIGURAZIONE RFID:")
        print("=" * 40)
        for direction, reader in self.readers.items():
            print(f"   {direction.upper():3s}: RST={reader.rst_pin:2d}, SDA={reader.sda_pin:2d}")
        print("=" * 40)
    
    def start_reading(self):
        """Avvia i thread di lettura per tutti i lettori attivi"""
        if not self.is_initialized:
            print("❌ RFID Manager non inizializzato")
            return False
        
        try:
            self.running = True
            
            # Avvia un thread per ogni lettore con priorità
            thread_priority = {"in": 1, "out": 2}  # IN ha priorità più alta
            
            for direction, reader in self.readers.items():
                thread = threading.Thread(
                    target=self._reader_thread,
                    args=(direction, reader),
                    daemon=True,
                    name=f"RFID-{direction.upper()}"
                )
                
                # Imposta priorità thread (opzionale)
                thread.start()
                
                self.reader_threads[direction] = thread
                print(f"🚀 Thread RFID {direction.upper()} avviato")
                
                # Piccola pausa tra avvii thread per stabilità
                time.sleep(0.2)
            
            print(f"✅ Tutti i thread di lettura RFID avviati ({len(self.reader_threads)} attivi)")
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
            if thread.is_alive():
                print(f"⏳ Attendendo terminazione thread RFID {direction.upper()}...")
                thread.join(timeout=3)
                
                if thread.is_alive():
                    print(f"⚠️ Thread RFID {direction.upper()} non terminato entro timeout")
                else:
                    print(f"🔴 Thread RFID {direction.upper()} terminato")
            else:
                print(f"🔴 Thread RFID {direction.upper()} già terminato")
        
        self.reader_threads.clear()
    
    def _reader_thread(self, direction, reader):
        """Thread di lettura per un singolo lettore RFID - VERSIONE OTTIMIZZATA"""
        print(f"📡 Thread RFID {direction.upper()} in ascolto...")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                # Legge una card (non bloccante)
                card_id, card_data = reader.read_card()
                
                if card_id is not None:
                    # Reset contatore errori
                    consecutive_errors = 0
                    
                    # Ottiene le informazioni complete della card
                    card_info = reader.get_card_info(card_id, card_data)
                    
                    # Aggiunge la direzione alle informazioni
                    card_info['direction'] = direction
                    card_info['reader_id'] = reader.reader_id
                    card_info['timestamp'] = time.time()
                    
                    # Mette la card nella coda
                    try:
                        self.card_queue.put(card_info, block=False)
                        print(f"📱 Card rilevata su lettore {direction.upper()}: {card_info['uid_formatted']}")
                    except:
                        print(f"⚠️ Coda card piena - card {card_info['uid_formatted']} ignorata")
                
                # Pausa ottimizzata per doppio RFID
                # Pausa più breve per permettere a entrambi i lettori di funzionare
                time.sleep(0.05)  # 50ms invece di 100ms
                
            except Exception as e:
                if self.running:  # Solo se non stiamo fermando il sistema
                    consecutive_errors += 1
                    
                    # Non spammare errori - solo errori significativi
                    if consecutive_errors <= 3:
                        error_msg = str(e)
                        if "timeout" not in error_msg.lower() and "no card" not in error_msg.lower():
                            print(f"⚠️ Errore nel thread RFID {direction.upper()}: {e}")
                    
                    # Se troppi errori consecutivi, pausa più lunga
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Troppi errori consecutivi su RFID {direction.upper()}, pausa lunga...")
                        time.sleep(2)
                        consecutive_errors = 0
                    else:
                        time.sleep(0.1)
        
        print(f"🏁 Thread RFID {direction.upper()} terminato")
    
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
            'gpio_initialized': self._gpio_initialized,
            'readers': {},
            'threads': {}
        }
        
        for direction, reader in self.readers.items():
            status['readers'][direction] = {
                'reader_id': reader.reader_id,
                'initialized': reader.is_initialized,
                'rst_pin': reader.rst_pin,
                'sda_pin': reader.sda_pin
            }
        
        for direction, thread in self.reader_threads.items():
            status['threads'][direction] = {
                'alive': thread.is_alive() if thread else False,
                'name': thread.name if thread else None
            }
        
        return status
    
    def test_all_readers(self):
        """Testa tutti i lettori configurati"""
        print("\n🧪 TEST TUTTI I LETTORI RFID")
        print("=" * 40)
        
        all_ok = True
        for direction, reader in self.readers.items():
            print(f"🔍 Test lettore {direction.upper()}...")
            if reader.test_connection():
                print(f"✅ Lettore {direction.upper()}: OK")
            else:
                print(f"❌ Lettore {direction.upper()}: FALLITO")
                all_ok = False
        
        print("=" * 40)
        if all_ok:
            print("✅ Tutti i lettori RFID funzionano correttamente")
        else:
            print("❌ Alcuni lettori RFID hanno problemi")
        
        return all_ok
    
    def cleanup(self):
        """Pulizia delle risorse"""
        try:
            print("🧹 RFID Manager cleanup...")
            
            # Ferma i thread
            self.stop_reading()
            
            # Pulisce i lettori
            for direction, reader in self.readers.items():
                reader.cleanup()
                print(f"🧹 Lettore RFID {direction.upper()} pulito")
            
            self.readers.clear()
            
            # Cleanup GPIO finale (solo se abbiamo inizializzato noi)
            if self._gpio_initialized:
                try:
                    GPIO.cleanup()
                    print("🧹 GPIO cleanup completato")
                except:
                    pass
                self._gpio_initialized = False
            
            print("✅ RFID Manager cleanup completato")
            
        except Exception as e:
            print(f"⚠️ Errore cleanup RFID Manager: {e}")
    
    def __del__(self):
        """Destructor - pulisce automaticamente"""
        self.cleanup()