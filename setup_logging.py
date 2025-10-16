#!/usr/bin/env python3
"""
📝 Quick Logging Setup per RFID Gate
===================================
Configura rapidamente il logging su file per il sistema RFID Gate.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

def setup_file_logging(log_directory="logs", log_level="INFO"):
    """
    Configura logging su file per il sistema RFID Gate.
    
    Args:
        log_directory: Directory dove salvare i log
        log_level: Livello di logging (DEBUG, INFO, WARNING, ERROR)
    """
    
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
            # File handler
            logging.FileHandler(log_file, encoding='utf-8'),
            # Console handler (per vedere anche nel terminale)
            logging.StreamHandler()
        ]
    )
    
    print(f"✅ Logging configurato:")
    print(f"   📁 Directory: {log_dir.absolute()}")
    print(f"   📄 File: {log_file.absolute()}")
    print(f"   📊 Livello: {log_level}")
    
    return logging.getLogger("rfid_gate")

def patch_print_to_logging(logger):
    """
    Patch temporaneo per redirigere print() al logging.
    ATTENZIONE: Questo è un hack, ma funziona per debug.
    """
    
    import builtins
    original_print = builtins.print
    
    def logged_print(*args, **kwargs):
        # Converti in stringa
        message = " ".join(str(arg) for arg in args)
        
        # Determina il livello in base al contenuto
        if "❌" in message or "ERROR" in message.upper():
            logger.error(message)
        elif "⚠️" in message or "WARNING" in message.upper():
            logger.warning(message)
        elif "✅" in message or "SUCCESS" in message.upper():
            logger.info(message)
        else:
            logger.info(message)
            
        # Stampa anche nel terminale
        original_print(*args, **kwargs)
    
    # Sostituisce temporaneamente print
    builtins.print = logged_print
    
    print("🔧 Print() ora scrive anche nei log!")
    
    return original_print

def test_logging():
    """Test del sistema di logging"""
    
    print("🧪 Test Sistema Logging")
    print("=" * 30)
    
    # Setup logging
    logger = setup_file_logging()
    
    # Test vari livelli
    logger.info("✅ Test logging INFO")
    logger.warning("⚠️ Test logging WARNING") 
    logger.error("❌ Test logging ERROR")
    
    # Test patch print
    print("\n🔧 Test patch print:")
    original_print = patch_print_to_logging(logger)
    
    print("✅ Questo dovrebbe apparire nei log")
    print("⚠️ Questo è un warning")
    print("❌ Questo è un errore")
    print("📋 Questo è un messaggio normale")
    
    # Verifica file creato
    log_file = Path("logs/system.log")
    if log_file.exists():
        print(f"\n📄 Log file creato: {log_file.absolute()}")
        print("   Contenuto:")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Ultimi 5
                print(f"      {line.strip()}")
    
    # Ripristina print originale se vuoi
    # builtins.print = original_print

if __name__ == "__main__":
    test_logging()