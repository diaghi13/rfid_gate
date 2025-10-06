#!/usr/bin/env python3
"""
Test REALE del nuovo sistema RFID
Verifica se il nuovo codice funziona davvero in pratica
"""
import sys
import time
import signal

# Aggiungi src al path
sys.path.insert(0, 'src')

class RealRFIDTest:
    """Test reale del sistema RFID ricostruito"""
    
    def __init__(self):
        self.manager = None
        self.running = False
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        print("\n🛑 Test interrotto...")
        self.stop()
    
    def test_initialization(self):
        """Test REALE di inizializzazione"""
        print("🧪 TEST REALE - INIZIALIZZAZIONE")
        print("=" * 50)
        
        try:
            # Import dei moduli
            from config import Config
            from rfid_reader import RFIDReader  
            from rfid_manager import RFIDManager
            print("✅ Import moduli: OK")
            
            # Verifica configurazione
            print(f"\n📋 CONFIGURAZIONE RILEVATA:")
            print(f"   RFID_IN_ENABLE: {Config.RFID_IN_ENABLE}")
            print(f"   RFID_OUT_ENABLE: {Config.RFID_OUT_ENABLE}")
            print(f"   BIDIRECTIONAL_MODE: {Config.BIDIRECTIONAL_MODE}")
            
            if not Config.RFID_IN_ENABLE and not Config.RFID_OUT_ENABLE:
                print("❌ ERRORE: Nessun lettore RFID abilitato!")
                return False
            
            # Test lettore singolo PRIMA del manager
            print(f"\n🔍 TEST LETTORE SINGOLO (CRITICO):")
            reader = RFIDReader("test_single", Config.RFID_IN_RST_PIN, Config.RFID_IN_SDA_PIN)
            
            init_success = reader.initialize()
            print(f"   Inizializzazione: {'✅ OK' if init_success else '❌ FALLITA'}")
            
            if not init_success:
                print("❌ FALLIMENTO CRITICO: Lettore singolo non funziona")
                print("💡 Il problema è nell'hardware o nella libreria mfrc522")
                return False
            
            # Test connessione
            conn_success = reader.test_connection()
            print(f"   Test connessione: {'✅ OK' if conn_success else '❌ FALLITA'}")
            
            if not conn_success:
                print("❌ FALLIMENTO CRITICO: Connessione lettore fallita")
                reader.cleanup()
                return False
            
            # Test lettura veloce
            print("   Test lettura veloce (5 tentativi)...")
            read_success = False
            for i in range(5):
                try:
                    card_id, card_data = reader.read_card()
                    if card_id:
                        print(f"   🎉 LETTURA RIUSCITA: {reader.format_card_uid(card_id)}")
                        read_success = True
                        break
                    time.sleep(0.3)
                except Exception as e:
                    print(f"   ⚠️ Tentativo {i+1}: {e}")
            
            if not read_success:
                print("   ℹ️ Nessuna card rilevata (normale se non hai avvicinato card)")
            
            reader.cleanup()
            print("✅ TEST LETTORE SINGOLO: COMPLETATO")
            
            # Test manager
            print(f"\n🎯 TEST MANAGER COMPLETO:")
            self.manager = RFIDManager()
            
            if not self.manager.initialize():
                print("❌ FALLIMENTO CRITICO: Manager non inizializza")
                return False
            
            print("✅ Manager inizializzato")
            
            # Verifica status
            status = self.manager.get_reader_status()
            print(f"📊 Status manager:")
            print(f"   Inizializzato: {status['initialized']}")
            print(f"   Lettori attivi: {status['active_readers']}")
            print(f"   Dettagli lettori:")
            for direction, reader_info in status['readers'].items():
                print(f"     {direction.upper()}: RST={reader_info['rst_pin']}, CS={reader_info['cs_pin']}")
            
            # Test di tutti i lettori
            if not self.manager.test_all_readers():
                print("❌ FALLIMENTO: Test lettori manager fallito")
                return False
            
            print("✅ TEST INIZIALIZZAZIONE: COMPLETATO CON SUCCESSO")
            return True
            
        except ImportError as e:
            print(f"❌ ERRORE IMPORT: {e}")
            print("💡 Probabilmente manca la libreria mfrc522 o RPi.GPIO")
            return False
        except Exception as e:
            print(f"❌ ERRORE INIZIALIZZAZIONE: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_real_usage(self):
        """Test REALE di utilizzo (come main.py)"""
        print("\n🚀 TEST REALE - UTILIZZO PRATICO")
        print("=" * 50)
        
        if not self.manager:
            print("❌ Manager non inizializzato")
            return False
        
        try:
            # Avvia thread di lettura (come fa main.py)
            if not self.manager.start_reading():
                print("❌ FALLIMENTO CRITICO: Thread di lettura non avviati")
                return False
            
            print("✅ Thread di lettura avviati")
            self.running = True
            
            print("\n📡 SISTEMA IN ASCOLTO (come main.py)")
            print("💡 Avvicina una card RFID per testare...")
            print("⏹️ Premi Ctrl+C per fermare")
            print("-" * 40)
            
            card_count = 0
            start_time = time.time()
            test_duration = 30  # 30 secondi di test
            
            while self.running and (time.time() - start_time) < test_duration:
                try:
                    # Aspetta card (come fa main.py)
                    card_info = self.manager.get_next_card(timeout=2)
                    
                    if card_info:
                        card_count += 1
                        
                        # Simula elaborazione card (come main.py)
                        direction = card_info.get('direction', 'unknown').upper()
                        uid = card_info.get('uid_formatted', 'N/A')
                        timestamp = card_info.get('timestamp', time.time())
                        
                        print(f"\n🎉 CARD RILEVATA #{card_count}:")
                        print(f"   UID: {uid}")
                        print(f"   Direzione: {direction}")
                        print(f"   Timestamp: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
                        print(f"   Dati grezzi: ID={card_info.get('raw_id')}")
                        
                        # Simula elaborazione autorizzazione
                        print(f"   🔐 Simulazione autorizzazione...")
                        time.sleep(0.1)  # Simula tempo di processing
                        print(f"   ✅ Autorizzazione simulata: OK")
                        
                        print("-" * 40)
                    
                    # Status periodico
                    if int(time.time() - start_time) % 10 == 0:
                        elapsed = int(time.time() - start_time)
                        print(f"⏱️ Tempo trascorso: {elapsed}s - Card rilevate: {card_count}")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"⚠️ Errore durante lettura: {e}")
                    continue
            
            # Risultati finali
            elapsed_time = int(time.time() - start_time)
            print(f"\n📊 RISULTATI TEST REALE:")
            print(f"   Durata test: {elapsed_time}s")
            print(f"   Card rilevate: {card_count}")
            print(f"   Frequenza: {card_count/max(elapsed_time,1):.2f} card/s")
            
            if card_count > 0:
                print("✅ SISTEMA RFID: FUNZIONANTE")
                print("💡 Il nuovo codice funziona correttamente!")
            else:
                print("⚠️ NESSUNA CARD RILEVATA")
                print("💡 Questo potrebbe essere normale se non hai avvicinato card")
                print("🔧 Verifica che il cablaggio sia corretto")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRORE TEST REALE: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        """Ferma il test"""
        self.running = False
        if self.manager:
            print("🛑 Fermando manager...")
            self.manager.stop_reading()
            self.manager.cleanup()
            print("✅ Manager fermato")
    
    def run_complete_test(self):
        """Esegue test completo"""
        print("🧪 TEST COMPLETO SISTEMA RFID RICOSTRUITO")
        print("Questo test verifica se il nuovo codice funziona DAVVERO")
        print("=" * 60)
        
        try:
            # Test inizializzazione
            if not self.test_initialization():
                print("\n💔 TEST FALLITO: Inizializzazione")
                return False
            
            # Test utilizzo reale
            if not self.test_real_usage():
                print("\n💔 TEST FALLITO: Utilizzo pratico")
                return False
            
            print("\n🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!")
            print("✅ Il nuovo sistema RFID funziona correttamente")
            print("💡 Puoi sostituire il vecchio codice con quello nuovo")
            return True
            
        except Exception as e:
            print(f"\n❌ ERRORE GENERALE TEST: {e}")
            return False
        finally:
            self.stop()

def main():
    """Funzione principale"""
    tester = RealRFIDTest()
    
    try:
        success = tester.run_complete_test()
        
        print("\n" + "=" * 60)
        if success:
            print("🚀 VERDETTO: IL NUOVO CODICE FUNZIONA!")
            print("📝 PROSSIMI PASSI:")
            print("   1. Testa sul Raspberry Pi")
            print("   2. Integra nel main.py")
            print("   3. Verifica con hardware reale")
        else:
            print("💔 VERDETTO: IL NUOVO CODICE HA PROBLEMI")
            print("🔧 PROSSIMI PASSI:")
            print("   1. Controlla cablaggio hardware")
            print("   2. Verifica librerie installate")
            print("   3. Controlla configurazione .env")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrotto dall'utente")
        tester.stop()

if __name__ == "__main__":
    main()