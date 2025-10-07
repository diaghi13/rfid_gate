#!/usr/bin/env python3
"""
🔍 Test Configurazioni UID PN532
===============================

Mostra come il PN532 può gestire diversi formati UID
"""

def demonstrate_uid_formats():
    """Dimostra i diversi formati UID supportati dal PN532"""
    
    print("🔢 FORMATI UID SUPPORTATI DAL PN532")
    print("=" * 50)
    
    # Esempi di UID reali dal PN532
    examples = [
        {
            'type': 'MIFARE Classic (4 byte)',
            'raw_bytes': [0x63, 0x2D, 0x39, 0x03],
            'hex_length': 8,
            'description': 'Carte RFID più comuni'
        },
        {
            'type': 'MIFARE Ultralight (7 byte)', 
            'raw_bytes': [0x04, 0xD5, 0xE7, 0x6A, 0x4F, 0x51, 0x80],
            'hex_length': 14,
            'description': 'Carte NFC, tag adesivi'
        },
        {
            'type': 'NTAG213/215/216 (7 byte)',
            'raw_bytes': [0x04, 0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0x6F],
            'hex_length': 14, 
            'description': 'Tag NFC programmabili'
        }
    ]
    
    print("📋 ESEMPI DI UID:")
    for example in examples:
        raw_hex = ''.join([f'{b:02X}' for b in example['raw_bytes']])
        print(f"\n🏷️ {example['type']}:")
        print(f"   Raw bytes: {example['raw_bytes']}")
        print(f"   Hex string: {raw_hex} ({len(raw_hex)} caratteri)")
        print(f"   Descrizione: {example['description']}")
    
    print("\n" + "=" * 50)
    print("🎯 CONFIGURAZIONI POSSIBILI")
    print("=" * 50)
    
    # Test con l'UID corrente
    current_uid = "632D3903"
    
    configs = [
        {
            'mode': 'remove_suffix',
            'chars_count': 2,
            'description': 'Rimuove ultimi 2 caratteri (attuale)',
            'result': current_uid[:-2] if len(current_uid) > 2 else current_uid
        },
        {
            'mode': 'remove_suffix', 
            'chars_count': 4,
            'description': 'Rimuove ultimi 4 caratteri (più corto)',
            'result': current_uid[:-4] if len(current_uid) > 4 else current_uid
        },
        {
            'mode': 'fixed_length',
            'target_length': 6,
            'description': 'Lunghezza fissa 6 caratteri',
            'result': current_uid[:6] if len(current_uid) > 6 else current_uid.ljust(6, '0')
        },
        {
            'mode': 'fixed_length',
            'target_length': 8,
            'description': 'Lunghezza fissa 8 caratteri (full UID)',
            'result': current_uid[:8] if len(current_uid) > 8 else current_uid.ljust(8, '0')
        },
        {
            'mode': 'raw',
            'description': 'UID completo senza modifiche',
            'result': current_uid
        }
    ]
    
    print(f"📊 Con UID esempio: {current_uid}")
    print("-" * 30)
    
    for config in configs:
        print(f"🔧 {config['mode']}: {config['result']}")
        print(f"   → {config['description']}")
        if 'chars_count' in config:
            print(f"   → chars_count: {config['chars_count']}")
        if 'target_length' in config:
            print(f"   → target_length: {config['target_length']}")
        print()
    
    print("💡 RACCOMANDAZIONI:")
    print("-" * 20)
    print("• Per massima compatibilità: fixed_length=6 o fixed_length=8")
    print("• Per carte miste (4/7 byte): remove_suffix con chars_count=2")  
    print("• Per UID completi: mode=raw")
    print("• Per debug: UID_DEBUG_MODE=True (mostra conversioni)")
    
    print(f"\n🔍 ANALISI ATTUALE:")
    print(f"   - Mode: remove_suffix, chars_count: 2")
    print(f"   - 632D3903 → 632D39 (4 byte → 6 caratteri)")
    print(f"   - Questo è normale per carte MIFARE Classic!")
    
    print(f"\n⚙️ PER CAMBIARE FORMATO, MODIFICA .env:")
    print("   UID_FORMAT_MODE=fixed_length")
    print("   UID_TARGET_LENGTH=8  # Per UID completo")
    print("   # oppure")
    print("   UID_FORMAT_MODE=raw  # Per nessuna modifica")


def show_current_config():
    """Mostra configurazione corrente"""
    try:
        import os
        import sys
        sys.path.append('.')
        
        from rfid_gate.config.settings import RFIDGateConfig
        
        config = RFIDGateConfig.from_env()
        
        print(f"\n🔧 CONFIGURAZIONE CORRENTE:")
        print(f"   UID_FORMAT_MODE: {config.system.uid_format_mode.value}")
        print(f"   UID_CHARS_COUNT: {config.system.uid_chars_count}")
        print(f"   UID_TARGET_LENGTH: {config.system.uid_target_length}")
        print(f"   UID_DEBUG_MODE: {config.system.uid_debug_mode}")
        
        # Simula formattazione con config attuale
        from rfid_gate.hardware.readers.base import BaseRFIDReader
        
        class TestReader(BaseRFIDReader):
            def get_reader_type(self): return "test"
            async def _hardware_init(self): return True
            async def _hardware_read(self): return None
            async def _hardware_cleanup(self): pass
        
        reader = TestReader("test")
        test_uid_bytes = bytes([0x63, 0x2D, 0x39, 0x03])
        
        formatted = reader.format_card_uid(
            test_uid_bytes,
            config.system.uid_format_mode.value,
            config.system.uid_chars_count,
            config.system.uid_target_length
        )
        
        print(f"\n🧪 TEST CON CONFIGURAZIONE ATTUALE:")
        print(f"   Raw UID: {test_uid_bytes.hex().upper()}")
        print(f"   Formatted: {formatted}")
        
    except Exception as e:
        print(f"⚠️ Errore caricamento config: {e}")


if __name__ == "__main__":
    demonstrate_uid_formats()
    show_current_config()