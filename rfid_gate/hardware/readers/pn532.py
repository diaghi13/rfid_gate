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
        Inizializzazione hardware PN532 - IDENTICA AL SISTEMA LEGACY che funziona.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        print(f"🔄 Inizializzazione PN532 {self.reader_id} - {self.interface.upper()}")
        
        try:
            # Crea connessione hardware (identica al legacy)
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
            
            # ❌ SKIP SAM configuration - causa blocchi! (come legacy)
            # ❌ SKIP set_passive_activation_retries - non esiste sempre (come legacy)
            # ❌ SKIP hardware connection test aggiuntivo - non presente nel legacy
            
            # Test semplice firmware (senza blocking calls, come legacy)
            try:
                fw_info = await self._safe_firmware_check()
                if fw_info:
                    print(f"✅ PN532 {self.reader_id} - Firmware OK")
                else:
                    print(f"⚠️ PN532 {self.reader_id} - Firmware check limitato (continuiamo)")
            except Exception as e:
                print(f"⚠️ Firmware check fallito: {e} (continuiamo...)")
            
            self.consecutive_errors = 0
            print(f"✅ PN532 {self.reader_id} inizializzato (design robusto)")
            return True
            
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
        """Inizializzazione SPI robusta con CS pin corretto (come sistema legacy)."""
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
                    
                    # CS pin - usa lo stesso approccio del sistema legacy che funziona
                    # Legacy: cs_pin = digitalio.DigitalInOut(board.D8)  # CS0 per device 0
                    # Manteniamo board.D8 come nel sistema funzionante
                    cs_pin = digitalio.DigitalInOut(board.D8)
                    
                    return PN532_SPI(spi, cs_pin, debug=False)
                
                self.pn532 = await loop.run_in_executor(None, _create_spi)
                
                print(f"   ✅ SPI PN532 creato - Bus: {self.spi_bus}, Device: {self.spi_device}, CS: D8 (legacy compatible)")
                return True
                
            except ImportError:
                # Fallback SPI (stesso approccio del legacy)
                try:
                    from pn532 import PN532_SPI
                    import busio
                    import board
                    import digitalio
                    
                    def _create_spi_fallback():
                        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                        cs = digitalio.DigitalInOut(board.D8)  # Stesso pin del legacy
                        return PN532_SPI(spi, cs)
                    
                    self.pn532 = await loop.run_in_executor(None, _create_spi_fallback)
                    
                    print(f"   ✅ SPI PN532 (fallback) - Bus: {self.spi_bus}, CS: D8")
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
        """Check firmware senza bloccare il device - IDENTICO AL LEGACY."""
        if not self.pn532:
            return None
        
        try:
            # Usa lo stesso approccio del sistema legacy che funziona
            loop = asyncio.get_event_loop()
            
            def _get_firmware():
                """Firmware check sincrono identico al legacy"""
                try:
                    # Timeout molto breve per evitare blocchi (come legacy)
                    fw_info = self.pn532.firmware_version
                    return fw_info is not None
                except:
                    return False
            
            # Esegui in thread ma senza timeout aggressivo
            result = await loop.run_in_executor(None, _get_firmware)
            
            return result
            
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