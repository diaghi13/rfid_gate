#!/usr/bin/env python3
"""
Test specifico per problema PN532 SPI - Rilevazione fallita
"""
import sys
sys.path.append('/opt/rfid-gate/src')

def test_pn532_spi_detection():
    """Test isolato del lettore SPI"""
    print("🧪 TEST PN532 SPI - Diagnosi 'Failed to detect'")
    print("=" * 50)
    
    try:
        # Test 1: Verifica librerie
        print("📋 1. Verifica librerie PN532...")
        try:
            import board
            import busio
            import digitalio
            print("✅ board, busio, digitalio disponibili")
        except ImportError as e:
            print(f"❌ Librerie mancanti: {e}")
            return False
        
        try:
            from adafruit_pn532.spi import PN532_SPI
            print("✅ adafruit_pn532.spi importata")
        except ImportError:
            try:
                from pn532 import PN532_SPI
                print("✅ pn532 lib importata")
            except ImportError as e:
                print(f"❌ Nessuna libreria PN532 SPI: {e}")
                return False
        
        # Test 2: Verifica SPI disponibilità
        print("\n📋 2. Verifica SPI hardware...")
        try:
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            print("✅ Bus SPI creato")
            
            # Test CS pins diversi
            cs_pins = [board.D8, board.D7]  # GPIO 8 e 7
            cs_names = ["GPIO 8 (CS0)", "GPIO 7 (CS1)"]
            
            for i, (cs_pin, cs_name) in enumerate(zip(cs_pins, cs_names)):
                print(f"\n📋 3.{i+1} Test CS {cs_name}...")
                try:
                    cs = digitalio.DigitalInOut(cs_pin)
                    print(f"✅ CS {cs_name} configurato")
                    
                    # Prova creazione PN532
                    pn532 = PN532_SPI(spi, cs, debug=False)
                    print(f"✅ PN532_SPI oggetto creato per {cs_name}")
                    
                    # Test rilevazione firmware
                    try:
                        fw = pn532.firmware_version
                        if fw:
                            print(f"🎉 PN532 RILEVATO su {cs_name}! Firmware: {fw}")
                            return True
                        else:
                            print(f"❌ Firmware non rilevato su {cs_name}")
                    except Exception as e:
                        print(f"❌ Errore firmware su {cs_name}: {e}")
                        
                except Exception as e:
                    print(f"❌ Errore CS {cs_name}: {e}")
            
        except Exception as e:
            print(f"❌ Errore SPI hardware: {e}")
        
        # Test 3: Suggerimenti troubleshooting
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"1. ✅ Verifica jumper PN532: LSB=○, MSB=● (SPI mode)")
        print(f"2. ✅ Verifica collegamento CS a GPIO 8 (Pin 24)")
        print(f"3. ✅ Verifica alimentazione 3.3V stabile")
        print(f"4. ✅ Prova CS alternativo (GPIO 7)")
        print(f"5. ✅ Test con un solo PN532 alla volta")
        
        return False
        
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return False

def test_dual_i2c_workaround():
    """Test configurazione dual I2C come workaround"""
    print(f"\n🔄 TEST WORKAROUND - Dual I2C")
    print("=" * 35)
    
    try:
        from rfid_readers.pn532_reader import PN532Reader
        
        # Test PN532 IN (0x24)
        print("🔵 Test PN532 IN (I2C 0x24)...")
        reader_in = PN532Reader("in", "i2c", i2c_address=0x24)
        if reader_in.initialize():
            print("✅ PN532 IN (0x24) inizializzato")
            in_ok = True
        else:
            print("❌ PN532 IN (0x24) fallito")
            in_ok = False
        
        # Test PN532 OUT (0x25) - ATTENZIONE: Potrebbe non funzionare se indirizzo fisso
        print("🟡 Test PN532 OUT (I2C 0x25)...")
        reader_out = PN532Reader("out", "i2c", i2c_address=0x25)
        if reader_out.initialize():
            print("✅ PN532 OUT (0x25) inizializzato")
            out_ok = True
        else:
            print("❌ PN532 OUT (0x25) fallito - Indirizzo fisso 0x24?")
            out_ok = False
        
        # Cleanup
        if in_ok:
            reader_in.cleanup()
        if out_ok:
            reader_out.cleanup()
        
        if in_ok and out_ok:
            print("🎉 DUAL I2C WORKAROUND FUNZIONANTE!")
            return True
        elif in_ok:
            print("⚠️ Solo IN funzionante - PN532 potrebbe avere indirizzo fisso 0x24")
            return False
        else:
            print("❌ Nessun lettore I2C funzionante")
            return False
            
    except Exception as e:
        print(f"❌ Errore test dual I2C: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DIAGNOSI PROBLEMA PN532 SPI")
    print("Questo script testa il problema 'Failed to detect the PN532' su SPI")
    print()
    
    # Test SPI
    spi_ok = test_pn532_spi_detection()
    
    # Test workaround I2C  
    i2c_workaround = test_dual_i2c_workaround()
    
    print(f"\n📊 RISULTATI:")
    print(f"   SPI PN532: {'✅ OK' if spi_ok else '❌ FAIL'}")
    print(f"   Dual I2C: {'✅ OK' if i2c_workaround else '❌ FAIL'}")
    
    if spi_ok:
        print(f"\n🎉 Problema SPI risolto!")
    elif i2c_workaround:
        print(f"\n🔄 Usa dual I2C come workaround temporaneo")
        print(f"   cp .env.dual_i2c .env")
    else:
        print(f"\n🔧 Controlla hardware PN532 e collegamenti")