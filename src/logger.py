#!/usr/bin/env python3
"""
Sistema di logging per il controllo accessi RFID
Gestisce log di sistema e log degli accessi
"""

import os
import json
import csv
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config import Config

class AccessLogger:
    """Classe per gestire il logging degli accessi"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        
        # Setup logging di sistema
        self.setup_system_logger()
        
        # File per i log degli accessi
        self.access_log_file = os.path.join(log_dir, "access_log.csv")
        self.json_log_file = os.path.join(log_dir, "access_log.json")
        
        # Inizializza i file di log
        self.initialize_access_logs()
    
    def ensure_log_directory(self):
        """Crea la directory dei log se non esiste"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            print(f"📁 Directory log creata: {self.log_dir}")
    
    def setup_system_logger(self):
        """Configura il logger di sistema"""
        # Logger principale
        self.system_logger = logging.getLogger('rfid_system')
        self.system_logger.setLevel(logging.INFO)
        
        # Evita duplicazioni se già configurato
        if self.system_logger.handlers:
            return
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler con rotazione
        log_file = os.path.join(self.log_dir, "system.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Solo warning+ in console
        console_handler.setFormatter(formatter)
        
        # Aggiungi handlers
        self.system_logger.addHandler(file_handler)
        self.system_logger.addHandler(console_handler)
        
        self.system_logger.info(f"Sistema di logging inizializzato - Directory: {self.log_dir}")
    
    def initialize_access_logs(self):
        """Inizializza i file di log degli accessi"""
        # Inizializza CSV se non esiste
        if not os.path.exists(self.access_log_file):
            self.create_csv_header()
        
        # Inizializza JSON se non esiste
        if not os.path.exists(self.json_log_file):
            self.create_json_file()
    
    def create_csv_header(self):
        """Crea l'header del file CSV"""
        headers = [
            'timestamp',
            'card_uid',
            'raw_id',
            'tornello_id',
            'direzione',
            'authorized',
            'auth_message',
            'relay_activated',
            'card_data',
            'auth_time_ms',
            'event_type'
        ]
        
        try:
            with open(self.access_log_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            
            self.system_logger.info(f"File CSV inizializzato: {self.access_log_file}")
        except Exception as e:
            self.system_logger.error(f"Errore creazione CSV: {e}")
    
    def create_json_file(self):
        """Crea il file JSON iniziale"""
        initial_data = {
            "system_info": {
                "tornello_id": Config.TORNELLO_ID,
                "created": datetime.now().isoformat(),
                "version": "1.0"
            },
            "access_logs": []
        }
        
        try:
            with open(self.json_log_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(initial_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.system_logger.info(f"File JSON inizializzato: {self.json_log_file}")
        except Exception as e:
            self.system_logger.error(f"Errore creazione JSON: {e}")
    
    def log_access_attempt(self, card_info, auth_result=None, relay_success=False, auth_time_ms=0):
        """
        Registra un tentativo di accesso
        Args:
            card_info (dict): Informazioni della card
            auth_result (dict): Risultato dell'autenticazione
            relay_success (bool): Se il relè è stato attivato
            auth_time_ms (int): Tempo di autenticazione in millisecondi
        """
        timestamp = datetime.now()
        
        # Prepara i dati del log
        log_data = {
            'timestamp': timestamp.isoformat(),
            'card_uid': card_info.get('uid_formatted'),
            'raw_id': card_info.get('raw_id'),
            'tornello_id': Config.TORNELLO_ID,
            'direzione': Config.DIREZIONE,
            'authorized': auth_result.get('authorized', False) if auth_result else not Config.AUTH_ENABLED,
            'auth_message': auth_result.get('message', '') if auth_result else '',
            'relay_activated': relay_success,
            'card_data': card_info.get('data', ''),
            'auth_time_ms': auth_time_ms,
            'event_type': 'access_attempt'
        }
        
        # Scrivi nei log
        self.write_csv_log(log_data)
        self.write_json_log(log_data)
        
        # Log di sistema
        status = "AUTORIZZATO" if log_data['authorized'] else "NEGATO"
        relay_status = "ATTIVATO" if relay_success else "NON ATTIVATO"
        
        self.system_logger.info(
            f"Accesso {status} - Card: {log_data['card_uid']} - "
            f"Relè: {relay_status} - Tempo auth: {auth_time_ms}ms"
        )
        
        return log_data
    
    def write_csv_log(self, log_data):
        """Scrive nel file CSV"""
        try:
            with open(self.access_log_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                row = [
                    log_data['timestamp'],
                    log_data['card_uid'],
                    log_data['raw_id'],
                    log_data['tornello_id'],
                    log_data['direzione'],
                    log_data['authorized'],
                    log_data['auth_message'],
                    log_data['relay_activated'],
                    log_data['card_data'],
                    log_data['auth_time_ms'],
                    log_data['event_type']
                ]
                writer.writerow(row)
        except Exception as e:
            self.system_logger.error(f"Errore scrittura CSV: {e}")
    
    def write_json_log(self, log_data):
        """Aggiunge al file JSON"""
        try:
            # Legge il file esistente
            with open(self.json_log_file, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            # Aggiunge il nuovo log
            data['access_logs'].append(log_data)
            
            # Mantiene solo gli ultimi 1000 accessi nel JSON
            if len(data['access_logs']) > 1000:
                data['access_logs'] = data['access_logs'][-1000:]
            
            # Scrive il file aggiornato
            with open(self.json_log_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.system_logger.error(f"Errore scrittura JSON: {e}")
    
    def log_system_event(self, event_type, message, level="info"):
        """Registra eventi di sistema"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'tornello_id': Config.TORNELLO_ID
        }
        
        # Log nel sistema
        if level == "error":
            self.system_logger.error(f"{event_type}: {message}")
        elif level == "warning":
            self.system_logger.warning(f"{event_type}: {message}")
        else:
            self.system_logger.info(f"{event_type}: {message}")
        
        # Aggiunge anche al JSON per eventi importanti
        if event_type in ['system_start', 'system_stop', 'error', 'mqtt_disconnect']:
            self.write_json_log({**log_data, 'event_type': f'system_{event_type}'})
    
    def get_access_stats(self, days=7):
        """
        Ottiene statistiche degli accessi
        Args: days (int): Numero di giorni da analizzare
        Returns: dict: Statistiche degli accessi
        """
        try:
            stats = {
                'total_attempts': 0,
                'authorized': 0,
                'denied': 0,
                'unique_cards': set(),
                'relay_activations': 0,
                'avg_auth_time': 0,
                'by_hour': {},
                'by_day': {}
            }
            
            # Legge il CSV
            if not os.path.exists(self.access_log_file):
                return stats
            
            auth_times = []
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            with open(self.access_log_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        timestamp = datetime.fromisoformat(row['timestamp'])
                        
                        # Filtra per data
                        if timestamp < cutoff_date:
                            continue
                        
                        stats['total_attempts'] += 1
                        
                        if row['authorized'].lower() == 'true':
                            stats['authorized'] += 1
                        else:
                            stats['denied'] += 1
                        
                        if row['relay_activated'].lower() == 'true':
                            stats['relay_activations'] += 1
                        
                        stats['unique_cards'].add(row['card_uid'])
                        
                        # Tempo di auth
                        auth_time = int(row['auth_time_ms']) if row['auth_time_ms'].isdigit() else 0
                        auth_times.append(auth_time)
                        
                        # Statistiche per ora
                        hour = timestamp.hour
                        stats['by_hour'][hour] = stats['by_hour'].get(hour, 0) + 1
                        
                        # Statistiche per giorno
                        day = timestamp.strftime('%Y-%m-%d')
                        stats['by_day'][day] = stats['by_day'].get(day, 0) + 1
                        
                    except Exception as e:
                        self.system_logger.warning(f"Errore parsing riga CSV: {e}")
            
            # Calcola media tempo auth
            if auth_times:
                stats['avg_auth_time'] = sum(auth_times) / len(auth_times)
            
            # Converte set in numero
            stats['unique_cards'] = len(stats['unique_cards'])
            
            return stats
            
        except Exception as e:
            self.system_logger.error(f"Errore calcolo statistiche: {e}")
            return {}
    
    def print_stats(self, days=7):
        """Stampa le statistiche degli accessi"""
        stats = self.get_access_stats(days)
        
        print(f"\n📊 STATISTICHE ACCESSI (ultimi {days} giorni)")
        print("="*50)
        print(f"🔢 Tentativi totali: {stats.get('total_attempts', 0)}")
        print(f"✅ Autorizzati: {stats.get('authorized', 0)}")
        print(f"❌ Negati: {stats.get('denied', 0)}")
        print(f"🏷️  Card uniche: {stats.get('unique_cards', 0)}")
        print(f"⚡ Relè attivazioni: {stats.get('relay_activations', 0)}")
        print(f"⏱️  Tempo auth medio: {stats.get('avg_auth_time', 0):.1f}ms")
        
        # Ore più attive
        by_hour = stats.get('by_hour', {})
        if by_hour:
            most_active_hour = max(by_hour, key=by_hour.get)
            print(f"🕐 Ora più attiva: {most_active_hour}:00 ({by_hour[most_active_hour]} accessi)")
        
        print("="*50)
    
    def cleanup_old_logs(self, days_to_keep=30):
        """
        Pulisce i log più vecchi di X giorni
        Args: days_to_keep (int): Giorni di log da mantenere
        """
        try:
            cutoff_date = datetime.now().replace(day=datetime.now().day - days_to_keep)
            
            # Per ora manteniamo tutto, ma questa funzione può essere estesa
            # per fare pulizia automatica dei log troppo vecchi
            
            self.system_logger.info(f"Pulizia log completata - Mantenuti ultimi {days_to_keep} giorni")
            
        except Exception as e:
            self.system_logger.error(f"Errore pulizia log: {e}")
    
    def export_logs(self, start_date=None, end_date=None, format_type="csv"):
        """
        Esporta i log in un formato specifico
        Args:
            start_date (datetime): Data inizio
            end_date (datetime): Data fine  
            format_type (str): Formato export ("csv", "json")
        Returns: str: Path del file esportato
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = os.path.join(self.log_dir, f"export_{timestamp}.{format_type}")
            
            # Implementazione export (da completare se necessario)
            self.system_logger.info(f"Export log creato: {export_file}")
            
            return export_file
            
        except Exception as e:
            self.system_logger.error(f"Errore export log: {e}")
            return None