#!/usr/bin/env python3
"""
Test FOCALIZZATO sui lettori RFID - Solo quello che serve
"""
import sys
import os
import time

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock per macOS
import platform
if platform.system() == "Darwin":
    import unittest.mock
    
    # Mock GPIO
    mock_gpio = unittest.mock.MagicMock()
    mock_gpio.BCM = "BCM"
    mock_gpio.OUT = "OUT"
    mock_gpio.HIGH = 1
    mock_gpio.LOW = 0
    sys.modules['RPi'] = unittest.mock.MagicMock()
    sys.modules['RPi.GPIO'] = mock_gpio
    
    # Mock PN532
    mock_pn532 = unittest.mock.MagicMock()
    sys.modules['pn532'] = mock_pn532
    sys.modules['pn532.i2c'] = mock_pn532
    sys.modules['pn532.spi'] = mock_pn532
    sys.modules['board'] = unittest.mock.MagicMock()
    sys.modules['busio'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.i2c'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.spi'] = unittest.mock.MagicMock()
    
    print("🍎 Mock caricati per macOS")

def test_only_rfid_readers():
    print("🎯 TEST FOCALIZZATO - SOLO LETTORI RFID")
    print("="*60)
    
    try:
        # Solo quello che serve per RFID
        from config import Config
        from rfid_manager import RFIDManager
        
        print("✅ Importazioni RFID completate")
        
        # Test configurazione
        print(f"\n📋 CONFIGURAZIONE ATTUALE:")
        print(f"ENABLE_IN_READER: {Config.ENABLE_IN_READER}")
        print(f"RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
        
        if Config.RFID_IN_READER_TYPE == 'pn532':
            print(f"PN532_INTERFACE: {Config.RFID_IN_PN532_INTERFACE}")
            print(f"PN532_I2C_ADDRESS: {hex(Config.RFID_IN_PN532_I2C_ADDRESS)}")
        
        if hasattr(Config, 'ENABLE_OUT_READER') and Config.ENABLE_OUT_READER:
            print(f"ENABLE_OUT_READER: {Config.ENABLE_OUT_READER}")
            print(f"RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
        
        print(f"\n🔧 CREAZIONE RFID MANAGER")
        rfid_manager = RFIDManager()
        print("✅ RFIDManager creato")
        
        print(f"\n🚀 INIZIALIZZAZIONE")
        init_result = rfid_manager.initialize()
        print(f"📊 Initialize result: {init_result}")
        
        if not init_result:
            print("❌ INIZIALIZZAZIONE FALLITA!")
            print(f"Readers: {rfid_manager.readers}")
            print(f"Is initialized: {rfid_manager.is_initialized}")
            
            # Debug più dettagliato
            print(f"\n🔍 DEBUG FACTORY:")
            from rfid_readers.reader_factory import RFIDReaderFactory
            
            # Test manuale del factory
            if Config.ENABLE_IN_READER:
                print(f"Tentativo creazione reader IN...")
                try:
                    reader_in = RFIDReaderFactory.create_reader(
                        reader_type=Config.RFID_IN_READER_TYPE,
                        reader_id="in",
                        interface=getattr(Config, 'RFID_IN_PN532_INTERFACE', 'i2c'),
                        i2c_address=getattr(Config, 'RFID_IN_PN532_I2C_ADDRESS', 0x24),
                    )
                    print(f"Reader IN creato: {reader_in}")
                    
                    if reader_in:
                        init_in = reader_in.initialize()
                        print(f"Reader IN initialize: {init_in}")
                        
                        if init_in:
                            test_conn = reader_in.test_connection()
                            print(f"Reader IN test connection: {test_conn}")
                            
                except Exception as e:
                    print(f"❌ Errore creazione reader IN: {e}")
            
            return False
        
        print("✅ RFID Manager inizializzato!")
        
        # Verifica lettori
        active_readers = rfid_manager.get_active_readers()
        print(f"📱 Lettori attivi: {active_readers}")
        
        if not active_readers:
            print("❌ NESSUN LETTORE ATTIVO!")
            return False
        
        print(f"\n🔄 START READING")
        start_result = rfid_manager.start_reading()
        print(f"📊 Start reading result: {start_result}")
        
        if not start_result:
            print("❌ START READING FALLITO!")
            return False
        
        print("✅ Sistema in lettura!")
        
        # Test breve di lettura
        print(f"\n⏳ Test lettura per 5 secondi...")
        start_time = time.time()
        found_cards = 0
        
        while (time.time() - start_time) < 5:
            try:
                card_info = rfid_manager.wait_for_card()
                if card_info:
                    found_cards += 1
                    print(f"🎉 CARD #{found_cards}: {card_info}")
                    break
                
                # Debug status ogni secondo
                elapsed = int(time.time() - start_time)
                if elapsed > 0 and elapsed % 1 == 0:
                    # Controlla se threads sono vivi
                    threads_alive = []
                    for reader_id, thread in rfid_manager.reader_threads.items():
                        status = "✅" if thread.is_alive() else "❌"
                        threads_alive.append(f"{reader_id}{status}")
                    
                    queue_size = rfid_manager.card_queue.qsize()
                    print(f"⏰ {elapsed}s - Threads: {' '.join(threads_alive)} - Queue: {queue_size}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"⚠️ Errore nel loop: {e}")
                break
        
        # Stop
        rfid_manager.stop_reading()
        print("🛑 Lettura fermata")
        
        if found_cards > 0:
            print(f"✅ SUCCESS: {found_cards} card rilevate!")
        else:
            print("⚠️ Nessuna card rilevata (normale su macOS senza hardware)")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_only_rfid_readers()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ TEST RFID COMPLETATO")
        print("Se hai visto 'Initialize result: False',")
        print("il problema è che su macOS mancano le librerie hardware.")
        print("Su Raspberry Pi dovrebbe funzionare.")
    else:
        print("❌ TEST FALLITO - Problema nel codice")
    print("="*60)