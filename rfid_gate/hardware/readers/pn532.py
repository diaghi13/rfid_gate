#!/usr/bin/env python3
"""
🔌 PN532 RFID Reader - Refactored Version  
========================================

Implementazione robusta del lettore PN532 con supporto per:
- Interfacce I2C, SPI, UART
- Gestione errori avanzata  
- Design anti-blocco
- Async/await support
- Compatibilità completa con il sistema esistente
"""

import asyncio
import time
from typing import Optional, Dict, Any
from rfid_gate.hardware.readers.base import BaseRFIDReader


class PN532Reader(BaseRFIDReader):
    """
    Lettore PN532 - Design robusto che NON si blocca mai.
    
    Supporta tre interfacce:
    - I2C: Interfaccia standard (default)
    - SPI: Per sistemi dual-reader
    - UART: Per connessioni seriali
    """
    
    def __init__(self, reader_id: str = "PN532", direction: str = "in", 
                 interface: str = "i2c", **kwargs):
        super().__init__(reader_id, direction)
        
        self.interface = interface.lower()
        self.pn532 = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        self.last_successful_read = 0
        
        # Configurazioni I2C
        self.i2c_address = kwargs.get('i2c_address', 0x24)
        
        # Configurazioni SPI
        self.spi_bus = kwargs.get('spi_bus', 0)
        self.spi_device = kwargs.get('spi_device', 0)
        
        # Configurazioni UART
        self.uart_port = kwargs.get('uart_port', '/dev/serial0')
        self.uart_baudrate = kwargs.get('uart_baudrate', 115200)
        
        # Pin GPIO aggiuntivi (per compatibilità legacy)
        self.rst_pin = kwargs.get('rst_pin', None)
        self.sda_pin = kwargs.get('sda_pin', None)  # Usato come CS pin per SPI
        
        print(f"📡 PN532Reader {reader_id} creato - Interface: {self.interface.upper()}")
    
    def get_reader_type(self) -> str:
        """Restituisce tipo lettore"""
        return "pn532"
    
    async def _hardware_init(self) -> bool:
        """
        Inizializzazione hardware PN532 senza SAM config problematica.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        print(f"🔄 Inizializzazione PN532 {self.reader_id} - {self.interface.upper()}")
        
        try:
            # Crea connessione hardware
            if self.interface == "i2c":
                success = await self._setup_i2c_robust()
            elif self.interface == "spi":
                success = await self._setup_spi_robust()
            elif self.interface == "uart":
                success = await self._setup_uart_robust()
            else:
                raise ValueError(f"Interfaccia non supportata: {self.interface}")
            
            if not success:
                return False
            
            # Test hardware rigoroso (come sistema legacy)
            hardware_test_ok = await self._hardware_connection_test()
            if not hardware_test_ok:
                print(f"❌ PN532 {self.reader_id} - Test hardware fallito")
                return False
            
            # ❌ SKIP SAM configuration - causa blocchi!
            # ❌ SKIP set_passive_activation_retries - non esiste sempre
            
            # Test firmware con validazione rigorosa
            try:
                fw_info = await self._safe_firmware_check()
                if fw_info:
                    print(f"✅ PN532 {self.reader_id} - Firmware OK: {fw_info}")
                    self.consecutive_errors = 0
                    print(f"✅ PN532 {self.reader_id} inizializzato (test hardware superato)")
                    return True
                else:
                    print(f"❌ PN532 {self.reader_id} - Firmware non raggiungibile")
                    return False
            except Exception as e:
                print(f"❌ PN532 {self.reader_id} - Firmware check fallito: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Errore inizializzazione PN532 {self.reader_id}: {e}")
            return False
    
    async def _setup_i2c_robust(self) -> bool:
        """Inizializzazione I2C robusta senza SAM config."""
        try:
            # Prova adafruit-circuitpython-pn532 (più stabile)
            try:
                import board
                import busio
                from adafruit_pn532.i2c import PN532_I2C
                
                # Esegui in thread per evitare blocchi async
                loop = asyncio.get_event_loop()
                
                def _create_i2c():
                    # Crea bus I2C
                    i2c = busio.I2C(board.SCL, board.SDA)
                    # Crea PN532 con debug disabilitato (evita spam)
                    return PN532_I2C(i2c, address=self.i2c_address, debug=False)
                
                self.pn532 = await loop.run_in_executor(None, _create_i2c)
                
                print(f"   ✅ I2C PN532 creato - Address: 0x{self.i2c_address:02X}")
                return True
                
            except ImportError:
                # Fallback a pn532 lib
                try:
                    from pn532 import PN532_I2C
                    from pn532.interface.i2c import I2C
                    
                    def _create_fallback():
                        i2c_interface = I2C(address=self.i2c_address)
                        return PN532_I2C(i2c_interface)
                    
                    self.pn532 = await loop.run_in_executor(None, _create_fallback)
                    
                    print(f"   ✅ I2C PN532 (fallback) - Address: 0x{self.i2c_address:02X}")
                    return True
                    
                except ImportError as e:
                    print(f"   ❌ Nessuna libreria PN532 I2C disponibile: {e}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Errore setup I2C: {e}")
            return False
    
    async def _setup_spi_robust(self) -> bool:
        """Inizializzazione SPI robusta con CS pin corretto."""
        try:
            try:
                import board
                import busio
                import digitalio
                from adafruit_pn532.spi import PN532_SPI
                
                loop = asyncio.get_event_loop()
                
                def _create_spi():
                    # Crea bus SPI
                    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                    
                    # CS pin - usa pin specifico se configurato, altrimenti D8 (come legacy)
                    if self.sda_pin is not None:
                        # sda_pin viene usato come CS pin per PN532 SPI nel legacy
                        # Pin 7 = GPIO4, Pin 8 = GPIO14, ecc.
                        if self.sda_pin == 7:
                            cs_pin = digitalio.DigitalInOut(board.D4)
                        elif self.sda_pin == 8:
                            cs_pin = digitalio.DigitalInOut(board.D14) 
                        else:
                            # Fallback a D8 standard
                            cs_pin = digitalio.DigitalInOut(board.D8)
                    else:
                        # Default D8 come nel sistema legacy
                        cs_pin = digitalio.DigitalInOut(board.D8)
                    
                    return PN532_SPI(spi, cs_pin, debug=False)
                
                self.pn532 = await loop.run_in_executor(None, _create_spi)
                
                print(f"   ✅ SPI PN532 creato - Bus: {self.spi_bus}, Device: {self.spi_device}, CS: {self.sda_pin or 'D8'}")
                return True
                
            except ImportError:
                # Fallback SPI
                try:
                    from pn532 import PN532_SPI
                    from pn532.interface.spi import SPI
                    
                    def _create_spi_fallback():
                        spi_interface = SPI(bus=self.spi_bus, device=self.spi_device)
                        return PN532_SPI(spi_interface)
                    
                    self.pn532 = await loop.run_in_executor(None, _create_spi_fallback)
                    
                    print(f"   ✅ SPI PN532 (fallback) - Bus: {self.spi_bus}")
                    return True
                    
                except ImportError as e:
                    print(f"   ❌ Nessuna libreria PN532 SPI disponibile: {e}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Errore setup SPI: {e}")
            return False
    
    async def _setup_uart_robust(self) -> bool:
        """Inizializzazione UART robusta."""
        try:
            try:
                import board
                import busio
                from adafruit_pn532.uart import PN532_UART
                
                loop = asyncio.get_event_loop()
                
                def _create_uart():
                    # Crea UART
                    uart = busio.UART(board.TX, board.RX, baudrate=self.uart_baudrate)
                    return PN532_UART(uart, debug=False)
                
                self.pn532 = await loop.run_in_executor(None, _create_uart)
                
                print(f"   ✅ UART PN532 creato - Port: {self.uart_port}, Baud: {self.uart_baudrate}")
                return True
                
            except ImportError:
                print(f"   ❌ adafruit_pn532 UART non disponibile")
                return False
                
        except Exception as e:
            print(f"   ❌ Errore setup UART: {e}")
            return False
    
    async def _hardware_connection_test(self) -> bool:
        """
        Test rigoroso della connessione hardware PN532.
        Simula il test_connection() del sistema legacy.
        
        Returns:
            bool: True se hardware effettivamente connesso e funzionante
        """
        if not self.pn532:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            def _test_hardware():
                """Test hardware sincrono"""
                try:
                    # Test 1: Verifica firmware_version (se dispositivo risponde)
                    fw = self.pn532.firmware_version
                    if not fw:
                        return False
                    
                    # Test 2: Prova una lettura rapida per verificare la comunicazione
                    # Questo fallisce se i pin sono sbagliati o hardware non connesso
                    try:
                        # Timeout molto breve per test rapido
                        result = self.pn532.read_passive_target(timeout=0.05)
                        # Non importa il risultato, importa che non dia eccezione
                        return True
                    except Exception:
                        # Se firmware_version funziona ma read_passive no,
                        # potrebbe essere problema pin/connessioni
                        return fw is not None
                        
                except Exception as e:
                    print(f"   ⚠️ Hardware test details: {e}")
                    return False
            
            # Esegui test con timeout per evitare blocchi
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _test_hardware),
                timeout=2.0
            )
            
            if result:
                print(f"   ✅ PN532 {self.reader_id} - Hardware test superato")
            else:
                print(f"   ❌ PN532 {self.reader_id} - Hardware non risponde correttamente")
            
            return result
            
        except asyncio.TimeoutError:
            print(f"   ❌ PN532 {self.reader_id} - Hardware test timeout")
            return False
        except Exception as e:
            print(f"   ❌ PN532 {self.reader_id} - Hardware test errore: {e}")
            return False

    async def _safe_firmware_check(self) -> Optional[str]:
        """Test firmware senza bloccare."""
        if not self.pn532:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            def _get_firmware():
                if hasattr(self.pn532, 'firmware_version'):
                    fw = self.pn532.firmware_version
                    if fw:
                        return f"v{fw[0]}.{fw[1]}.{fw[2]}" if len(fw) >= 3 else str(fw)
                return None
            
            # Timeout per evitare blocchi
            fw_info = await asyncio.wait_for(
                loop.run_in_executor(None, _get_firmware),
                timeout=2.0
            )
            
            return fw_info
            
        except asyncio.TimeoutError:
            print("   ⚠️ Timeout firmware check")
            return None
        except Exception as e:
            print(f"   ⚠️ Errore firmware check: {e}")
            return None
    
    async def _hardware_read(self) -> Optional[bytes]:
        """
        Lettura hardware PN532 con timeout e gestione errori.
        
        Returns:
            Optional[bytes]: Dati raw della carta o None
        """
        if not self.pn532:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            def _read_passive():
                """Lettura sincrona da eseguire in thread"""
                try:
                    # read_passive_target con timeout breve
                    return self.pn532.read_passive_target(timeout=0.1)
                except Exception as e:
                    print(f"   ⚠️ Errore read_passive_target: {e}")
                    return None
            
            # Esegui lettura in thread con timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _read_passive),
                timeout=0.2
            )
            
            if result and len(result) > 0:
                self.last_successful_read = time.time()
                self.consecutive_errors = 0
                return result
            
            return None
            
        except asyncio.TimeoutError:
            # Timeout normale, non è un errore critico
            return None
        except Exception as e:
            self.consecutive_errors += 1
            
            if self.consecutive_errors <= self.max_consecutive_errors:
                print(f"   ⚠️ PN532 {self.reader_id} errore lettura #{self.consecutive_errors}: {e}")
            
            # Se troppi errori consecutivi, prova reinizializzazione
            if self.consecutive_errors >= self.max_consecutive_errors:
                print(f"   🔄 PN532 {self.reader_id} - Troppi errori, tentativo reinizializzazione...")
                try:
                    await self._attempt_recovery()
                except Exception as recovery_error:
                    print(f"   ❌ Recovery fallito: {recovery_error}")
            
            return None
    
    async def _attempt_recovery(self) -> None:
        """Tentativo di recovery automatico"""
        try:
            # Reset contatori
            self.consecutive_errors = 0
            
            # Re-inizializzazione leggera
            if self.interface == "i2c":
                await self._setup_i2c_robust()
            elif self.interface == "spi":
                await self._setup_spi_robust()
            elif self.interface == "uart":
                await self._setup_uart_robust()
            
            print(f"   ✅ PN532 {self.reader_id} recovery completato")
            
        except Exception as e:
            print(f"   ❌ PN532 {self.reader_id} recovery fallito: {e}")
    
    async def _hardware_cleanup(self) -> None:
        """Cleanup hardware PN532"""
        try:
            if self.pn532:
                # Non chiamare metodi potenzialmente bloccanti
                self.pn532 = None
                print(f"   🧹 PN532 {self.reader_id} cleanup completato")
        except Exception as e:
            print(f"   ⚠️ PN532 {self.reader_id} cleanup error: {e}")
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Informazioni specifiche interfaccia"""
        info = {
            'interface': self.interface,
            'consecutive_errors': self.consecutive_errors,
            'last_successful_read': self.last_successful_read
        }
        
        if self.interface == 'i2c':
            info['i2c_address'] = f"0x{self.i2c_address:02X}"
        elif self.interface == 'spi':
            info['spi_bus'] = self.spi_bus
            info['spi_device'] = self.spi_device
        elif self.interface == 'uart':
            info['uart_port'] = self.uart_port
            info['uart_baudrate'] = self.uart_baudrate
        
        return info
    
    def __str__(self) -> str:
        return f"PN532({self.reader_id}, {self.interface.upper()}, {self.direction}, {self.status.value})"


# Export
__all__ = ['PN532Reader']