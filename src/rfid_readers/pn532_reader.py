#!/usr/bin/env python3
"""
Implementazione per lettore Waveshare PN532
"""
import time
from .base_reader import BaseRFIDReader

class PN532Reader(BaseRFIDReader):
    """Lettore RFID PN532 - Ottimizzato per doppio lettore IN/OUT"""
    
    def __init__(self, reader_id="pn532", interface="i2c", **kwargs):
        super().__init__(reader_id, **kwargs)
        self.interface = interface.lower()
        self.pn532 = None
        self.reader_instance = None
        
        # Parametri di connessione
        if self.interface == "i2c":
            self.i2c_address = kwargs.get('i2c_address', 0x24)
        elif self.interface == "spi":
            self.spi_bus = kwargs.get('spi_bus', 0)
            self.spi_device = kwargs.get('spi_device', 0)
        elif self.interface == "uart":
            self.uart_port = kwargs.get('uart_port', '/dev/serial0')
            self.uart_baudrate = kwargs.get('uart_baudrate', 115200)
    
    def initialize(self):
        """Inizializza lettore PN532"""
        try:
            print(f"🔄 Inizializzazione PN532 {self.reader_id} via {self.interface.upper()}...")
            
            # Import della libreria PN532 con fallback robusto
            if self.interface == "i2c":
                try:
                    from pn532 import PN532_I2C
                    import busio
                    import board
                    
                    i2c = busio.I2C(board.SCL, board.SDA)
                    self.pn532 = PN532_I2C(i2c, address=self.i2c_address, debug=False)
                    print(f"🔵 PN532 I2C configurato - Address: 0x{self.i2c_address:02X}")
                    
                except ImportError:
                    # Fallback per librerie alternative
                    print("⚠️ Libreria pn532 standard non trovata, provo alternative...")
                    try:
                        import board
                        import busio
                        from adafruit_pn532.i2c import PN532_I2C
                        
                        i2c = busio.I2C(board.SCL, board.SDA)
                        self.pn532 = PN532_I2C(i2c, address=self.i2c_address, debug=False)
                        print(f"🔵 PN532 Adafruit I2C configurato - Address: 0x{self.i2c_address:02X}")
                        
                    except ImportError as e:
                        print(f"❌ Nessuna libreria PN532 I2C trovata: {e}")
                        return False
                
            elif self.interface == "spi":
                try:
                    from pn532 import PN532_SPI
                    import busio
                    import board
                    import digitalio
                    
                    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                    cs_pin = digitalio.DigitalInOut(board.D8)
                    self.pn532 = PN532_SPI(spi, cs_pin, debug=False)
                    print(f"🟠 PN532 SPI configurato - Bus:{self.spi_bus}, Device:{self.spi_device}")
                    
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
                        
                    except ImportError as e:
                        print(f"❌ Nessuna libreria PN532 SPI trovata: {e}")
                        return False
                
            elif self.interface == "uart":
                try:
                    from pn532 import PN532_UART
                    import serial
                    
                    uart = serial.Serial(self.uart_port, baudrate=self.uart_baudrate, timeout=1)
                    self.pn532 = PN532_UART(uart, debug=False)
                    print(f"🟡 PN532 UART configurato - Port:{self.uart_port}, Baud:{self.uart_baudrate}")
                    
                except ImportError:
                    try:
                        import board
                        import busio
                        from adafruit_pn532.uart import PN532_UART
                        
                        uart = busio.UART(board.TX, board.RX, baudrate=self.uart_baudrate, timeout=1)
                        self.pn532 = PN532_UART(uart, debug=False)
                        print(f"🟡 PN532 Adafruit UART configurato")
                        
                    except ImportError as e:
                        print(f"❌ Nessuna libreria PN532 UART trovata: {e}")
                        return False
            
            else:
                raise ValueError(f"Interfaccia non supportata: {self.interface}")
            
            # Configura PN532 e verifica comunicazione
            self.pn532.SAM_configuration()
            
            # Verifica versione firmware
            try:
                ic, ver, rev, support = self.pn532.firmware_version
                print(f"✅ PN532 {self.reader_id} connesso - FW: v{ver}.{rev} (IC: 0x{ic:02X})")
                
                # Configurazione ottimale per lettura rapida
                self.pn532.set_passive_activation_retries(0xFF)  # Retry infiniti per stabilità
                
                self.is_initialized = True
                return True
                
            except Exception as fw_error:
                print(f"❌ Errore comunicazione PN532: {fw_error}")
                return False
            
        except ImportError as e:
            print(f"❌ Libreria PN532 non installata: {e}")
            print("💡 Installa con: pip install adafruit-circuitpython-pn532 adafruit-blinka")
            return False
        except Exception as e:
            print(f"❌ Errore init PN532 {self.reader_id}: {e}")
            return False
    
    def read_card(self):
        """Legge card PN532 - Ottimizzato per performance"""
        if not self.is_initialized:
            return None, None
        
        try:
            # Legge card ISO14443A (Mifare, NTAG, ecc.) con timeout breve
            uid = self.pn532.read_passive_target(timeout=0.1)  # Timeout ridotto per reattività
            
            if uid is not None:
                # Converte UID in formato compatibile con MFRC522
                if isinstance(uid, (bytes, bytearray)):
                    # Converte bytes in int per compatibilità totale
                    card_id = int.from_bytes(uid, byteorder='big')
                else:
                    card_id = uid
                
                if not self.apply_debounce(card_id):
                    return None, None  # Ignora per debounce
                
                # PN532 restituisce solo UID, dati vuoti per compatibilità
                card_data = ""
                
                return card_id, card_data
            
            return None, None
            
        except Exception as e:
            # Non stampiamo errore per timeout normale (evita spam)
            if "timeout" not in str(e).lower() and "no card" not in str(e).lower():
                print(f"Errore lettura PN532 {self.reader_id}: {e}")
            return None, None
    
    def read_card_detailed(self):
        """Lettura dettagliata con informazioni aggiuntive"""
        if not self.is_initialized:
            return None, None, None
        
        try:
            uid = self.pn532.read_passive_target(timeout=0.5)
            
            if uid is not None:
                card_id = int.from_bytes(uid, byteorder='big') if isinstance(uid, (bytes, bytearray)) else uid
                
                if not self.apply_debounce(card_id):
                    return None, None, None
                
                # Informazioni aggiuntive sulla card
                card_info = {
                    'uid_bytes': uid,
                    'uid_length': len(uid) if isinstance(uid, (bytes, bytearray)) else 4,
                    'type': 'ISO14443A',
                    'interface': self.interface
                }
                
                return card_id, "", card_info
            
            return None, None, None
            
        except Exception as e:
            if "timeout" not in str(e).lower():
                print(f"Errore lettura dettagliata PN532 {self.reader_id}: {e}")
            return None, None, None
    
    def test_connection(self):
        """Test connessione PN532"""
        if not self.is_initialized:
            return False
        
        try:
            # Verifica comunicazione leggendo versione firmware
            ic, ver, rev, support = self.pn532.firmware_version
            return True
        except Exception as e:
            print(f"Test PN532 {self.reader_id} fallito: {e}")
            return False
    
    def cleanup(self):
        """Cleanup PN532"""
        try:
            if self.pn532:
                # PN532 non ha metodi specifici di cleanup
                self.pn532 = None
            self.is_initialized = False
        except:
            pass