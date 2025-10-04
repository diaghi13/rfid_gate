#!/usr/bin/env python3
"""
🧪 TEST DEBUG LETTURA CARD - Diagnosi problema lettura
"""
import sys
import os
import time
sys.path.append('src')

def test_reader_initialization():
    """Test inizializzazione lettori"""
    print("🔍 TEST INIZIALIZZAZIONE LETTORI")
    print("=" * 50)
    
    try:
        from rfid_manager import RFIDManager
        from config import Config
        
        # Crea RFIDManager
        rfid_manager = RFIDManager()
        print("✅ RFIDManager creato")
        
        # Test inizializzazione
        if rfid_manager.initialize():
            print("✅ Inizializzazione riuscita")
            
            # Info lettori attivi
            active_readers = rfid_manager.get_active_readers()
            print(f"📱 Lettori attivi: {active_readers}")
            
            # Info dettagliata lettori
            reader_info = rfid_manager.get_reader_info()
            for reader_id, info in reader_info.items():
                print(f"🔍 {reader_id}: {info}")
            
            return rfid_manager
        else:
            print("❌ Inizializzazione fallita")
            return None
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        return None

def test_manual_card_reading(rfid_manager):
    """Test lettura manuale delle card"""
    print(f"\n🧪 TEST LETTURA MANUALE CARD")
    print("=" * 40)
    
    if not rfid_manager:
        print("❌ RFIDManager non disponibile")
        return
    
    # Test lettura diretta dai lettori
    for reader_id, reader in rfid_manager.readers.items():
        print(f"\n🔵 Test lettore {reader_id.upper()}:")
        print(f"   Interface: {reader.interface}")
        print(f"   Initialized: {reader.is_initialized}")
        
        # Test lettura diretta (5 tentativi)
        for i in range(5):
            try:
                result = reader.read_card()
                if result and result[0]:
                    card_id, card_data = result
                    print(f"   ✅ CARD TROVATA: {card_id}")
                    print(f"   📄 Data: {card_data}")
                    return True
                else:
                    print(f"   🔍 Tentativo {i+1}: Nessuna card")
                
                time.sleep(0.2)  # Pausa tra tentativi
                
            except Exception as e:
                print(f"   ❌ Errore tentativo {i+1}: {e}")
        
        print(f"   ⚠️ Nessuna card rilevata su {reader_id}")
    
    return False

def test_reader_loop_simulation(rfid_manager):
    """Simula il loop di lettura come nel sistema reale"""
    print(f"\n🔄 TEST SIMULAZIONE LOOP LETTURA")
    print("=" * 40)
    
    if not rfid_manager:
        print("❌ RFIDManager non disponibile")
        return
    
    print("🚀 Avvio simulazione loop (10 secondi)...")
    print("   Avvicina una card a uno dei lettori...")
    
    start_time = time.time()
    cards_found = 0
    
    while (time.time() - start_time) < 10:  # 10 secondi di test
        try:
            # Simula _reader_loop per ogni lettore
            for reader_id, reader in rfid_manager.readers.items():
                result = reader.read_card()
                
                if result and result[0]:
                    card_id, card_data = result
                    
                    # Applica debounce globale
                    if rfid_manager.apply_global_debounce(card_id, reader_id):
                        cards_found += 1
                        print(f"🎉 CARD {cards_found}: {card_id} su {reader_id.upper()}")
                        print(f"    Data: {card_data}")
            
            time.sleep(0.1)  # CARD_READ_INTERVAL
            
        except KeyboardInterrupt:
            print(f"\n⏹️ Test interrotto dall'utente")
            break
        except Exception as e:
            print(f"❌ Errore loop: {e}")
    
    print(f"\n📊 RISULTATI:")
    print(f"   Card rilevate: {cards_found}")
    print(f"   Durata test: {time.time() - start_time:.1f}s")
    
    return cards_found > 0

def test_configuration_check():
    """Verifica configurazione"""
    print(f"\n⚙️ VERIFICA CONFIGURAZIONE")
    print("=" * 30)
    
    try:
        from config import Config
        
        print(f"📋 Configurazione attiva:")
        print(f"   IN:  {Config.RFID_IN_READER_TYPE} ({Config.RFID_IN_PN532_INTERFACE})")
        print(f"   OUT: {Config.RFID_OUT_READER_TYPE} ({Config.RFID_OUT_PN532_INTERFACE})")
        print(f"   CARD_READ_INTERVAL: {Config.CARD_READ_INTERVAL}s")
        print(f"   GLOBAL_DEBOUNCE: {Config.GLOBAL_DEBOUNCE_TIME}s")
        print(f"   PN532_TIMEOUT: {Config.PN532_READ_TIMEOUT}s")
        
        # Check problemi comuni
        if Config.CARD_READ_INTERVAL > 0.5:
            print("⚠️ CARD_READ_INTERVAL troppo alto (>0.5s)")
        
        if Config.PN532_READ_TIMEOUT > 0.1:
            print("⚠️ PN532_READ_TIMEOUT troppo alto (>0.1s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore config: {e}")
        return False

def diagnose_hardware_issues():
    """Diagnosi problemi hardware comuni"""
    print(f"\n🔧 DIAGNOSI PROBLEMI HARDWARE")
    print("=" * 35)
    
    print("🔍 Possibili cause mancata lettura:")
    print("   1. PN532 non correttamente collegato")
    print("   2. Jumper PN532 non configurati (I2C: LSB=●, MSB=○)")
    print("   3. Alimentazione 3.3V instabile")
    print("   4. Interferenze elettromagnetiche")
    print("   5. Card NFC/RFID non compatibile")
    print("   6. Distanza troppo grande (>3cm)")
    
    print(f"\n🧪 Test hardware manuali:")
    print("   - i2cdetect -y 1 (deve mostrare 24 per IN)")
    print("   - ls /dev/spidev* (deve mostrare spi0.0 per OUT)")
    print("   - Prova con una sola card alla volta")
    print("   - Testa con card diverse (Mifare, NTAG)")

def main():
    print("🧪 DEBUG LETTURA CARD - Sistema RFID")
    print("Questo script diagnostica perché i lettori non leggono le card")
    print()
    
    # Test 1: Configurazione
    config_ok = test_configuration_check()
    
    # Test 2: Inizializzazione
    rfid_manager = test_reader_initialization()
    
    # Test 3: Lettura manuale
    manual_ok = test_manual_card_reading(rfid_manager)
    
    # Test 4: Loop simulation (solo se manuale fallisce)
    if not manual_ok and rfid_manager:
        loop_ok = test_reader_loop_simulation(rfid_manager)
    else:
        loop_ok = manual_ok
    
    # Test 5: Diagnosi hardware
    diagnose_hardware_issues()
    
    # Cleanup
    if rfid_manager:
        rfid_manager.cleanup()
    
    print(f"\n🎯 DIAGNOSI FINALE:")
    if loop_ok:
        print("✅ Lettori FUNZIONANTI - Card rilevate!")
    elif rfid_manager and rfid_manager.readers:
        print("⚠️ Lettori inizializzati ma NON leggono card")
        print("🔧 Controlla hardware: collegamenti, jumper, alimentazione")
    else:
        print("❌ Lettori NON inizializzati")
        print("🔧 Controlla configurazione e librerie")

if __name__ == "__main__":
    main()