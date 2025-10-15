#!/usr/bin/env python3
"""
Config Manager per RFID Gate Web UI
===================================

Gestisce la lettura e scrittura del file .env
e la sincronizzazione con le configurazioni di sistema.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ConfigManager:
    """Gestisce le configurazioni del sistema RFID Gate"""
    
    def __init__(self, project_root: str = None):
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect project root
            current_dir = Path(__file__).parent
            self.project_root = current_dir.parent
        
        self.env_file = self.project_root / ".env"
        self.backup_dir = self.project_root / "backups" / "config"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def load_env_config(self) -> Dict[str, str]:
        """Carica configurazione da file .env"""
        config = {}
        
        if not self.env_file.exists():
            return config
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Ignora linee vuote e commenti
                    if not line or line.startswith('#'):
                        continue
                    
                    # Cerca formato KEY=VALUE
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Rimuovi commenti inline
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    
                    # Rimuovi virgolette se presenti
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    config[key] = value
            
            return config
            
        except Exception as e:
            print(f"⚠️ Errore caricamento .env: {e}")
            return {}
    
    def save_env_config(self, config: Dict[str, str], create_backup: bool = True) -> bool:
        """Salva configurazione nel file .env"""
        try:
            # Crea backup se richiesto
            if create_backup and self.env_file.exists():
                self._create_backup()
            
            # Leggi il file esistente per preservare commenti e struttura
            original_lines = []
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()
            
            # Processa le linee
            new_lines = []
            updated_keys = set()
            
            for line in original_lines:
                stripped_line = line.strip()
                
                # Preserva commenti e linee vuote
                if not stripped_line or stripped_line.startswith('#'):
                    new_lines.append(line)
                    continue
                
                # Cerca chiavi da aggiornare
                if '=' in stripped_line:
                    key = stripped_line.split('=')[0].strip()
                    if key in config:
                        # Aggiorna valore mantenendo eventuale commento inline
                        comment = ""
                        if '#' in line:
                            comment = ' ' + '#'.join(line.split('#')[1:])
                        
                        new_lines.append(f"{key}={config[key]}{comment}")
                        updated_keys.add(key)
                    else:
                        # Mantieni linea originale
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Aggiungi nuove chiavi non presenti nel file originale
            new_keys = set(config.keys()) - updated_keys
            if new_keys:
                new_lines.append("\n# Configurazioni aggiunte automaticamente\n")
                for key in sorted(new_keys):
                    new_lines.append(f"{key}={config[key]}\n")
            
            # Scrivi il file aggiornato
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            print(f"✅ Configurazione salvata in {self.env_file}")
            print(f"   📝 Aggiornate {len(updated_keys)} chiavi esistenti")
            print(f"   ➕ Aggiunte {len(new_keys)} nuove chiavi")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore salvataggio .env: {e}")
            return False
    
    def _create_backup(self) -> str:
        """Crea backup del file .env corrente"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f".env_backup_{timestamp}"
        backup_path = self.backup_dir / backup_filename
        
        try:
            shutil.copy2(self.env_file, backup_path)
            print(f"💾 Backup creato: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"⚠️ Errore creazione backup: {e}")
            return ""
    
    def get_config_sections(self) -> Dict[str, Dict[str, str]]:
        """Organizza la configurazione in sezioni logiche"""
        config = self.load_env_config()
        
        sections = {
            "mqtt": {},
            "readers": {},
            "system": {},
            "security": {},
            "relay": {},
            "logging": {},
            "offline": {},
            "sync": {},
            "timing": {},
            "uid": {},
            "debug": {},
            "other": {}
        }
        
        # Mappatura chiavi -> sezioni
        section_mapping = {
            # MQTT
            "MQTT_": "mqtt",
            # Readers
            "RFID_": "readers", 
            "PN532_": "readers",
            "MFRC522_": "readers",
            # System  
            "TORNELLO_": "system",
            "BIDIRECTIONAL_": "system",
            "ENABLE_": "system",
            # Security
            "AUTH_": "security",
            "MANUAL_OPEN_": "security",
            # Relay
            "RELAY_": "relay",
            # Logging
            "LOG_": "logging",
            "ACCESS_LOG": "logging",
            # Offline
            "OFFLINE_": "offline",
            "CONNECTION_": "offline",
            # Sync
            "SYNC_": "sync",
            # Timing
            "CARD_READ_INTERVAL": "timing",
            "RFID_DEBOUNCE_TIME": "timing", 
            "GLOBAL_DEBOUNCE_TIME": "timing",
            "MQTT_TIMEOUT": "timing",
            # UID
            "UID_": "uid",
            # Debug
            "DEBUG_": "debug",
            "SIMULATION_": "debug",
        }
        
        for key, value in config.items():
            section = "other"
            for prefix, target_section in section_mapping.items():
                if key.startswith(prefix) or key == prefix:
                    section = target_section
                    break
            
            sections[section][key] = value
        
        return sections
    
    def update_section(self, section_name: str, section_config: Dict[str, str]) -> bool:
        """Aggiorna una sezione specifica della configurazione"""
        current_config = self.load_env_config()
        
        # Aggiorna solo le chiavi della sezione
        current_config.update(section_config)
        
        return self.save_env_config(current_config)
    
    def validate_config(self, config: Dict[str, str]) -> List[str]:
        """Valida la configurazione e restituisce eventuali errori"""
        errors = []
        
        # Validazioni base
        required_keys = [
            "MQTT_BROKER",
            "TORNELLO_ID",
            "RFID_IN_READER_TYPE"
        ]
        
        for key in required_keys:
            if key not in config or not config[key]:
                errors.append(f"Campo obbligatorio mancante: {key}")
        
        # Validazione valori numerici
        numeric_validations = {
            "MQTT_PORT": (1, 65535, "MQTT_PORT deve essere tra 1 e 65535"),
            "RELAY_IN_PIN": (1, 40, "RELAY_IN_PIN deve essere tra 1 e 40"),
            "RELAY_OUT_PIN": (1, 40, "RELAY_OUT_PIN deve essere tra 1 e 40"),
            "BIDIRECTIONAL_TIMEOUT_HOURS": (0.1, 168.0, "BIDIRECTIONAL_TIMEOUT_HOURS deve essere tra 0.1 e 168 ore"),
            "SYNC_UPDATES_INTERVAL": (1, 1440, "SYNC_UPDATES_INTERVAL deve essere tra 1 e 1440 minuti"),
            "SYNC_LOGS_INTERVAL": (1, 60, "SYNC_LOGS_INTERVAL deve essere tra 1 e 60 minuti"),
            "CARD_READ_INTERVAL": (0.01, 5.0, "CARD_READ_INTERVAL deve essere tra 0.01 e 5.0 secondi"),
            "RFID_DEBOUNCE_TIME": (0.1, 10.0, "RFID_DEBOUNCE_TIME deve essere tra 0.1 e 10.0 secondi"),
        }
        
        for key, (min_val, max_val, error_msg) in numeric_validations.items():
            if key in config and config[key]:
                try:
                    value = float(config[key])
                    if not (min_val <= value <= max_val):
                        errors.append(error_msg)
                except ValueError:
                    errors.append(f"{key} deve essere un numero")
        
        # Validazioni specifiche
        if "UID_FORMAT_MODE" in config:
            valid_modes = ["remove_suffix", "fixed_length", "raw"]
            if config["UID_FORMAT_MODE"] not in valid_modes:
                errors.append(f"UID_FORMAT_MODE deve essere uno di: {', '.join(valid_modes)}")
        
        if "RFID_IN_READER_TYPE" in config:
            valid_types = ["mfrc522", "pn532"]
            if config["RFID_IN_READER_TYPE"] not in valid_types:
                errors.append(f"RFID_IN_READER_TYPE deve essere uno di: {', '.join(valid_types)}")
        
        if "RFID_IN_PN532_INTERFACE" in config:
            valid_interfaces = ["i2c", "spi", "uart"]
            if config["RFID_IN_PN532_INTERFACE"] not in valid_interfaces:
                errors.append(f"RFID_IN_PN532_INTERFACE deve essere uno di: {', '.join(valid_interfaces)}")
        
        # Validazioni URL
        if "SYNC_SERVER_URL" in config and config["SYNC_SERVER_URL"]:
            url = config["SYNC_SERVER_URL"]
            if not (url.startswith("http://") or url.startswith("https://")):
                errors.append("SYNC_SERVER_URL deve iniziare con http:// o https://")
        
        return errors
    
    def get_config_descriptions(self) -> Dict[str, Dict[str, str]]:
        """Restituisce descrizioni per tutte le configurazioni"""
        return {
            "mqtt": {
                "MQTT_BROKER": "Indirizzo del broker MQTT",
                "MQTT_PORT": "Porta del broker MQTT (1883 o 8883)",
                "MQTT_USERNAME": "Username per autenticazione MQTT",
                "MQTT_PASSWORD": "Password per autenticazione MQTT",
                "MQTT_USE_TLS": "Abilita connessione sicura TLS",
                "MQTT_KEEP_ALIVE": "Intervallo keep-alive in secondi",
                "MQTT_CARD_READ_TOPIC": "Topic per invio letture carte",
                "MQTT_AUTH_RESPONSE_TOPIC": "Topic per risposte autenticazione",
                "MQTT_MANUAL_OPEN_TOPIC": "Topic per aperture manuali"
            },
            "system": {
                "TORNELLO_ID": "Identificativo unico del tornello",
                "BIDIRECTIONAL_MODE": "Abilita controllo bidirezionale",
                "BIDIRECTIONAL_TIMEOUT_HOURS": "Timeout reset stato direzione (ore)",
                "ENABLE_IN_READER": "Abilita lettore ingresso",
                "ENABLE_OUT_READER": "Abilita lettore uscita"
            },
            "readers": {
                "RFID_IN_READER_TYPE": "Tipo lettore ingresso (mfrc522/pn532)",
                "RFID_IN_PN532_INTERFACE": "Interfaccia PN532 (i2c/spi/uart)",
                "RFID_IN_PN532_I2C_ADDRESS": "Indirizzo I2C del PN532",
                "RFID_OUT_READER_TYPE": "Tipo lettore uscita (mfrc522/pn532)",
                "RFID_OUT_PN532_INTERFACE": "Interfaccia PN532 uscita",
                "PN532_READ_TIMEOUT": "Timeout lettura PN532 (secondi)",
                "PN532_MAX_ERRORS": "Massimo errori consecutivi PN532",
                "PN532_RESET_DELAY": "Delay reset PN532 (secondi)"
            },
            "sync": {
                "SYNC_ENABLED": "Abilita sistema sincronizzazione",
                "SYNC_SERVER_URL": "URL server per sincronizzazione",
                "SYNC_DAILY_TIME": "Ora sync giornaliera (HH:MM)",
                "SYNC_UPDATES_INTERVAL": "Intervallo check aggiornamenti (minuti)",
                "SYNC_LOGS_INTERVAL": "Intervallo sync log (minuti)",
                "SYNC_CONNECTION_TIMEOUT": "Timeout connessione sync (secondi)"
            },
            "timing": {
                "RELAY_CLOSE_DELAY": "Delay chiusura relay (secondi)",
                "RELAY_OPEN_DURATION": "Durata apertura relay (secondi)",
                "READ_INTERVAL": "Intervallo tra letture RFID (secondi)"
            },
            "uid": {
                "UID_FORMAT_MODE": "Formato UID (hex/dec/bytes)",
                "UID_PREFIX": "Prefisso per UID formattati",
                "UID_SUFFIX": "Suffisso per UID formattati"
            },
            "debug": {
                "DEBUG_MODE": "Abilita modalità debug",
                "LOG_LEVEL": "Livello di logging",
                "LOG_TO_FILE": "Salva log su file",
                "LOG_RETENTION_DAYS": "Giorni di conservazione log"
            }
        }

    def _create_backup(self):
        """Ottiene lista dei backup disponibili"""
        backups = []
        
        for backup_file in self.backup_dir.glob(".env_backup_*"):
            try:
                stat = backup_file.stat()
                timestamp_str = backup_file.name.replace(".env_backup_", "")
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "timestamp": timestamp.isoformat(),
                    "size": stat.st_size,
                    "created": timestamp.strftime("%d/%m/%Y %H:%M:%S")
                })
            except Exception:
                continue
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Ripristina un backup specifico"""
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            print(f"❌ Backup non trovato: {backup_filename}")
            return False
        
        try:
            # Crea backup dello stato attuale prima del ripristino
            self._create_backup()
            
            # Ripristina il backup
            shutil.copy2(backup_path, self.env_file)
            print(f"✅ Configurazione ripristinata da: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"❌ Errore ripristino backup: {e}")
            return False


# ==============================================================================
# 🧪 TESTING E DEMO
# ==============================================================================

def demo_config_manager():
    """Demo delle funzionalità del ConfigManager"""
    print("🧪 Demo ConfigManager")
    print("=" * 50)
    
    # Inizializza manager
    manager = ConfigManager()
    
    # Carica configurazione attuale
    print("\n📖 Configurazione attuale:")
    config = manager.load_env_config()
    for key, value in list(config.items())[:5]:  # Solo primi 5 per brevità
        print(f"  {key}={value}")
    
    # Mostra sezioni
    print("\n📂 Sezioni configurazione:")
    sections = manager.get_config_sections()
    for section_name, section_config in sections.items():
        if section_config:  # Solo sezioni non vuote
            print(f"  📁 {section_name}: {len(section_config)} parametri")
    
    # Simula aggiornamento
    print("\n💾 Test aggiornamento configurazione...")
    test_config = config.copy()
    test_config["TEST_DEMO"] = "demo_value_" + datetime.now().strftime("%H%M%S")
    
    if manager.save_env_config(test_config):
        print("✅ Test aggiornamento riuscito")
    
    # Lista backup
    print("\n📋 Backup disponibili:")
    backups = manager.get_backup_list()
    for backup in backups[:3]:  # Solo primi 3
        print(f"  💾 {backup['filename']} - {backup['created']}")


if __name__ == "__main__":
    demo_config_manager()