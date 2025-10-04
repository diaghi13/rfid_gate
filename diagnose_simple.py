#!/usr/bin/env python3
"""
Test diagnostico semplificato - Identifica problema PN532 SPI
"""
import os
import sys

def check_environment():
    """Verifica ambiente di sviluppo vs produzione"""
    print("🔍 DIAGNOSI AMBIENTE")
    print("=" * 30)
    
    # Check se siamo su Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            is_rpi = 'BCM' in cpuinfo or 'Raspberry' in cpuinfo
    except:
        is_rpi = False
    
    print(f"📍 Sistema: {'Raspberry Pi' if is_rpi else 'PC di sviluppo'}")
    print(f"📍 OS: {os.uname().sysname}")
    print(f"📍 Python: {sys.version}")
    
    return is_rpi

def check_spi_system():
    """Verifica configurazione SPI di sistema"""
    print(f"\n🔧 VERIFICA SPI SISTEMA")
    print("=" * 30)
    
    # Check /dev/spidev*
    spi_devices = []
    for i in range(3):  # spi0, spi1, spi2
        for j in range(3):  # cs0, cs1, cs2
            dev = f"/dev/spidev{i}.{j}"
            if os.path.exists(dev):
                spi_devices.append(dev)
    
    if spi_devices:
        print(f"✅ Dispositivi SPI trovati: {spi_devices}")
    else:
        print(f"❌ Nessun dispositivo /dev/spidev* trovato")
        print(f"   🔧 Esegui: sudo raspi-config > Interfacing > SPI > Enable")
    
    # Check moduli kernel
    try:
        with open('/proc/modules', 'r') as f:
            modules = f.read()
            spi_loaded = 'spi_bcm' in modules
    except:
        spi_loaded = False
    
    print(f"📋 Modulo SPI kernel: {'✅ Caricato' if spi_loaded else '❌ Non caricato'}")
    
    return len(spi_devices) > 0

def analyze_error_logs():
    """Analizza i log per capire il problema specifico"""
    print(f"\n📋 ANALISI LOG ERRORI")
    print("=" * 30)
    
    log_file = "/Users/davidedonghi/Apps/_micro services/rfid_gate/logs/system.log"
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Cerca errori PN532 SPI
            pn532_errors = []
            for line in lines[-50:]:  # Ultime 50 righe
                if 'PN532' in line and ('error' in line.lower() or 'fail' in line.lower()):
                    pn532_errors.append(line.strip())
            
            if pn532_errors:
                print(f"❌ Errori PN532 trovati:")
                for error in pn532_errors[-5:]:  # Ultimi 5 errori
                    print(f"   {error}")
            else:
                print(f"✅ Nessun errore PN532 nei log recenti")
                
        except Exception as e:
            print(f"❌ Errore lettura log: {e}")
    else:
        print(f"⚠️ File di log non trovato: {log_file}")

def suggest_solutions():
    """Suggerisce soluzioni basate sull'ambiente"""
    print(f"\n💡 SOLUZIONI SUGGERITE")
    print("=" * 30)
    
    print(f"🔧 HARDWARE PN532:")
    print(f"   1. Verifica jumper: LSB=○ (OFF), MSB=● (ON) per SPI")
    print(f"   2. Collegamento CS: GPIO 8 (Pin 24 fisico)")
    print(f"   3. Alimentazione: 3.3V stabile, non 5V")
    print(f"   4. Ground comune tra RPi e PN532")
    
    print(f"\n🔧 SOFTWARE:")
    print(f"   1. sudo raspi-config > Interface > SPI > Enable")
    print(f"   2. sudo reboot (dopo enable SPI)")
    print(f"   3. pip3 install adafruit-circuitpython-pn532")
    print(f"   4. Test con un solo PN532 per volta")
    
    print(f"\n🔄 WORKAROUND IMMEDIATO:")
    print(f"   1. Usa dual I2C invece di SPI+I2C:")
    print(f"      cp .env.dual_i2c .env")
    print(f"   2. Configura entrambi PN532 su I2C (indirizzo 0x24)")
    print(f"   3. Usa lettori in sequenza, non parallelo")

def main():
    print("🚀 DIAGNOSI PROBLEMA 'Failed to detect the PN532'")
    print("=" * 55)
    
    # Check ambiente
    is_rpi = check_environment()
    
    # Check SPI solo su RPi
    if is_rpi:
        spi_ok = check_spi_system()
    else:
        print(f"\n⚠️ Test SPI saltato (non su Raspberry Pi)")
        spi_ok = False
    
    # Analizza log
    analyze_error_logs()
    
    # Suggerimenti
    suggest_solutions()
    
    print(f"\n📊 CONCLUSIONI:")
    if is_rpi and spi_ok:
        print(f"✅ SPI abilitato - Problema probabilmente hardware")
        print(f"🔧 Controlla jumper e collegamenti PN532")
    elif is_rpi:
        print(f"❌ SPI non configurato")
        print(f"🔧 Esegui: sudo raspi-config > Interface > SPI")
    else:
        print(f"💻 Test su PC sviluppo - Deploy su RPi per test hardware")

if __name__ == "__main__":
    main()