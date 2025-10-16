#!/usr/bin/env python3
"""
🔧 RFID Gate Logging Integrator
==============================
Integra il sistema di logging nel main.py del sistema RFID Gate.
"""

import os
import sys
from pathlib import Path

def integrate_logging_to_main():
    """
    Integra il sistema di logging nel main.py
    """
    
    main_file = Path("main.py")
    
    if not main_file.exists():
        print("❌ File main.py non trovato!")
        return False
    
    # Leggi il contenuto attuale
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Controlla se il logging è già integrato
    if "setup_file_logging" in content:
        print("✅ Logging già integrato in main.py")
        return True
    
    # Codice di logging da aggiungere
    logging_code = '''
# 📝 Setup Logging Sistema
import logging
from pathlib import Path

def setup_file_logging(log_directory="logs", log_level="INFO"):
    """Configura logging su file per il sistema RFID Gate."""
    
    # Crea directory log se non esiste
    log_dir = Path(log_directory)
    log_dir.mkdir(exist_ok=True)
    
    # File di log
    log_file = log_dir / "system.log"
    
    # Configura logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    print(f"✅ Logging attivo: {log_file}")
    return logging.getLogger("rfid_gate")

# Inizializza logging all'avvio
logger = setup_file_logging()
logger.info("sistema_avviato: RFID Gate System Started")
'''
    
    # Trova dove inserire il codice (dopo gli import)
    lines = content.split('\n')
    insert_pos = 0
    
    # Cerca la fine degli import
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            insert_pos = i + 1
        elif line.strip() == '' and insert_pos > 0:
            continue
        elif line.strip() and not line.strip().startswith('#') and insert_pos > 0:
            break
    
    # Inserisci il codice di logging
    lines.insert(insert_pos, logging_code)
    
    # Backup del file originale
    backup_file = main_file.with_suffix('.py.backup')
    main_file.rename(backup_file)
    print(f"💾 Backup creato: {backup_file}")
    
    # Scrivi il nuovo contenuto
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Logging integrato in main.py!")
    return True

def quick_log_viewer():
    """Visualizza rapidamente gli ultimi log"""
    
    log_file = Path("logs/system.log")
    
    if not log_file.exists():
        print("❌ File di log non trovato!")
        return
    
    print("📋 Ultimi 20 log:")
    print("=" * 50)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Mostra gli ultimi 20
    for line in lines[-20:]:
        line = line.strip()
        if "ERROR" in line:
            print(f"❌ {line}")
        elif "WARNING" in line:
            print(f"⚠️ {line}")
        elif "AUTORIZZATO" in line:
            print(f"✅ {line}")
        else:
            print(f"📋 {line}")

def watch_logs():
    """Segue i log in tempo reale (come tail -f)"""
    
    log_file = Path("logs/system.log")
    
    if not log_file.exists():
        print("❌ File di log non trovato!")
        return
    
    print("👀 Seguendo i log in tempo reale... (Ctrl+C per uscire)")
    print("=" * 50)
    
    try:
        # Semplice implementazione di tail -f
        with open(log_file, 'r', encoding='utf-8') as f:
            # Va alla fine del file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    line = line.strip()
                    if "ERROR" in line:
                        print(f"❌ {line}")
                    elif "WARNING" in line:
                        print(f"⚠️ {line}")
                    elif "AUTORIZZATO" in line:
                        print(f"✅ {line}")
                    else:
                        print(f"📋 {line}")
                else:
                    import time
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\n👋 Stop watching logs.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "integrate":
            integrate_logging_to_main()
        elif sys.argv[1] == "view":
            quick_log_viewer()
        elif sys.argv[1] == "watch":
            watch_logs()
        else:
            print("Usage: python logging_helper.py [integrate|view|watch]")
    else:
        print("🔧 RFID Gate Logging Helper")
        print("=" * 30)
        print("integrate  - Integra logging in main.py")
        print("view       - Mostra ultimi 20 log")
        print("watch      - Segue log in tempo reale")