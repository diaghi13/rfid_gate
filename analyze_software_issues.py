#!/usr/bin/env python3
"""
🔍 ANALISI PROBLEMI SOFTWARE - Raspberry Pi
"""
import sys
import os
import time

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_software_issues():
    print("🐛 ANALISI PROBLEMI SOFTWARE")
    print("="*60)
    
    # Carica config
    from config import Config
    
    # 1. Verifica configurazione
    print("1️⃣ CONFIGURAZIONE ATTUALE")
    print(f"ENABLE_IN_READER: {Config.ENABLE_IN_READER}")
    print(f"RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
    print(f"RFID_IN_PN532_INTERFACE: {Config.RFID_IN_PN532_INTERFACE}")
    print(f"RFID_IN_PN532_I2C_ADDRESS: {hex(Config.RFID_IN_PN532_I2C_ADDRESS)}")
    
    if hasattr(Config, 'ENABLE_OUT_READER') and Config.ENABLE_OUT_READER:
        print(f"ENABLE_OUT_READER: {Config.ENABLE_OUT_READER}")
        print(f"RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
        print(f"RFID_OUT_PN532_INTERFACE: {Config.RFID_OUT_PN532_INTERFACE}")
    
    # 2. Verifica il problema principale
    print(f"\n2️⃣ ANALISI PROBLEMA PRINCIPALE")
    
    # Problema comune 1: Timeout troppo brevi
    card_read_interval = getattr(Config, 'CARD_READ_INTERVAL', 0.1)
    print(f"CARD_READ_INTERVAL: {card_read_interval}s")
    
    if card_read_interval < 0.1:
        print("⚠️ CARD_READ_INTERVAL troppo basso - può causare problemi")
    
    # Problema comune 2: Threading issues
    print(f"\n🧵 VERIFICA THREADING")
    
    try:
        from rfid_manager import RFIDManager
        
        rfid_manager = RFIDManager()
        
        # Verifica se il debounce è troppo alto
        debounce_time = rfid_manager.global_debounce_time
        print(f"Global debounce time: {debounce_time}s")
        
        if debounce_time > 2.0:
            print("⚠️ Debounce time troppo alto - card potrebbero essere ignorate")
        
    except Exception as e:
        print(f"❌ Errore caricamento RFIDManager: {e}")
        return False
    
    # 3. Test specifico del problema
    print(f"\n3️⃣ TEST SPECIFICO PROBLEMA")
    
    # Il problema potrebbe essere nell'interfaccia wait_for_card
    print("Problema comune: wait_for_card() con timeout troppo breve")
    
    try:
        # Test del reader factory
        from rfid_readers.reader_factory import RFIDReaderFactory
        
        print("🏭 Test Reader Factory...")
        
        # Crea reader come fa il sistema
        reader = RFIDReaderFactory.create_reader(
            reader_type=Config.RFID_IN_READER_TYPE,
            reader_id="test",
            interface=Config.RFID_IN_PN532_INTERFACE,
            i2c_address=Config.RFID_IN_PN532_I2C_ADDRESS,
        )
        
        if reader:
            print("✅ Reader creato")
            
            # Test inizializzazione
            init_result = reader.initialize()
            print(f"Initialize: {init_result}")
            
            if init_result:
                print("\n🔄 TEST LETTURA MANUALE")
                print("Passa una card ADESSO...")
                
                for i in range(20):  # 10 secondi
                    try:
                        result = reader.read_card()
                        if result:
                            print(f"\n🎉 CARD LETTA: {result}")
                            return True
                        
                        print(f"⏳ Tentativo {i+1}/20", end="\r")
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"\n❌ Errore lettura: {e}")
                        break
                
                print("\n⏰ Nessuna card rilevata")
                
                # Diagnosi finale
                print(f"\n🔍 DIAGNOSI:")
                print("Se il test hardware (diagnose_rpi_hardware.py) funziona")
                print("ma questo test fallisce, il problema è in:")
                print("1. 🎯 read_card() implementation nel PN532Reader")
                print("2. 🔄 Timeout settings troppo bassi")
                print("3. 🧵 Threading issues nel RFIDManager")
                print("4. ⚡ Blocking vs non-blocking read")
                
            else:
                print("❌ Initialize fallito - problema hardware")
        else:
            print("❌ Reader non creato - problema factory")
            
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

def analyze_main_loop_issue():
    print(f"\n4️⃣ ANALISI MAIN LOOP")
    print("="*40)
    
    print("🔍 PROBLEMA COMUNE: main loop non riceve card")
    print()
    print("Il sistema potrebbe:")
    print("1. 📡 Leggere la card ma non metterla in queue")
    print("2. 🧵 Thread reader morto")
    print("3. ⏰ wait_for_card() con timeout sbagliato")
    print("4. 🔄 Debounce che scarta card valide")
    print("5. 📦 Queue piena o bloccata")
    
    print(f"\n💡 SOLUZIONI:")
    print("1. Aumenta timeout in wait_for_card()")
    print("2. Riduci global_debounce_time")
    print("3. Aggiungi debug print nel reader thread")
    print("4. Verifica is_alive() dei thread")

def main():
    print("🎯 ANALISI PROBLEMI SOFTWARE RASPBERRY PI")
    print("Da eseguire DOPO diagnose_rpi_hardware.py")
    print()
    
    try:
        success = analyze_software_issues()
        analyze_main_loop_issue()
        
        if not success:
            print(f"\n📋 PROSSIMI PASSI:")
            print("1. Esegui: python3 diagnose_rpi_hardware.py")
            print("2. Se hardware OK, il problema è nel software")
            print("3. Controlla timeout e threading")
            
    except Exception as e:
        print(f"❌ Errore analisi: {e}")

if __name__ == "__main__":
    main()