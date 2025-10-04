#!/usr/bin/env python3
"""
Test finale semplificato - verifica che il PN532Reader funzioni
"""
import sys
import os
import time

# Aggiungi src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simplified_pn532():
    print("🎯 TEST FINALE - PN532 SEMPLIFICATO")
    print("="*50)
    
    try:
        from config import Config
        from rfid_readers.pn532_reader import PN532Reader
        from logger import AccessLogger
        
        print("✅ Import: OK")
        
        # Test configurazione
        config = Config()
        print(f"✅ Config: {config.RFID_IN_READER_TYPE}")
        
        # Logger semplificato
        logger = AccessLogger()
        
        # Test solo il lettore IN (il più semplice)
        print("\n🔧 Test PN532 IN (I2C)...")
        
        reader_config = {
            'reader_id': 'test_in',
            'interface': config.RFID_IN_PN532_INTERFACE,
            'i2c_address': config.RFID_IN_PN532_I2C_ADDRESS,
            'spi_bus': config.RFID_IN_PN532_SPI_BUS,
            'spi_device': config.RFID_IN_PN532_SPI_DEVICE,
            'uart_port': config.RFID_IN_PN532_UART_PORT,
            'uart_baudrate': config.RFID_IN_PN532_UART_BAUDRATE
        }
        
        print(f"📋 Configurazione: {reader_config}")
        
        # Crea reader con parametri corretti
        reader = PN532Reader(
            reader_id='test_in',
            interface=config.RFID_IN_PN532_INTERFACE,
            i2c_address=config.RFID_IN_PN532_I2C_ADDRESS,
            spi_bus=config.RFID_IN_PN532_SPI_BUS,
            spi_device=config.RFID_IN_PN532_SPI_DEVICE,
            uart_port=config.RFID_IN_PN532_UART_PORT,
            uart_baudrate=config.RFID_IN_PN532_UART_BAUDRATE
        )
        
        # Test inizializzazione
        print("🔄 Inizializzazione...")
        if reader.initialize():
            print("✅ PN532 inizializzato")
            
            # Test lettura per 10 secondi
            print("\n📱 TEST LETTURA - 10 secondi")
            print("🔍 Avvicina una carta...")
            
            start_time = time.time()
            cards_found = 0
            
            while time.time() - start_time < 10:
                uid, card_type = reader.read_card()
                
                if uid:
                    cards_found += 1
                    print(f"\n🎉 CARTA #{cards_found}:")
                    print(f"   📱 UID: {uid}")
                    print(f"   📋 Tipo: {card_type}")
                    print(f"   ⏱️  Time: {time.time():.2f}")
                    
                    # Pausa per evitare spam
                    time.sleep(1)
                
                time.sleep(0.1)
            
            print(f"\n📊 Risultato: {cards_found} carte lette")
            
            if cards_found > 0:
                print("🎉 ✅ SUCCESSO - Il PN532 legge le carte!")
                return True
            else:
                print("⚠️ ❌ NESSUNA CARTA - Controlla hardware o avvicina carta")
                return False
                
        else:
            print("❌ Inizializzazione fallita")
            print("🔧 Possibili cause:")
            print("   • Hardware non collegato")
            print("   • Indirizzo I2C errato") 
            print("   • Alimentazione insufficiente")
            print("   • Conflitti bus I2C/SPI")
            return False
            
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 RFID GATE - TEST FINALE PN532")
    print("🎯 Obiettivo: Verificare che 'deve funzionare al primo colpo'")
    print()
    
    success = test_simplified_pn532()
    
    print("\n" + "="*50)
    if success:
        print("🎉 SISTEMA PRONTO PER PRODUZIONE!")
        print("✅ Il PN532 legge le carte correttamente")
        print("🚀 Puoi avviare il sistema principale")
    else:
        print("💔 SISTEMA NON PRONTO")
        print("🔧 Controlla hardware e configurazione")
        print("📋 Verifica i collegamenti I2C/SPI")
        
    exit(0 if success else 1)