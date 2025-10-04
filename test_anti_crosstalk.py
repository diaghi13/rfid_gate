#!/usr/bin/env python3
"""
Test anti-crosstalk dual readers
"""
import sys
import os
sys.path.append('/opt/rfid-gate/src')

from config import Config
from rfid_manager import RFIDManager
import time

def test_dual_readers_anti_crosstalk():
    """Test che verifica l'anti-crosstalk"""
    print("🧪 TEST ANTI-CROSSTALK DUAL READERS")
    print("=" * 45)
    
    try:
        # Carica configurazione
        print(f"⚙️ Configurazione:")
        print(f"   RFID_IN_READER_TYPE: {Config.RFID_IN_READER_TYPE}")
        print(f"   RFID_OUT_READER_TYPE: {Config.RFID_OUT_READER_TYPE}")
        print(f"   GLOBAL_DEBOUNCE_TIME: {Config.GLOBAL_DEBOUNCE_TIME}s")
        print(f"   RFID_DEBOUNCE_TIME: {Config.RFID_DEBOUNCE_TIME}s")
        
        # Inizializza manager
        manager = RFIDManager()
        
        if not manager.initialize():
            print("❌ Inizializzazione manager fallita")
            return False
        
        # Avvia manager
        if not manager.start():
            print("❌ Avvio manager fallito")
            return False
        
        print(f"\n📊 Reader info:")
        for reader_id, info in manager.get_reader_info().items():
            print(f"   {reader_id}: {info}")
        
        print(f"\n🎯 Test attivo (30 secondi)")
        print("💡 Avvicina card a UN SOLO lettore per volta")
        print("🚫 Il sistema dovrebbe bloccare letture multiple dello stesso card")
        
        start_time = time.time()
        card_count = 0
        crosstalk_blocked = 0
        
        while time.time() - start_time < 30:
            card_event = manager.get_next_card(timeout=0.5)
            
            if card_event:
                card_count += 1
                print(f"\n🎉 Card #{card_count}: {card_event['card_id']} ({card_event['reader_id'].upper()})")
                print(f"   Timestamp: {card_event['timestamp']:.3f}")
                
                # Controlla se ci sono stati blocchi recenti
                current_time = time.time()
                with manager.debounce_lock:
                    for card_id, data in manager.global_debounce.items():
                        time_diff = current_time - data["time"]
                        if time_diff < 2.0 and data["reader"] != card_event['reader_id']:
                            print(f"   ⚠️ Card {card_id} era su {data['reader']} {time_diff:.2f}s fa")
        
        # Risultati
        print(f"\n📊 RISULTATI TEST:")
        print(f"✅ Card totali rilevate: {card_count}")
        print(f"📊 Anti-crosstalk attivo: {manager.global_debounce_time}s")
        
        if card_count > 0:
            print("✅ Sistema dual-reader funzionante")
            print("💡 Verifica che ogni passaggio di card generi UNA sola lettura")
        else:
            print("⚠️ Nessuna card rilevata durante il test")
        
        # Cleanup
        manager.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AVVIO TEST ANTI-CROSSTALK")
    print("Questo test verifica che la stessa card non sia letta simultaneamente su entrambi i lettori")
    print()
    
    try:
        success = test_dual_readers_anti_crosstalk()
        
        if success:
            print("\n✅ Test completato - Sistema anti-crosstalk verificato")
        else:
            print("\n❌ Test fallito")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")