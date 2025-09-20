#!/usr/bin/env python3
"""
Test PIN SPECIFICI per identificare quali pin usa la libreria mfrc522
"""
import sys
import time

def test_common_pin_combinations():
    """Testa le combinazioni di pin più comuni per mfrc522"""
    print("🔍 TEST PIN COMBINATIONS COMUNI")
    print("=" * 60)
    
    try:
        # Aggiungi src al path
        sys.path.insert(0, 'src')
        
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
        
        # Cleanup iniziale
        try:
            GPIO.cleanup()
            time.sleep(0.5)
        except:
            pass
        
        # Combinazioni di pin comuni per mfrc522
        pin_combinations = [
            {"name": "Standard RC522", "rst": 22, "cs": 8},
            {"name": "Alternative 1", "rst": 25, "cs": 8},
            {"name": "Alternative 2", "rst": 22, "cs": 7},
            {"name": "Alternative 3", "rst": 25, "cs": 7},
            {"name": "Alternative 4", "rst": 18, "cs": 24},
            {"name": "Configurazione attuale", "rst": 22, "cs": 8},  # Dal tuo .env
        ]
        
        working_combinations = []
        
        for combo in pin_combinations:
            print(f"\n🧪 TEST: {combo['name']}")
            print(f"   RST={combo['rst']}, CS={combo['cs']}")
            
            try:
                # Configura GPIO per questa combinazione
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                
                # Crea reader
                reader = SimpleMFRC522()
                
                # Prova a configurare pin se possibile
                if hasattr(reader, 'READER'):
                    hw_reader = reader.READER
                    
                    # Prova a impostare pin
                    try:
                        if hasattr(hw_reader, 'RST'):
                            hw_reader.RST = combo['rst']
                        if hasattr(hw_reader, 'CS'):
                            hw_reader.CS = combo['cs']
                        if hasattr(hw_reader, 'SDA'):
                            hw_reader.SDA = combo['cs']
                    except:
                        pass
                
                # Test rapido lettura (3 tentativi)
                cards_found = 0
                print(f"   Test lettura (avvicina card)...")
                
                for i in range(3):
                    try:
                        if hasattr(reader, 'read_no_block'):
                            card_id, card_data = reader.read_no_block()
                        else:
                            card_id, card_data = reader.read()
                        
                        if card_id is not None:
                            cards_found += 1
                            print(f"   🎉 CARD RILEVATA! ID={card_id}")
                            working_combinations.append(combo)
                            break
                            
                    except Exception as e:
                        error_msg = str(e).lower()
                        if not any(skip in error_msg for skip in ["no card", "timeout"]):
                            print(f"   ⚠️ Errore: {e}")
                    
                    time.sleep(0.5)
                
                if cards_found == 0:
                    print(f"   ⚪ Nessuna card rilevata")
                
                # Cleanup per prossima combinazione
                GPIO.cleanup()
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Errore combinazione: {e}")
                try:
                    GPIO.cleanup()
                    time.sleep(0.5)
                except:
                    pass
        
        # Risultati finali
        print(f"\n📊 RISULTATI FINALI:")
        print("=" * 40)
        
        if working_combinations:
            print(f"✅ COMBINAZIONI FUNZIONANTI:")
            for combo in working_combinations:
                print(f"   🎯 {combo['name']}: RST={combo['rst']}, CS={combo['cs']}")
            
            # Suggerisci configurazione .env
            best_combo = working_combinations[0]
            print(f"\n🔧 CONFIGURAZIONE .env SUGGERITA:")
            print(f"   RFID_IN_RST_PIN={best_combo['rst']}")
            print(f"   RFID_IN_SDA_PIN={best_combo['cs']}")
            
        else:
            print(f"❌ NESSUNA COMBINAZIONE FUNZIONANTE")
            print(f"💡 Possibili cause:")
            print(f"   1. Hardware/cablaggio problema")
            print(f"   2. Card non compatibile")
            print(f"   3. Alimentazione insufficiente")
            print(f"   4. SPI non abilitato")
        
        return len(working_combinations) > 0
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_current_wiring():
    """Verifica il cablaggio attuale confrontandolo con pin standard"""
    print("\n🔌 VERIFICA CABLAGGIO ATTUALE")
    print("=" * 40)
    
    try:
        sys.path.insert(0, 'src')
        from config import Config
        
        current_rst = Config.RFID_IN_RST_PIN
        current_cs = Config.RFID_IN_SDA_PIN
        
        print(f"📋 Configurazione attuale (.env):")
        print(f"   RST: GPIO{current_rst} (Pin fisico {gpio_to_physical(current_rst)})")
        print(f"   CS:  GPIO{current_cs} (Pin fisico {gpio_to_physical(current_cs)})")
        
        print(f"\n📋 Pin standard per RC522:")
        print(f"   RST comune: GPIO22 (Pin fisico 15)")
        print(f"   CS comune:  GPIO8 (Pin fisico 24)")
        
        if current_rst == 22 and current_cs == 8:
            print(f"✅ Configurazione standard - dovrebbe funzionare")
        else:
            print(f"⚠️ Configurazione non standard")
            print(f"💡 Prova a cambiare cablaggio su pin standard")
        
    except Exception as e:
        print(f"❌ Errore verifica: {e}")

def gpio_to_physical(gpio_pin):
    """Converte GPIO in pin fisico"""
    gpio_map = {
        22: 15, 8: 24, 25: 22, 7: 26, 18: 12, 24: 18
    }
    return gpio_map.get(gpio_pin, "?")

def main():
    print("🔍 IDENTIFICAZIONE PIN MFRC522")
    print("Questo test identifica quali pin usa REALMENTE la libreria")
    print("=" * 60)
    
    # Verifica cablaggio attuale
    check_current_wiring()
    
    # Test combinazioni pin
    success = test_common_pin_combinations()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SOLUZIONE TROVATA!")
        print("💡 Aggiorna il file .env con i pin che funzionano")
        print("🔧 Poi riavvia il sistema principale")
    else:
        print("💔 NESSUNA COMBINAZIONE FUNZIONA")
        print("🔧 Controlla cablaggio hardware e alimentazione")
    print("=" * 60)

if __name__ == "__main__":
    main()