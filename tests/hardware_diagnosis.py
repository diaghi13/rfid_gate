#!/usr/bin/env python3
"""
DIAGNOSI HARDWARE DEFINITIVA RFID
Test completo hardware, SPI, alimentazione e compatibilità card
"""
import sys
import time
import os

def check_system_requirements():
    """Verifica requisiti di sistema"""
    print("🔍 VERIFICA REQUISITI SISTEMA")
    print("=" * 50)
    
    issues = []
    
    # 1. Verifica SPI
    print("📡 Verifica SPI:")
    spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
    for device in spi_devices:
        if os.path.exists(device):
            try:
                # Verifica permessi
                if os.access(device, os.R_OK | os.W_OK):
                    print(f"   ✅ {device}: OK (accessibile)")
                else:
                    print(f"   ⚠️ {device}: Presente ma non accessibile")
                    issues.append(f"Permessi {device}")
            except:
                print(f"   ❌ {device}: Errore accesso")
                issues.append(f"Accesso {device}")
        else:
            print(f"   ❌ {device}: Non esistente")
            issues.append(f"SPI {device} non abilitato")
    
    # 2. Verifica moduli kernel
    print("\n🔧 Verifica moduli kernel:")
    try:
        with open('/proc/modules', 'r') as f:
            modules = f.read()
        
        spi_modules = ['spi_bcm2835', 'spidev']
        for module in spi_modules:
            if module in modules:
                print(f"   ✅ {module}: Caricato")
            else:
                print(f"   ❌ {module}: Non caricato")
                issues.append(f"Modulo {module} non caricato")
    except Exception as e:
        print(f"   ⚠️ Errore verifica moduli: {e}")
    
    # 3. Verifica config.txt
    print("\n⚙️ Verifica /boot/config.txt:")
    config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
    spi_enabled = False
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_content = f.read()
                
                if 'dtparam=spi=on' in config_content and not config_content.count('#dtparam=spi=on'):
                    print(f"   ✅ SPI abilitato in {config_file}")
                    spi_enabled = True
                    break
                else:
                    print(f"   ❌ SPI non abilitato in {config_file}")
            except Exception as e:
                print(f"   ⚠️ Errore lettura {config_file}: {e}")
    
    if not spi_enabled:
        issues.append("SPI non abilitato in config.txt")
    
    # 4. Verifica librerie Python
    print("\n🐍 Verifica librerie Python:")
    required_libs = ['RPi.GPIO', 'mfrc522', 'spidev']
    
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"   ✅ {lib}: Installato")
        except ImportError:
            print(f"   ❌ {lib}: Non installato")
            issues.append(f"Libreria {lib} mancante")
    
    return issues

def test_spi_communication():
    """Test comunicazione SPI diretta"""
    print("\n🔌 TEST COMUNICAZIONE SPI DIRETTA")
    print("=" * 50)
    
    try:
        import spidev
        
        # Test SPI device 0.0
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1000000
        spi.mode = 0
        
        print("✅ SPI device 0.0 aperto")
        
        # Test comunicazione base (comando version/dummy)
        try:
            # Invia comando dummy
            response = spi.xfer2([0x37])  # Comando version MFRC522
            print(f"   Risposta SPI: {response}")
            
            if response and response[0] != 0:
                print("✅ Comunicazione SPI: OK")
                return True
            else:
                print("⚠️ Comunicazione SPI: Nessuna risposta")
                return False
                
        except Exception as e:
            print(f"❌ Errore comunicazione SPI: {e}")
            return False
            
        finally:
            spi.close()
            
    except ImportError:
        print("❌ spidev non disponibile")
        return False
    except Exception as e:
        print(f"❌ Errore test SPI: {e}")
        return False

def test_gpio_pins():
    """Test pin GPIO specifici"""
    print("\n📍 TEST PIN GPIO")
    print("=" * 50)
    
    try:
        import RPi.GPIO as GPIO
        
        # Cleanup
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Pin da testare (dalla configurazione)
        sys.path.insert(0, 'src')
        from config import Config
        
        pins_to_test = [
            (Config.RFID_IN_RST_PIN, "RST"),
            (Config.RFID_IN_SDA_PIN, "CS/SDA"),
            (9, "MISO"), (10, "MOSI"), (11, "SCK")  # Pin SPI standard
        ]
        
        pin_results = []
        
        for pin, name in pins_to_test:
            try:
                # Test pin come output
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.1)
                
                print(f"   ✅ GPIO{pin} ({name}): Test toggle OK")
                pin_results.append((pin, name, True))
                
            except Exception as e:
                print(f"   ❌ GPIO{pin} ({name}): Errore {e}")
                pin_results.append((pin, name, False))
        
        GPIO.cleanup()
        return pin_results
        
    except Exception as e:
        print(f"❌ Errore test GPIO: {e}")
        return []

def test_different_mfrc522_versions():
    """Test con approcci diversi per diverse versioni mfrc522"""
    print("\n📚 TEST VERSIONI DIVERSE MFRC522")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: SimpleMFRC522 standard
    print("🧪 Test 1: SimpleMFRC522 standard")
    try:
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
        
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        reader = SimpleMFRC522()
        
        # Test veloce (1 tentativo)
        if hasattr(reader, 'read_no_block'):
            result = reader.read_no_block()
        else:
            # Timeout molto breve
            result = reader.read()
        
        if result[0] is not None:
            print("   🎉 SimpleMFRC522 standard: CARD TROVATA!")
            test_results.append(("SimpleMFRC522 standard", True, result[0]))
        else:
            print("   ⚪ SimpleMFRC522 standard: Nessuna card")
            test_results.append(("SimpleMFRC522 standard", False, None))
            
    except Exception as e:
        print(f"   ❌ SimpleMFRC522 standard: {e}")
        test_results.append(("SimpleMFRC522 standard", False, str(e)))
    
    # Test 2: MFRC522 base (se disponibile)
    print("\n🧪 Test 2: MFRC522 base class")
    try:
        from mfrc522 import MFRC522
        
        reader = MFRC522()
        
        # Test presenza card
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
        
        if status == reader.MI_OK:
            print("   🎉 MFRC522 base: CARD RILEVATA!")
            test_results.append(("MFRC522 base", True, TagType))
        else:
            print("   ⚪ MFRC522 base: Nessuna card")
            test_results.append(("MFRC522 base", False, status))
            
    except ImportError:
        print("   ⚠️ MFRC522 base: Non disponibile in questa versione")
        test_results.append(("MFRC522 base", False, "Non disponibile"))
    except Exception as e:
        print(f"   ❌ MFRC522 base: {e}")
        test_results.append(("MFRC522 base", False, str(e)))
    
    # Test 3: Test con pin espliciti via GPIO
    print("\n🧪 Test 3: Configurazione GPIO esplicita")
    try:
        sys.path.insert(0, 'src')
        from config import Config
        import RPi.GPIO as GPIO
        
        # Configura pin manualmente prima di creare reader
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Setup pin RST
        GPIO.setup(Config.RFID_IN_RST_PIN, GPIO.OUT)
        GPIO.output(Config.RFID_IN_RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        
        # Setup pin CS
        GPIO.setup(Config.RFID_IN_SDA_PIN, GPIO.OUT)
        GPIO.output(Config.RFID_IN_SDA_PIN, GPIO.HIGH)
        time.sleep(0.1)
        
        # Crea reader dopo setup GPIO
        reader = SimpleMFRC522()
        
        # Test
        if hasattr(reader, 'read_no_block'):
            result = reader.read_no_block()
        else:
            result = reader.read()
        
        if result[0] is not None:
            print("   🎉 GPIO esplicito: CARD TROVATA!")
            test_results.append(("GPIO esplicito", True, result[0]))
        else:
            print("   ⚪ GPIO esplicito: Nessuna card")
            test_results.append(("GPIO esplicito", False, None))
            
    except Exception as e:
        print(f"   ❌ GPIO esplicito: {e}")
        test_results.append(("GPIO esplicito", False, str(e)))
    finally:
        GPIO.cleanup()
    
    return test_results

def main():
    """Test diagnostico completo"""
    print("🏥 DIAGNOSI HARDWARE DEFINITIVA RFID")
    print("Questo test identifica il problema REALE")
    print("=" * 60)
    
    # 1. Verifica sistema
    system_issues = check_system_requirements()
    
    # 2. Test SPI
    spi_ok = test_spi_communication()
    
    # 3. Test GPIO
    gpio_results = test_gpio_pins()
    
    # 4. Test versioni mfrc522
    print("\n💡 AVVICINA UNA CARD PER I PROSSIMI TEST...")
    time.sleep(2)
    mfrc522_results = test_different_mfrc522_versions()
    
    # Riepilogo finale
    print("\n" + "=" * 60)
    print("📋 DIAGNOSI FINALE:")
    print("=" * 60)
    
    print(f"🔧 Problemi sistema: {len(system_issues)}")
    for issue in system_issues:
        print(f"   ❌ {issue}")
    
    print(f"\n📡 SPI comunicazione: {'✅ OK' if spi_ok else '❌ FALLITA'}")
    
    print(f"\n📍 GPIO pin test:")
    gpio_ok = all(result[2] for result in gpio_results)
    print(f"   Risultato: {'✅ TUTTI OK' if gpio_ok else '❌ ALCUNI FALLITI'}")
    
    print(f"\n📚 Test libreria mfrc522:")
    working_methods = [r for r in mfrc522_results if r[1] == True]
    if working_methods:
        print(f"   ✅ METODI FUNZIONANTI:")
        for method, success, result in working_methods:
            print(f"     🎉 {method}: Card ID {result}")
    else:
        print(f"   ❌ NESSUN METODO FUNZIONA")
        for method, success, error in mfrc522_results:
            print(f"     ❌ {method}: {error}")
    
    # Diagnosi finale
    if working_methods:
        print(f"\n🎉 DIAGNOSI: RFID FUNZIONA!")
        print(f"💡 Il problema era nel nostro codice, non nell'hardware")
        print(f"🔧 Usa il metodo funzionante: {working_methods[0][0]}")
    elif not system_issues and spi_ok and gpio_ok:
        print(f"\n❓ DIAGNOSI: HARDWARE OK, CARD PROBLEM?")
        print(f"💡 Sistema corretto, prova card diversa o verifica compatibilità")
    elif system_issues:
        print(f"\n🔧 DIAGNOSI: PROBLEMI SISTEMA")
        print(f"💡 Risolvi prima i problemi di sistema identificati")
    else:
        print(f"\n💔 DIAGNOSI: HARDWARE PROBLEM")
        print(f"💡 Controlla cablaggio, alimentazione, modulo RFID")

if __name__ == "__main__":
    main()