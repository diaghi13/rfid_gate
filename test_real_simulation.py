#!/usr/bin/env python3
"""
Test REALE del sistema - Simula esattamente quello che fa l'utente
"""
import sys
import os
import time
from datetime import datetime

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock automatico per macOS
import platform
if platform.system() == "Darwin":  # macOS
    print("🍎 macOS rilevato - Carico mock per test")
    
    # Mock per RPi.GPIO
    import unittest.mock
    mock_gpio = unittest.mock.MagicMock()
    mock_gpio.BCM = "BCM"
    mock_gpio.OUT = "OUT"
    mock_gpio.HIGH = 1
    mock_gpio.LOW = 0
    sys.modules['RPi'] = unittest.mock.MagicMock()
    sys.modules['RPi.GPIO'] = mock_gpio
    
    # Mock per PN532 libraries
    mock_pn532 = unittest.mock.MagicMock()
    mock_pn532.read_passive_target.return_value = [1, 2, 3, 4]
    sys.modules['pn532'] = mock_pn532
    sys.modules['pn532.i2c'] = mock_pn532
    sys.modules['pn532.spi'] = mock_pn532
    sys.modules['board'] = unittest.mock.MagicMock()
    sys.modules['busio'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.i2c'] = unittest.mock.MagicMock()
    sys.modules['adafruit_pn532.spi'] = unittest.mock.MagicMock()

def test_real_system_startup():
    print("🔍 TEST SISTEMA REALE - Come fa l'utente")
    print("="*60)
    
    try:
        # Importa esattamente come fa main.py
        from config import Config
        from rfid_manager import RFIDManager
        from relay_manager import RelayManager
        from mqtt_client import MQTTClient
        from logger import AccessLogger
        from offline_manager import OfflineManager
        from manual_control import ManualControl
        
        print("✅ Tutte le importazioni riuscite")
        
        # Simula AccessControlSystem.__init__
        print("\n1️⃣ INIZIALIZZAZIONE COMPONENTI")
        
        # Logger
        try:
            logger = AccessLogger(Config.LOG_DIRECTORY)
            print("✅ Logger inizializzato")
        except Exception as e:
            print(f"❌ Errore Logger: {e}")
            return False
        
        # RFID Manager - IL PUNTO CRITICO
        print("\n2️⃣ RFID MANAGER - PUNTO CRITICO")
        try:
            rfid_manager = RFIDManager()
            print("✅ RFIDManager creato")
            
            # Inizializza - QUI È DOVE PROBABILMENTE FALLISCE
            print("🔄 Inizializzazione in corso...")
            init_result = rfid_manager.initialize()
            print(f"📊 Risultato inizializzazione: {init_result}")
            
            if not init_result:
                print("❌ PROBLEMA IDENTIFICATO: RFIDManager.initialize() fallisce")
                print("🔍 Debug dettagliato:")
                
                # Verifica configurazione
                print(f"  - ENABLE_IN_READER: {Config.ENABLE_IN_READER}")
                print(f"  - RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
                print(f"  - RFID_IN_PN532_INTERFACE: {Config.RFID_IN_PN532_INTERFACE}")
                print(f"  - RFID_IN_PN532_I2C_ADDRESS: {hex(Config.RFID_IN_PN532_I2C_ADDRESS)}")
                
                if hasattr(Config, 'ENABLE_OUT_READER') and Config.ENABLE_OUT_READER:
                    print(f"  - ENABLE_OUT_READER: {Config.ENABLE_OUT_READER}")
                    print(f"  - RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
                    print(f"  - RFID_OUT_PN532_INTERFACE: {Config.RFID_OUT_PN532_INTERFACE}")
                
                # Verifica cosa c'è nei readers
                print(f"  - readers dict: {rfid_manager.readers}")
                print(f"  - is_initialized: {rfid_manager.is_initialized}")
                
                return False
            
            print("✅ RFIDManager inizializzato correttamente")
            
            # Verifica lettori attivi
            active_readers = rfid_manager.get_active_readers()
            print(f"📱 Lettori attivi: {active_readers}")
            
            if not active_readers:
                print("❌ PROBLEMA: Nessun lettore attivo")
                return False
            
        except Exception as e:
            print(f"❌ Errore critico RFIDManager: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Relay Manager
        print("\n3️⃣ RELAY MANAGER")
        try:
            relay_manager = RelayManager()
            relay_init = relay_manager.initialize()
            print(f"✅ RelayManager: {relay_init}")
        except Exception as e:
            print(f"⚠️ RelayManager error: {e}")
        
        # Test start reading - SECONDO PUNTO CRITICO
        print("\n4️⃣ START READING - SECONDO PUNTO CRITICO")
        try:
            start_result = rfid_manager.start_reading()
            print(f"📊 Start reading result: {start_result}")
            
            if not start_result:
                print("❌ PROBLEMA: start_reading() fallisce")
                return False
            
            print("✅ Sistema in lettura")
            
        except Exception as e:
            print(f"❌ Errore start_reading: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test lettura simulata come fa il main loop
        print("\n5️⃣ TEST MAIN LOOP SIMULATO")
        print("⏳ In attesa card (simulando main loop)...")
        
        start_time = time.time()
        timeout = 10
        
        while (time.time() - start_time) < timeout:
            try:
                # Questo è esattamente quello che fa il main loop
                card_info = rfid_manager.wait_for_card()
                
                if card_info is not None:
                    print(f"\n🎉 CARD TROVATA: {card_info}")
                    break
                
                # Stampa status ogni 2 secondi per debug
                if int(time.time() - start_time) % 2 == 0:
                    # Verifica se i thread sono attivi
                    thread_status = []
                    for reader_id, thread in rfid_manager.reader_threads.items():
                        status = "ATTIVO" if thread.is_alive() else "MORTO"
                        thread_status.append(f"{reader_id}:{status}")
                    
                    print(f"⏰ {int(time.time() - start_time)}s - Threads: {', '.join(thread_status)}")
                    
                    # Verifica queue
                    queue_size = rfid_manager.card_queue.qsize()
                    print(f"📦 Queue size: {queue_size}")
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n⚠️ Interrotto dall'utente")
                break
            except Exception as e:
                print(f"⚠️ Errore nel loop: {e}")
                break
        
        print(f"\n⏰ Timeout {timeout}s raggiunto")
        
        # Cleanup
        try:
            rfid_manager.stop_reading()
            print("🛑 Sistema fermato")
        except Exception as e:
            print(f"⚠️ Errore stop: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 QUESTO TEST SIMULA ESATTAMENTE QUELLO CHE STAI FACENDO")
    print("Se fallisce qui, fallisce anche nel sistema reale")
    print()
    
    success = test_real_system_startup()
    
    print("\n" + "="*60)
    if success:
        print("✅ Test completato - Il sistema dovrebbe funzionare")
    else:
        print("❌ Test fallito - Qui è il problema!")
    print("="*60)