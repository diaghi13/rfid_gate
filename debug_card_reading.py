#!/usr/bin/env python3
"""
Debug completo per identificare problemi lettura card
"""
import sys
import os
import time
from datetime import datetime

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_system():
    print("🔍 DEBUG CARD READING")
    print("="*60)
    
    # 1. Test importazioni
    print("\n1️⃣ TEST IMPORTAZIONI")
    try:
        from config import Config
        print("✅ Config importato")
        
        from rfid_manager import RFIDManager
        print("✅ RFIDManager importato")
        
        from rfid_readers.base_reader import BaseRFIDReader
        print("✅ BaseRFIDReader importato")
        
        # Test specifico PN532
        try:
            from rfid_readers.pn532_reader import PN532Reader
            print("✅ PN532Reader importato")
        except Exception as e:
            print(f"❌ PN532Reader: {e}")
        
        # Test specifico MFRC522
        try:
            from rfid_readers.mfrc522_reader import MFRC522Reader
            print("✅ MFRC522Reader importato")
        except Exception as e:
            print(f"❌ MFRC522Reader: {e}")
            
    except Exception as e:
        print(f"❌ Errore importazione: {e}")
        return False
    
    # 2. Test configurazione
    print("\n2️⃣ TEST CONFIGURAZIONE")
    try:
        # Configurazione RFID IN
        print(f"RFID_IN_ENABLE: {Config.RFID_IN_ENABLE}")
        print(f"RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
        
        if Config.RFID_IN_READER_TYPE == 'pn532':
            print(f"RFID_IN_PN532_INTERFACE: {Config.RFID_IN_PN532_INTERFACE}")
            print(f"RFID_IN_PN532_I2C_ADDRESS: {hex(Config.RFID_IN_PN532_I2C_ADDRESS)}")
        elif Config.RFID_IN_READER_TYPE == 'mfrc522':
            print(f"RFID_IN_RST_PIN: {Config.RFID_IN_RST_PIN}")
            print(f"RFID_IN_SDA_PIN: {Config.RFID_IN_SDA_PIN}")
        
        # Configurazione RFID OUT
        if Config.BIDIRECTIONAL_MODE and Config.ENABLE_OUT_READER:
            print(f"RFID_OUT_ENABLE: {Config.RFID_OUT_ENABLE}")
            print(f"RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
            
            if Config.RFID_OUT_READER_TYPE == 'pn532':
                print(f"RFID_OUT_PN532_INTERFACE: {Config.RFID_OUT_PN532_INTERFACE}")
                print(f"RFID_OUT_PN532_I2C_ADDRESS: {hex(Config.RFID_OUT_PN532_I2C_ADDRESS)}")
        
        print("✅ Configurazione caricata")
        
    except Exception as e:
        print(f"❌ Errore configurazione: {e}")
        return False
    
    # 3. Test inizializzazione RFIDManager
    print("\n3️⃣ TEST RFID MANAGER")
    try:
        rfid_manager = RFIDManager()
        print("✅ RFIDManager creato")
        
        # Inizializza
        init_result = rfid_manager.initialize()
        print(f"Inizializzazione: {init_result}")
        
        if init_result:
            # Lettori attivi
            active_readers = rfid_manager.get_active_readers()
            print(f"Lettori attivi: {active_readers}")
            
            # Test start reading
            start_result = rfid_manager.start_reading()
            print(f"Start reading: {start_result}")
            
            if start_result:
                print("\n🔄 SISTEMA IN ASCOLTO")
                print("Prova a passare una card nei prossimi 10 secondi...")
                
                # Test lettura con timeout
                start_time = time.time()
                timeout = 10
                
                while (time.time() - start_time) < timeout:
                    try:
                        # Verifica se c'è una card in coda
                        if not rfid_manager.card_queue.empty():
                            card_info = rfid_manager.card_queue.get_nowait()
                            print(f"\n🎉 CARD LETTA: {card_info}")
                            break
                        
                        # Verifica stato lettori
                        for direction, reader in rfid_manager.readers.items():
                            if reader and hasattr(reader, 'read_card'):
                                try:
                                    # Test lettura diretta (non-blocking)
                                    result = reader.read_card()
                                    if result:
                                        print(f"\n🎯 LETTURA DIRETTA {direction}: {result}")
                                except Exception as e:
                                    # Errore normale se non c'è card
                                    pass
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"⚠️ Errore durante test: {e}")
                        break
                
                print(f"\n⏰ Timeout {timeout}s scaduto")
                
                # Stop reading
                rfid_manager.stop_reading()
                print("🛑 Lettura fermata")
            else:
                print("❌ Impossibile avviare lettura")
        else:
            print("❌ Inizializzazione fallita")
            
            # Debug dettagliato su errori
            print("\n🔍 DEBUG DETTAGLIATO:")
            print(f"Lettori dict: {rfid_manager.readers}")
            
            # Test creazione lettori manuale
            print("\n🛠️ TEST CREAZIONE LETTORI MANUALE")
            
            if Config.RFID_IN_ENABLE and Config.RFID_IN_READER_TYPE == 'pn532':
                try:
                    from rfid_readers.pn532_reader import PN532Reader
                    print("Tentativo creazione PN532Reader IN...")
                    pn532_in = PN532Reader(
                        interface=Config.RFID_IN_PN532_INTERFACE,
                        direction='in',
                        i2c_address=Config.RFID_IN_PN532_I2C_ADDRESS
                    )
                    init_pn532 = pn532_in.initialize()
                    print(f"PN532 IN initialize: {init_pn532}")
                    
                except Exception as e:
                    print(f"❌ Errore PN532 IN: {e}")
            
            if Config.RFID_IN_ENABLE and Config.RFID_IN_READER_TYPE == 'mfrc522':
                try:
                    from rfid_readers.mfrc522_reader import MFRC522Reader
                    print("Tentativo creazione MFRC522Reader IN...")
                    mfrc522_in = MFRC522Reader(
                        rst_pin=Config.RFID_IN_RST_PIN,
                        sda_pin=Config.RFID_IN_SDA_PIN,
                        direction='in'
                    )
                    init_mfrc522 = mfrc522_in.initialize()
                    print(f"MFRC522 IN initialize: {init_mfrc522}")
                    
                except Exception as e:
                    print(f"❌ Errore MFRC522 IN: {e}")
        
    except Exception as e:
        print(f"❌ Errore RFIDManager: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("🏁 DEBUG COMPLETATO")
    return True

if __name__ == "__main__":
    debug_system()