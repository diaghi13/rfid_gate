#!/usr/bin/env python3
"""
Test simulazione lettura PN532 con UID formattato
"""
import sys
import os

# Aggiungi il percorso src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 SIMULAZIONE LETTURA PN532 CON FORMATTAZIONE")
print("=" * 50)

try:
    # Simula la lettura di una carta PN532
    mock_uid_bytes = bytes([0x63, 0x2D, 0x39, 0x03])  # Simula UID letto da PN532
    
    print(f"📡 UID Raw (bytes): {mock_uid_bytes}")
    print(f"📡 UID Raw (hex): {mock_uid_bytes.hex().upper()}")
    
    # Converte in intero come farebbe il PN532Reader
    card_id = int.from_bytes(mock_uid_bytes, byteorder='big')
    print(f"📊 card_id (int): {card_id}")
    print(f"📊 card_id (hex): 0x{card_id:X}")
    
    # Simula formattazione come nel config
    uid_hex = ''.join([f'{b:02X}' for b in mock_uid_bytes])
    print(f"🔧 uid_hex: {uid_hex}")
    
    # Simula configurazione
    class MockConfig:
        UID_FORMAT_MODE = 'remove_suffix'
        UID_CHARS_COUNT = 2
        UID_TARGET_LENGTH = 8
        UID_DEBUG_MODE = True
    
    # Applica formattazione
    if MockConfig.UID_FORMAT_MODE == 'remove_suffix' and len(uid_hex) > MockConfig.UID_CHARS_COUNT:
        formatted_uid = uid_hex[:-MockConfig.UID_CHARS_COUNT]
    else:
        formatted_uid = uid_hex.zfill(8)
    
    print(f"✨ UID Formattato: {formatted_uid}")
    
    # Simula output completo
    print(f"\n📇 OUTPUT ATTESO:")
    print(f"📇 PN532 - Carta: {formatted_uid} (PN532-4byte)")
    
    print(f"\n🔧 DEBUG INFO:")
    print(f"🔧 PN532 UID: raw={uid_hex}, formatted={formatted_uid}, mode={MockConfig.UID_FORMAT_MODE}")
    
    print(f"\n✅ TUPLA RITORNATA: ({card_id}, '')")
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 CONFRONTO:")
print("❌ PRIMA: in - Carta: ['0X63', '0X2D', '0X39', '0X03 (PN532-4byte)")
print("✅ ORA:   PN532 - Carta: 632D39 (PN532-4byte)")
print("          🔧 PN532 UID: raw=632D3903, formatted=632D39, mode=remove_suffix")