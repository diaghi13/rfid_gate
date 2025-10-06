#!/usr/bin/env python3
"""
🏭 RFID Reader Factory - Dynamic Reader Creation
===============================================

Factory pattern per creare lettori RFID dinamicamente.
Supporta configurazione type-safe e compatibilità completa.
"""

from typing import Optional, Dict, Any, Type, Union
from rfid_gate.hardware.readers.base import BaseRFIDReader
from rfid_gate.hardware.readers.mfrc522 import MFRC522Reader  
from rfid_gate.hardware.readers.pn532 import PN532Reader
from rfid_gate.config.settings import RFIDReaderConfig, ReaderType, PN532Interface


class ReaderFactory:
    """
    Factory per creare lettori RFID basato su configurazione.
    
    Supporta:
    - MFRC522 (GPIO standard)
    - PN532 (I2C, SPI, UART)
    - Registrazione lettori personalizzati
    - Configurazione type-safe
    """
    
    # Registry dei lettori disponibili
    _readers: Dict[str, Type[BaseRFIDReader]] = {
        'mfrc522': MFRC522Reader,
        'pn532': PN532Reader
    }
    
    @classmethod
    def register_reader(cls, reader_type: str, reader_class: Type[BaseRFIDReader]) -> None:
        """
        Registra un nuovo tipo di lettore.
        
        Args:
            reader_type: Nome del tipo lettore
            reader_class: Classe del lettore (deve ereditare da BaseRFIDReader)
        """
        if not issubclass(reader_class, BaseRFIDReader):
            raise ValueError(f"Reader class deve ereditare da BaseRFIDReader")
        
        cls._readers[reader_type.lower()] = reader_class
        print(f"📝 Registrato reader: {reader_type} -> {reader_class.__name__}")
    
    @classmethod
    def get_available_readers(cls) -> Dict[str, Type[BaseRFIDReader]]:
        """Restituisce tutti i lettori disponibili"""
        return cls._readers.copy()
    
    @classmethod
    def create_reader(cls, reader_config: RFIDReaderConfig, 
                     reader_id: str, direction: str = "in") -> Optional[BaseRFIDReader]:
        """
        Crea lettore basato su configurazione type-safe.
        
        Args:
            reader_config: Configurazione del lettore
            reader_id: ID univoco del lettore
            direction: Direzione ("in" o "out")
            
        Returns:
            Optional[BaseRFIDReader]: Istanza del lettore o None se errore
        """
        if not reader_config.enabled:
            print(f"⚠️ Reader {reader_id} disabilitato nella configurazione")
            return None
        
        reader_type = reader_config.reader_type.value.lower()
        
        if reader_type not in cls._readers:
            print(f"❌ Tipo lettore non supportato: {reader_type}")
            print(f"   Lettori disponibili: {list(cls._readers.keys())}")
            return None
        
        try:
            reader_class = cls._readers[reader_type]
            
            # Crea parametri specifici per tipo lettore
            if reader_type == 'mfrc522':
                kwargs = {
                    'rst_pin': reader_config.rst_pin,
                    'sda_pin': reader_config.sda_pin
                }
            elif reader_type == 'pn532':
                kwargs = {
                    'interface': reader_config.pn532_interface.value,
                    'i2c_address': reader_config.pn532_i2c_address,
                    'spi_bus': reader_config.pn532_spi_bus,
                    'spi_device': reader_config.pn532_spi_device,
                    'uart_port': reader_config.pn532_uart_port,
                    'uart_baudrate': reader_config.pn532_uart_baudrate
                }
            else:
                kwargs = {}
            
            # Crea istanza lettore
            reader = reader_class(
                reader_id=reader_id,
                direction=direction,
                **kwargs
            )
            
            print(f"✅ Creato reader: {reader}")
            return reader
            
        except Exception as e:
            print(f"❌ Errore creazione reader {reader_id}: {e}")
            return None
    
    @classmethod
    def create_reader_legacy(cls, reader_type: str, reader_id: str, 
                           direction: str = "in", **kwargs) -> Optional[BaseRFIDReader]:
        """
        Crea lettore con parametri legacy (compatibilità).
        
        Args:
            reader_type: Tipo lettore ("mfrc522", "pn532")
            reader_id: ID univoco del lettore
            direction: Direzione ("in" o "out")
            **kwargs: Parametri specifici del lettore
            
        Returns:
            Optional[BaseRFIDReader]: Istanza del lettore o None se errore
        """
        reader_type = reader_type.lower()
        
        if reader_type not in cls._readers:
            print(f"❌ Tipo lettore non supportato: {reader_type}")
            return None
        
        try:
            reader_class = cls._readers[reader_type]
            reader = reader_class(reader_id=reader_id, direction=direction, **kwargs)
            
            print(f"✅ Creato reader (legacy): {reader}")
            return reader
            
        except Exception as e:
            print(f"❌ Errore creazione reader legacy {reader_id}: {e}")
            return None
    
    @classmethod
    def create_dual_readers(cls, in_config: RFIDReaderConfig, 
                          out_config: RFIDReaderConfig) -> Dict[str, Optional[BaseRFIDReader]]:
        """
        Crea configurazione dual reader.
        
        Args:
            in_config: Configurazione lettore IN
            out_config: Configurazione lettore OUT
            
        Returns:
            Dict[str, Optional[BaseRFIDReader]]: Dizionario con lettori creati
        """
        readers = {}
        
        # Crea lettore IN
        if in_config.enabled:
            readers['in'] = cls.create_reader(in_config, "rfid_in", "in")
        else:
            readers['in'] = None
        
        # Crea lettore OUT
        if out_config.enabled:
            readers['out'] = cls.create_reader(out_config, "rfid_out", "out")
        else:
            readers['out'] = None
        
        # Verifica che almeno un lettore sia attivo
        active_count = sum(1 for reader in readers.values() if reader is not None)
        
        if active_count == 0:
            print("❌ Nessun lettore attivo nella configurazione dual reader")
        else:
            print(f"✅ Configurazione dual reader: {active_count} lettori attivi")
        
        return readers
    
    @classmethod
    def validate_reader_config(cls, reader_config: RFIDReaderConfig) -> list:
        """
        Valida configurazione lettore.
        
        Args:
            reader_config: Configurazione da validare
            
        Returns:
            list: Lista errori di validazione (vuota se OK)
        """
        errors = []
        
        if not reader_config.enabled:
            return errors  # Non validiamo lettori disabilitati
        
        reader_type = reader_config.reader_type.value.lower()
        
        # Verifica tipo supportato
        if reader_type not in cls._readers:
            errors.append(f"Tipo lettore non supportato: {reader_type}")
            return errors
        
        # Validazione specifica per tipo
        if reader_type == 'mfrc522':
            if not (1 <= reader_config.rst_pin <= 40):
                errors.append(f"RST pin fuori range: {reader_config.rst_pin}")
            if not (1 <= reader_config.sda_pin <= 40):
                errors.append(f"SDA pin fuori range: {reader_config.sda_pin}")
        
        elif reader_type == 'pn532':
            interface = reader_config.pn532_interface
            
            if interface == PN532Interface.I2C:
                if not (0x01 <= reader_config.pn532_i2c_address <= 0x7F):
                    errors.append(f"Indirizzo I2C non valido: 0x{reader_config.pn532_i2c_address:02X}")
            
            elif interface == PN532Interface.SPI:
                if reader_config.pn532_spi_bus < 0:
                    errors.append(f"SPI bus non valido: {reader_config.pn532_spi_bus}")
                if reader_config.pn532_spi_device < 0:
                    errors.append(f"SPI device non valido: {reader_config.pn532_spi_device}")
            
            elif interface == PN532Interface.UART:
                if not reader_config.pn532_uart_port:
                    errors.append("UART port richiesto per interfaccia UART")
                if reader_config.pn532_uart_baudrate <= 0:
                    errors.append(f"UART baudrate non valido: {reader_config.pn532_uart_baudrate}")
        
        return errors
    
    @classmethod
    def get_reader_info(cls, reader_type: str) -> Dict[str, Any]:
        """
        Informazioni sul tipo di lettore.
        
        Args:
            reader_type: Tipo lettore
            
        Returns:
            Dict[str, Any]: Informazioni del lettore
        """
        reader_type = reader_type.lower()
        
        if reader_type not in cls._readers:
            return {'error': f'Tipo lettore non supportato: {reader_type}'}
        
        reader_class = cls._readers[reader_type]
        
        info = {
            'type': reader_type,
            'class': reader_class.__name__,
            'module': reader_class.__module__,
            'supported': True
        }
        
        # Informazioni specifiche per tipo
        if reader_type == 'mfrc522':
            info.update({
                'interfaces': ['GPIO'],
                'description': 'Lettore MFRC522 con interfaccia GPIO/SPI',
                'pins_required': ['RST', 'SDA'],
                'typical_pins': {'rst': 22, 'sda': 8}
            })
        elif reader_type == 'pn532':
            info.update({
                'interfaces': ['I2C', 'SPI', 'UART'],
                'description': 'Lettore PN532 multi-interfaccia',
                'default_interface': 'I2C',
                'typical_addresses': {'i2c': '0x24', 'i2c_alt': '0x25'}
            })
        
        return info


# Convenience functions per compatibilità
def create_mfrc522_reader(reader_id: str, direction: str = "in", 
                         rst_pin: int = 22, sda_pin: int = 8) -> Optional[BaseRFIDReader]:
    """Crea lettore MFRC522 con parametri semplificati"""
    return ReaderFactory.create_reader_legacy(
        'mfrc522', reader_id, direction,
        rst_pin=rst_pin, sda_pin=sda_pin
    )


def create_pn532_reader(reader_id: str, direction: str = "in", 
                       interface: str = "i2c", **kwargs) -> Optional[BaseRFIDReader]:
    """Crea lettore PN532 con parametri semplificati"""
    return ReaderFactory.create_reader_legacy(
        'pn532', reader_id, direction,
        interface=interface, **kwargs
    )


# Export
__all__ = [
    'ReaderFactory',
    'create_mfrc522_reader',
    'create_pn532_reader'
]


# Test factory se eseguito direttamente
if __name__ == "__main__":
    print("🧪 Test ReaderFactory")
    print("=" * 40)
    
    # Info lettori disponibili
    print("Lettori disponibili:")
    for reader_type, reader_class in ReaderFactory.get_available_readers().items():
        info = ReaderFactory.get_reader_info(reader_type)
        print(f"  - {reader_type}: {info.get('description', 'N/A')}")
    
    # Test creazione lettori
    print("\nTest creazione lettori:")
    
    # MFRC522
    mfrc522 = create_mfrc522_reader("test_mfrc522", "in")
    if mfrc522:
        print(f"✅ MFRC522 creato: {mfrc522}")
    
    # PN532
    pn532 = create_pn532_reader("test_pn532", "out", "i2c", i2c_address=0x24)
    if pn532:
        print(f"✅ PN532 creato: {pn532}")
    
    print("\n🎯 Factory test completato!")