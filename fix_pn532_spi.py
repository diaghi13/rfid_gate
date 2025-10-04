#!/usr/bin/env python3
"""
🔧 SCRIPT RISOLUZIONE DEFINITIVA PN532 SPI
Questo script risolve il problema "Failed to detect the PN532"
"""
import os
import sys
import time

def print_banner():
    print("🚀 RISOLUZIONE PN532 SPI - 'Failed to detect'")
    print("=" * 50)
    print("Questo script risolve definitivamente il problema")
    print()

def check_raspberry_pi():
    """Verifica se siamo su Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            is_rpi = 'BCM' in cpuinfo or 'Raspberry' in cpuinfo
    except:
        is_rpi = False
    
    if not is_rpi:
        print("⚠️ ATTENZIONE: Non su Raspberry Pi")
        print("   Questo script deve essere eseguito su RPi")
        print("   Attualmente su:", os.uname().sysname)
        return False
    
    print("✅ Raspberry Pi rilevato")
    return True

def check_spi_enabled():
    """Verifica se SPI è abilitato"""
    print("\n🔧 Verifica SPI...")
    
    # Check dispositivi SPI
    spi_devices = []
    for i in range(3):
        for j in range(3):
            dev = f"/dev/spidev{i}.{j}"
            if os.path.exists(dev):
                spi_devices.append(dev)
    
    if not spi_devices:
        print("❌ SPI non abilitato")
        print("🔧 SOLUZIONE:")
        print("   sudo raspi-config")
        print("   > Interfacing Options > SPI > Yes")
        print("   sudo reboot")
        return False
    
    print(f"✅ SPI abilitato: {spi_devices}")
    return True

def test_pn532_hardware():
    """Test hardware PN532 step by step"""
    print("\n🧪 Test PN532 Hardware...")
    
    try:
        # Import librerie
        print("📦 Import librerie...")
        try:
            import board
            import busio
            import digitalio
            from adafruit_pn532.spi import PN532_SPI
            print("✅ Librerie importate")
        except ImportError as e:
            print(f"❌ Librerie mancanti: {e}")
            print("🔧 SOLUZIONE:")
            print("   pip3 install adafruit-circuitpython-pn532")
            return False
        
        # Test SPI bus
        print("🔌 Creazione bus SPI...")
        try:
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            print("✅ Bus SPI creato")
        except Exception as e:
            print(f"❌ Errore bus SPI: {e}")
            return False
        
        # Test CS pins (GPIO 8 e 7)
        cs_tests = [
            (board.D8, "GPIO 8 (CE0)"),
            (board.D7, "GPIO 7 (CE1)")
        ]
        
        for cs_pin, cs_name in cs_tests:
            print(f"\n🎯 Test {cs_name}...")
            try:
                cs = digitalio.DigitalInOut(cs_pin)
                pn532 = PN532_SPI(spi, cs, debug=False)
                
                print(f"   Tentativo rilevazione firmware...")
                fw = pn532.firmware_version
                
                if fw:
                    print(f"🎉 PN532 TROVATO su {cs_name}!")
                    print(f"   Firmware: {fw}")
                    return True
                else:
                    print(f"   ❌ Nessuna risposta su {cs_name}")
                    
            except Exception as e:
                print(f"   ❌ Errore {cs_name}: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Errore generale test: {e}")
        return False

def suggest_hardware_check():
    """Suggerisce controlli hardware"""
    print("\n🔧 CONTROLLI HARDWARE NECESSARI:")
    print("=" * 40)
    
    print("📌 1. JUMPER PN532:")
    print("   LSB: ○ (OFF) - MSB: ● (ON) = SPI Mode")
    print("   ❌ Non: LSB=●, MSB=○ (I2C mode)")
    
    print("\n📌 2. COLLEGAMENTI:")
    print("   RPi Pin 19 (MOSI) → PN532 SDA/MOSI")
    print("   RPi Pin 21 (MISO) → PN532 MISO")
    print("   RPi Pin 23 (SCLK) → PN532 SCL/SCLK")
    print("   RPi Pin 24 (CE0)  → PN532 SS/CS")
    print("   RPi Pin 1  (3.3V) → PN532 VCC")
    print("   RPi Pin 6  (GND)  → PN532 GND")
    
    print("\n📌 3. ALIMENTAZIONE:")
    print("   ✅ 3.3V (NON 5V!)")
    print("   ✅ Ground comune")
    print("   ✅ Cavi corti (<15cm)")

def create_workaround():
    """Crea configurazione workaround"""
    print("\n🔄 CREAZIONE WORKAROUND...")
    
    workaround_env = """# Configurazione WORKAROUND - Dual I2C
# Per problemi SPI PN532

# Lettore IN - PN532 I2C  
READER_IN_TYPE=pn532
READER_IN_INTERFACE=i2c
READER_IN_I2C_ADDRESS=0x24

# Lettore OUT - PN532 I2C (stesso indirizzo, usato in sequenza)
READER_OUT_TYPE=pn532
READER_OUT_INTERFACE=i2c  
READER_OUT_I2C_ADDRESS=0x24

# Anti-crosstalk
GLOBAL_DEBOUNCE_TIME=0.8

# MQTT
MQTT_ENABLED=true
MQTT_BROKER=mqbrk.ddns.net
MQTT_PORT=8883
MQTT_USE_TLS=true

# Sistema
LOGGING_LEVEL=INFO
"""
    
    try:
        with open('.env.workaround', 'w') as f:
            f.write(workaround_env)
        print("✅ Creato .env.workaround")
        
        # Applica workaround
        os.system("cp .env.workaround .env")
        print("✅ Workaround applicato a .env")
        
        return True
    except Exception as e:
        print(f"❌ Errore creazione workaround: {e}")
        return False

def main():
    print_banner()
    
    # Step 1: Check Raspberry Pi
    if not check_raspberry_pi():
        print("\n💻 Esegui questo script su Raspberry Pi per il test completo")
        suggest_hardware_check()
        create_workaround()
        return
    
    # Step 2: Check SPI
    if not check_spi_enabled():
        print("\n🔧 Abilita SPI prima di continuare")
        return
    
    # Step 3: Test hardware
    hardware_ok = test_pn532_hardware()
    
    if hardware_ok:
        print("\n🎉 PN532 SPI FUNZIONANTE!")
        print("✅ Problema risolto")
        
        # Ripristina configurazione ottimale
        if os.path.exists('.env.optimal'):
            os.system("cp .env.optimal .env")
            print("✅ Configurazione ottimale ripristinata")
    else:
        print("\n❌ PN532 SPI non rilevato")
        suggest_hardware_check()
        
        # Crea workaround
        if create_workaround():
            print("\n🔄 Workaround dual I2C attivato")
            print("   Il sistema può funzionare con questa configurazione")
        
    print(f"\n📚 Guida completa: docs/PN532_SPI_TROUBLESHOOTING.md")

if __name__ == "__main__":
    main()