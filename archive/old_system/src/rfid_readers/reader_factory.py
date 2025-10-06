#!/usr/bin/env python3
"""
Factory per creare lettori RFID - Gestione robusta e switch automatico
"""
try:
    from .mfrc522_reader import MFRC522Reader
    from .pn532_reader import PN532Reader
except ImportError:
    # Fallback per ambiente di sviluppo (macOS, Windows)
    print("⚠️ Librerie hardware non disponibili, uso mock readers")
    from .mock_readers import MockMFRC522Reader as MFRC522Reader
    from .mock_readers import MockPN532Reader as PN532Reader

class RFIDReaderFactory:
    """Factory per creare lettori RFID con fallback automatico"""
    
    SUPPORTED_READERS = {
        'mfrc522': MFRC522Reader,
        'pn532': PN532Reader,
        'rc522': MFRC522Reader,  # Alias per compatibilità
    }
    
    @classmethod
    def create_reader(cls, reader_type, reader_id, **kwargs):
        """
        Crea un lettore del tipo specificato con fallback automatico
        
        Args:
            reader_type (str): Tipo di lettore ('mfrc522', 'pn532')
            reader_id (str): ID del lettore
            **kwargs: Parametri specifici per il lettore
        
        Returns:
            BaseRFIDReader: Istanza del lettore
        """
        reader_type = reader_type.lower()
        
        if reader_type not in cls.SUPPORTED_READERS:
            print(f"⚠️ Lettore non supportato: {reader_type}. Fallback a MFRC522.")
            reader_type = 'mfrc522'
        
        reader_class = cls.SUPPORTED_READERS[reader_type]
        
        try:
            return reader_class(reader_id=reader_id, **kwargs)
        except Exception as e:
            print(f"❌ Errore creazione lettore {reader_type}: {e}")
            # Fallback a MFRC522 in caso di errore
            if reader_type != 'mfrc522':
                print("🔄 Fallback automatico a MFRC522...")
                return MFRC522Reader(reader_id=reader_id, **kwargs)
            raise
    
    @classmethod
    def get_supported_readers(cls):
        """Restituisce la lista dei lettori supportati"""
        return list(cls.SUPPORTED_READERS.keys())
    
    @classmethod
    def create_from_config(cls, reader_id, config_prefix="RFID_IN"):
        """
        Crea un lettore dalla configurazione con fallback robusto
        
        Args:
            reader_id (str): ID del lettore
            config_prefix (str): Prefisso della configurazione (RFID_IN, RFID_OUT)
        
        Returns:
            BaseRFIDReader: Istanza del lettore
        """
        from config import Config
        
        # Determina il tipo di lettore dalla config
        reader_type_attr = f"{config_prefix}_READER_TYPE"
        reader_type = getattr(Config, reader_type_attr, 'mfrc522')
        
        print(f"🔧 Creazione lettore {reader_id}: tipo {reader_type.upper()}")
        
        # Parametri comuni
        kwargs = {
            'debounce_time': Config.RFID_DEBOUNCE_TIME
        }
        
        # Parametri specifici per tipo
        if reader_type.lower() in ['mfrc522', 'rc522']:
            rst_attr = f"{config_prefix}_RST_PIN"
            sda_attr = f"{config_prefix}_SDA_PIN"
            
            kwargs.update({
                'rst_pin': getattr(Config, rst_attr, Config.RFID_IN_RST_PIN),
                'sda_pin': getattr(Config, sda_attr, Config.RFID_IN_SDA_PIN)
            })
            
            print(f"   📍 MFRC522 - RST:{kwargs['rst_pin']}, SDA:{kwargs['sda_pin']}")
            
        elif reader_type.lower() == 'pn532':
            interface_attr = f"{config_prefix}_PN532_INTERFACE"
            interface = getattr(Config, interface_attr, 'i2c')
            
            kwargs['interface'] = interface
            
            if interface == 'i2c':
                addr_attr = f"{config_prefix}_PN532_I2C_ADDRESS"
                kwargs['i2c_address'] = getattr(Config, addr_attr, 0x24)
                print(f"   📍 PN532 I2C - Address: 0x{kwargs['i2c_address']:02X}")
                
            elif interface == 'spi':
                bus_attr = f"{config_prefix}_PN532_SPI_BUS"
                dev_attr = f"{config_prefix}_PN532_SPI_DEVICE"
                kwargs['spi_bus'] = getattr(Config, bus_attr, 0)
                kwargs['spi_device'] = getattr(Config, dev_attr, 0)
                print(f"   📍 PN532 SPI - Bus:{kwargs['spi_bus']}, Device:{kwargs['spi_device']}")
                
            elif interface == 'uart':
                port_attr = f"{config_prefix}_PN532_UART_PORT"
                baud_attr = f"{config_prefix}_PN532_UART_BAUDRATE"
                kwargs['uart_port'] = getattr(Config, port_attr, '/dev/serial0')
                kwargs['uart_baudrate'] = getattr(Config, baud_attr, 115200)
                print(f"   📍 PN532 UART - Port:{kwargs['uart_port']}, Baud:{kwargs['uart_baudrate']}")
        
        return cls.create_reader(reader_type, reader_id, **kwargs)
    
    @classmethod
    def auto_detect_reader(cls, reader_id, preferred_type="pn532"):
        """
        Auto-rilevamento lettore con preferenza per tipo specificato
        
        Args:
            reader_id (str): ID del lettore
            preferred_type (str): Tipo preferito da testare per primo
        
        Returns:
            BaseRFIDReader: Lettore funzionante o None
        """
        print(f"🔍 Auto-rilevamento lettore per {reader_id}...")
        
        # Testa prima il tipo preferito
        test_order = [preferred_type] + [t for t in cls.SUPPORTED_READERS.keys() if t != preferred_type]
        
        for reader_type in test_order:
            try:
                print(f"   🧪 Test {reader_type.upper()}...")
                
                # Parametri di default per test
                if reader_type.lower() in ['mfrc522', 'rc522']:
                    kwargs = {'rst_pin': 22, 'sda_pin': 8}
                elif reader_type.lower() == 'pn532':
                    kwargs = {'interface': 'i2c', 'i2c_address': 0x24}
                else:
                    kwargs = {}
                
                reader = cls.create_reader(reader_type, f"test_{reader_id}", **kwargs)
                
                if reader.initialize():
                    if reader.test_connection():
                        print(f"   ✅ {reader_type.upper()} rilevato e funzionante!")
                        reader.cleanup()
                        return reader_type
                    reader.cleanup()
                
            except Exception as e:
                print(f"   ❌ {reader_type.upper()} non disponibile: {e}")
                continue
        
        print(f"   ⚠️ Nessun lettore RFID rilevato per {reader_id}")
        return None