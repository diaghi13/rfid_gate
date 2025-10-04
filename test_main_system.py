#!/usr/bin/env python3
"""
Test semplificato del sistema principale senza MQTT
per verificare la lettura carte
"""
import sys
import os
import time

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_main_system():
    print("🚀 TEST SISTEMA PRINCIPALE - SOLO LETTURA CARTE")
    print("="*60)
    
    try:
        # Import necessari
        from config import Config
        from rfid_manager import RFIDManager
        from logger import AccessLogger
        
        print("✅ Import: OK")
        
        # Setup logger
        logger = AccessLogger()
        
        # Inizializza RFID Manager
        print("\n🔧 Inizializzazione RFID Manager...")
        rfid_manager = RFIDManager()
        
        # Avvia solo i lettori
        print("🎯 Avvio lettori RFID...")
        rfid_manager.start_reading()
        
        print("📋 Lettori attivi:")
        active_readers = rfid_manager.get_active_readers()
        for reader_name in active_readers:
            print(f"   ✅ {reader_name}")
        
        # Test lettura per 15 secondi
        print(f"\n⏱️  TEST LETTURA - 15 secondi")
        print("🔍 Avvicina una carta RFID/NFC ai lettori...")
        
        start_time = time.time()
        last_card = None
        card_count = 0
        
        while time.time() - start_time < 15:
            # Controlla lettori
            for reader_name in active_readers:
                try:
                    uid, card_type = rfid_manager.wait_for_card(timeout=0.1)
                    
                    if uid and uid != last_card:
                        card_count += 1
                        last_card = uid
                        
                        print(f"\n🎉 CARTA RILEVATA #{card_count}:")
                        print(f"   📱 UID: {uid}")
                        print(f"   📋 Tipo: {card_type}")
                        print(f"   ⏱️  Timestamp: {time.time():.2f}")
                        print(f"   🔍 Reader: {reader_name}")
                        
                        # Breve pausa per evitare letture multiple
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"   ⚠️ Errore lettura {reader_name}: {e}")
            
            time.sleep(0.1)
        
        print(f"\n📊 RISULTATI TEST:")
        print(f"   🎯 Carte lette: {card_count}")
        print(f"   ⏱️  Durata test: 15 secondi")
        print(f"   📡 Lettori attivi: {len(active_readers)}")
        
        # Cleanup
        print("\n🧹 Cleanup sistema...")
        rfid_manager.cleanup()
        
        if card_count > 0:
            print("\n🎉 ✅ SISTEMA FUNZIONANTE - Carte lette correttamente!")
        else:
            print("\n⚠️ ❌ NESSUNA CARTA LETTA - Controlla hardware")
            print("     🔧 Possibili cause:")
            print("     • Hardware non collegato")
            print("     • Configurazione errata")
            print("     • Problemi di alimentazione")
            print("     • Conflitti I2C/SPI")
        
        return card_count > 0
        
    except Exception as e:
        print(f"\n❌ ERRORE SISTEMA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_main_system()
    exit(0 if success else 1)