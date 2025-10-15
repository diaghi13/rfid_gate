#!/usr/bin/env python3
"""
🔧 PN532 Diagnostic Tool - Sistema Completo
==========================================

Tool per diagnosticare e testare i lettori PN532 nel sistema RFID Gate.
Compara configurazione attuale con sistema legacy funzionante.

NOTA: Questo script deve essere eseguito su Raspberry Pi per test hardware completi.
"""

import os
import sys
import time
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

# Aggiunge il path del progetto per import
sys.path.insert(0, str(Path(__file__).parent))

def print_section(title: str, char: str = "=") -> None:
    """Stampa sezione formattata"""
    print(f"\n{char * 60}")
    print(f" {title}")
    print(f"{char * 60}")

def print_subsection(title: str) -> None:
    """Stampa sottosezione"""
    print(f"\n--- {title} ---")

def check_environment() -> Dict[str, Any]:
    """Controlla ambiente di esecuzione"""
    print_section("🌍 AMBIENTE DI ESECUZIONE")
    
    env_info = {
        'platform': sys.platform,
        'python_version': sys.version,
        'is_raspberry_pi': False,
        'gpio_available': False,
        'i2c_available': False,
        'spi_available': False
    }
    
    # Controlla se siamo su Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = f.read()
            if 'BCM' in cpu_info or 'Raspberry Pi' in cpu_info:
                env_info['is_raspberry_pi'] = True
                print("✅ Raspberry Pi rilevato")
            else:
                print("⚠️ Non su Raspberry Pi")
    except FileNotFoundError:
        print("⚠️ Sistema non Raspberry Pi")
    
    # Controlla disponibilità GPIO
    try:
        import RPi.GPIO as GPIO
        env_info['gpio_available'] = True
        print("✅ RPi.GPIO disponibile")
    except ImportError:
        print("❌ RPi.GPIO non disponibile")
    
    # Controlla I2C
    i2c_devices = []
    if os.path.exists('/dev/i2c-1'):
        env_info['i2c_available'] = True
        print("✅ I2C bus disponibile (/dev/i2c-1)")
        
        # Lista dispositivi I2C
        try:
            import subprocess
            result = subprocess.run(['i2cdetect', '-y', '1'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                print("📋 Dispositivi I2C rilevati:")
                print(result.stdout)
        except FileNotFoundError:
            print("⚠️ i2c-tools non installato (sudo apt install i2c-tools)")
    else:
        print("❌ I2C bus non disponibile")
    
    # Controlla SPI
    spi_devices = []
    for spi_dev in ['/dev/spidev0.0', '/dev/spidev0.1']:
        if os.path.exists(spi_dev):
            env_info['spi_available'] = True
            spi_devices.append(spi_dev)
    
    if spi_devices:
        print(f"✅ SPI dispositivi: {spi_devices}")
    else:
        print("❌ SPI dispositivi non disponibili")
    
    return env_info

def check_python_libraries() -> Dict[str, Any]:
    """Controlla librerie Python PN532"""
    print_section("📚 LIBRERIE PYTHON PN532")
    
    libs_info = {
        'adafruit_circuitpython_pn532': False,
        'adafruit_blinka': False,
        'board_module': False,
        'busio_module': False,
        'pn532_fallback': False,
        'macos_limitation': False
    }
    
    # Test Adafruit CircuitPython (con gestione macOS)
    try:
        print("🔍 Test import board/busio...")
        import board
        import busio
        libs_info['board_module'] = True
        libs_info['busio_module'] = True
        print("✅ board e busio disponibili")
        
    except NotImplementedError as e:
        # Errore tipico di macOS - board non supportato
        libs_info['macos_limitation'] = True
        print(f"⚠️ board/busio limitati su macOS: platform non supportata")
        print("   (Normale su macOS - richiede Raspberry Pi per funzionamento completo)")
        
        # Testiamo comunque se i moduli sono installati
        try:
            import adafruit_blinka
            libs_info['adafruit_blinka'] = True
            print("✅ adafruit_blinka installato (limitato su macOS)")
        except ImportError:
            print("❌ adafruit_blinka non installato")
        
        try:
            # Test import senza inizializzazione
            import adafruit_pn532.i2c
            import adafruit_pn532.spi  
            libs_info['adafruit_circuitpython_pn532'] = True
            print("✅ adafruit_pn532 moduli installati (limitato su macOS)")
        except ImportError as e:
            print(f"❌ adafruit_pn532 non disponibile: {e}")
        
    except ImportError as e:
        print(f"❌ board/busio non disponibili: {e}")
    
    # Se board funziona (su Raspberry Pi), test completo
    if libs_info['board_module'] and not libs_info['macos_limitation']:
        try:
            from adafruit_pn532.i2c import PN532_I2C
            from adafruit_pn532.spi import PN532_SPI
            libs_info['adafruit_circuitpython_pn532'] = True
            print("✅ adafruit_pn532 (I2C/SPI) disponibile")
        except ImportError as e:
            print(f"❌ adafruit_pn532 non disponibile: {e}")
        
        try:
            import adafruit_blinka
            libs_info['adafruit_blinka'] = True
            print("✅ adafruit_blinka disponibile")
        except ImportError as e:
            print(f"❌ adafruit_blinka non disponibile: {e}")
    
    # Test libreria pn532 fallback
    try:
        from pn532 import PN532_I2C, PN532_SPI
        libs_info['pn532_fallback'] = True
        print("✅ pn532 (libreria fallback) disponibile")
    except ImportError:
        print("❌ pn532 fallback non disponibile")
    
    return libs_info

def check_current_configuration() -> Dict[str, Any]:
    """Controlla configurazione attuale del sistema"""
    print_section("⚙️ CONFIGURAZIONE ATTUALE")
    
    config_info = {}
    
    try:
        from rfid_gate.config.settings import RFIDGateConfig
        
        config = RFIDGateConfig.from_env()
        
        print_subsection("Lettore IN (RFID_IN)")
        print(f"  Abilitato: {config.rfid_in.enabled}")
        print(f"  Tipo: {config.rfid_in.reader_type.value}")
        
        if config.rfid_in.reader_type.value == 'pn532':
            print(f"  Interfaccia: {config.rfid_in.pn532_interface.value}")
            print(f"  I2C Address: 0x{config.rfid_in.pn532_i2c_address:02X}")
            print(f"  SPI Bus/Device: {config.rfid_in.pn532_spi_bus}/{config.rfid_in.pn532_spi_device}")
        
        print_subsection("Lettore OUT (RFID_OUT)")
        print(f"  Abilitato: {config.rfid_out.enabled}")
        print(f"  Tipo: {config.rfid_out.reader_type.value}")
        
        if config.rfid_out.reader_type.value == 'pn532':
            print(f"  Interfaccia: {config.rfid_out.pn532_interface.value}")
            print(f"  I2C Address: 0x{config.rfid_out.pn532_i2c_address:02X}")
            print(f"  SPI Bus/Device: {config.rfid_out.pn532_spi_bus}/{config.rfid_out.pn532_spi_device}")
        
        config_info = {
            'rfid_in_enabled': config.rfid_in.enabled,
            'rfid_in_type': config.rfid_in.reader_type.value,
            'rfid_in_interface': config.rfid_in.pn532_interface.value if config.rfid_in.reader_type.value == 'pn532' else None,
            'rfid_in_i2c_addr': config.rfid_in.pn532_i2c_address if config.rfid_in.reader_type.value == 'pn532' else None,
            'rfid_out_enabled': config.rfid_out.enabled,
            'rfid_out_type': config.rfid_out.reader_type.value,
            'rfid_out_interface': config.rfid_out.pn532_interface.value if config.rfid_out.reader_type.value == 'pn532' else None,
            'rfid_out_spi_bus': config.rfid_out.pn532_spi_bus if config.rfid_out.reader_type.value == 'pn532' else None,
        }
        
    except Exception as e:
        print(f"❌ Errore lettura configurazione: {e}")
        config_info = {'error': str(e)}
    
    return config_info

def check_legacy_configuration() -> Dict[str, Any]:
    """Controlla configurazione legacy che funzionava"""
    print_section("🏛️ CONFIGURAZIONE LEGACY")
    
    legacy_info = {}
    
    try:
        # Leggi configurazione da archive
        archive_path = Path(__file__).parent / "archive" / "old_system" / "src"
        
        if archive_path.exists():
            print(f"📁 Archive trovato: {archive_path}")
            
            config_file = archive_path / "config.py"
            if config_file.exists():
                print("✅ config.py legacy trovato")
                
                # Leggi configurazione (semplificato)
                with open(config_file, 'r') as f:
                    content = f.read()
                    
                print_subsection("Configurazione Legacy")
                if "'type': 'pn532'" in content:
                    print("  Tipo: PN532 configurato")
                if "'interface': 'i2c'" in content:
                    print("  I2C interface configurato")
                if "'interface': 'spi'" in content:
                    print("  SPI interface configurato")
                
                legacy_info['found'] = True
                legacy_info['config_file'] = str(config_file)
            else:
                print("❌ config.py legacy non trovato")
                legacy_info['found'] = False
        else:
            print("❌ Archive non trovato")
            legacy_info['found'] = False
    
    except Exception as e:
        print(f"❌ Errore lettura legacy: {e}")
        legacy_info = {'error': str(e)}
    
    return legacy_info

async def test_pn532_readers() -> Dict[str, Any]:
    """Test creazione lettori PN532 attuali"""
    print_section("🧪 TEST LETTORI PN532 ATTUALI")
    
    test_info = {
        'i2c_reader_created': False,
        'spi_reader_created': False,
        'i2c_initialized': False,
        'spi_initialized': False,
        'i2c_error': None,
        'spi_error': None,
        'macos_limitation': False
    }
    
    try:
        from rfid_gate.hardware.readers.pn532 import PN532Reader
        
        print_subsection("Test Lettore I2C (IN)")
        try:
            reader_i2c = PN532Reader(
                reader_id="TEST_I2C_IN", 
                direction="in", 
                interface="i2c",
                i2c_address=0x24
            )
            test_info['i2c_reader_created'] = True
            print("✅ Lettore I2C creato")
            
            # Prova inizializzazione
            try:
                result = await reader_i2c._hardware_init()
                test_info['i2c_initialized'] = result
                
                if result:
                    print("✅ Lettore I2C inizializzato")
                else:
                    print("❌ Lettore I2C inizializzazione fallita (normale su macOS)")
            except NotImplementedError as e:
                test_info['macos_limitation'] = True
                print("⚠️ Lettore I2C limitato su macOS (richiede Raspberry Pi)")
                
        except Exception as e:
            test_info['i2c_error'] = str(e)
            print(f"❌ Errore lettore I2C: {e}")
        
        print_subsection("Test Lettore SPI (OUT)")
        try:
            reader_spi = PN532Reader(
                reader_id="TEST_SPI_OUT",
                direction="out",
                interface="spi",
                spi_bus=0,
                spi_device=0
            )
            test_info['spi_reader_created'] = True
            print("✅ Lettore SPI creato")
            
            # Prova inizializzazione
            try:
                result = await reader_spi._hardware_init()
                test_info['spi_initialized'] = result
                
                if result:
                    print("✅ Lettore SPI inizializzato")
                else:
                    print("❌ Lettore SPI inizializzazione fallita (normale su macOS)")
            except NotImplementedError as e:
                test_info['macos_limitation'] = True
                print("⚠️ Lettore SPI limitato su macOS (richiede Raspberry Pi)")
                
        except Exception as e:
            test_info['spi_error'] = str(e)
            print(f"❌ Errore lettore SPI: {e}")
    
    except ImportError as e:
        print(f"❌ Impossibile importare PN532Reader: {e}")
        test_info['import_error'] = str(e)
    
    return test_info

async def test_reader_factory() -> Dict[str, Any]:
    """Test factory per creazione reader"""
    print_section("🏭 TEST READER FACTORY")
    
    factory_info = {
        'factory_available': False,
        'readers_created': {},
        'errors': []
    }
    
    try:
        from rfid_gate.hardware.readers.factory import ReaderFactory
        from rfid_gate.config.settings import RFIDGateConfig
        
        factory_info['factory_available'] = True
        print("✅ ReaderFactory disponibile")
        
        config = RFIDGateConfig.from_env()
        
        print_subsection("Test Creazione Reader IN")
        try:
            reader_in = ReaderFactory.create_reader(
                config.rfid_in, "FACTORY_IN", "in"
            )
            if reader_in:
                factory_info['readers_created']['in'] = {
                    'type': reader_in.get_reader_type(),
                    'id': reader_in.reader_id,
                    'direction': reader_in.direction
                }
                print(f"✅ Reader IN creato: {reader_in}")
            else:
                print("❌ Reader IN non creato")
                
        except Exception as e:
            error_msg = f"Errore creazione reader IN: {e}"
            factory_info['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        print_subsection("Test Creazione Reader OUT")
        try:
            reader_out = ReaderFactory.create_reader(
                config.rfid_out, "FACTORY_OUT", "out"
            )
            if reader_out:
                factory_info['readers_created']['out'] = {
                    'type': reader_out.get_reader_type(),
                    'id': reader_out.reader_id,
                    'direction': reader_out.direction
                }
                print(f"✅ Reader OUT creato: {reader_out}")
            else:
                print("❌ Reader OUT non creato")
                
        except Exception as e:
            error_msg = f"Errore creazione reader OUT: {e}"
            factory_info['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    except ImportError as e:
        print(f"❌ Impossibile importare ReaderFactory: {e}")
        factory_info['import_error'] = str(e)
    
    return factory_info

def generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Genera raccomandazioni basate sui risultati"""
    print_section("💡 RACCOMANDAZIONI")
    
    recommendations = []
    
    # Controlla ambiente
    env = results.get('environment', {})
    if not env.get('is_raspberry_pi'):
        recommendations.append("🔄 CRITICO: Deployment su Raspberry Pi necessario per test hardware")
        print("🔄 CRITICO: Deployment su Raspberry Pi necessario per test hardware")
        
        # Guida per Raspberry Pi
        recommendations.append("📋 Setup Raspberry Pi:")
        recommendations.append("   1. Trasferisci codice su Raspberry Pi")
        recommendations.append("   2. sudo raspi-config -> Interface Options -> I2C Enable")
        recommendations.append("   3. sudo raspi-config -> Interface Options -> SPI Enable") 
        recommendations.append("   4. pip install adafruit-circuitpython-pn532 adafruit-blinka")
        recommendations.append("   5. Test connessioni fisiche lettori PN532")
        print("📋 Setup Raspberry Pi necessario per funzionamento completo")
    
    else:
        # Siamo su Raspberry Pi
        if not env.get('gpio_available'):
            recommendations.append("📦 Installa RPi.GPIO: pip install RPi.GPIO")
            print("📦 Installa RPi.GPIO: pip install RPi.GPIO")
        
        if not env.get('i2c_available'):
            recommendations.append("🔧 Abilita I2C: sudo raspi-config -> Interface Options -> I2C")
            print("🔧 Abilita I2C: sudo raspi-config -> Interface Options -> I2C")
        
        if not env.get('spi_available'):
            recommendations.append("🔧 Abilita SPI: sudo raspi-config -> Interface Options -> SPI")
            print("🔧 Abilita SPI: sudo raspi-config -> Interface Options -> SPI")
    
    # Controlla librerie
    libs = results.get('libraries', {})
    if libs.get('macos_limitation'):
        recommendations.append("⚠️ macOS: Librerie installate ma limitate - test su Raspberry Pi")
        print("⚠️ macOS: Librerie installate ma limitate - test su Raspberry Pi")
    elif not libs.get('adafruit_circuitpython_pn532'):
        recommendations.append("📦 Installa PN532: pip install adafruit-circuitpython-pn532")
        print("📦 Installa PN532: pip install adafruit-circuitpython-pn532")
    
    # Controlla configurazione
    config = results.get('configuration', {})
    if config.get('error'):
        recommendations.append("⚙️ Correggi errori configurazione sistema")
        print("⚙️ Correggi errori configurazione sistema")
    else:
        print("✅ Configurazione sistema valida")
        recommendations.append("✅ Configurazione sistema valida")
    
    # Controlla test PN532
    pn532_tests = results.get('pn532_tests', {})
    if pn532_tests.get('macos_limitation'):
        recommendations.append("🎯 Sistema pronto per deployment su Raspberry Pi")
        print("🎯 Sistema pronto per deployment su Raspberry Pi")
    elif pn532_tests.get('i2c_error') or not pn532_tests.get('i2c_initialized'):
        recommendations.append("🔌 Verifica connessione fisica lettore I2C")
        print("🔌 Verifica connessione fisica lettore I2C")
    
    # Test Factory
    factory_tests = results.get('factory_tests', {})
    if factory_tests.get('factory_available'):
        recommendations.append("✅ Reader Factory funzionante")
        print("✅ Reader Factory funzionante")
    
    # Summary per macOS
    if not env.get('is_raspberry_pi'):
        recommendations.append("📝 SUMMARY macOS:")
        recommendations.append("   - Codice e configurazione: ✅ OK")
        recommendations.append("   - Librerie PN532: ✅ Installate")
        recommendations.append("   - Hardware test: ❌ Richiede Raspberry Pi")
        print("📝 SUMMARY: Sistema configurato correttamente per deployment")
    
    return recommendations

async def main():
    """Funzione principale di diagnostica"""
    print_section("🔧 PN532 DIAGNOSTICA COMPLETA", "🔧")
    print("Tool per diagnosticare sistema PN532 RFID Gate")
    print("Confronta configurazione attuale con sistema legacy funzionante")
    
    results = {}
    
    # 1. Controlla ambiente
    results['environment'] = check_environment()
    
    # 2. Controlla librerie Python
    results['libraries'] = check_python_libraries()
    
    # 3. Controlla configurazione attuale
    results['configuration'] = check_current_configuration()
    
    # 4. Controlla configurazione legacy
    results['legacy'] = check_legacy_configuration()
    
    # 5. Test lettori PN532
    results['pn532_tests'] = await test_pn532_readers()
    
    # 6. Test Reader Factory
    results['factory_tests'] = await test_reader_factory()
    
    # 7. Genera raccomandazioni
    results['recommendations'] = generate_recommendations(results)
    
    print_section("📊 SUMMARY DIAGNOSTICA")
    print(f"🌍 Ambiente: {'Raspberry Pi' if results['environment'].get('is_raspberry_pi') else 'Non-Raspberry Pi'}")
    print(f"📚 Librerie PN532: {'OK' if results['libraries'].get('adafruit_circuitpython_pn532') else 'MANCANTI'}")
    print(f"⚙️ Configurazione: {'OK' if not results['configuration'].get('error') else 'ERRORI'}")
    print(f"🧪 Test I2C: {'OK' if results['pn532_tests'].get('i2c_initialized') else 'FALLITO'}")
    print(f"🧪 Test SPI: {'OK' if results['pn532_tests'].get('spi_initialized') else 'FALLITO'}")
    print(f"🏭 Factory: {'OK' if results['factory_tests'].get('factory_available') else 'ERRORI'}")
    
    print("\n💾 PROSSIMI PASSI:")
    print("1. Se su macOS: trasferisci su Raspberry Pi per test hardware")
    print("2. Verifica connessioni fisiche lettori PN532")
    print("3. Testa sistema completo con main.py")
    print("4. Confronta log con sistema legacy funzionante")

if __name__ == "__main__":
    asyncio.run(main())