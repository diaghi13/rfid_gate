#!/usr/bin/env python3
"""
Analisi COMPLETA della libreria mfrc522 installata
Identifica la struttura REALE della libreria
"""
import sys
import time

def analyze_mfrc522_library():
    """Analizza in dettaglio la libreria mfrc522 installata"""
    print("🔍 ANALISI COMPLETA LIBRERIA MFRC522")
    print("=" * 60)
    
    try:
        # Aggiungi src al path
        sys.path.insert(0, 'src')
        
        from config import Config
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
        
        print("✅ Import riuscito")
        
        # Cleanup GPIO
        try:
            GPIO.cleanup()
            time.sleep(0.5)
        except:
            pass
        
        # Configura GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO configurato")
        
        # Crea reader
        print("\n🔧 CREAZIONE READER...")
        reader = SimpleMFRC522()
        print("✅ Reader creato")
        
        # ANALISI 1: Struttura del reader
        print(f"\n📋 ANALISI 1: STRUTTURA READER")
        print(f"   Tipo reader: {type(reader)}")
        print(f"   Attributi reader:")
        
        reader_attrs = [attr for attr in dir(reader) if not attr.startswith('_')]
        for attr in reader_attrs:
            try:
                value = getattr(reader, attr)
                attr_type = type(value).__name__
                print(f"     {attr}: {attr_type}")
            except:
                print(f"     {attr}: <inaccessibile>")
        
        # ANALISI 2: Reader interno (se esiste)
        print(f"\n📋 ANALISI 2: READER INTERNO")
        if hasattr(reader, 'READER'):
            hw_reader = reader.READER
            print(f"   Tipo READER interno: {type(hw_reader)}")
            print(f"   Attributi READER interno:")
            
            hw_attrs = [attr for attr in dir(hw_reader) if not attr.startswith('_')]
            for attr in hw_attrs:
                try:
                    value = getattr(hw_reader, attr)
                    attr_type = type(value).__name__
                    if attr_type in ['int', 'str', 'bool']:
                        print(f"     {attr}: {value} ({attr_type})")
                    else:
                        print(f"     {attr}: {attr_type}")
                except:
                    print(f"     {attr}: <inaccessibile>")
        else:
            print("   ❌ READER interno non trovato")
        
        # ANALISI 3: Metodi disponibili
        print(f"\n📋 ANALISI 3: METODI DISPONIBILI")
        methods = [attr for attr in dir(reader) if callable(getattr(reader, attr)) and not attr.startswith('_')]
        for method in methods:
            print(f"   {method}()")
        
        # ANALISI 4: Test configurazione pin (metodi diversi)
        print(f"\n📋 ANALISI 4: TEST CONFIGURAZIONE PIN")
        
        expected_rst = Config.RFID_IN_RST_PIN
        expected_cs = Config.RFID_IN_SDA_PIN
        
        print(f"   Pin da configurare: RST={expected_rst}, CS={expected_cs}")
        
        # Metodo 1: READER.RST/CS
        if hasattr(reader, 'READER'):
            hw_reader = reader.READER
            print(f"\n   🧪 METODO 1: hw_reader.RST/CS")
            
            try:
                # Prova RST
                if hasattr(hw_reader, 'RST'):
                    old_rst = getattr(hw_reader, 'RST', 'Non trovato')
                    hw_reader.RST = expected_rst
                    new_rst = getattr(hw_reader, 'RST', 'Errore')
                    print(f"     RST: {old_rst} → {new_rst}")
                else:
                    print(f"     RST: Attributo non esistente")
                
                # Prova CS
                if hasattr(hw_reader, 'CS'):
                    old_cs = getattr(hw_reader, 'CS', 'Non trovato')
                    hw_reader.CS = expected_cs
                    new_cs = getattr(hw_reader, 'CS', 'Errore')
                    print(f"     CS: {old_cs} → {new_cs}")
                else:
                    print(f"     CS: Attributo non esistente")
                
                # Prova SDA
                if hasattr(hw_reader, 'SDA'):
                    old_sda = getattr(hw_reader, 'SDA', 'Non trovato')
                    hw_reader.SDA = expected_cs
                    new_sda = getattr(hw_reader, 'SDA', 'Errore')
                    print(f"     SDA: {old_sda} → {new_sda}")
                else:
                    print(f"     SDA: Attributo non esistente")
                    
            except Exception as e:
                print(f"     ❌ Errore metodo 1: {e}")
        
        # Metodo 2: Accesso diretto a reader
        print(f"\n   🧪 METODO 2: reader.RST/CS")
        try:
            if hasattr(reader, 'RST'):
                old_rst = getattr(reader, 'RST', 'Non trovato')
                reader.RST = expected_rst
                new_rst = getattr(reader, 'RST', 'Errore')
                print(f"     RST: {old_rst} → {new_rst}")
            else:
                print(f"     RST: Attributo non esistente su reader")
            
            if hasattr(reader, 'CS'):
                old_cs = getattr(reader, 'CS', 'Non trovato')
                reader.CS = expected_cs
                new_cs = getattr(reader, 'CS', 'Errore')
                print(f"     CS: {old_cs} → {new_cs}")
            else:
                print(f"     CS: Attributo non esistente su reader")
                
        except Exception as e:
            print(f"     ❌ Errore metodo 2: {e}")
        
        # Metodo 3: Verifica metodi di configurazione
        print(f"\n   🧪 METODO 3: METODI CONFIGURAZIONE")
        config_methods = ['set_pin', 'setPin', 'configure_pins', 'setup_pins']
        for method_name in config_methods:
            if hasattr(reader, method_name):
                print(f"     ✅ {method_name}() disponibile")
            elif hasattr(reader, 'READER') and hasattr(reader.READER, method_name):
                print(f"     ✅ READER.{method_name}() disponibile")
            else:
                print(f"     ❌ {method_name}() non trovato")
        
        # ANALISI 5: Test lettura con configurazione di default
        print(f"\n📋 ANALISI 5: TEST LETTURA DEFAULT")
        print("   💡 Avvicina una card per testare con pin di default...")
        
        cards_found = 0
        for i in range(10):
            try:
                print(f"   Tentativo {i+1}/10...", end='')
                
                if hasattr(reader, 'read_no_block'):
                    card_id, card_data = reader.read_no_block()
                else:
                    card_id, card_data = reader.read()
                
                if card_id is not None:
                    cards_found += 1
                    print(f" 🎉 CARD TROVATA CON PIN DEFAULT!")
                    print(f"     ID: {card_id}, Hex: {hex(card_id)}")
                    break
                else:
                    print(" ⚪")
                
            except Exception as e:
                error_msg = str(e).lower()
                if "no card" in error_msg or "timeout" in error_msg:
                    print(" ⚪")
                else:
                    print(f" ❌ {e}")
            
            time.sleep(0.5)
        
        if cards_found > 0:
            print(f"\n   🎉 LETTURA RIUSCITA CON PIN DEFAULT!")
            print(f"   💡 Il problema è che la libreria usa pin fissi")
            print(f"   🔧 Soluzione: Usa i pin di default della libreria")
        else:
            print(f"\n   ❌ Nessuna card con pin default")
        
        # ANALISI 6: Identificazione pin di default
        print(f"\n📋 ANALISI 6: PIN DI DEFAULT DELLA LIBRERIA")
        
        # Controlla pin comuni
        common_pins = {
            'RST': [22, 25, 18],
            'CS': [8, 7, 24], 
            'SDA': [8, 7, 24]
        }
        
        if hasattr(reader, 'READER'):
            hw_reader = reader.READER
            
            for pin_name, possible_values in common_pins.items():
                if hasattr(hw_reader, pin_name):
                    actual_value = getattr(hw_reader, pin_name, 'Non impostato')
                    print(f"   {pin_name}: {actual_value}")
                    
                    if actual_value in possible_values:
                        print(f"     ✅ Pin standard riconosciuto")
                    else:
                        print(f"     ⚠️ Pin non standard")
        
        # Cleanup
        GPIO.cleanup()
        
        print(f"\n📋 RIEPILOGO ANALISI:")
        print(f"   Lettura con pin default: {'✅ OK' if cards_found > 0 else '❌ FALLITA'}")
        print(f"   Configurazione pin supportata: Verificare metodi sopra")
        
        return cards_found > 0
        
    except Exception as e:
        print(f"❌ Errore analisi: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 ANALISI COMPLETA LIBRERIA MFRC522")
    print("Questo test identifica come funziona REALMENTE la tua libreria")
    print("=" * 60)
    
    success = analyze_mfrc522_library()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SOLUZIONE TROVATA!")
        print("💡 La libreria funziona ma usa pin diversi da quelli configurati")
        print("🔧 Ora possiamo correggere il sistema per usare i pin giusti")
    else:
        print("🔍 ANALISI COMPLETATA")
        print("💡 Controlla i risultati sopra per identificare il problema")
    print("=" * 60)

if __name__ == "__main__":
    main()