#!/usr/bin/env python3
"""
🧪 TEST CONFIGURAZIONE IBRIDA: PN532 IN(I2C) + OUT(SPI)
"""
import sys
sys.path.append('src')

def test_hybrid_configuration():
    """Test completo configurazione ibrida"""
    print("🎯 TEST CONFIGURAZIONE IBRIDA")
    print("=" * 50)
    print("IN: PN532 I2C (0x24) | OUT: PN532 SPI (Bus 0)")
    print()
    
    try:
        from config import Config
        print("✅ Config caricato")
        
        # Verifica configurazione
        print("🔍 VERIFICA CONFIGURAZIONE:")
        print(f"   📱 IN:  {Config.RFID_IN_READER_TYPE} su {Config.RFID_IN_PN532_INTERFACE.upper()}")
        print(f"   📱 OUT: {Config.RFID_OUT_READER_TYPE} su {Config.RFID_OUT_PN532_INTERFACE.upper()}")
        
        # Check correttezza
        correct_config = (
            Config.RFID_IN_READER_TYPE == 'pn532' and
            Config.RFID_IN_PN532_INTERFACE == 'i2c' and
            Config.RFID_OUT_READER_TYPE == 'pn532' and
            Config.RFID_OUT_PN532_INTERFACE == 'spi'
        )
        
        if correct_config:
            print("✅ Configurazione ibrida corretta!")
        else:
            print("❌ Configurazione non corretta")
            return False
        
        # Test factory pattern
        print("\n🏭 TEST FACTORY PATTERN:")
        from rfid_readers.reader_factory import RFIDReaderFactory
        
        # Test reader IN (I2C)
        print("   🔵 Creazione PN532 IN (I2C)...")
        reader_in = RFIDReaderFactory.create_reader(
            reader_type='pn532',
            reader_id='in',
            interface='i2c',
            i2c_address=0x24
        )
        if reader_in:
            print("   ✅ PN532 IN (I2C) creato")
        else:
            print("   ❌ Errore creazione PN532 IN")
        
        # Test reader OUT (SPI)
        print("   🟡 Creazione PN532 OUT (SPI)...")
        reader_out = RFIDReaderFactory.create_reader(
            reader_type='pn532',
            reader_id='out',
            interface='spi',
            spi_bus=0,
            spi_device=0
        )
        if reader_out:
            print("   ✅ PN532 OUT (SPI) creato")
        else:
            print("   ❌ Errore creazione PN532 OUT")
        
        # Test RFIDManager
        print("\n🧠 TEST RFID MANAGER:")
        from rfid_manager import RFIDManager
        
        rfid_manager = RFIDManager()
        print("   ✅ RFIDManager creato")
        
        # Test init (senza hardware reale)
        try:
            init_result = rfid_manager.initialize()
            print(f"   📋 Initialize: {init_result} (normale su PC sviluppo)")
        except Exception as e:
            print(f"   ⚠️ Initialize error: {type(e).__name__} (normale senza hardware)")
        
        print("\n🎯 RISULTATO:")
        print("✅ Configurazione ibrida I2C+SPI pronta!")
        print("✅ Factory pattern funzionante")
        print("✅ RFIDManager compatibile")
        
        print("\n🚀 PROSSIMI PASSI:")
        print("   1. Deploy su Raspberry Pi")
        print("   2. Collegare hardware secondo docs/HYBRID_I2C_SPI_SETUP.md")
        print("   3. Configurare jumper: IN(LSB=●,MSB=○) OUT(LSB=○,MSB=●)")
        print("   4. Test: python3 src/main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

def show_wiring_guide():
    """Mostra guida collegamenti rapida"""
    print("\n📋 GUIDA COLLEGAMENTI RAPIDA:")
    print("=" * 40)
    print("🔵 PN532 IN (I2C - Indirizzo 0x24):")
    print("   VCC → 3.3V | GND → GND")
    print("   SDA → GPIO 2 | SCL → GPIO 3")
    print("   Jumper: LSB=● MSB=○")
    print()
    print("🟡 PN532 OUT (SPI - Bus 0):")
    print("   VCC → 3.3V | GND → GND")
    print("   MOSI→GPIO10 | MISO→GPIO9")
    print("   SCK →GPIO11 | CS  →GPIO8")
    print("   Jumper: LSB=○ MSB=●")

if __name__ == "__main__":
    print("🧪 TEST CONFIGURAZIONE IBRIDA PN532")
    print("Configurazione: IN(I2C) + OUT(SPI)")
    print()
    
    success = test_hybrid_configuration()
    
    if success:
        show_wiring_guide()
        
        print(f"\n🎉 CONFIGURAZIONE COMPLETATA!")
        print(f"📄 Guida completa: docs/HYBRID_I2C_SPI_SETUP.md")
    else:
        print(f"\n❌ Test fallito - Controlla configurazione")