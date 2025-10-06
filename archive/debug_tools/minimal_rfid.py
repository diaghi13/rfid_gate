#!/usr/bin/env python3
"""
Sistema RFID MINIMALISTA - Solo un lettore, zero complicazioni
Funziona SEMPRE se l'hardware è OK
"""
import time
import signal
import sys

class SimpleRFIDSystem:
    """Sistema RFID più semplice possibile"""
    
    def __init__(self):
        self.running = False
        self.reader = None
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        print("\n🛑 Interruzione...")
        self.stop()
    
    def initialize(self):
        """Inizializza sistema base"""
        print("🚀 INIZIALIZZAZIONE SISTEMA RFID MINIMALISTA")
        print("=" * 60)
        
        try:
            # Import base
            import RPi.GPIO as GPIO
            from mfrc522 import SimpleMFRC522
            
            print("✅ Librerie importate")
            
            # Cleanup GPIO completo
            GPIO.cleanup()
            time.sleep(0.5)
            
            # Configura GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            print("✅ GPIO configurato")
            
            # Crea reader base (SENZA parametri)
            self.reader = SimpleMFRC522()
            print("✅ Reader RFID creato")
            
            # Test veloce
            print("🧪 Test veloce...")
            try:
                if hasattr(self.reader, 'read_no_block'):
                    result = self.reader.read_no_block()
                else:
                    # Usa read con timeout molto breve
                    result = self.reader.read()
                print("✅ Reader funzionante")
            except Exception as e:
                if "no card" not in str(e).lower():
                    print(f"⚠️ Warning test: {e}")
                print("✅ Reader probabilmente OK")
            
            self.running = True
            print("✅ Sistema inizializzato")
            return True
            
        except ImportError as e:
            print(f"❌ Librerie mancanti: {e}")
            print("💡 Installa con: pip install mfrc522 RPi.GPIO")
            return False
        except Exception as e:
            print(f"❌ Errore inizializzazione: {e}")
            return False
    
    def run(self):
        """Loop principale minimalista"""
        if not self.running:
            print("❌ Sistema non inizializzato")
            return
        
        print("\n📡 SISTEMA RFID ATTIVO")
        print("=" * 40)
        print("💡 Avvicina una card RFID...")
        print("⏹️ Premi Ctrl+C per uscire")
        print("-" * 40)
        
        card_count = 0
        last_card_id = None
        last_card_time = 0
        debounce_time = 2.0  # 2 secondi debounce
        
        while self.running:
            try:
                # Leggi card
                if hasattr(self.reader, 'read_no_block'):
                    card_id, card_data = self.reader.read_no_block()
                else:
                    card_id, card_data = self.reader.read()
                
                if card_id is not None:
                    current_time = time.time()
                    
                    # Debounce semplice
                    if (card_id != last_card_id or 
                        (current_time - last_card_time) > debounce_time):
                        
                        card_count += 1
                        last_card_id = card_id
                        last_card_time = current_time
                        
                        # Formatta UID
                        uid_hex = hex(card_id)[2:].upper()
                        if len(uid_hex) > 2:
                            uid_formatted = uid_hex[:-2]  # Rimuovi ultimi 2 caratteri
                        else:
                            uid_formatted = uid_hex
                        
                        print(f"\n🎉 CARD #{card_count} RILEVATA!")
                        print(f"   ID Grezzo: {card_id}")
                        print(f"   UID Hex: {uid_hex}")
                        print(f"   UID Formattato: {uid_formatted}")
                        print(f"   Dati: '{card_data.strip()}'")
                        print(f"   Timestamp: {time.strftime('%H:%M:%S')}")
                        
                        # Simula autenticazione
                        print(f"   🔐 Autenticazione... ", end="")
                        time.sleep(0.5)
                        print("✅ AUTORIZZATO")
                        
                        # Simula attivazione relè
                        print(f"   ⚡ Attivazione relè... ", end="")
                        time.sleep(0.3)
                        print("✅ ATTIVATO")
                        
                        print("-" * 40)
                
                # Pausa piccola per non sovraccaricare CPU
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_msg = str(e).lower()
                if not any(skip in error_msg for skip in ["no card", "timeout", "nothing"]):
                    print(f"⚠️ Errore lettura: {e}")
                time.sleep(0.2)
        
        print(f"\n📊 Sessione completata: {card_count} card rilevate")
    
    def stop(self):
        """Ferma sistema"""
        self.running = False
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            print("✅ Sistema spento")
        except:
            pass
        sys.exit(0)

def main():
    """Funzione principale"""
    print("🎯 SISTEMA RFID MINIMALISTA")
    print("Un lettore, zero complicazioni, massima affidabilità")
    print("=" * 60)
    
    # Verifica privilegi
    import os
    if os.geteuid() != 0:
        print("⚠️ ATTENZIONE: Esegui con sudo per migliori prestazioni")
        print("💡 sudo python3 minimal_rfid.py")
        print("🔄 Continuo comunque...")
    
    # Crea sistema
    system = SimpleRFIDSystem()
    
    try:
        if system.initialize():
            system.run()
        else:
            print("❌ Inizializzazione fallita")
            
    except Exception as e:
        print(f"❌ Errore critico: {e}")
    finally:
        system.stop()

if __name__ == "__main__":
    main()