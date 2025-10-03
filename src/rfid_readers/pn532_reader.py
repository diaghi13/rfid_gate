#!/usr/bin/env python3
"""
PN532 RFID Reader Implementation - Versione Compatibile
Supporta interfacce I2C, SPI e UART con gestione errori robusta.
"""

import time
from .base_reader import BaseRFIDReader


class PN532Reader(BaseRFIDReader):
    """Implementazione del lettore PN532 per NFC/RFID - Versione compatibile."""
    
    def __init__(self, reader_id="PN532", interface="i2c", **kwargs):
        super().__init__(reader_id)
        
        self.interface = interface.lower()
        self.pn532 = None
        
        # Configurazioni I2C
        self.i2c_address = kwargs.get('i2c_address', 0x24)  # Indirizzo fisso Waveshare
        
        # Configurazioni SPI
        self.spi_bus = kwargs.get('spi_bus', 0)
        self.spi_device = kwargs.get('spi_device', 0)
        
        # Configurazioni UART
        self.uart_port = kwargs.get('uart_port', '/dev/serial0')
        self.uart_baudrate = kwargs.get('uart_baudrate', 115200)
        
        print(f"📡 PN532Reader {reader_id} creato - Interface: {self.interface.upper()}")
    
    def initialize(self):
        """Inizializza il lettore PN532 con gestione errori robusta."""
        if self.is_initialized:
            return True
        
        print(f"🔄 Inizializzazione PN532 {self.reader_id} - {self.interface.upper()}")
        
        try:
            # Configura interfaccia specifica
            if self.interface == "i2c":
                success = self._setup_i2c()
            elif self.interface == "spi":
                success = self._setup_spi()
            elif self.interface == "uart":
                success = self._setup_uart()
            else:
                raise ValueError(f"Interfaccia non supportata: {self.interface}")
            
            if not success:
                return False
            
            # Configura PN532 con retry robusto
            return self._configure_pn532()
            
        except ImportError as e:
            print(f"❌ Libreria PN532 non installata: {e}")
            print("💡 Installa con: pip install adafruit-circuitpython-pn532 adafruit-blinka")
            return False
        except Exception as e:
            print(f"❌ Errore init PN532 {self.reader_id}: {e}")
            self._print_hardware_checklist()
            return False
    
    def _setup_i2c(self):
        """Configura interfaccia I2C con fallback alle librerie disponibili."""
        # Prova prima con libreria dedicata PN532
        try:
            from pn532 import PN532_I2C
            import board
            import busio
            
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pn532 = PN532_I2C(i2c, address=self.i2c_address, debug=False)
            print(f"🔵 PN532 I2C configurato - Indirizzo: 0x{self.i2c_address:02X}")
            return True
            
        except ImportError:
            # Fallback a Adafruit se libreria dedicata non disponibile
            try:
                import board
                import busio
                from adafruit_pn532.i2c import PN532_I2C
                
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pn532 = PN532_I2C(i2c, address=self.i2c_address, debug=False)
                print(f"🔵 PN532 Adafruit I2C configurato - Indirizzo: 0x{self.i2c_address:02X}")
                return True
                
            except ImportError as e:
                print(f"❌ Nessuna libreria PN532 I2C trovata: {e}")
                return False
    
    def _setup_spi(self):
        """Configura interfaccia SPI con fallback alle librerie disponibili."""
        try:
            from pn532 import PN532_SPI
            import busio
            import board
            import digitalio
            
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            cs_pin = digitalio.DigitalInOut(board.D8)
            self.pn532 = PN532_SPI(spi, cs_pin, debug=False)
            print(f"🟠 PN532 SPI configurato - Bus:{self.spi_bus}, Device:{self.spi_device}")
            return True
            
        except ImportError:
            try:
                import board
                import busio
                import digitalio
                from adafruit_pn532.spi import PN532_SPI
                
                spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                cs_pin = digitalio.DigitalInOut(board.D8)
                self.pn532 = PN532_SPI(spi, cs_pin, debug=False)
                print(f"🟠 PN532 Adafruit SPI configurato")
                return True
                
            except ImportError as e:
                print(f"❌ Nessuna libreria PN532 SPI trovata: {e}")
                return False
    
    def _setup_uart(self):
        """Configura interfaccia UART con fallback alle librerie disponibili."""
        try:
            from pn532 import PN532_UART
            import serial
            
            uart = serial.Serial(self.uart_port, baudrate=self.uart_baudrate, timeout=1)
            self.pn532 = PN532_UART(uart, debug=False)
            print(f"🟡 PN532 UART configurato - Port:{self.uart_port}, Baud:{self.uart_baudrate}")
            return True
            
        except ImportError:
            try:
                import board
                import busio
                from adafruit_pn532.uart import PN532_UART
                
                uart = busio.UART(board.TX, board.RX, baudrate=self.uart_baudrate, timeout=1)
                self.pn532 = PN532_UART(uart, debug=False)
                print(f"🟡 PN532 Adafruit UART configurato")
                return True
                
            except ImportError as e:
                print(f"❌ Nessuna libreria PN532 UART trovata: {e}")
                return False
    
    def _configure_pn532(self):
        """Configura PN532 con retry robusto per SAM e firmware."""
        print("🔧 Configurazione PN532...")
        
        # Configurazione SAM (opzionale - non blocca se fallisce)
        try:
            self.pn532.SAM_configuration()
            print("✅ SAM configurato")
        except Exception as e:
            print(f"⚠️ SAM configurazione fallita: {e}")
            print("   (Continuando senza SAM - normale per alcuni moduli)")
        
        # Verifica versione firmware con retry
        print("🔍 Verifica firmware...")
        for attempt in range(3):
            try:
                fw_info = self.pn532.firmware_version
                if fw_info and len(fw_info) >= 4:
                    ic, ver, rev, support = fw_info
                    print(f"✅ PN532 {self.reader_id} connesso - FW: v{ver}.{rev} (IC: 0x{ic:02X})")
                else:
                    print(f"✅ PN532 {self.reader_id} connesso (info firmware limitata)")
                
                # Configurazioni opzionali compatibili
                self._apply_optional_configs()
                
                self.is_initialized = True
                return True
                
            except Exception as fw_error:
                print(f"⚠️ Tentativo {attempt + 1} firmware fallito: {fw_error}")
                if attempt == 2:
                    print(f"❌ Errore comunicazione PN532 dopo 3 tentativi: {fw_error}")
                    return False
                time.sleep(1.0)  # Attesa più lunga tra tentativi
        
        return False
    
    def _apply_optional_configs(self):
        """Applica configurazioni opzionali se disponibili - NON usa metodi deprecati."""
        try:
            # RIMOSSO: set_passive_activation_retries - non disponibile in tutte le versioni
            # Non applichiamo configurazioni che potrebbero causare errori
            print("🔧 Configurazioni base applicate")
        except Exception as e:
            print(f"⚠️ Configurazioni opzionali fallite: {e}")
    
    def _print_hardware_checklist(self):
        """Stampa checklist per verifica hardware."""
        print("🔧 Verificare:")
        print("   - Connessioni hardware (VCC, GND, SDA, SCL)")
        print("   - Jumper I2C: LSB=ON, MSB=OFF")
        print("   - I2C abilitato: sudo raspi-config")
        print("   - Dispositivo visibile: sudo i2cdetect -y 1")
    
    def read_card(self):
        """Legge una carta RFID/NFC - COMPATIBILE CON SISTEMA ESISTENTE."""
        if not self.is_initialized:
            return None, None  # Restituisce tupla per compatibilità
        
        try:
            # Legge UID della carta con timeout breve per performance
            uid = self.pn532.read_passive_target(timeout=0.1)
            
            if uid is None:
                return None, None  # Nessuna carta rilevata
            
            # Converte UID in formato numerico per compatibilità
            if isinstance(uid, (bytes, bytearray)):
                # Converte bytes in intero
                card_id = int.from_bytes(uid, byteorder='big')
                # Crea anche rappresentazione hex pulita
                uid_hex = ''.join([f'{b:02X}' for b in uid])
            else:
                # Se è già una lista o altro formato
                card_id = uid if isinstance(uid, int) else hash(str(uid))
                uid_hex = str(uid)
            
            # Applica debounce usando card_id numerico
            if not self.apply_debounce(card_id):
                return None, None  # Ignora per debounce
            
            # Formatta UID secondo configurazione di sistema
            try:
                from config import Config
                
                # Usa l'UID hex per la formattazione
                if Config.UID_FORMAT_MODE == 'remove_suffix' and len(uid_hex) > Config.UID_CHARS_COUNT:
                    formatted_uid = uid_hex[:-Config.UID_CHARS_COUNT]
                elif Config.UID_FORMAT_MODE == 'truncate':
                    formatted_uid = uid_hex[:Config.UID_TARGET_LENGTH]
                elif Config.UID_FORMAT_MODE == 'take_last':
                    formatted_uid = uid_hex[-Config.UID_TARGET_LENGTH:]
                elif Config.UID_FORMAT_MODE == 'fixed_length':
                    if len(uid_hex) > Config.UID_TARGET_LENGTH:
                        formatted_uid = uid_hex[:Config.UID_TARGET_LENGTH]
                    else:
                        formatted_uid = uid_hex.zfill(Config.UID_TARGET_LENGTH)
                else:
                    formatted_uid = uid_hex.zfill(8)
                
                # Debug se abilitato
                if hasattr(Config, 'UID_DEBUG_MODE') and Config.UID_DEBUG_MODE:
                    print(f"🔧 PN532 UID: raw={uid_hex}, formatted={formatted_uid}, mode={Config.UID_FORMAT_MODE}")
                
            except Exception as e:
                print(f"⚠️ Errore formattazione UID: {e}")
                formatted_uid = uid_hex.zfill(8)
            
            # Prepara card_data vuoto (PN532 non legge automaticamente dati NDEF)
            card_data = ""
            
            print(f"📇 {self.reader_id} - Carta: {formatted_uid} (PN532-{len(uid)}byte)")
            
            # Restituisce tupla compatibile con sistema esistente
            return card_id, card_data
            
        except Exception as e:
            # Non stampiamo errore per timeout normale
            error_msg = str(e).lower()
            if not any(x in error_msg for x in ['timeout', 'no card', 'did not receive', 'ack']):
                print(f"❌ Errore lettura PN532: {e}")
            return None, None  # Sempre restituire tupla
    
    def test_connection(self):
        """Test connessione PN532 - IMPLEMENTAZIONE RICHIESTA."""
        if not self.is_initialized or not self.pn532:
            print(f"⚠️ PN532 {self.reader_id} non inizializzato")
            return False
        
        try:
            # Test semplice: prova a leggere versione firmware
            fw_info = self.pn532.firmware_version
            if fw_info:
                print(f"✅ Test connessione PN532 {self.reader_id} OK")
                return True
            else:
                print(f"❌ Test connessione PN532 {self.reader_id} fallito - no firmware info")
                return False
                
        except Exception as e:
            print(f"❌ Test connessione PN532 {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Pulizia risorse PN532."""
        if self.pn532:
            try:
                # Non ci sono operazioni specifiche di cleanup per PN532
                print(f"🧹 PN532 {self.reader_id} - Cleanup completato")
            except Exception as e:
                print(f"⚠️ Errore durante cleanup PN532: {e}")
        
        self.is_initialized = False
        self.pn532 = None
    
    def get_status(self):
        """Restituisce lo stato del lettore PN532."""
        if not self.is_initialized:
            return {
                'reader_id': self.reader_id,
                'type': 'PN532',
                'interface': self.interface,
                'status': 'disconnected',
                'firmware': 'unknown'
            }
        
        try:
            fw_info = self.pn532.firmware_version
            if fw_info and len(fw_info) >= 4:
                ic, ver, rev, support = fw_info
                return {
                    'reader_id': self.reader_id,
                    'type': 'PN532',
                    'interface': self.interface,
                    'status': 'connected',
                    'firmware': f"v{ver}.{rev}",
                    'ic': f"0x{ic:02X}",
                    'address': f"0x{self.i2c_address:02X}" if self.interface == "i2c" else "N/A"
                }
            else:
                return {
                    'reader_id': self.reader_id,
                    'type': 'PN532',
                    'interface': self.interface,
                    'status': 'connected',
                    'firmware': 'detected',
                    'address': f"0x{self.i2c_address:02X}" if self.interface == "i2c" else "N/A"
                }
        except:
            return {
                'reader_id': self.reader_id,
                'type': 'PN532',
                'interface': self.interface,
                'status': 'error',
                'firmware': 'unreachable'
            }