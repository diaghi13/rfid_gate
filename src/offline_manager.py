#!/usr/bin/env python3
"""
Modulo per la gestione della modalità offline e sincronizzazione
"""

import json
import os
import time
import threading
import socket
from datetime import datetime
from queue import Queue, Empty
from config import Config

class OfflineManager:
    """Classe per gestire la modalità offline e la sincronizzazione"""
    
    def __init__(self, mqtt_client=None, logger=None):
        self.mqtt_client = mqtt_client
        self.logger = logger
        self.is_online = False
        self.last_connection_check = 0
        
        # Coda per i messaggi offline
        self.offline_queue = Queue()
        self.queue_file_path = os.path.join(Config.LOG_DIRECTORY, Config.OFFLINE_STORAGE_FILE)
        
        # Thread per il controllo connessione e sync
        self.connection_thread = None
        self.sync_thread = None
        self.running = False
        
        # Lock per thread safety
        self._lock = threading.Lock()
        
        # Carica la coda dai file persistente
        self.load_offline_queue()
        
        # Statistiche
        self.stats = {
            'total_offline_accesses': 0,
            'pending_sync': self.offline_queue.qsize(),
            'last_sync_attempt': None,
            'last_successful_sync': None,
            'connection_checks': 0
        }
    
    def initialize(self):
        """Inizializza il manager offline"""
        try:
            print("🌐 Inizializzazione Offline Manager...")
            
            if not Config.OFFLINE_MODE_ENABLED:
                print("🔴 Modalità offline disabilitata")
                return False
            
            # Verifica connessione iniziale
            self.check_connection()
            
            # Avvia i thread di monitoraggio
            self.start_monitoring_threads()
            
            print(f"✅ Offline Manager inizializzato")
            print(f"   📊 Elementi in coda: {self.offline_queue.qsize()}")
            print(f"   🌐 Stato connessione: {'Online' if self.is_online else 'Offline'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione Offline Manager: {e}")
            return False
    
    def start_monitoring_threads(self):
        """Avvia i thread di monitoraggio"""
        self.running = True
        
        # Thread per controllo connessione
        self.connection_thread = threading.Thread(
            target=self._connection_monitor_thread,
            daemon=True,
            name="ConnectionMonitor"
        )
        self.connection_thread.start()
        
        # Thread per sincronizzazione
        if Config.OFFLINE_SYNC_ENABLED:
            self.sync_thread = threading.Thread(
                target=self._sync_thread,
                daemon=True,
                name="OfflineSync"
            )
            self.sync_thread.start()
    
    def stop_monitoring_threads(self):
        """Ferma i thread di monitoraggio"""
        self.running = False
        
        if self.connection_thread:
            self.connection_thread.join(timeout=2)
        
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
    
    def check_connection(self):
        """Controlla se c'è connessione internet"""
        try:
            # Prova a connettersi al broker MQTT
            socket.create_connection((Config.MQTT_BROKER, Config.MQTT_PORT), timeout=5)
            
            # Se arriviamo qui, la connessione c'è
            was_offline = not self.is_online
            self.is_online = True
            self.last_connection_check = time.time()
            self.stats['connection_checks'] += 1
            
            if was_offline:
                print("🟢 Connessione internet ripristinata!")
                if self.logger:
                    self.logger.log_system_event("connection_restored", "Connessione internet ripristinata")
                
                # Avvia sync se abilitata
                if Config.OFFLINE_SYNC_ENABLED and not self.offline_queue.empty():
                    print(f"📤 Avvio sincronizzazione ({self.offline_queue.qsize()} elementi in coda)")
            
            return True
            
        except (socket.timeout, socket.error, OSError) as e:
            was_online = self.is_online
            self.is_online = False
            self.last_connection_check = time.time()
            self.stats['connection_checks'] += 1
            
            if was_online:
                print("🔴 Connessione internet persa - Attivazione modalità offline")
                if self.logger:
                    self.logger.log_system_event("connection_lost", f"Connessione internet persa: {e}", "warning")
            
            return False
        
        except Exception as e:
            print(f"⚠️ Errore controllo connessione: {e}")
            return False
    
    def _connection_monitor_thread(self):
        """Thread per il monitoraggio continuo della connessione"""
        while self.running:
            try:
                # Controlla connessione ogni X secondi
                if time.time() - self.last_connection_check >= Config.CONNECTION_CHECK_INTERVAL:
                    self.check_connection()
                
                time.sleep(5)  # Controlla ogni 5 secondi per responsività
                
            except Exception as e:
                if self.logger:
                    self.logger.log_system_event("connection_monitor_error", str(e), "error")
                time.sleep(10)
    
    def _sync_thread(self):
        """Thread per la sincronizzazione automatica"""
        while self.running:
            try:
                if self.is_online and not self.offline_queue.empty():
                    self.sync_offline_data()
                
                time.sleep(10)  # Tenta sync ogni 10 secondi quando online
                
            except Exception as e:
                if self.logger:
                    self.logger.log_system_event("sync_thread_error", str(e), "error")
                time.sleep(30)
    
    def handle_card_access(self, card_info):
        """
        Gestisce l'accesso di una card in modalità online/offline
        Returns: dict con risultato dell'autenticazione
        """
        if self.is_online and self.mqtt_client and self.mqtt_client.is_connected:
            # Modalità online - autenticazione normale
            try:
                return self.mqtt_client.publish_card_data_and_wait_auth(card_info)
            except Exception as e:
                print(f"⚠️ Errore autenticazione online, fallback offline: {e}")
                return self._handle_offline_access(card_info)
        else:
            # Modalità offline
            return self._handle_offline_access(card_info)
    
    def _handle_offline_access(self, card_info):
        """Gestisce l'accesso in modalità offline"""
        if not Config.OFFLINE_MODE_ENABLED:
            return {
                'authorized': False,
                'error': 'Sistema offline e modalità offline disabilitata',
                'offline_mode': False
            }
        
        if not Config.OFFLINE_ALLOW_ACCESS:
            return {
                'authorized': False,
                'error': 'Accesso negato in modalità offline',
                'offline_mode': True
            }
        
        # In modalità offline, consentiamo l'accesso
        print("🟡 MODALITÀ OFFLINE - Accesso consentito")
        
        # Aggiungi alla coda per sync successiva
        self._add_to_offline_queue(card_info)
        
        # Aggiorna statistiche
        self.stats['total_offline_accesses'] += 1
        self.stats['pending_sync'] = self.offline_queue.qsize()
        
        return {
            'authorized': True,
            'message': 'Accesso offline autorizzato - Sincronizzazione pending',
            'offline_mode': True
        }
    
    def _add_to_offline_queue(self, card_info):
        """Aggiunge un accesso alla coda offline"""
        try:
            # Prepara i dati per la coda
            offline_entry = {
                'timestamp': datetime.now().isoformat(),
                'card_info': card_info,
                'sync_attempts': 0,
                'created_offline': True
            }
            
            # Controlla se la coda è piena
            if self.offline_queue.qsize() >= Config.OFFLINE_MAX_QUEUE_SIZE:
                print(f"⚠️ Coda offline piena ({Config.OFFLINE_MAX_QUEUE_SIZE}), rimuovo elemento più vecchio")
                try:
                    self.offline_queue.get_nowait()
                except Empty:
                    pass
            
            # Aggiungi alla coda
            self.offline_queue.put(offline_entry)
            
            # Salva su file
            self.save_offline_queue()
            
            print(f"💾 Accesso salvato in coda offline ({self.offline_queue.qsize()} elementi)")
            
        except Exception as e:
            print(f"❌ Errore salvataggio coda offline: {e}")
            if self.logger:
                self.logger.log_system_event("offline_queue_error", str(e), "error")
    
    def sync_offline_data(self):
        """Sincronizza i dati offline con il server"""
        if not self.is_online or not Config.OFFLINE_SYNC_ENABLED:
            return
        
        if self.offline_queue.empty():
            return
        
        self.stats['last_sync_attempt'] = datetime.now().isoformat()
        synced_count = 0
        failed_count = 0
        
        print(f"📤 Inizio sincronizzazione offline ({self.offline_queue.qsize()} elementi)")
        
        # Lista temporanea per elementi falliti
        failed_items = []
        
        while not self.offline_queue.empty() and self.is_online:
            try:
                # Ottieni il prossimo elemento
                offline_entry = self.offline_queue.get_nowait()
                card_info = offline_entry['card_info']
                
                # Tenta la sincronizzazione
                try:
                    if self.mqtt_client and self.mqtt_client.is_connected:
                        # Invia solo i dati (senza aspettare auth response)
                        success = self.mqtt_client.publish_card_data(card_info)
                        
                        if success:
                            synced_count += 1
                            print(f"✅ Sincronizzato: {card_info.get('uid_formatted')} ({synced_count})")
                        else:
                            offline_entry['sync_attempts'] += 1
                            failed_items.append(offline_entry)
                            failed_count += 1
                    else:
                        # Connessione MQTT persa
                        failed_items.append(offline_entry)
                        failed_count += 1
                        break
                        
                except Exception as e:
                    print(f"⚠️ Errore sincronizzazione elemento: {e}")
                    offline_entry['sync_attempts'] += 1
                    
                    # Se troppi tentativi, scarta
                    if offline_entry['sync_attempts'] < Config.CONNECTION_RETRY_ATTEMPTS:
                        failed_items.append(offline_entry)
                    
                    failed_count += 1
                
                # Pausa breve per non sovraccaricare
                time.sleep(0.1)
                
            except Empty:
                break
            except Exception as e:
                print(f"❌ Errore durante sync: {e}")
                break
        
        # Rimetti gli elementi falliti in coda
        for item in failed_items:
            self.offline_queue.put(item)
        
        # Salva la coda aggiornata
        self.save_offline_queue()
        
        # Aggiorna statistiche
        self.stats['pending_sync'] = self.offline_queue.qsize()
        if synced_count > 0:
            self.stats['last_successful_sync'] = datetime.now().isoformat()
        
        # Report finale
        if synced_count > 0 or failed_count > 0:
            print(f"📊 Sincronizzazione completata:")
            print(f"   ✅ Sincronizzati: {synced_count}")
            print(f"   ❌ Falliti: {failed_count}")
            print(f"   ⏳ Rimanenti in coda: {self.offline_queue.qsize()}")
            
            if self.logger:
                self.logger.log_system_event(
                    "offline_sync_completed", 
                    f"Sync: {synced_count} ok, {failed_count} falliti, {self.offline_queue.qsize()} rimanenti"
                )
    
    def save_offline_queue(self):
        """Salva la coda offline su file"""
        try:
            # Converte la coda in lista
            queue_data = []
            temp_queue = Queue()
            
            while not self.offline_queue.empty():
                try:
                    item = self.offline_queue.get_nowait()
                    queue_data.append(item)
                    temp_queue.put(item)
                except Empty:
                    break
            
            # Rimetti tutto nella coda originale
            self.offline_queue = temp_queue
            
            # Salva su file
            with open(self.queue_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'saved_at': datetime.now().isoformat(),
                    'queue_size': len(queue_data),
                    'queue_data': queue_data
                }, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Errore salvataggio coda offline: {e}")
    
    def load_offline_queue(self):
        """Carica la coda offline da file"""
        try:
            if not os.path.exists(self.queue_file_path):
                return
            
            with open(self.queue_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            queue_data = data.get('queue_data', [])
            
            for item in queue_data:
                self.offline_queue.put(item)
            
            if queue_data:
                print(f"📥 Caricati {len(queue_data)} elementi dalla coda offline persistente")
                
        except Exception as e:
            print(f"⚠️ Errore caricamento coda offline: {e}")
    
    def get_status(self):
        """Restituisce lo stato del manager offline"""
        return {
            'enabled': Config.OFFLINE_MODE_ENABLED,
            'online': self.is_online,
            'allow_offline_access': Config.OFFLINE_ALLOW_ACCESS,
            'sync_enabled': Config.OFFLINE_SYNC_ENABLED,
            'queue_size': self.offline_queue.qsize(),
            'stats': self.stats.copy(),
            'last_connection_check': self.last_connection_check
        }
    
    def clear_offline_queue(self):
        """Pulisce la coda offline (usa con cautela!)"""
        try:
            # Svuota la coda
            while not self.offline_queue.empty():
                self.offline_queue.get_nowait()
            
            # Rimuovi il file
            if os.path.exists(self.queue_file_path):
                os.remove(self.queue_file_path)
            
            # Reset statistiche
            self.stats['pending_sync'] = 0
            
            print("🧹 Coda offline pulita")
            
        except Exception as e:
            print(f"❌ Errore pulizia coda offline: {e}")
    
    def force_sync(self):
        """Forza una sincronizzazione immediata"""
        if not self.is_online:
            print("🔴 Impossibile sincronizzare: sistema offline")
            return False
        
        print("🔄 Forzando sincronizzazione...")
        self.sync_offline_data()
        return True
    
    def cleanup(self):
        """Pulizia delle risorse"""
        try:
            print("🛑 Cleanup Offline Manager...")
            
            # Ferma i thread
            self.stop_monitoring_threads()
            
            # Salva la coda finale
            self.save_offline_queue()
            
            print("🧹 Offline Manager cleanup completato")
            
        except Exception as e:
            print(f"⚠️ Errore cleanup Offline Manager: {e}")
    
    def __del__(self):
        """Destructor - cleanup automatico"""
        self.cleanup()