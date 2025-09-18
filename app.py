#!/usr/bin/env python3
"""
RFID RC522 Reader per Raspberry Pi
Versione semplificata e ottimizzata
"""

import sys
import time
import signal

def test_imports():
    """Testa se tutte le librerie sono disponibili"""
    print("🔍 Test delle librerie...")
    
    try:
        global GPIO, SimpleMFRC522
        import RPi.GPIO as GPIO
        from mfrc522 import SimpleMFRC522
        print("✅ Tutte le librerie caricate correttamente!")
        return True
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        print("\n💡 Soluzioni:")
        print("1. Attiva l'ambiente virtuale: source venv/bin/activate")
        print("2. Installa: pip install mfrc522 RPi.GPIO")
        print("3. Se RPi.GPIO fallisce: sudo apt install python3-rpi.gpio")
        return False

def signal_handler(sig, frame):
    """Gestisce l'interruzione Ctrl+C"""
    print("\n\n🛑 Interruzione ricevuta...")
    cleanup_and_exit()

def cleanup_and_exit():
    """Pulisce GPIO e termina"""
    try:
        GPIO.cleanup()
        print("🧹 GPIO cleanup completato")
    except:
        pass
    print("👋 Programma terminato!")
    sys.exit(0)

def read_cards():
    """Funzione principale per leggere le card"""
    print("\n" + "="*50)
    print("🎯 LETTORE RFID RC522 ATTIVO")
    print("="*50)
    print("📱 Avvicina una card NFC/RFID al lettore...")
    print("⏹️  Premi Ctrl+C per uscire")
    print("-"*50)

    # Inizializza il lettore
    reader = SimpleMFRC522()
    
    try:
        while True:
            print("\n⏳ In attesa di una card...")
            
            # Legge la card (si blocca fino a quando non ne trova una)
            card_id, card_data = reader.read()
            
            # Mostra i risultati
            print("\n" + "🎉 CARD RILEVATA! 🎉".center(40))
            print("="*40)
            print(f"🆔 ID Univoco: {card_id}")
            print(f"📝 Dati: {card_data.strip() if card_data and card_data.strip() else 'Vuoto'}")
            print(f"🕐 Orario: {time.strftime('%H:%M:%S - %d/%m/%Y')}")
            print("="*40)
            
            # Converte l'ID in formati diversi per debug
            print(f"🔢 ID Decimale: {card_id}")
            print(f"🔤 ID Esadecimale: {hex(card_id)}")
            print(f"📊 Lunghezza dati: {len(card_data) if card_data else 0} caratteri")
            
            print("\n✅ Lettura completata! Rimuovi la card...")
            time.sleep(2)
            print("🔄 Pronto per la prossima lettura...")
            
    except Exception as e:
        print(f"\n❌ Errore durante la lettura: {e}")
        print("🔧 Verifica i collegamenti e riprova")

def main():
    """Funzione principale"""
    print("🚀 Avvio RFID Reader...")
    
    # Configura il gestore di segnali per Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Testa le librerie
    if not test_imports():
        sys.exit(1)
    
    # Testa la connessione del modulo
    print("\n🔌 Test connessione RC522...")
    try:
        reader = SimpleMFRC522()
        print("✅ Modulo RC522 connesso correttamente!")
        del reader  # Libera la risorsa
        GPIO.cleanup()
    except Exception as e:
        print(f"❌ Errore connessione RC522: {e}")
        print("\n🔧 Verifica:")
        print("- Collegamenti SPI corretti")
        print("- SPI abilitato con raspi-config")
        print("- Alimentazione modulo (3.3V)")
        sys.exit(1)
    
    # Avvia la lettura
    read_cards()

if __name__ == "__main__":
    main()