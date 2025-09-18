#!/usr/bin/env python3
"""
Sistema di logging semplificato e corretto
"""
import os
import json
import csv
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config import Config

class AccessLogger:
    """Logger semplificato per gli accessi"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        self.setup_system_logger()
        
        # File log
        self.access_log_file = os.path.join(log_dir, "access_log.csv")
        self.json_log_file = os.path.join(log_dir, "access_log.json")
        
        self.initialize_access_logs()
    
    def ensure_log_directory(self):
        """Crea directory log"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_system_logger(self):
        """Setup logger di sistema"""
        self.system_logger = logging.getLogger('rfid_system')
        self.system_logger.setLevel(logging.INFO)
        
        if self.system_logger.handlers:
            return
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        log_file = os.path.join(self.log_dir, "system.log")
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        self.system_logger.addHandler(file_handler)
        self.system_logger.info("Logger inizializzato")
    
    def initialize_access_logs(self):
        """Inizializza file log accessi"""
        if not os.path.exists(self.access_log_file):
            self.create_csv_header()
        
        if not os.path.exists(self.json_log_file):
            self.create_json_file()
    
    def create_csv_header(self):
        """Crea header CSV"""
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
        except Exception as e:
            print(f"Errore creazione CSV: {e}")
    
    def create_json_file(self):
        """Crea file JSON iniziale"""
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
        except Exception as e:
            print(f"Errore creazione JSON: {e}")
    
    def log_access_attempt(self, card_info, auth_result=None, relay_success=False, auth_time_ms=0):
        """Registra tentativo accesso"""
        timestamp = datetime.now()
        
        # Dati log
        log_data = {
            'timestamp': timestamp.isoformat(),
            'card_uid': card_info.get('uid_formatted', 'N/A'),
            'raw_id': card_info.get('raw_id', 'N/A'),
            'tornello_id': Config.TORNELLO_ID,
            'direzione': card_info.get('direction', 'unknown'),  # CORRETTO: dalla card_info
            'authorized': auth_result.get('authorized', False) if auth_result else False,
            'auth_message': auth_result.get('message', '') if auth_result else '',
            'relay_activated': relay_success,
            'card_data': card_info.get('data', ''),
            'auth_time_ms': auth_time_ms,
            'event_type': 'access_attempt'
        }
        
        # Scrivi log
        self.write_csv_log(log_data)
        self.write_json_log(log_data)
        
        # Log sistema
        status = "AUTORIZZATO" if log_data['authorized'] else "NEGATO"
        relay_status = "ATTIVATO" if relay_success else "NON ATTIVATO"
        
        self.system_logger.info(
            f"Accesso {status} - Card: {log_data['card_uid']} - "
            f"Dir: {log_data['direzione']} - Relè: {relay_status}"
        )
        
        return log_data
    
    def write_csv_log(self, log_data):
        """Scrivi CSV"""
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
            print(f"Errore CSV: {e}")
    
    def write_json_log(self, log_data):
        """Scrivi JSON"""
        try:
            # Leggi esistente
            with open(self.json_log_file, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            # Aggiungi nuovo
            data['access_logs'].append(log_data)
            
            # Mantieni ultimi 500
            if len(data['access_logs']) > 500:
                data['access_logs'] = data['access_logs'][-500:]
            
            # Scrivi
            with open(self.json_log_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Errore JSON: {e}")
    
    def log_system_event(self, event_type, message, level="info"):
        """Log evento sistema"""
        if level == "error":
            self.system_logger.error(f"{event_type}: {message}")
        elif level == "warning":
            self.system_logger.warning(f"{event_type}: {message}")
        else:
            self.system_logger.info(f"{event_type}: {message}")
    
    def get_access_stats(self, days=7):
        """Statistiche accessi"""
        try:
            stats = {
                'total_attempts': 0,
                'authorized': 0,
                'denied': 0,
                'unique_cards': set(),
                'relay_activations': 0
            }
            
            if not os.path.exists(self.access_log_file):
                return stats
            
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            with open(self.access_log_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        timestamp = datetime.fromisoformat(row['timestamp'])
                        
                        stats['total_attempts'] += 1
                        
                        if row['authorized'].lower() == 'true':
                            stats['authorized'] += 1
                        else:
                            stats['denied'] += 1
                        
                        if row['relay_activated'].lower() == 'true':
                            stats['relay_activations'] += 1
                        
                        stats['unique_cards'].add(row['card_uid'])
                        
                    except Exception:
                        continue
            
            stats['unique_cards'] = len(stats['unique_cards'])
            return stats
            
        except Exception as e:
            print(f"Errore statistiche: {e}")
            return {}
    
    def print_stats(self, days=7):
        """Stampa statistiche"""
        stats = self.get_access_stats(days)
        
        print(f"\n📊 STATISTICHE ACCESSI (ultimi {days} giorni)")
        print("="*40)
        print(f"🔢 Tentativi totali: {stats.get('total_attempts', 0)}")
        print(f"✅ Autorizzati: {stats.get('authorized', 0)}")
        print(f"❌ Negati: {stats.get('denied', 0)}")
        print(f"🏷️  Card uniche: {stats.get('unique_cards', 0)}")
        print(f"⚡ Relè attivazioni: {stats.get('relay_activations', 0)}")
        print("="*40)