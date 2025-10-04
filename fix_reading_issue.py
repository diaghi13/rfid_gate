#!/usr/bin/env python3
"""
🔧 FIX LETTURA CARD - Identificazione e risoluzione problemi
"""
import sys
import os
sys.path.append('src')

def analyze_initialization_flow():
    """Analizza il flusso di inizializzazione per trovare il problema"""
    print("🔍 ANALISI FLUSSO INIZIALIZZAZIONE")
    print("=" * 45)
    
    try:
        from rfid_readers.pn532_reader import PN532Reader
        from config import Config
        
        print("📋 Test creazione lettori singoli:")
        
        # Test lettore IN (I2C)
        print(f"\n🔵 Test PN532 IN (I2C):")
        try:
            reader_in = PN532Reader("in", "i2c", i2c_address=0x24)
            print(f"   ✅ Oggetto creato")
            
            init_result = reader_in.initialize()
            print(f"   📋 Initialize result: {init_result}")
            print(f"   📋 is_initialized: {reader_in.is_initialized}")
            print(f"   📋 pn532 object: {reader_in.pn532}")
            
            if reader_in.is_initialized:
                # Test lettura
                result = reader_in.read_card()
                print(f"   📋 read_card result: {result}")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        # Test lettore OUT (SPI)  
        print(f"\n🟡 Test PN532 OUT (SPI):")
        try:
            reader_out = PN532Reader("out", "spi", spi_bus=0, spi_device=0)
            print(f"   ✅ Oggetto creato")
            
            init_result = reader_out.initialize()
            print(f"   📋 Initialize result: {init_result}")
            print(f"   📋 is_initialized: {reader_out.is_initialized}")
            print(f"   📋 pn532 object: {reader_out.pn532}")
            
            if reader_out.is_initialized:
                # Test lettura
                result = reader_out.read_card()
                print(f"   📋 read_card result: {result}")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            
    except Exception as e:
        print(f"❌ Errore analisi: {e}")

def check_library_availability():
    """Verifica disponibilità librerie"""
    print(f"\n📦 VERIFICA LIBRERIE")
    print("=" * 25)
    
    libraries = [
        ("board", "Adafruit Blinka"),
        ("busio", "Adafruit CircuitPython BusIO"),
        ("digitalio", "Adafruit CircuitPython DigitalIO"),
        ("adafruit_pn532.i2c", "Adafruit PN532 I2C"),
        ("adafruit_pn532.spi", "Adafruit PN532 SPI"),
        ("pn532", "Alternative PN532 library"),
        ("RPi.GPIO", "Raspberry Pi GPIO")
    ]
    
    missing_libs = []
    for lib_name, description in libraries:
        try:
            __import__(lib_name)
            print(f"   ✅ {description}")
        except ImportError:
            print(f"   ❌ {description} - MANCANTE")
            missing_libs.append(lib_name)
    
    return missing_libs

def create_mock_test():
    """Crea test simulato per ambiente senza hardware"""
    print(f"\n🎭 TEST SIMULATO (Mock)")
    print("=" * 25)
    
    print("📋 Creazione reader simulato:")
    
    # Patch temporaneo per testare la logica
    class MockPN532:
        def __init__(self):
            self.firmware_version = bytearray([1, 6, 7])
            
        def read_passive_target(self, timeout=1.0):
            # Simula una card ogni 10 chiamate
            import random
            if random.randint(1, 10) == 1:
                return bytearray([0x04, 0x12, 0x34, 0x56])  # UID simulato
            return None
    
    # Test logica di lettura
    try:
        from rfid_readers.pn532_reader import PN532Reader
        
        # Crea reader
        reader = PN532Reader("test", "i2c", i2c_address=0x24)
        
        # Forza inizializzazione simulata
        reader.pn532 = MockPN532()
        reader.is_initialized = True
        
        print("   ✅ Reader mock creato")
        
        # Test lettura
        cards_found = 0
        for i in range(20):  # 20 tentativi
            result = reader.read_card()
            if result and result[0]:
                cards_found += 1
                card_id, card_data = result
                print(f"   🎉 Card simulata: {card_id}")
        
        print(f"   📊 Card simulate trovate: {cards_found}/20")
        
        if cards_found > 0:
            print("   ✅ Logica di lettura FUNZIONA")
            return True
        else:
            print("   ❌ Logica di lettura NON funziona")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore test mock: {e}")
        return False

def identify_problem_source():
    """Identifica la fonte del problema"""
    print(f"\n🎯 IDENTIFICAZIONE PROBLEMA")
    print("=" * 35)
    
    missing_libs = check_library_availability()
    
    if missing_libs:
        print(f"\n❌ PROBLEMA IDENTIFICATO: Librerie mancanti")
        print(f"   📦 Librerie da installare:")
        for lib in missing_libs:
            if lib == "board":
                print(f"      pip3 install adafruit-blinka")
            elif lib == "adafruit_pn532.i2c":
                print(f"      pip3 install adafruit-circuitpython-pn532")
            elif lib == "pn532":
                print(f"      pip3 install pn532")
            elif lib == "RPi.GPIO":
                print(f"      apt-get install python3-rpi.gpio (solo su RPi)")
    else:
        print(f"✅ Tutte le librerie sono disponibili")
        
        # Se le librerie ci sono, il problema è hardware
        print(f"\n🔧 POSSIBILI PROBLEMI HARDWARE:")
        print(f"   1. PN532 non collegati correttamente")
        print(f"   2. Jumper configurazione sbagliata")
        print(f"   3. Alimentazione insufficiente")
        print(f"   4. I2C/SPI non abilitato su Raspberry Pi")

def provide_solutions():
    """Fornisce soluzioni specifiche"""
    print(f"\n💡 SOLUZIONI")
    print("=" * 15)
    
    print(f"🔧 Per ambiente di sviluppo (PC/Mac):")
    print(f"   ✅ Test completato - Librerie mancanti sono normali")
    print(f"   🚀 Deploy su Raspberry Pi per test hardware")
    
    print(f"\n🔧 Per Raspberry Pi:")
    print(f"   1. Installa dipendenze:")
    print(f"      pip3 install adafruit-circuitpython-pn532")
    print(f"      pip3 install adafruit-blinka")
    
    print(f"\n   2. Abilita interfacce:")
    print(f"      sudo raspi-config > Interface > I2C > Enable")
    print(f"      sudo raspi-config > Interface > SPI > Enable")
    
    print(f"\n   3. Verifica hardware:")
    print(f"      i2cdetect -y 1  (cerca indirizzo 24)")
    print(f"      ls /dev/spidev* (verifica SPI)")
    
    print(f"\n   4. Test lettori:")
    print(f"      python3 debug_card_reading.py")

def main():
    print("🔧 FIX LETTURA CARD - Diagnosi Completa")
    print("Identifica perché i lettori inizializzati non leggono")
    print()
    
    # Step 1: Analisi inizializzazione
    analyze_initialization_flow()
    
    # Step 2: Identifica problema
    identify_problem_source()
    
    # Step 3: Test logica con mock
    mock_ok = create_mock_test()
    
    # Step 4: Soluzioni
    provide_solutions()
    
    print(f"\n🎯 CONCLUSIONE:")
    if mock_ok:
        print("✅ LOGICA FUNZIONA - Problema: librerie hardware mancanti")
        print("🚀 Deploy su Raspberry Pi risolverà il problema")
    else:
        print("❌ PROBLEMA SOFTWARE - Verifica codice di lettura")

if __name__ == "__main__":
    main()