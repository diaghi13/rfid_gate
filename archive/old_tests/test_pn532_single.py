#!/usr/bin/env python3
"""
Script per testare manualmente il sistema PN532 semplificato
Usa .env.pn532_single per test isolati
"""

import os
import sys
import time

# Aggiunge il percorso src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config

def test_pn532_single():
    """Test del singolo lettore PN532 con configurazione semplificata."""
    print("🧪 Test PN532 - Configurazione singola")
    print("=" * 50)
    
    # Carica configurazione da .env.pn532_single
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'examples', '.env.pn532_single')
    
    if not os.path.exists(config_path):
        print(f"❌ File configurazione non trovato: {config_path}")
        return False
    
    # Forza il caricamento della configurazione specifica
    config = Config(config_path)
    
    try:
        from rfid_readers.reader_factory import ReaderFactory
        
        # Crea lettore PN532
        print("🔧 Creazione lettore PN532...")
        reader = ReaderFactory.create_from_config(config)
        
        if not reader:
            print("❌ Impossibile creare lettore PN532")
            return False
        
        print(f"✅ Lettore creato: {reader.reader_id}")
        
        # Test inizializzazione
        print("\n🔄 Test inizializzazione...")
        if reader.initialize():
            print("✅ Inizializzazione riuscita!")
            
            # Test status
            status = reader.get_status()
            print(f"📊 Status: {status}")
            
            # Test lettura per 30 secondi
            print("\n📖 Test lettura carte (30 secondi)...")
            print("💳 Avvicina una carta NFC/RFID...")
            
            start_time = time.time()
            while time.time() - start_time < 30:
                card = reader.read_card()
                if card:
                    print(f"🎯 Carta rilevata: {card}")
                time.sleep(0.1)
            
            print("\n⏰ Test completato")
            reader.cleanup()
            return True
            
        else:
            print("❌ Inizializzazione fallita")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pn532_single()
    sys.exit(0 if success else 1)