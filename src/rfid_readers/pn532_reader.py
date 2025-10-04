#!/usr/bin/env python3
"""
PN532 RFID Reader Implementation - Design Robusto Anti-Blocco
Supporta interfacce I2C, SPI e UART con gestione errori che previene blocchi.
"""

import time
from .base_reader import BaseRFIDReader


class PN532Reader(BaseRFIDReader):
    """Lettore PN532 - Design robusto che NON si blocca mai."""
    
    def __init__(self, reader_id="PN532", interface="i2c", **kwargs):
        super().__init__(reader_id)
        
        self.interface = interface.lower()
        self.pn532 = None
        self.last_successful_read = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
        # Configurazioni I2C
        self.i2c_address = kwargs.get('i2c_address', 0x24)
        
        # Configurazioni SPI
        self.spi_bus = kwargs.get('spi_bus', 0)
        self.spi_device = kwargs.get('spi_device', 0)
        
        # Configurazioni UART
        self.uart_port = kwargs.get('uart_port', '/dev/serial0')
        self.uart_baudrate = kwargs.get('uart_baudrate', 115200)
        
        print(f"📡 PN532Reader {reader_id} creato - Interface: {self.interface.upper()}")
    
    def initialize(self):
        """Inizializzazione PN532 senza SAM config problematica."""
        if self.is_initialized:
            return True
        
        print(f"🔄 Inizializzazione PN532 {self.reader_id} - {self.interface.upper()}")
        
        try:
            # Crea connessione hardware
            if self.interface == "i2c":
                success = self._setup_i2c_robust()
            elif self.interface == "spi":
                success = self._setup_spi_robust()
            elif self.interface == "uart":
                success = self._setup_uart_robust()
            else:
                raise ValueError(f"Interfaccia non supportata: {self.interface}")
            
            if not success:
                return False
            
            # ❌ SKIP SAM configuration - causa blocchi!
            # ❌ SKIP set_passive_activation_retries - non esiste sempre
            
            # Test semplice firmware (senza blocking calls)
            try:
                fw_info = self._safe_firmware_check()
                if fw_info:
                    print(f"✅ PN532 {self.reader_id} - Firmware OK")
                else:
                    print(f"⚠️ PN532 {self.reader_id} - Firmware check limitato (continuiamo)")
            except Exception as e:
                print(f"⚠️ Firmware check fallito: {e} (continuiamo...)")
            
            self.is_initialized = True
            self.consecutive_errors = 0
            print(f"✅ PN532 {self.reader_id} inizializzato (design robusto)")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione PN532 {self.reader_id}: {e}")
            return False
    
    def _setup_i2c_robust(self):
        """Inizializzazione I2C robusta senza SAM config."""
        try:
            # Prova adafruit-circuitpython-pn532 (più stabile)
            try:
                import board
                import busio
                from adafruit_pn532.i2c import PN532_I2C
                
                # Crea bus I2C
                i2c = busio.I2C(board.SCL, board.SDA)
                
                # Crea PN532 con debug disabilitato (evita spam)
                self.pn532 = PN532_I2C(i2c, address=self.i2c_address, debug=False)
                
                print(f"   ✅ I2C PN532 creato - Address: 0x{self.i2c_address:02X}")
                return True
                
            except ImportError:
                # Fallback a pn532 lib
                try:
                    from pn532 import PN532_I2C
                    import board
                    import busio
                    
                    i2c_bus = busio.I2C(board.SCL, board.SDA)
                    self.pn532 = PN532_I2C(i2c_bus, address=self.i2c_address)
                    
                    print(f"   ✅ pn532 lib caricata - I2C {hex(self.i2c_address)}")
                    return True
                except ImportError as e:
                    print(f"❌ Nessuna libreria PN532 I2C trovata: {e}")
                    return False
        except Exception as e:
            print(f"❌ Errore setup I2C: {e}")
            return False
    
    def _setup_spi_robust(self):
        """Inizializzazione SPI robusta."""
        try:
            # Prova adafruit-circuitpython-pn532 (più stabile)
            try:
                import board
                import busio
                import digitalio
                from adafruit_pn532.spi import PN532_SPI
                
                spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                cs_pin = digitalio.DigitalInOut(board.D8)  # CS0 per device 0
                
                self.pn532 = PN532_SPI(spi, cs_pin, debug=False)
                
                print(f"   ✅ SPI PN532 creato - Bus: {self.spi_bus}, Device: {self.spi_device}")
                return True
                
            except ImportError:
                # Fallback a pn532 lib
                try:
                    from pn532 import PN532_SPI
                    import busio
                    import board
                    import digitalio
                    
                    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                    cs = digitalio.DigitalInOut(board.D8)
                    self.pn532 = PN532_SPI(spi, cs)
                    
                    print(f"   ✅ pn532 lib caricata - SPI")
                    return True
                except ImportError as e:
                    print(f"❌ Nessuna libreria PN532 SPI trovata: {e}")
                    return False
        except Exception as e:
            print(f"❌ Errore setup SPI: {e}")
            return False
    
    def _setup_uart_robust(self):
        """Inizializzazione UART robusta."""
        try:
            # Prova adafruit-circuitpython-pn532
            try:
                import board
                import busio
                from adafruit_pn532.uart import PN532_UART
                
                uart = busio.UART(board.TX, board.RX, baudrate=self.uart_baudrate)
                self.pn532 = PN532_UART(uart, debug=False)
                
                print(f"   ✅ UART PN532 creato - Port: {self.uart_port}, Baud: {self.uart_baudrate}")
                return True
                
            except ImportError:
                # Fallback a pn532 lib
                try:
                    from pn532 import PN532_UART
                    import serial
                    
                    self.pn532 = PN532_UART(self.uart_port, self.uart_baudrate)
                    
                    print(f"   ✅ pn532 lib caricata - UART {self.uart_port}")
                    return True
                except ImportError as e:
                    print(f"❌ Nessuna libreria PN532 UART trovata: {e}")
                    return False
        except Exception as e:
            print(f"❌ Errore setup UART: {e}")
            return False
    
    def _safe_firmware_check(self):
        """Check firmware senza bloccare il device."""
        try:
            # Timeout molto breve per evitare blocchi
            fw_info = self.pn532.firmware_version
            return fw_info is not None
        except:
            return False
    
    def read_card(self):
        """
        Legge la carta RFID/NFC - versione semplificata
        Returns: tuple (uid, card_type) o (None, None) se nessuna carta
        """
        if not self.is_initialized or not self.pn532:
            return None, None
        
        try:
            uid = self.pn532.read_passive_target(timeout=0.01)
            if uid:
                uid_hex = ''.join([f'{i:02x}' for i in uid])
                return uid_hex, 'mifare'
                
        except Exception as e:
            # Log solo per debug, non bloccare
            pass
                
        return None, None
    
    def _soft_reset(self):
        """
        Soft reset che NON richiede reboot sistema.
        """
        try:
            # Metodo 1: Recreate del device object
            old_pn532 = self.pn532
            self.pn532 = None
            
            # Breve pausa
            time.sleep(0.05)
            
            # Ricrea connessione
            if self.interface == "i2c":
                self._setup_i2c_robust()
            elif self.interface == "spi":
                self._setup_spi_robust()
            elif self.interface == "uart":
                self._setup_uart_robust()
            
            print(f"✅ PN532 {self.reader_id}: soft reset completato")
            
        except Exception as e:
            print(f"❌ Soft reset fallito: {e}")
    
    def test_connection(self):
        """Test connessione semplice."""
        if not self.is_initialized or not self.pn532:
            return False
        
        try:
            # Test molto semplice
            return self._safe_firmware_check()
        except:
            return False
    
    def cleanup(self):
        """Cleanup senza operazioni pericolose."""
        try:
            # NON chiamare metodi che possono bloccare
            self.pn532 = None
            self.is_initialized = False
            print(f"🧹 PN532 {self.reader_id} cleanup completato")
        except Exception as e:
            print(f"⚠️ Errore cleanup: {e}")
    
    def get_firmware_version(self):
        """Ottiene versione firmware (safe)."""
        if not self.is_initialized or not self.pn532:
            return None
        try:
            return self.pn532.firmware_version
        except:
            return None
    
    def get_reader_info(self):
        """Informazioni del lettore."""
        return {
            'type': 'PN532',
            'interface': self.interface,
            'initialized': self.is_initialized,
            'consecutive_errors': self.consecutive_errors,
            'last_read': self.last_successful_read
        }