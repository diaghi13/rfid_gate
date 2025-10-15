#!/usr/bin/env python3
"""
🎛️ GPIO Configuration Helper - RFID Gate
========================================

Script interattivo per configurare i pin GPIO del sistema RFID Gate.
Mantiene compatibilità con sistema legacy e permette personalizzazioni.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Colori per output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_colored(text: str, color: str = Colors.NC) -> None:
    """Stampa testo colorato"""
    print(f"{color}{text}{Colors.NC}")

def print_header(title: str) -> None:
    """Stampa intestazione formattata"""
    print_colored("\n" + "=" * 60, Colors.BLUE)
    print_colored(f" {title}", Colors.WHITE)
    print_colored("=" * 60, Colors.BLUE)

def print_section(title: str) -> None:
    """Stampa sezione"""
    print_colored(f"\n--- {title} ---", Colors.CYAN)

# Configurazioni predefinite
LEGACY_CONFIG = {
    'in_reader': {
        'rst_pin': 22,
        'sda_pin': 8,
        'description': 'PN532 I2C - Sistema Legacy Testato'
    },
    'out_reader': {
        'rst_pin': 25,
        'sda_pin': 7,
        'description': 'PN532 SPI - Sistema Legacy Testato'
    }
}

ALTERNATIVE_CONFIGS = {
    'mfrc522_standard': {
        'in_reader': {
            'rst_pin': 22,
            'sda_pin': 24,
            'description': 'MFRC522 Standard Wiring'
        },
        'out_reader': {
            'rst_pin': 25,
            'sda_pin': 8,
            'description': 'MFRC522 Dual Reader Setup'
        }
    },
    'custom_pn532': {
        'in_reader': {
            'rst_pin': 18,
            'sda_pin': 23,
            'description': 'PN532 Custom Wiring'
        },
        'out_reader': {
            'rst_pin': 24,
            'sda_pin': 25,
            'description': 'PN532 Custom Dual Setup'
        }
    }
}

def get_gpio_info() -> Dict[str, str]:
    """Restituisce informazioni sui pin GPIO Raspberry Pi"""
    return {
        '7': 'GPIO 4',
        '8': 'GPIO 14',
        '10': 'GPIO 15',
        '11': 'GPIO 17',
        '12': 'GPIO 18',
        '13': 'GPIO 27',
        '15': 'GPIO 22',
        '16': 'GPIO 23',
        '18': 'GPIO 24',
        '19': 'GPIO 10',
        '21': 'GPIO 9',
        '22': 'GPIO 25',
        '23': 'GPIO 11',
        '24': 'GPIO 8',
        '26': 'GPIO 7',
        '29': 'GPIO 5',
        '31': 'GPIO 6',
        '32': 'GPIO 12',
        '33': 'GPIO 13',
        '35': 'GPIO 19',
        '36': 'GPIO 16',
        '37': 'GPIO 26',
        '38': 'GPIO 20',
        '40': 'GPIO 21'
    }

def show_current_config() -> Dict[str, Any]:
    """Mostra configurazione attuale dal .env"""
    print_section("Configurazione Attuale")
    
    env_file = Path('.env')
    if not env_file.exists():
        print_colored("⚠️ File .env non trovato!", Colors.YELLOW)
        return {}
    
    current_config = {}
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Rimuovi commenti inline
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    
                    current_config[key] = value
        
        # Estrai configurazione GPIO
        gpio_config = {
            'in_reader': {
                'rst_pin': int(current_config.get('RFID_IN_RST_PIN', 22)),
                'sda_pin': int(current_config.get('RFID_IN_SDA_PIN', 8))
            },
            'out_reader': {
                'rst_pin': int(current_config.get('RFID_OUT_RST_PIN', 25)),
                'sda_pin': int(current_config.get('RFID_OUT_SDA_PIN', 7))
            }
        }
        
        print_colored("📋 Configurazione GPIO Attuale:", Colors.GREEN)
        print(f"  🔵 Lettore IN:  RST={gpio_config['in_reader']['rst_pin']}, SDA={gpio_config['in_reader']['sda_pin']}")
        print(f"  🟡 Lettore OUT: RST={gpio_config['out_reader']['rst_pin']}, SDA={gpio_config['out_reader']['sda_pin']}")
        
        return gpio_config
        
    except Exception as e:
        print_colored(f"❌ Errore lettura .env: {e}", Colors.RED)
        return {}

def show_predefined_configs() -> None:
    """Mostra configurazioni predefinite"""
    print_section("Configurazioni Predefinite")
    
    print_colored("1️⃣ Sistema Legacy (Raccomandato - Testato e Funzionante)", Colors.GREEN)
    print(f"   🔵 IN:  RST={LEGACY_CONFIG['in_reader']['rst_pin']}, SDA={LEGACY_CONFIG['in_reader']['sda_pin']} ({LEGACY_CONFIG['in_reader']['description']})")
    print(f"   🟡 OUT: RST={LEGACY_CONFIG['out_reader']['rst_pin']}, SDA={LEGACY_CONFIG['out_reader']['sda_pin']} ({LEGACY_CONFIG['out_reader']['description']})")
    
    print_colored("\n2️⃣ MFRC522 Standard", Colors.BLUE)
    config = ALTERNATIVE_CONFIGS['mfrc522_standard']
    print(f"   🔵 IN:  RST={config['in_reader']['rst_pin']}, SDA={config['in_reader']['sda_pin']} ({config['in_reader']['description']})")
    print(f"   🟡 OUT: RST={config['out_reader']['rst_pin']}, SDA={config['out_reader']['sda_pin']} ({config['out_reader']['description']})")
    
    print_colored("\n3️⃣ PN532 Custom", Colors.PURPLE)
    config = ALTERNATIVE_CONFIGS['custom_pn532']
    print(f"   🔵 IN:  RST={config['in_reader']['rst_pin']}, SDA={config['in_reader']['sda_pin']} ({config['in_reader']['description']})")
    print(f"   🟡 OUT: RST={config['out_reader']['rst_pin']}, SDA={config['out_reader']['sda_pin']} ({config['out_reader']['description']})")
    
    print_colored("\n4️⃣ Configurazione Personalizzata", Colors.CYAN)

def show_gpio_pinout() -> None:
    """Mostra pinout GPIO Raspberry Pi"""
    print_section("GPIO Pinout Raspberry Pi (Pins Utilizzabili)")
    
    gpio_info = get_gpio_info()
    
    print_colored("📌 Pin Fisici Disponibili:", Colors.YELLOW)
    for i, (pin, gpio) in enumerate(sorted(gpio_info.items(), key=lambda x: int(x[0]))):
        if i % 4 == 0:
            print()
        print(f"Pin {pin:2s}({gpio:8s})", end="  ")
    print("\n")

def get_user_choice() -> str:
    """Ottiene scelta utente"""
    while True:
        choice = input(f"\n{Colors.WHITE}Seleziona configurazione (1-4): {Colors.NC}").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print_colored("⚠️ Scelta non valida. Inserisci 1, 2, 3 o 4.", Colors.YELLOW)

def get_custom_config() -> Dict[str, Any]:
    """Ottiene configurazione personalizzata dall'utente"""
    print_section("Configurazione Personalizzata")
    
    config = {'in_reader': {}, 'out_reader': {}}
    
    # Configurazione lettore IN
    print_colored("🔵 Configurazione Lettore IN:", Colors.BLUE)
    config['in_reader']['rst_pin'] = get_pin_input("RST pin lettore IN", 22)
    config['in_reader']['sda_pin'] = get_pin_input("SDA/CS pin lettore IN", 8)
    
    # Configurazione lettore OUT
    print_colored("🟡 Configurazione Lettore OUT:", Colors.PURPLE)
    config['out_reader']['rst_pin'] = get_pin_input("RST pin lettore OUT", 25)
    config['out_reader']['sda_pin'] = get_pin_input("SDA/CS pin lettore OUT", 7)
    
    return config

def get_pin_input(description: str, default: int) -> int:
    """Ottiene input pin dall'utente con validazione"""
    gpio_info = get_gpio_info()
    
    while True:
        try:
            user_input = input(f"  {description} (default {default}): ").strip()
            
            if not user_input:
                return default
            
            pin = int(user_input)
            
            # Validazione pin
            if str(pin) not in gpio_info:
                print_colored(f"    ⚠️ Pin {pin} non valido. Usa un pin dalla lista.", Colors.YELLOW)
                continue
            
            return pin
            
        except ValueError:
            print_colored("    ⚠️ Inserisci un numero valido.", Colors.YELLOW)

def update_env_file(config: Dict[str, Any]) -> bool:
    """Aggiorna file .env con nuova configurazione"""
    print_section("Aggiornamento File .env")
    
    env_file = Path('.env')
    if not env_file.exists():
        print_colored("❌ File .env non trovato!", Colors.RED)
        return False
    
    try:
        # Backup del file originale
        backup_file = env_file.with_suffix('.env.backup')
        with open(env_file, 'r') as original:
            with open(backup_file, 'w') as backup:
                backup.write(original.read())
        
        print_colored(f"💾 Backup creato: {backup_file}", Colors.YELLOW)
        
        # Leggi e aggiorna contenuto
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Aggiorna linee GPIO
        updated_lines = []
        for line in lines:
            if line.startswith('RFID_IN_RST_PIN='):
                updated_lines.append(f"RFID_IN_RST_PIN={config['in_reader']['rst_pin']}\n")
            elif line.startswith('RFID_IN_SDA_PIN='):
                updated_lines.append(f"RFID_IN_SDA_PIN={config['in_reader']['sda_pin']}\n")
            elif line.startswith('RFID_OUT_RST_PIN='):
                updated_lines.append(f"RFID_OUT_RST_PIN={config['out_reader']['rst_pin']}\n")
            elif line.startswith('RFID_OUT_SDA_PIN='):
                updated_lines.append(f"RFID_OUT_SDA_PIN={config['out_reader']['sda_pin']}\n")
            else:
                updated_lines.append(line)
        
        # Scrivi file aggiornato
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print_colored("✅ File .env aggiornato con successo!", Colors.GREEN)
        return True
        
    except Exception as e:
        print_colored(f"❌ Errore aggiornamento .env: {e}", Colors.RED)
        return False

def show_final_config(config: Dict[str, Any]) -> None:
    """Mostra configurazione finale"""
    print_section("Configurazione Finale")
    
    gpio_info = get_gpio_info()
    
    print_colored("📋 Configurazione GPIO Applicata:", Colors.GREEN)
    
    # Lettore IN
    in_rst = config['in_reader']['rst_pin']
    in_sda = config['in_reader']['sda_pin']
    in_rst_gpio = gpio_info.get(str(in_rst), f"GPIO {in_rst}")
    in_sda_gpio = gpio_info.get(str(in_sda), f"GPIO {in_sda}")
    
    print(f"  🔵 Lettore IN:")
    print(f"     RST: Pin {in_rst} ({in_rst_gpio})")
    print(f"     SDA: Pin {in_sda} ({in_sda_gpio})")
    
    # Lettore OUT
    out_rst = config['out_reader']['rst_pin']
    out_sda = config['out_reader']['sda_pin']
    out_rst_gpio = gpio_info.get(str(out_rst), f"GPIO {out_rst}")
    out_sda_gpio = gpio_info.get(str(out_sda), f"GPIO {out_sda}")
    
    print(f"  🟡 Lettore OUT:")
    print(f"     RST: Pin {out_rst} ({out_rst_gpio})")
    print(f"     SDA: Pin {out_sda} ({out_sda_gpio})")
    
    print_colored("\n🔄 Prossimi Passi:", Colors.CYAN)
    print("1. Verifica connessioni fisiche dei lettori")
    print("2. Riavvia il sistema: python3 main.py")
    print("3. Test configurazione: python3 test_legacy_pn532.py")

def main():
    """Funzione principale"""
    print_header("🎛️ GPIO Configuration Helper - RFID Gate")
    print_colored("Configurazione pin GPIO per lettori RFID", Colors.WHITE)
    
    # Mostra configurazione attuale
    current_config = show_current_config()
    
    # Mostra pinout GPIO
    show_gpio_pinout()
    
    # Mostra configurazioni predefinite
    show_predefined_configs()
    
    # Ottieni scelta utente
    choice = get_user_choice()
    
    # Elabora scelta
    if choice == '1':
        new_config = LEGACY_CONFIG
        print_colored("\n✅ Configurazione Legacy selezionata (Raccomandato)", Colors.GREEN)
    elif choice == '2':
        new_config = ALTERNATIVE_CONFIGS['mfrc522_standard']
        print_colored("\n🔧 Configurazione MFRC522 Standard selezionata", Colors.BLUE)
    elif choice == '3':
        new_config = ALTERNATIVE_CONFIGS['custom_pn532']
        print_colored("\n🔧 Configurazione PN532 Custom selezionata", Colors.PURPLE)
    elif choice == '4':
        new_config = get_custom_config()
        print_colored("\n🎨 Configurazione Personalizzata creata", Colors.CYAN)
    
    # Conferma before applying
    print_colored(f"\n📋 Nuova Configurazione:", Colors.YELLOW)
    print(f"  🔵 IN:  RST={new_config['in_reader']['rst_pin']}, SDA={new_config['in_reader']['sda_pin']}")
    print(f"  🟡 OUT: RST={new_config['out_reader']['rst_pin']}, SDA={new_config['out_reader']['sda_pin']}")
    
    confirm = input(f"\n{Colors.WHITE}Applicare questa configurazione? (y/N): {Colors.NC}").strip().lower()
    
    if confirm in ['y', 'yes', 'si', 's']:
        if update_env_file(new_config):
            show_final_config(new_config)
            print_colored("\n🎉 Configurazione completata con successo!", Colors.GREEN)
        else:
            print_colored("\n❌ Errore durante la configurazione.", Colors.RED)
            sys.exit(1)
    else:
        print_colored("\n❌ Configurazione annullata.", Colors.YELLOW)
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n⏹️ Configurazione interrotta dall'utente.", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n❌ Errore imprevisto: {e}", Colors.RED)
        sys.exit(1)