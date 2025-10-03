#!/usr/bin/env python3
"""
PN532 RFID Reader Implementation
Supporta interfacce I2C, SPI e UART con gestione errori avanzata.
"""

import time
from .base_reader import BaseRFIDReader


class PN532Reader(BaseRFIDReader):
    """Implementazione del lettore PN532 per NFC/RFID."""
    
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
        self.uart_port = kwargs.get('uart_port', '/dev/ttyAMA0')
        self.uart_baudrate = kwargs.get('uart_baudrate', 115200)
        
        print(f"📡 PN532Reader {reader_id} creato - Interface: {self.interface.upper()}")
    
    def initialize(self):
        """Inizializza il lettore PN532 con gestione avanzata degli errori e retry."""
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
        
        # Retry della configurazione SAM fino a 3 volte
        for attempt in range(3):
            try:
                self.pn532.SAM_configuration()
                print(f"✅ SAM configurato al tentativo {attempt + 1}")
                break
            except Exception as e:
                print(f"⚠️ Tentativo {attempt + 1} SAM fallito: {e}")
                if attempt == 2:
                    raise
                time.sleep(0.5)
        
        # Verifica versione firmware con timeout esteso
        print("🔍 Verifica firmware...")
        for attempt in range(3):
            try:
                ic, ver, rev, support = self.pn532.firmware_version
                print(f"✅ PN532 {self.reader_id} connesso - FW: v{ver}.{rev} (IC: 0x{ic:02X})")
                
                # Configurazione ottimale per lettura rapida
                try:
                    self.pn532.set_passive_activation_retries(0xFF)
                    print("🔧 Retry infiniti configurati")
                except:
                    print("⚠️ set_passive_activation_retries non supportato")
                
                self.is_initialized = True
                return True
                
            except Exception as fw_error:
                print(f"⚠️ Tentativo {attempt + 1} firmware fallito: {fw_error}")
                if attempt == 2:
                    print(f"❌ Errore comunicazione PN532 dopo 3 tentativi: {fw_error}")
                    return False
                time.sleep(1.0)  # Attesa più lunga tra tentativi
        
        return False
    
    def _print_hardware_checklist(self):
        """Stampa checklist per verifica hardware."""
        print("🔧 Verificare:")
        print("   - Connessioni hardware (VCC, GND, SDA, SCL)")
        print("   - Jumper I2C: LSB=ON, MSB=OFF")
        print("   - I2C abilitato: sudo raspi-config")
        print("   - Dispositivo visibile: sudo i2cdetect -y 1")
    
    def read_card(self):
        """Legge una carta RFID/NFC."""
        if not self.is_initialized:
            print(f"❌ PN532 {self.reader_id} non inizializzato")
            return None
        
        try:
            # Legge UID della carta con timeout breve per performance
            uid = self.pn532.read_passive_target(timeout=0.5)
            
            if uid is None:
                return None
            
            # Formatta UID come stringa esadecimale
            uid_str = self.format_card_uid([hex(byte) for byte in uid])
            
            # Applica debounce se configurato
            current_time = time.time()
            if self.apply_debounce(uid_str, current_time):
                return None
            
            # Prepara informazioni carta
            card_info = self.get_card_info(uid_str, len(uid))
            
            print(f"📇 {self.reader_id} - Carta: {card_info['uid']} ({card_info['type']})")
            return card_info
            
        except Exception as e:
            print(f"❌ Errore lettura PN532: {e}")
            return None
    
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
            ic, ver, rev, support = self.pn532.firmware_version
            return {
                'reader_id': self.reader_id,
                'type': 'PN532',
                'interface': self.interface,
                'status': 'connected',
                'firmware': f"v{ver}.{rev}",
                'ic': f"0x{ic:02X}",
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