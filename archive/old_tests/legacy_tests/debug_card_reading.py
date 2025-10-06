#!/usr/bin/env python3
"""
Debug SPECIFICO per lettura card RFID - VERSIONE CORRETTA
Questo test identifica ESATTAMENTE perché le card non vengono lette
"""
import sys
import time

# Aggiungi src al path
sys.path.insert(0, 'src')

def debug_card_reading():
    """Debug molto dettagliato della lettura card"""
    print("🔍 DEBUG LETTURA CARD RFID")
    print("=" * 50)
    
    try:
        from config import Config
        from rfid_reader import RFIDReader
        
        # Prima di tutto, verifichiamo che tipo di libreria mfrc522 abbiamo
        print("🔧 Verifica libreria mfrc522...")
        try:
            from mfrc522 import SimpleMFRC522
            
            # Test che costruttore supporta
            print("📋 Test costruttore SimpleMFRC522:")
            try:
                # Prova con parametri
                test_reader = SimpleMFRC522(rst=22, cs=8)
                test_reader = None  # Cleanup
                print("   ✅ Costruttore con parametri: SUPPORTATO")
                constructor_supports_params = True
            except TypeError as e:
                print(f"   ❌ Costruttore con parametri: NON SUPPORTATO ({e})")
                constructor_supports_params = False
            
            # Prova costruttore base
            try:
                test_reader = SimpleMFRC522()
                test_reader = None  # Cleanup  
                print("   ✅ Costruttore base: OK")
                constructor_base_works = True
            except Exception as e:
                print(f"   ❌ Costruttore base: FALLITO ({e})")
                constructor_base_works = False
                
        except ImportError as e:
            print(f"❌ Errore import mfrc522: {e}")
            return
        
        if not constructor_base_works:
            print("❌ La libreria mfrc522 ha problemi di base")
            return
        
        # Crea lettore
        print(f"\n🔧 Creazione lettore RFID...")
        reader = RFIDReader("debug", Config.RFID_IN_RST_PIN, Config.RFID_IN_SDA_PIN)
        
        if not reader.initialize():
            print("❌ Inizializzazione fallita")
            return
        
        print("✅ Lettore inizializzato")
        print(f"📍 Pin: RST={reader.rst_pin}, CS={reader.cs_pin}")
        print(f"⏰ Debounce time: {reader.debounce_time}s")
        
        # Test lettura DIRETTA con libreria (SENZA parametri)
        print("\n🧪 TEST 1: Lettura diretta con mfrc522 (costruttore base)")
        print("Avvicina una card ADESSO...")
        
        # Usa costruttore SENZA parametri (come fa la maggior parte delle versioni)
        direct_reader = SimpleMFRC522()
        
        for i in range(10):
            try:
                print(f"   Tentativo {i+1}/10...")
                
                # Usa read_no_block per non bloccare
                if hasattr(direct_reader, 'read_no_block'):
                    card_id, card_data = direct_reader.read_no_block()
                else:
                    print("   ⚠️ read_no_block non disponibile, uso read() con timeout")
                    # Se non ha read_no_block, è una versione più vecchia
                    card_id, card_data = direct_reader.read()
                
                if card_id is not None:
                    print(f"   🎉 CARD TROVATA: ID={card_id}")
                    print(f"   📊 Dati: '{card_data}'")
                    print(f"   📊 UID hex: {hex(card_id)}")
                    break
                else:
                    print(f"   ⚪ Nessuna card (tentativo {i+1})")
                
            except Exception as e:
                error_msg = str(e).lower()
                if any(skip in error_msg for skip in ["no card", "timeout", "nothing"]):
                    print(f"   ⚪ Nessuna card (timeout/no card)")
                else:
                    print(f"   ❌ Errore: {e}")
            
            time.sleep(0.5)
        else:
            print("   ❌ Nessuna card rilevata con lettura diretta")
        
        # Test lettura con nostro RFIDReader
        print("\n🧪 TEST 2: Lettura con nostro RFIDReader")
        print("Avvicina di nuovo la card...")
        
        for i in range(10):
            try:
                print(f"   Tentativo {i+1}/10...")
                card_id, card_data = reader.read_card()
                
                if card_id is not None:
                    print(f"   🎉 CARD TROVATA con nostro reader!")
                    print(f"   📊 ID: {card_id}")
                    print(f"   📊 UID formattato: {reader.format_card_uid(card_id)}")
                    print(f"   📊 Dati: '{card_data}'")
                    break
                else:
                    print(f"   ⚪ Nessuna card (nostro reader)")
                
            except Exception as e:
                print(f"   ❌ Errore nostro reader: {e}")
            
            time.sleep(0.5)
        else:
            print("   ❌ Nessuna card rilevata con nostro reader")
        
        # Test SENZA debounce
        print("\n🧪 TEST 3: Lettura SENZA debounce")
        print("Avvicina di nuovo la card...")
        
        # Disabilita temporaneamente debounce
        original_debounce = reader.debounce_time
        reader.debounce_time = 0
        reader.last_card_id = None
        reader.last_read_time = 0
        
        for i in range(10):
            try:
                print(f"   Tentativo {i+1}/10 (no debounce)...")
                card_id, card_data = reader.read_card()
                
                if card_id is not None:
                    print(f"   🎉 CARD TROVATA senza debounce!")
                    print(f"   📊 ID: {card_id}")
                    break
                else:
                    print(f"   ⚪ Nessuna card")
                
            except Exception as e:
                print(f"   ❌ Errore: {e}")
            
            time.sleep(0.3)
        else:
            print("   ❌ Nessuna card anche senza debounce")
        
        # Ripristina debounce
        reader.debounce_time = original_debounce
        
        # Test con timing diversi
        print("\n🧪 TEST 4: Lettura con timing aggressivo")
        print("Tieni la card FERMA sul lettore...")
        
        for i in range(20):
            try:
                card_id, card_data = reader.read_card()
                if card_id is not None:
                    print(f"   🎉 CARD TROVATA al tentativo {i+1}!")
                    break
                time.sleep(0.1)  # Timing molto veloce
            except Exception as e:
                if "no card" not in str(e).lower():
                    print(f"   ❌ Errore: {e}")
        else:
            print("   ❌ Nessuna card anche con timing aggressivo")
        
        # Test di configurazione pin
        print("\n🧪 TEST 5: Verifica configurazione pin")
        try:
            # Verifica che i pin siano configurati correttamente
            if hasattr(reader.reader, 'READER'):
                hw_reader = reader.reader.READER
                print("   🔧 Verifica pin configurati:")
                
                if hasattr(hw_reader, 'RST'):
                    print(f"   📍 RST pin: {getattr(hw_reader, 'RST', 'Non impostato')}")
                if hasattr(hw_reader, 'CS'):
                    print(f"   📍 CS pin: {getattr(hw_reader, 'CS', 'Non impostato')}")
                if hasattr(hw_reader, 'SDA'):
                    print(f"   📍 SDA pin: {getattr(hw_reader, 'SDA', 'Non impostato')}")
                
                # Verifica che i pin siano quelli giusti
                expected_rst = Config.RFID_IN_RST_PIN
                expected_cs = Config.RFID_IN_SDA_PIN
                
                actual_rst = getattr(hw_reader, 'RST', None)
                actual_cs = getattr(hw_reader, 'CS', None) or getattr(hw_reader, 'SDA', None)
                
                print(f"   🎯 Pin attesi: RST={expected_rst}, CS={expected_cs}")
                print(f"   🎯 Pin attuali: RST={actual_rst}, CS={actual_cs}")
                
                if actual_rst == expected_rst and actual_cs == expected_cs:
                    print("   ✅ Pin configurati correttamente")
                else:
                    print("   ❌ Pin NON configurati correttamente!")
                    print("   💡 Questo spiega perché le card non vengono lette")
                    
            else:
                print("   ⚠️ Accesso ai pin non disponibile")
                
        except Exception as e:
            print(f"   ❌ Errore verifica pin: {e}")
        
        # Test con reader configurato manualmente
        print("\n🧪 TEST 6: Reader con configurazione manuale forzata")
        try:
            manual_reader = SimpleMFRC522()
            
            # Configura manualmente i pin
            if hasattr(manual_reader, 'READER'):
                hw_reader = manual_reader.READER
                hw_reader.RST = Config.RFID_IN_RST_PIN
                if hasattr(hw_reader, 'CS'):
                    hw_reader.CS = Config.RFID_IN_SDA_PIN
                if hasattr(hw_reader, 'SDA'):
                    hw_reader.SDA = Config.RFID_IN_SDA_PIN
                    
                print(f"   🔧 Pin configurati manualmente: RST={hw_reader.RST}, CS/SDA={Config.RFID_IN_SDA_PIN}")
                
                print("   📖 Test lettura con pin configurati manualmente...")
                for i in range(5):
                    try:
                        if hasattr(manual_reader, 'read_no_block'):
                            card_id, card_data = manual_reader.read_no_block()
                        else:
                            card_id, card_data = manual_reader.read()
                            
                        if card_id is not None:
                            print(f"   🎉 CARD TROVATA con config manuale!")
                            print(f"   📊 ID: {card_id}")
                            break
                        time.sleep(0.5)
                    except Exception as e:
                        if "no card" not in str(e).lower():
                            print(f"   ⚠️ Errore config manuale: {e}")
                else:
                    print("   ❌ Nessuna card con config manuale")
            
        except Exception as e:
            print(f"   ❌ Errore test config manuale: {e}")
        
        reader.cleanup()
        
        # Riepilogo
        print("\n📋 RIEPILOGO DEBUG:")
        print("Se NESSUN test ha rilevato card:")
        print("   1. ❌ Problema hardware/cablaggio")
        print("   2. ❌ Card non compatibile")  
        print("   3. ❌ Alimentazione insufficiente")
        print("   4. ❌ SPI non configurato correttamente")
        print()
        print("Se solo TEST 1 funziona:")
        print("   1. ❌ Problema di configurazione pin nel nostro codice")
        print("   2. ❌ Lock SPI interferisce")
        print()
        print("Se TEST 5 mostra pin non configurati:")
        print("   1. ❌ La libreria non supporta pin personalizzati")
        print("   2. ❌ Bisogna usare solo i pin di default")
        print()
        print("Se TEST 6 funziona:")
        print("   1. ✅ Il problema è come configuriamo i pin")
        print("   2. 🔧 Dobbiamo correggere RFIDReader")
        
    except Exception as e:
        print(f"❌ Errore generale debug: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 DEBUG SPECIFICO LETTURA CARD - VERSIONE CORRETTA")
    print("Questo test identifica ESATTAMENTE perché le card non vengono lette")
    print("=" * 60)
    
    debug_card_reading()
    
    print("\n💡 PROSSIMI PASSI in base ai risultati:")
    print("📝 Se nessun test funziona → Problema hardware")
    print("🔧 Se solo alcuni test funzionano → Problema software")
    print("⚡ Se tutto funziona qui ma non nel test reale → Problema di threading")
    print("🎯 Se pin non configurati → Dobbiamo correggere RFIDReader")

if __name__ == "__main__":
    main()