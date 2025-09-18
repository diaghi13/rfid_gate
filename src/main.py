#!/usr/bin/env python3
"""
Sistema di Controllo Accessi RFID Bidirezionale
Supporta lettori RFID e relè multipli per gestione IN/OUT
"""

import sys
import time
import signal
import os
from datetime import datetime

# Import dei moduli personalizzati
from config import Config
from rfid_manager import RFIDManager
from relay_manager import RelayManager
from mqtt_client import MQTTClient
from logger import AccessLogger
from offline_manager import OfflineManager
from manual_control import ManualControl

class BidirectionalAccessSystem:
    """Sistema principale di controllo accessi bidirezionale"""
    
    def __init__(self):
        self.rfid_manager = None
        self.relay_manager = None
        self.mqtt_client = None
        self.logger = None
        self.offline_manager = None
        self.manual_control = None
        self.running = False
        
        # Configura il gestore per Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Gestisce l'interruzione del programma"""
        print("\n\n🛑 Interruzione ricevuta...")
        self.shutdown()
    
    def initialize(self):
        """Inizializza tutti i componenti del sistema"""
        print("🚀 Avvio Sistema di Controllo Accessi RFID Bidirezionale...")
        print("="*70)
        
        # Valida la configurazione
        config_errors = Config.validate_config()
        if config_errors:
            print("❌ Errori di configurazione:")
            for error in config_errors:
                print(f"   - {error}")
            return False
        
        # Stampa la configurazione
        Config.print_config()
        print("="*70)
        
        # Inizializza Logger
        print("\n📝 Inizializzazione Sistema di Logging...")
        try:
            self.logger = AccessLogger(Config.LOG_DIRECTORY)
            self.logger.log_system_event("system_start", f"Sistema bidirezionale avviato - Modalità: {'Bidirezionale' if Config.BIDIRECTIONAL_MODE else 'Unidirezionale'}")
        except Exception as e:
            print(f"❌ Errore inizializzazione Logger: {e}")
            return False
        
        # Inizializza RFID Manager
        print("\n📖 Inizializzazione RFID Manager...")
        try:
            self.rfid_manager = RFIDManager()
            if not self.rfid_manager.initialize():
                self.logger.log_system_event("rfid_manager_error", "Errore inizializzazione RFID Manager", "error")
                return False
            
            active_readers = self.rfid_manager.get_active_readers()
            self.logger.log_system_event("rfid_manager_init", f"RFID Manager inizializzato con lettori: {active_readers}")
        except Exception as e:
            print(f"❌ Errore RFID Manager: {e}")
            if self.logger:
                self.logger.log_system_event("rfid_manager_error", str(e), "error")
            return False
        
        # Inizializza Relay Manager
        print("\n⚡ Inizializzazione Relay Manager...")
        try:
            self.relay_manager = RelayManager()
            if not self.relay_manager.initialize():
                self.logger.log_system_event("relay_manager_error", "Errore inizializzazione Relay Manager", "error")
                return False
            
            active_relays = self.relay_manager.get_active_relays()
            self.logger.log_system_event("relay_manager_init", f"Relay Manager inizializzato con relè: {active_relays}")
        except Exception as e:
            print(f"❌ Errore Relay Manager: {e}")
            if self.logger:
                self.logger.log_system_event("relay_manager_error", str(e), "error")
            return False
        
        # Inizializza MQTT Client
        print("\n🌐 Inizializzazione MQTT Client...")
        mqtt_connected = False
        try:
            self.mqtt_client = MQTTClient()
            if self.mqtt_client.initialize():
                if self.mqtt_client.connect():
                    # Invia messaggio di stato
                    self.mqtt_client.publish_status("online")
                    self.logger.log_system_event("mqtt_init", f"MQTT Client connesso a {Config.MQTT_BROKER}")
                    print("✅ MQTT Client connesso")
                    mqtt_connected = True
                else:
                    print("⚠️ MQTT Client inizializzato ma non connesso")
                    self.logger.log_system_event("mqtt_connection_warning", "MQTT inizializzato ma connessione fallita", "warning")
            else:
                print("⚠️ MQTT Client non inizializzato")
                self.logger.log_system_event("mqtt_init_warning", "MQTT Client non inizializzato", "warning")
        except Exception as e:
            print(f"⚠️ Errore MQTT Client: {e}")
            if self.logger:
                self.logger.log_system_event("mqtt_init_error", str(e), "warning")
            # Non bloccare l'avvio se MQTT fallisce in modalità offline
        
        # Inizializza Offline Manager (SEMPRE, anche se MQTT fallisce)
        print("\n🌐 Inizializzazione Offline Manager...")
        try:
            self.offline_manager = OfflineManager(self.mqtt_client, self.logger)
            if self.offline_manager.initialize():
                self.logger.log_system_event("offline_manager_init", "Offline Manager inizializzato")
                print("✅ Offline Manager attivato")
                
                # Verifica stato iniziale
                offline_status = self.offline_manager.get_status()
                if offline_status['online']:
                    print("🟢 Sistema: ONLINE")
                else:
                    print("🔴 Sistema: OFFLINE - Modalità fallback attiva")
            else:
                print("❌ Offline Manager non inizializzato - Sistema potrebbe non funzionare offline")
                # Non bloccare l'avvio, ma avvisa
        except Exception as e:
            print(f"❌ Errore Offline Manager: {e}")
            if self.logger:
                self.logger.log_system_event("offline_manager_error", str(e), "error")
            print("⚠️ Sistema continuerà senza fallback offline")
        
        # Inizializza Manual Control
        print("\n🔓 Inizializzazione Controllo Manuale...")
        try:
            self.manual_control = ManualControl(self.mqtt_client, self.relay_manager, self.logger)
            if self.manual_control.initialize():
                self.logger.log_system_event("manual_control_init", "Controllo manuale inizializzato")
                print("✅ Controllo manuale attivato")
            else:
                print("⚠️ Controllo manuale non inizializzato")
        except Exception as e:
            print(f"⚠️ Errore Controllo Manuale: {e}")
            if self.logger:
                self.logger.log_system_event("manual_control_error", str(e), "warning")
            print("⚠️ Sistema continuerà senza controllo manuale")
        
        print("\n✅ Inizializzazione completata!")
        
        # Report finale configurazione
        if self.offline_manager:
            offline_status = self.offline_manager.get_status()
            print(f"📊 Modalità offline: {'✅ Abilitata' if offline_status['enabled'] else '❌ Disabilitata'}")
            if offline_status['enabled']:
                print(f"🚪 Accesso offline: {'✅ Consentito' if offline_status['allow_offline_access'] else '❌ Negato'}")
        else:
            print("📊 Modalità offline: ❌ Non disponibile")
        
        if self.manual_control:
            manual_status = self.manual_control.get_status()
            print(f"🔓 Controllo manuale: {'✅ Attivo' if manual_status['enabled'] else '❌ Disattivo'}")
            if manual_status['enabled']:
                print(f"🔑 Auth richiesta: {'✅ Sì' if manual_status['config']['auth_required'] else '❌ No'}")
        else:
            print("🔓 Controllo manuale: ❌ Non disponibile")
        
        return True
    
    def run(self):
        """Avvia il loop principale del sistema"""
        if not self.initialize():
            print("\n❌ Inizializzazione fallita. Uscita...")
            return
        
        # Avvia i thread di lettura RFID
        try:
            if not self.rfid_manager.start_reading():
                print("❌ Errore avvio thread RFID")
                return
        except Exception as e:
            print(f"❌ Errore avvio RFID Manager: {e}")
            return
        
        self.running = True
        
        print("\n" + "="*80)
        print("🎯 SISTEMA DI CONTROLLO ACCESSI BIDIREZIONALE ATTIVO")
        print("="*80)
        
        # Mostra configurazione attiva
        try:
            active_readers = self.rfid_manager.get_active_readers()
            active_relays = self.relay_manager.get_active_relays()
            
            print(f"📱 Lettori RFID attivi: {', '.join([r.upper() for r in active_readers])}")
            print(f"⚡ Relè attivi: {', '.join([r.upper() for r in active_relays])}")
            print("📡 Dati inviati via MQTT con TLS e autenticazione")
            print("🌐 Modalità offline abilitata per continuità servizio")
            print("🔓 Controllo manuale remoto e locale disponibile")
            print("📝 Tutti gli accessi vengono registrati nei log")
            print("⏹️  Premi Ctrl+C per uscire")
            print("-"*80)
            
            # Mostra status offline se disponibile
            if self.offline_manager:
                offline_status = self.offline_manager.get_status()
                connection_status = "🟢 Online" if offline_status['online'] else "🔴 Offline"
                print(f"🌐 Stato connessione: {connection_status}")
                if offline_status['queue_size'] > 0:
                    print(f"📤 In coda per sync: {offline_status['queue_size']} elementi")
            
            # Mostra status controllo manuale
            if self.manual_control:
                manual_status = self.manual_control.get_status()
                if manual_status['enabled']:
                    mqtt_status = "🟢" if manual_status['mqtt_available'] else "🔴"
                    print(f"🔓 Controllo manuale: {mqtt_status} {'Remoto+Locale' if manual_status['mqtt_available'] else 'Solo Locale'}")
            
            # Mostra statistiche precedenti se disponibili
            if os.path.exists(os.path.join(Config.LOG_DIRECTORY, "access_log.csv")):
                self.logger.print_stats(7)
        except Exception as e:
            print(f"⚠️ Errore visualizzazione status: {e}")
        
        self._main_loop()
    
    def _main_loop(self):
        """Loop principale di gestione degli accessi"""
        card_count = 0
        
        try:
            print("\n⏳ Sistema in ascolto per card RFID...")
            
            while self.running:
                try:
                    # Aspetta la prossima card da qualsiasi lettore
                    card_info = self.rfid_manager.wait_for_card()
                    
                    if card_info is None:
                        continue
                    
                    # Incrementa il contatore
                    card_count += 1
                    
                    # Mostra le informazioni della card
                    self._display_card_info(card_info, card_count)
                    
                    # Misura il tempo di autenticazione
                    auth_start_time = time.time()
                    
                    # Usa il sistema offline/online per l'autenticazione
                    auth_result = None
                    
                    try:
                        if self.offline_manager:
                            # Usa l'offline manager (gestisce automaticamente online/offline)
                            auth_result = self.offline_manager.handle_card_access(card_info)
                        elif self.mqtt_client and hasattr(self.mqtt_client, 'is_connected') and self.mqtt_client.is_connected:
                            # Fallback diretto a MQTT se offline manager non disponibile
                            auth_result = self.mqtt_client.publish_card_data_and_wait_auth(card_info)
                        else:
                            # Sistema completamente offline
                            print("🔴 Sistema offline - Nessuna connessione disponibile")
                            auth_result = {
                                'authorized': Config.OFFLINE_ALLOW_ACCESS if Config.OFFLINE_MODE_ENABLED else False,
                                'message': 'Sistema offline - Accesso locale',
                                'offline_mode': True,
                                'error': None if (Config.OFFLINE_ALLOW_ACCESS and Config.OFFLINE_MODE_ENABLED) else 'Sistema offline e accessi offline disabilitati'
                            }
                    except Exception as e:
                        print(f"⚠️ Errore durante autenticazione: {e}")
                        # Fallback di emergenza
                        auth_result = {
                            'authorized': Config.OFFLINE_ALLOW_ACCESS if Config.OFFLINE_MODE_ENABLED else False,
                            'message': f'Fallback offline - Errore: {str(e)[:50]}...',
                            'offline_mode': True,
                            'error': str(e) if not (Config.OFFLINE_ALLOW_ACCESS and Config.OFFLINE_MODE_ENABLED) else None
                        }
                    
                    # Fallback di sicurezza finale
                    if auth_result is None:
                        print("❌ Errore sistema autenticazione - Fallback di sicurezza")
                        auth_result = {
                            'authorized': False,
                            'error': 'Errore critico sistema autenticazione',
                            'offline_mode': False
                        }
                    
                    # Calcola il tempo di autenticazione
                    auth_time_ms = int((time.time() - auth_start_time) * 1000)
                    
                    # Mostra il risultato dell'autenticazione
                    self._display_auth_result(auth_result)
                    
                    # Attiva il relè corrispondente solo se autorizzato
                    success_relay = False
                    direction = card_info.get('direction', 'in')
                    
                    if auth_result.get('authorized', False):
                        mode = "OFFLINE" if auth_result.get('offline_mode', False) else "ONLINE"
                        print(f"🔓 Accesso autorizzato ({mode}) per direzione {direction.upper()} - Attivazione relè...")
                        
                        # Debug: mostra relè disponibili
                        if self.relay_manager:
                            available_relays = self.relay_manager.get_active_relays()
                            print(f"🔧 Debug: Relè disponibili: {available_relays}")
                            
                            # Controlla se il relè per questa direzione è disponibile
                            if direction in available_relays:
                                print(f"⚡ Attivazione relè {direction.upper()}...")
                                success_relay = self.relay_manager.activate_relay(direction)
                                if success_relay:
                                    print(f"✅ Relè {direction.upper()} attivato con successo")
                                else:
                                    print(f"❌ Errore attivazione relè {direction.upper()}")
                            else:
                                print(f"⚠️ Relè {direction.upper()} non configurato - usando primo relè disponibile")
                                if available_relays:
                                    first_relay = available_relays[0]
                                    print(f"⚡ Attivazione relè alternativo {first_relay.upper()}...")
                                    success_relay = self.relay_manager.activate_relay(first_relay)
                                    if success_relay:
                                        print(f"✅ Relè alternativo {first_relay.upper()} attivato")
                                    else:
                                        print(f"❌ Errore attivazione relè alternativo {first_relay.upper()}")
                                else:
                                    print("❌ Nessun relè disponibile!")
                        else:
                            print("❌ Relay Manager non disponibile!")
                    else:
                        mode = "OFFLINE" if auth_result.get('offline_mode', False) else "ONLINE"
                        print(f"🔒 Accesso negato ({mode}) per direzione {direction.upper()} - Relè non attivato")
                        reason = auth_result.get('error') or auth_result.get('message', 'Motivo sconosciuto')
                        print(f"❌ Motivo: {reason}")
                        
                        # Debug: anche per accessi negati mostra relè disponibili
                        if self.relay_manager:
                            available_relays = self.relay_manager.get_active_relays()
                            print(f"🔧 Debug: Relè disponibili (non attivati): {available_relays}")
                    
                    # REGISTRA NEI LOG
                    try:
                        log_entry = self.logger.log_access_attempt(
                            card_info=card_info,
                            auth_result=auth_result,
                            relay_success=success_relay,
                            auth_time_ms=auth_time_ms
                        )
                    except Exception as e:
                        print(f"⚠️ Errore logging: {e}")
                    
                    # Riepilogo operazione
                    self._display_operation_summary(True, success_relay, auth_result, direction)
                    
                    print("\n✅ Operazione completata! Sistema pronto per la prossima card...")
                    print("-" * 50)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"⚠️ Errore elaborazione card: {e}")
                    continue
                
        except Exception as e:
            print(f"\n❌ Errore nel loop principale: {e}")
            if self.logger:
                self.logger.log_system_event("main_loop_error", str(e), "error")
            print("🔧 Il sistema continuerà a funzionare...")
            time.sleep(2)
    
    def _display_card_info(self, card_info, card_count):
        """Mostra le informazioni della card letta"""
        direction = card_info.get('direction', 'unknown').upper()
        reader_id = card_info.get('reader_id', 'unknown')
        
        print("\n" + f"🎉 CARD RILEVATA su {direction}! 🎉".center(70))
        print("="*70)
        print(f"📊 Accesso #{card_count}")
        print(f"🔵 Lettore: {reader_id.upper()} (Direzione: {direction})")
        print(f"🆔 ID Numerico: {card_info.get('raw_id')}")
        print(f"🏷️  UID MIFARE: {card_info.get('uid_formatted')}")
        print(f"🔤 ID Esadecimale: {card_info.get('uid_hex')}")
        print(f"📝 Dati Card: {card_info.get('data') or 'Vuoto'}")
        print(f"📏 Lunghezza Dati: {card_info.get('data_length')} caratteri")
        print(f"🕐 Timestamp: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}")
        print(f"🚪 Tornello: {Config.TORNELLO_ID}")
        print("="*70)
    
    def _display_auth_result(self, auth_result):
        """Mostra il risultato dell'autenticazione"""
        authorized = auth_result.get('authorized', False)
        message = auth_result.get('message', '')
        error = auth_result.get('error', '')
        offline_mode = auth_result.get('offline_mode', False)
        
        mode_indicator = "🌐" if not offline_mode else "🔴"
        mode_text = "ONLINE" if not offline_mode else "OFFLINE"
        
        if authorized:
            print(f"🟢 AUTENTICAZIONE RIUSCITA ({mode_indicator} {mode_text})")
            if message:
                print(f"💬 Messaggio: {message}")
        else:
            print(f"🔴 AUTENTICAZIONE FALLITA ({mode_indicator} {mode_text})")
            if error:
                print(f"❌ Errore: {error}")
            elif message:
                print(f"💬 Messaggio: {message}")
    
    def _display_operation_summary(self, mqtt_success, relay_success, auth_result, direction):
        """Mostra il riepilogo delle operazioni"""
        offline_mode = auth_result.get('offline_mode', False)
        mode_text = "OFFLINE" if offline_mode else "ONLINE"
        
        print(f"\n📋 Riepilogo operazioni ({direction.upper()} - {mode_text}):")
        
        if offline_mode:
            mqtt_status = "📤 In coda sync" if mqtt_success else "❌ Errore coda"
        else:
            mqtt_status = "✅ Inviato" if mqtt_success else "❌ Fallito"
        
        auth_status = "✅ Autorizzato" if auth_result.get('authorized', False) else "❌ Negato"
        relay_status = f"✅ Attivato ({direction.upper()})" if relay_success else f"❌ Non attivato ({direction.upper()})"
        
        print(f"   📡 MQTT: {mqtt_status}")
        if Config.AUTH_ENABLED or offline_mode:
            print(f"   🔐 Auth: {auth_status}")
        print(f"   ⚡ Relè: {relay_status}")
        
        if auth_result.get('authorized', False):
            if relay_success:
                if offline_mode:
                    print(f"   🎯 Accesso {direction.upper()} offline completato - Sync al ripristino connessione")
                else:
                    print(f"   🎯 Accesso {direction.upper()} completato con successo!")
            else:
                print(f"   ⚠️ Accesso autorizzato ma relè {direction.upper()} non attivato")
        else:
            print("   🔒 Accesso negato o errore sistema")
    
    def get_system_status(self):
        """Restituisce lo stato di tutti i componenti"""
        status = {
            'logger': bool(self.logger),
            'running': self.running,
            'config': {
                'tornello_id': Config.TORNELLO_ID,
                'bidirectional_mode': Config.BIDIRECTIONAL_MODE,
                'auth_enabled': Config.AUTH_ENABLED,
                'offline_enabled': Config.OFFLINE_MODE_ENABLED,
                'manual_enabled': Config.MANUAL_OPEN_ENABLED,
                'log_directory': Config.LOG_DIRECTORY
            }
        }
        
        # Status RFID Manager
        if self.rfid_manager:
            status['rfid_manager'] = self.rfid_manager.get_reader_status()
            status['config']['active_readers'] = self.rfid_manager.get_active_readers()
        else:
            status['rfid_manager'] = None
            status['config']['active_readers'] = []
        
        # Status Relay Manager
        if self.relay_manager:
            status['relay_manager'] = self.relay_manager.get_all_status()
            status['config']['active_relays'] = self.relay_manager.get_active_relays()
        else:
            status['relay_manager'] = None
            status['config']['active_relays'] = []
        
        # Status MQTT
        if self.mqtt_client:
            status['mqtt'] = self.mqtt_client.get_status()
        else:
            status['mqtt'] = None
        
        # Status Offline Manager
        if self.offline_manager:
            status['offline_manager'] = self.offline_manager.get_status()
        else:
            status['offline_manager'] = None
        
        # Status Manual Control
        if self.manual_control:
            status['manual_control'] = self.manual_control.get_status()
        else:
            status['manual_control'] = None
        
        return status
    
    def shutdown(self):
        """Spegne il sistema in modo pulito"""
        print("\n🛑 Spegnimento del sistema bidirezionale...")
        self.running = False
        
        # Log di sistema
        if self.logger:
            self.logger.log_system_event("system_shutdown", "Spegnimento sistema bidirezionale in corso")
            
            # Mostra statistiche finali
            try:
                print("\n📊 Statistiche finali della sessione:")
                self.logger.print_stats(1)  # Statistiche di oggi
            except Exception as e:
                print(f"⚠️ Errore statistiche: {e}")
        
        # Ferma i thread RFID
        if self.rfid_manager:
            try:
                self.rfid_manager.stop_reading()
                if self.logger:
                    self.logger.log_system_event("rfid_manager_stop", "Thread RFID fermati")
            except Exception as e:
                print(f"⚠️ Errore stop RFID Manager: {e}")
        
        # Ferma Controllo Manuale
        if self.manual_control:
            try:
                self.manual_control.cleanup()
                if self.logger:
                    manual_stats = self.manual_control.get_stats()
                    self.logger.log_system_event("manual_control_stop", f"Controllo manuale fermato - {manual_stats['manual_opens']} aperture manuali eseguite")
            except Exception as e:
                print(f"⚠️ Errore stop Controllo Manuale: {e}")
        
        # Ferma Offline Manager
        if self.offline_manager:
            try:
                # Forza un ultimo sync se possibile
                if self.offline_manager.is_online and self.offline_manager.offline_queue.qsize() > 0:
                    print("📤 Tentativo sync finale...")
                    self.offline_manager.force_sync()
                
                self.offline_manager.cleanup()
                if self.logger:
                    queue_size = self.offline_manager.offline_queue.qsize()
                    self.logger.log_system_event("offline_manager_stop", f"Offline Manager fermato - {queue_size} elementi salvati per sync futuro")
            except Exception as e:
                print(f"⚠️ Errore stop Offline Manager: {e}")
        
        # Spegne MQTT
        if self.mqtt_client:
            try:
                self.mqtt_client.publish_status("offline")
                self.mqtt_client.disconnect()
                if self.logger:
                    self.logger.log_system_event("mqtt_disconnect", "MQTT disconnesso")
            except Exception as e:
                print(f"⚠️ Errore disconnect MQTT: {e}")
        
        # Spegne tutti i relè
        if self.relay_manager:
            try:
                self.relay_manager.reset_all_to_initial_state()
                self.relay_manager.cleanup()
                if self.logger:
                    self.logger.log_system_event("relay_manager_stop", "Tutti i relè ripristinati e GPIO puliti")
            except Exception as e:
                print(f"⚠️ Errore cleanup relè: {e}")
        
        # Pulisce i lettori RFID
        if self.rfid_manager:
            try:
                self.rfid_manager.cleanup()
                if self.logger:
                    self.logger.log_system_event("rfid_manager_cleanup", "RFID Manager pulito")
            except Exception as e:
                print(f"⚠️ Errore cleanup RFID Manager: {e}")
        
        # Log finale
        if self.logger:
            self.logger.log_system_event("system_stop", "Sistema bidirezionale spento correttamente")
        
        print("👋 Sistema bidirezionale spento correttamente!")
        sys.exit(0)

def print_startup_info():
    """Stampa informazioni di avvio del sistema"""
    print("📡 Sistema di Controllo Accessi RFID Bidirezionale")
    print("🔧 Configurazione automatica:")
    
    if Config.BIDIRECTIONAL_MODE:
        print("   🔄 Modalità: BIDIREZIONALE")
        readers = []
        if Config.RFID_IN_ENABLE:
            readers.append("IN")
        if Config.RFID_OUT_ENABLE:
            readers.append("OUT")
        print(f"   📖 Lettori attivi: {', '.join(readers) if readers else 'Nessuno'}")
        
        relays = []
        if Config.RELAY_IN_ENABLE:
            relays.append("IN")
        if Config.RELAY_OUT_ENABLE:
            relays.append("OUT")
        print(f"   ⚡ Relè attivi: {', '.join(relays) if relays else 'Nessuno'}")
    else:
        print("   ➡️ Modalità: UNIDIREZIONALE")
        if Config.RFID_IN_ENABLE:
            print("   📖 Lettore: IN")
        if Config.RELAY_IN_ENABLE:
            print("   ⚡ Relè: IN")
    
    # Mostra info modalità offline
    if Config.OFFLINE_MODE_ENABLED:
        print("   🌐 Fallback Offline: ATTIVO")
        print(f"      └─ Accesso offline: {'Consentito' if Config.OFFLINE_ALLOW_ACCESS else 'Negato'}")
    else:
        print("   🌐 Fallback Offline: DISATTIVO")
    
    # Mostra info controllo manuale
    if Config.MANUAL_OPEN_ENABLED:
        print("   🔓 Controllo manuale: ATTIVO")
        print(f"      └─ Auth richiesta: {'Sì' if Config.MANUAL_OPEN_AUTH_REQUIRED else 'No'}")
    else:
        print("   🔓 Controllo manuale: DISATTIVO")
    
    print("")

def main():
    """Funzione principale"""
    try:
        # Verifica che stiamo eseguendo come root/sudo
        if not check_permissions():
            print("❌ Questo programma deve essere eseguito con sudo")
            print("💡 Usa: sudo python3 main.py")
            sys.exit(1)
        
        # Mostra info di avvio
        print_startup_info()
        
        # Crea e avvia il sistema
        system = BidirectionalAccessSystem()
        system.run()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interruzione da tastiera")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore critico: {e}")
        import traceback
        traceback.print_exc()
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