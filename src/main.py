#!/usr/bin/env python3
"""
Sistema di Controllo Accessi RFID
Applicazione principale con architettura modulare
"""

import sys
import time
import signal
import os
from datetime import datetime

# Import dei moduli personalizzati
from config import Config
from rfid_reader import RFIDReader
from relay_controller import RelayController
from mqtt_client import MQTTClient
from logger import AccessLogger

class AccessControlSystem:
    """Sistema principale di controllo accessi"""
    
    def __init__(self):
        self.rfid_reader = None
        self.relay_controller = None
        self.mqtt_client = None
        self.logger = None
        self.running = False
        
        # Configura il gestore per Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Gestisce l'interruzione del programma"""
        print("\n\n🛑 Interruzione ricevuta...")
        self.shutdown()
    
    def initialize(self):
        """Inizializza tutti i componenti del sistema"""
        print("🚀 Avvio Sistema di Controllo Accessi RFID...")
        print("="*60)
        
        # Valida la configurazione
        config_errors = Config.validate_config()
        if config_errors:
            print("❌ Errori di configurazione:")
            for error in config_errors:
                print(f"   - {error}")
            return False
        
        # Stampa la configurazione
        Config.print_config()
        print("="*60)
        
        # Inizializza Logger
        print("\n📝 Inizializzazione Sistema di Logging...")
        self.logger = AccessLogger(Config.LOG_DIRECTORY)
        self.logger.log_system_event("system_start", "Sistema di controllo accessi avviato")
        
        # Inizializza RFID Reader
        print("\n📖 Inizializzazione RFID Reader...")
        self.rfid_reader = RFIDReader()
        if not self.rfid_reader.initialize():
            self.logger.log_system_event("rfid_init_error", "Errore inizializzazione RFID", "error")
            return False
        
        if not self.rfid_reader.test_connection():
            self.logger.log_system_event("rfid_connection_error", "Test connessione RFID fallito", "error")
            return False
        
        self.logger.log_system_event("rfid_init", "RFID Reader inizializzato correttamente")
        
        # Inizializza Relay Controller
        print("\n⚡ Inizializzazione Relay Controller...")
        self.relay_controller = RelayController()
        if not self.relay_controller.initialize():
            self.logger.log_system_event("relay_init_error", "Errore inizializzazione relè", "error")
            return False
        
        # Test del relè
        if not self.relay_controller.test_relay():
            self.logger.log_system_event("relay_test_error", "Test relè fallito", "warning")
            return False
        
        self.logger.log_system_event("relay_init", "Relay Controller inizializzato correttamente")
        
        # Inizializza MQTT Client
        print("\n🌐 Inizializzazione MQTT Client...")
        self.mqtt_client = MQTTClient()
        if not self.mqtt_client.initialize():
            self.logger.log_system_event("mqtt_init_error", "Errore inizializzazione MQTT", "error")
            return False
        
        if not self.mqtt_client.connect():
            self.logger.log_system_event("mqtt_connection_error", "Connessione MQTT fallita", "error")
            return False
        
        # Invia messaggio di stato
        self.mqtt_client.publish_status("online")
        self.logger.log_system_event("mqtt_init", f"MQTT Client connesso a {Config.MQTT_BROKER}")
        
        print("\n✅ Tutti i componenti inizializzati correttamente!")
        return True
    
    def run(self):
        """Avvia il loop principale del sistema"""
        if not self.initialize():
            print("\n❌ Inizializzazione fallita. Uscita...")
            return
        
        self.running = True
        
        print("\n" + "="*70)
        print("🎯 SISTEMA DI CONTROLLO ACCESSI ATTIVO")
        print("="*70)
        print("📱 Avvicina una card NFC/RFID al lettore...")
        print("⚡ Il relè si attiverà automaticamente")
        print("📡 I dati verranno inviati via MQTT con TLS")
        print("📝 Tutti gli accessi verranno registrati nei log")
        print("⏹️  Premi Ctrl+C per uscire")
        print("-"*70)
        
        # Mostra statistiche precedenti
        if os.path.exists(os.path.join(Config.LOG_DIRECTORY, "access_log.csv")):
            self.logger.print_stats(7)
        
        self._main_loop()
    
    def _main_loop(self):
        """Loop principale di lettura delle card"""
        card_count = 0
        
        try:
            while self.running:
                print(f"\n⏳ In attesa di una card... (#{card_count + 1})")
                
                # Legge la card
                card_id, card_data = self.rfid_reader.read_card()
                
                if card_id is None:
                    print("⚠️ Errore lettura card, riprovo...")
                    time.sleep(1)
                    continue
                
                # Incrementa il contatore
                card_count += 1
                
                # Ottiene le informazioni complete della card
                card_info = self.rfid_reader.get_card_info(card_id, card_data)
                
                # Mostra le informazioni
                self._display_card_info(card_info, card_count)
                
                # Misura il tempo di autenticazione
                auth_start_time = time.time()
                
                # Invia i dati via MQTT e aspetta l'autorizzazione
                auth_result = self.mqtt_client.publish_card_data_and_wait_auth(card_info)
                
                # Calcola il tempo di autenticazione
                auth_time_ms = int((time.time() - auth_start_time) * 1000)
                
                # Mostra il risultato dell'autenticazione
                self._display_auth_result(auth_result)
                
                # Attiva il relè solo se autorizzato
                success_relay = False
                if auth_result.get('authorized', False):
                    print("🔓 Accesso autorizzato - Attivazione relè...")
                    success_relay = self.relay_controller.activate()
                else:
                    print("🔒 Accesso negato - Relè non attivato")
                    reason = auth_result.get('error') or auth_result.get('message', 'Motivo sconosciuto')
                    print(f"❌ Motivo: {reason}")
                
                # REGISTRA NEI LOG
                log_entry = self.logger.log_access_attempt(
                    card_info=card_info,
                    auth_result=auth_result,
                    relay_success=success_relay,
                    auth_time_ms=auth_time_ms
                )
                
                # Riepilogo operazione
                self._display_operation_summary(True, success_relay, auth_result)
                
                print("\n✅ Operazione completata! Rimuovi la card...")
                time.sleep(1)
                print("🔄 Pronto per la prossima lettura...")
                
        except Exception as e:
            print(f"\n❌ Errore nel loop principale: {e}")
            if self.logger:
                self.logger.log_system_event("main_loop_error", str(e), "error")
            print("🔧 Il sistema continuerà a funzionare...")
            time.sleep(2)
    
    def _display_card_info(self, card_info, card_count):
        """Mostra le informazioni della card letta"""
        print("\n" + "🎉 CARD RILEVATA! 🎉".center(60))
        print("="*60)
        print(f"📊 Lettura #{card_count}")
        print(f"🆔 ID Numerico: {card_info.get('raw_id')}")
        print(f"🏷️  UID MIFARE: {card_info.get('uid_formatted')}")
        print(f"🔤 ID Esadecimale: {card_info.get('uid_hex')}")
        print(f"📝 Dati Card: {card_info.get('data') or 'Vuoto'}")
        print(f"📏 Lunghezza Dati: {card_info.get('data_length')} caratteri")
        print(f"🕐 Timestamp: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}")
        print(f"🚪 Tornello: {Config.TORNELLO_ID}")
        print(f"➡️  Direzione: {Config.DIREZIONE}")
        print("="*60)
    
    def _display_auth_result(self, auth_result):
        """Mostra il risultato dell'autenticazione"""
        authorized = auth_result.get('authorized', False)
        message = auth_result.get('message', '')
        error = auth_result.get('error', '')
        
        if authorized:
            print("🟢 AUTENTICAZIONE RIUSCITA")
            if message:
                print(f"💬 Messaggio server: {message}")
        else:
            print("🔴 AUTENTICAZIONE FALLITA")
            if error:
                print(f"❌ Errore: {error}")
            elif message:
                print(f"💬 Messaggio server: {message}")
    
    def _display_operation_summary(self, mqtt_success, relay_success, auth_result):
        """Mostra il riepilogo delle operazioni"""
        print(f"\n📋 Riepilogo operazioni:")
        
        mqtt_status = "✅ Inviato" if mqtt_success else "❌ Fallito"
        auth_status = "✅ Autorizzato" if auth_result.get('authorized', False) else "❌ Negato"
        relay_status = "✅ Attivato" if relay_success else "❌ Non attivato"
        
        print(f"   📡 MQTT: {mqtt_status}")
        if Config.AUTH_ENABLED:
            print(f"   🔐 Auth: {auth_status}")
        print(f"   ⚡ Relè: {relay_status}")
        
        if mqtt_success and (not Config.AUTH_ENABLED or auth_result.get('authorized', False)):
            if relay_success:
                print("   🎯 Accesso completato con successo!")
            else:
                print("   ⚠️ Accesso autorizzato ma relè non attivato")
        else:
            print("   🔒 Accesso negato o errore sistema")
    
    def get_system_status(self):
        """Restituisce lo stato di tutti i componenti"""
        return {
            'rfid': self.rfid_reader.is_initialized if self.rfid_reader else False,
            'relay': self.relay_controller.get_status() if self.relay_controller else None,
            'mqtt': self.mqtt_client.get_status() if self.mqtt_client else None,
            'logger': bool(self.logger),
            'running': self.running,
            'config': {
                'tornello_id': Config.TORNELLO_ID,
                'direzione': Config.DIREZIONE,
                'auth_enabled': Config.AUTH_ENABLED,
                'log_directory': Config.LOG_DIRECTORY
            }
        }
    
    def shutdown(self):
        """Spegne il sistema in modo pulito"""
        print("\n🛑 Spegnimento del sistema...")
        self.running = False
        
        # Log di sistema
        if self.logger:
            self.logger.log_system_event("system_shutdown", "Spegnimento sistema in corso")
            
            # Mostra statistiche finali
            print("\n📊 Statistiche finali della sessione:")
            self.logger.print_stats(1)  # Statistiche di oggi
        
        # Spegne MQTT
        if self.mqtt_client:
            self.mqtt_client.publish_status("offline")
            self.mqtt_client.disconnect()
            if self.logger:
                self.logger.log_system_event("mqtt_disconnect", "MQTT disconnesso")
        
        # Spegne il relè
        if self.relay_controller:
            self.relay_controller.reset_to_initial_state()
            self.relay_controller.cleanup()
            if self.logger:
                self.logger.log_system_event("relay_shutdown", "Relè ripristinato stato iniziale e GPIO puliti")
        
        # Pulisce RFID
        if self.rfid_reader:
            self.rfid_reader.cleanup()
            if self.logger:
                self.logger.log_system_event("rfid_shutdown", "RFID Reader spento")
        
        # Log finale
        if self.logger:
            self.logger.log_system_event("system_stop", "Sistema spento correttamente")
        
        print("👋 Sistema spento correttamente!")
        sys.exit(0)

def main():
    """Funzione principale"""
    try:
        # Verifica che stiamo eseguendo come root/sudo
        if not check_permissions():
            print("❌ Questo programma deve essere eseguito con sudo")
            print("💡 Usa: sudo python3 main.py")
            sys.exit(1)
        
        # Crea e avvia il sistema
        system = AccessControlSystem()
        system.run()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interruzione da tastiera")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore critico: {e}")
        sys.exit(1)

def check_permissions():
    """Verifica i permessi per accedere ai GPIO"""
    try:
        import os
        return os.geteuid() == 0
    except:
        return True  # Se non possiamo verificare, assumiamo che sia ok

if __name__ == "__main__":
    main()