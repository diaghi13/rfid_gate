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
            "DEBOUNCE_": "system",
            # Security
            "AUTH_": "security",
            "MANUAL_OPEN_": "security",
            # Relay
            "RELAY_": "relay",
            # Logging
            "LOG_": "logging",
            # Offline
            "OFFLINE_": "offline",
            "CONNECTION_": "offline",
        }
        
        for key, value in config.items():
            section = "other"
            for prefix, target_section in section_mapping.items():
                if key.startswith(prefix):
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
        
        # Validazione valori
        if "MQTT_PORT" in config:
            try:
                port = int(config["MQTT_PORT"])
                if not (1 <= port <= 65535):
                    errors.append("MQTT_PORT deve essere tra 1 e 65535")
            except ValueError:
                errors.append("MQTT_PORT deve essere un numero")
        
        if "RELAY_IN_PIN" in config:
            try:
                pin = int(config["RELAY_IN_PIN"])
                if not (1 <= pin <= 40):
                    errors.append("RELAY_IN_PIN deve essere tra 1 e 40")
            except ValueError:
                errors.append("RELAY_IN_PIN deve essere un numero")
        
        # Validazione formato booleano
        bool_keys = [
            "MQTT_USE_TLS", "BIDIRECTIONAL_MODE", "RFID_IN_ENABLE", 
            "RFID_OUT_ENABLE", "AUTH_ENABLED", "OFFLINE_MODE_ENABLED"
        ]
        
        for key in bool_keys:
            if key in config and config[key].lower() not in ['true', 'false']:
                errors.append(f"{key} deve essere 'True' o 'False'")
        
        return errors
    
    def get_backup_list(self) -> List[Dict[str, str]]:
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