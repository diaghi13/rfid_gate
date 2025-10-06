#!/usr/bin/env python3
"""
Test specifico per il sistema doppio RFID
"""
import sys
import os
import time
import threading

# Aggiungi src al path
sys.path.insert(0, 'src')

from config import Config
from rfid_manager import RFIDManager
from rfid_reader import RFIDReader

def test_rfid_config():
    """Testa la configurazione RFID"""
    print("🔧 TEST CONFIGURAZIONE RFID")
    print("=" * 50)
    
    print(f"Modalità bidirezionale: {Config.BIDIRECTIONAL_MODE}")
    print(f"RFID IN abilitato: {Config.RFID_IN_ENABLE}")
    print(f"RFID OUT abilitato: {Config.RFID_OUT_ENABLE}")
    
    if Config.RFID_IN_ENABLE:
        print(f"RFID IN - RST: {Config.RFID_IN_RST_PIN}, SDA: {Config.RFID_IN_SDA_PIN}")
    
    if Config.RFID_OUT_ENABLE:
        print(f"RFID OUT - RST: {Config.RFID_OUT_RST_PIN}, SDA: {Config.RFID_OUT_SDA_PIN}")
    
    # Verifica pin conflict
    errors = []
    
    if Config.RFID_IN_ENABLE and Config.RFID_OUT_ENABLE:
        if Config.RFID_IN_SDA_PIN == Config.RFID_OUT_SDA_PIN:
            errors.append(f"CONFLITTO SDA: IN e OUT usano entrambi pin {Config.RFID_IN_SDA_PIN}")
        
        if Config.RFID_IN_RST_PIN == Config.RFID_OUT_RST_PIN:
            errors.append(f"CONFLITTO RST: IN e OUT usano entrambi pin {Config.RFID_IN_RST_PIN}")
    
    if errors:
        print("\n❌ ERRORI RILEVATI:")
        for error in errors:
            print(f"   - {error}")
        print("\n💡 SOLUZIONE:")
        print("   Modifica .env con pin diversi, esempio:")
        print("   RFID_IN_RST_PIN=22")
        print("   RFID_IN_SDA_PIN=8")
        print("   RFID_OUT_RST_PIN=25") 
        print("   RFID_OUT_SDA_PIN=7")
        return False
    else:
        print("\n✅ Configurazione pin OK")
        return True

def test_individual_readers():
    """Testa lettori RFID individualmente"""
    print("\n🔍 TEST LETTORI INDIVIDUALI")
    print("=" * 50)
    
    readers_to_test = []
    
    if Config.RFID_IN_ENABLE:
        readers_to_test.append(("in", Config.RFID_IN_RST_PIN, Config.RFID_IN_SDA_PIN))
    
    if Config.RFID_OUT_ENABLE:
        readers_to_test.append(("out", Config.RFID_OUT_RST_PIN, Config.RFID_OUT_SDA_PIN))
    
    success = True
    
    for reader_id, rst_pin, sda_pin in readers_to_test:
        print(f"\n🧪 Test lettore {reader_id.upper()} (RST:{rst_pin}, SDA:{sda_pin})")
        
        try:
            reader = RFIDReader(reader_id, rst_pin, sda_pin)
            
            if reader.initialize():
                print(f"✅ Inizializzazione {reader_id}: OK")
                
                if reader.test_connection():
                    print(f"✅ Test connessione {reader_id}: OK")
                else:
                    print(f"❌ Test connessione {reader_id}: FALLITO")
                    success = False
            else:
                print(f"❌ Inizializzazione {reader_id}: FALLITA")
                success = False
            
            reader.cleanup()
            
        except Exception as e:
            print(f"❌ Errore test {reader_id}: {e}")
            success = False
        
        # Pausa tra test
        time.sleep(0.5)
    
    return success

def test_rfid_manager():
    """Testa il manager RFID completo"""
    print("\n📱 TEST RFID MANAGER")
    print("=" * 50)
    
    try:
        manager = RFIDManager()
        
        # Test inizializzazione
        if not manager.initialize():
            print("❌ Inizializzazione manager fallita")
            return False
        
        print("✅ Manager inizializzato")
        
        # Test status
        status = manager.get_reader_status()
        print(f"📊 Status: {status['active_readers']} lettori attivi")
        
        for direction, reader_status in status['readers'].items():
            print(f"   {direction.upper()}: RST={reader_status['rst_pin']}, SDA={reader_status['sda_pin']}")
        
        # Test tutti i lettori
        if manager.test_all_readers():
            print("✅ Tutti i lettori OK")
        else:
            print("❌ Alcuni lettori hanno problemi")
            return False
        
        # Test reading threads
        print("\n🚀 Test thread di lettura...")
        
        if manager.start_reading():
            print("✅ Thread avviati")
            
            # Monitora per qualche secondo
            print("⏳ Monitoraggio per 10 secondi... (avvicina una card)")
            
            cards_detected = 0
            start_time = time.time()
            
            while time.time() - start_time < 10:
                card_info = manager.get_next_card(timeout=1)
                
                if card_info:
                    cards_detected += 1
                    print(f"🎉 Card #{cards_detected}: {card_info['uid_formatted']} "
                          f"su lettore {card_info['direction'].upper()}")
                
                if cards_detected >= 3:  # Limite per test
                    break
            
            manager.stop_reading()
            print(f"📊 Test completato: {cards_detected} card rilevate")
        
        else:
            print("❌ Errore avvio thread")
            return False
        
        manager.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Errore test manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_reading():
    """Testa lettura concorrente su entrambi i lettori"""
    print("\n🔄 TEST LETTURA CONCORRENTE")
    print("=" * 50)
    
    if not (Config.RFID_IN_ENABLE and Config.RFID_OUT_ENABLE):
        print("⚠️ Test richiede entrambi i lettori abilitati")
        return True
    
    try:
        manager = RFIDManager()
        
        if not manager.initialize():
            print("❌ Inizializzazione fallita")
            return False
        
        if not manager.start_reading():
            print("❌ Avvio lettura fallito")
            return False
        
        print("🎯 Test concorrenza attivo!")
        print("💡 Prova ad avvicinare card a entrambi i lettori simultaneamente")
        print("⏳ Monitoraggio per 15 secondi...")
        
        cards_in = 0
        cards_out = 0
        start_time = time.time()
        
        while time.time() - start_time < 15:
            card_info = manager.get_next_card(timeout=0.5)
            
            if card_info:
                direction = card_info['direction']
                uid = card_info['uid_formatted']
                
                if direction == 'in':
                    cards_in += 1
                    print(f"🔵 IN  #{cards_in}: {uid}")
                elif direction == 'out':
                    cards_out += 1
                    print(f"🔴 OUT #{cards_out}: {uid}")
        
        manager.stop_reading()
        manager.cleanup()
        
        print(f"\n📊 RISULTATI CONCORRENZA:")
        print(f"   🔵 Lettore IN:  {cards_in} card")
        print(f"   🔴 Lettore OUT: {cards_out} card")
        print(f"   📱 Totale: {cards_in + cards_out} card")
        
        if cards_in > 0 and cards_out > 0:
            print("✅ Test concorrenza: SUCCESSO - Entrambi i lettori funzionano")
        elif cards_in > 0 or cards_out > 0:
            print("⚠️ Test concorrenza: PARZIALE - Solo un lettore ha rilevato card")
        else:
            print("❌ Test concorrenza: FALLITO - Nessuna card rilevata")
        
        return cards_in > 0 or cards_out > 0
        
    except Exception as e:
        print(f"❌ Errore test concorrenza: {e}")
        return False

def test_debounce_system():
    """Testa il sistema di debounce"""
    print("\n⏱️ TEST SISTEMA DEBOUNCE")
    print("=" * 50)
    
    try:
        manager = RFIDManager()
        
        if not manager.initialize():
            return False
        
        if not manager.start_reading():
            return False
        
        print(f"🔧 Debounce configurato: {Config.RFID_DEBOUNCE_TIME}s")
        print("💡 Tieni una card vicino al lettore per testare il debounce")
        print("⏳ Test per 10 secondi...")
        
        detected_cards = []
        start_time = time.time()
        
        while time.time() - start_time < 10:
            card_info = manager.get_next_card(timeout=0.5)
            
            if card_info:
                timestamp = time.time()
                detected_cards.append({
                    'uid': card_info['uid_formatted'],
                    'direction': card_info['direction'],
                    'timestamp': timestamp
                })
                
                print(f"📱 Card: {card_info['uid_formatted']} su {card_info['direction'].upper()}")
        
        manager.stop_reading()
        manager.cleanup()
        
        # Analizza debounce
        if len(detected_cards) > 1:
            print(f"\n📊 ANALISI DEBOUNCE:")
            print(f"   Totale rilevazioni: {len(detected_cards)}")
            
            # Raggruppa per UID
            by_uid = {}
            for card in detected_cards:
                uid = card['uid']
                if uid not in by_uid:
                    by_uid[uid] = []
                by_uid[uid].append(card)
            
            for uid, readings in by_uid.items():
                print(f"   Card {uid}: {len(readings)} letture")
                
                if len(readings) > 1:
                    intervals = []
                    for i in range(1, len(readings)):
                        interval = readings[i]['timestamp'] - readings[i-1]['timestamp']
                        intervals.append(interval)
                    
                    min_interval = min(intervals)
                    print(f"      Intervallo minimo: {min_interval:.2f}s")
                    
                    if min_interval < Config.RFID_DEBOUNCE_TIME:
                        print(f"      ⚠️ Debounce inefficace (< {Config.RFID_DEBOUNCE_TIME}s)")
                    else:
                        print(f"      ✅ Debounce funzionante")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test debounce: {e}")
        return False

def print_troubleshooting_guide():
    """Stampa guida risoluzione problemi"""
    print("\n🔧 GUIDA RISOLUZIONE PROBLEMI DOPPIO RFID")
    print("=" * 60)
    
    print("❌ PROBLEMA: Nessun lettore funziona")
    print("   🔍 Verifica:")
    print("   • SPI abilitato: sudo raspi-config > Interfacing > SPI > Enable")
    print("   • Cablaggio corretto (VCC=3.3V, GND=GND)")
    print("   • Moduli RFID funzionanti")
    
    print("\n❌ PROBLEMA: Solo un lettore funziona")
    print("   🔍 Verifica:")
    print("   • Pin SDA diversi per IN e OUT")
    print("   • Pin RST diversi per IN e OUT")
    print("   • Alimentazione sufficiente per entrambi i moduli")
    print("   • Cavi non danneggiati")
    
    print("\n❌ PROBLEMA: Letture instabili/duplicate")
    print("   🔍 Verifica:")
    print("   • RFID_DEBOUNCE_TIME >= 2.0")
    print("   • Distanza tra moduli >= 10cm")
    print("   • Alimentazione stabile")
    print("   • Cavi corti e schermati")
    
    print("\n✅ CONFIGURAZIONE RACCOMANDATA:")
    print("   BIDIRECTIONAL_MODE=True")
    print("   ENABLE_IN_READER=True")
    print("   ENABLE_OUT_READER=True")
    print("   RFID_IN_RST_PIN=22")
    print("   RFID_IN_SDA_PIN=8")
    print("   RFID_OUT_RST_PIN=25")
    print("   RFID_OUT_SDA_PIN=7")
    print("   RFID_DEBOUNCE_TIME=2.0")
    
    print("\n🔌 CABLAGGIO RACCOMANDATO:")
    print("   MODULO IN:   RST→22, SDA→8,  SCK→11, MOSI→10, MISO→9,  VCC→3.3V, GND→GND")
    print("   MODULO OUT:  RST→25, SDA→7,  SCK→11, MOSI→10, MISO→9,  VCC→3.3V, GND→GND")
    print("   Nota: SCK, MOSI, MISO sono condivisi (bus SPI)")

def main():
    """Funzione principale"""
    if os.geteuid() != 0:
        print("❌ Eseguire con sudo")
        print("💡 sudo python3 test_double_rfid.py")
        sys.exit(1)
    
    print("🧪 TEST SISTEMA DOPPIO RFID")
    print("=" * 60)
    print("Questo script testa la configurazione e funzionamento")
    print("del sistema doppio RFID per tornelli bidirezionali.")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Configurazione
    print("\n" + "="*60)
    result1 = test_rfid_config()
    test_results.append(("Configurazione Pin", result1))
    
    if not result1:
        print_troubleshooting_guide()
        return
    
    # Test 2: Lettori individuali
    print("\n" + "="*60)
    result2 = test_individual_readers()
    test_results.append(("Lettori Individuali", result2))
    
    # Test 3: Manager RFID
    print("\n" + "="*60)
    result3 = test_rfid_manager()
    test_results.append(("RFID Manager", result3))
    
    # Test 4: Lettura concorrente (solo se entrambi abilitati)
    if Config.RFID_IN_ENABLE and Config.RFID_OUT_ENABLE:
        print("\n" + "="*60)
        result4 = test_concurrent_reading()
        test_results.append(("Lettura Concorrente", result4))
    
    # Test 5: Debounce
    print("\n" + "="*60)
    result5 = test_debounce_system()
    test_results.append(("Sistema Debounce", result5))
    
    # Riepilogo finale
    print("\n" + "="*60)
    print("📊 RIEPILOGO RISULTATI TEST")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:20s}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 TUTTI I TEST SUPERATI!")
        print("✅ Sistema doppio RFID configurato correttamente")
        print("🚀 Il sistema è pronto per l'uso")
    else:
        print("❌ ALCUNI TEST FALLITI")
        print("🔧 Controlla la configurazione e il cablaggio")
        print_troubleshooting_guide()
    
    print("\n💡 Per maggiori informazioni, consulta la documentazione")
    print("   o esegui: sudo systemctl status rfid-gate")

if __name__ == "__main__":
    main()