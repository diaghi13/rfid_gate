#!/usr/bin/env python3
"""
Sistema controllo accessi RFID - Versione semplificata
"""
import sys
import time
import signal
from datetime import datetime

from config import Config
from rfid_manager import RFIDManager
from relay_manager import RelayManager
from mqtt_client import MQTTClient
from logger import AccessLogger
from offline_manager import OfflineManager
from manual_control import ManualControl

class AccessControlSystem:
    """Sistema principale controllo accessi"""
    
    def __init__(self):
        self.rfid_manager = None
        self.relay_manager = None
        self.mqtt_client = None
        self.logger = None
        self.offline_manager = None
        self.manual_control = None
        self.running = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        print("\n🛑 Interruzione ricevuta...")
        self.shutdown()
    
    def initialize(self):
        """Inizializza sistema"""
        print("🚀 Avvio sistema controllo accessi...")
        
        # Valida config
        errors = Config.validate_config()
        if errors:
            print("❌ Errori configurazione:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # Logger
        try:
            self.logger = AccessLogger(Config.LOG_DIRECTORY)
            self.logger.log_system_event("system_start", "Sistema avviato")
        except Exception as e:
            print(f"❌ Errore Logger: {e}")
            return False
        
        # RFID Manager
        try:
            self.rfid_manager = RFIDManager()
            if not self.rfid_manager.initialize():
                return False
        except Exception as e:
            print(f"❌ Errore RFID: {e}")
            return False
        
        # Relay Manager
        try:
            self.relay_manager = RelayManager()
            if not self.relay_manager.initialize():
                return False
        except Exception as e:
            print(f"❌ Errore Relay: {e}")
            return False
        
        # MQTT Client (opzionale)
        try:
            self.mqtt_client = MQTTClient()
            if self.mqtt_client.initialize():
                if self.mqtt_client.connect():
                    self.mqtt_client.publish_status("online")
                    print("✅ MQTT connesso")
                else:
                    print("⚠️ MQTT non connesso")
            else:
                print("⚠️ MQTT non inizializzato")
        except Exception as e:
            print(f"⚠️ MQTT error: {e}")
        
        # Offline Manager
        try:
            self.offline_manager = OfflineManager(self.mqtt_client, self.logger)
            if self.offline_manager.initialize():
                print("✅ Offline Manager attivo")
            else:
                print("⚠️ Offline Manager non attivo")
        except Exception as e:
            print(f"⚠️ Offline Manager error: {e}")
        
        # Manual Control
        try:
            self.manual_control = ManualControl(self.mqtt_client, self.relay_manager, self.logger)
            if self.manual_control.initialize():
                print("✅ Controllo manuale attivo")
            else:
                print("⚠️ Controllo manuale non attivo")
        except Exception as e:
            print(f"⚠️ Manual Control error: {e}")
        
        print("✅ Inizializzazione completata")
        return True
    
    def run(self):
        """Avvia sistema"""
        if not self.initialize():
            print("❌ Inizializzazione fallita")
            return
        
        # Avvia lettura RFID
        if not self.rfid_manager.start_reading():
            print("❌ Errore avvio RFID")
            return
        
        self.running = True
        
        print("\n" + "="*60)
        print("🎯 SISTEMA CONTROLLO ACCESSI ATTIVO")
        print("="*60)
        
        # Info sistema
        active_readers = self.rfid_manager.get_active_readers()
        active_relays = self.relay_manager.get_active_relays()
        
        print(f"📱 Lettori RFID: {', '.join([r.upper() for r in active_readers])}")
        print(f"⚡ Relè: {', '.join([r.upper() for r in active_relays])}")
        
        # Status connessione
        if self.offline_manager:
            status = self.offline_manager.get_status()
            conn_status = "🟢 Online" if status['online'] else "🔴 Offline"
            print(f"🌐 Connessione: {conn_status}")
            if status['queue_size'] > 0:
                print(f"📤 In coda sync: {status['queue_size']}")
        
        print("⏹️ Premi Ctrl+C per uscire")
        print("-"*60)
        
        self._main_loop()
    
    def _main_loop(self):
        """Loop principale"""
        card_count = 0
        
        try:
            print("⏳ In attesa card RFID...")
            
            while self.running:
                try:
                    # Attendi prossima card
                    card_info = self.rfid_manager.wait_for_card()
                    
                    if card_info is None:
                        continue
                    
                    card_count += 1
                    
                    # Info card
                    direction = card_info.get('direction', 'unknown').upper()
                    uid = card_info.get('uid_formatted', 'N/A')
                    
                    print(f"\n🎉 Card #{card_count}: {uid} ({direction})")
                    
                    # Autenticazione
                    auth_start = time.time()
                    
                    if self.offline_manager:
                        auth_result = self.offline_manager.handle_card_access(card_info)
                    else:
                        # Fallback diretto
                        if self.mqtt_client and self.mqtt_client.is_connected:
                            auth_result = self.mqtt_client.publish_card_data_and_wait_auth(card_info)
                        else:
                            auth_result = {
                                'authorized': Config.OFFLINE_ALLOW_ACCESS if Config.OFFLINE_MODE_ENABLED else False,
                                'message': 'Sistema offline',
                                'offline_mode': True
                            }
                    
                    auth_time = int((time.time() - auth_start) * 1000)
                    
                    # Risultato auth
                    authorized = auth_result.get('authorized', False)
                    offline_mode = auth_result.get('offline_mode', False)
                    message = auth_result.get('message', auth_result.get('error', ''))
                    
                    mode_text = "OFFLINE" if offline_mode else "ONLINE"
                    auth_text = "✅ AUTORIZZATO" if authorized else "❌ NEGATO"
                    print(f"🔐 {auth_text} ({mode_text}) - {auth_time}ms")
                    if message:
                        print(f"💬 {message}")
                    
                    # Attiva relè se autorizzato
                    relay_success = False
                    if authorized:
                        direction_key = card_info.get('direction', 'in')
                        available_relays = self.relay_manager.get_active_relays()
                        
                        if direction_key in available_relays:
                            relay_success = self.relay_manager.activate_relay(direction_key)
                            if relay_success:
                                print(f"⚡ Relè {direction_key.upper()} attivato")
                            else:
                                print(f"❌ Errore relè {direction_key.upper()}")
                        elif available_relays:
                            # Usa primo relè disponibile
                            relay_key = available_relays[0]
                            relay_success = self.relay_manager.activate_relay(relay_key)
                            if relay_success:
                                print(f"⚡ Relè {relay_key.upper()} attivato")
                            else:
                                print(f"❌ Errore relè {relay_key.upper()}")
                        else:
                            print("❌ Nessun relè disponibile")
                    else:
                        print("🔒 Accesso negato - Relè non attivato")
                    
                    # Log accesso
                    if self.logger:
                        self.logger.log_access_attempt(
                            card_info=card_info,
                            auth_result=auth_result,
                            relay_success=relay_success,
                            auth_time_ms=auth_time
                        )
                    
                    # Riepilogo
                    print(f"📊 Riepilogo: Auth={auth_text}, Relè={'✅' if relay_success else '❌'}")
                    print("-"*50)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"⚠️ Errore elaborazione card: {e}")
                    continue
                
        except Exception as e:
            print(f"❌ Errore loop principale: {e}")
    
    def shutdown(self):
        """Spegne sistema"""
        print("🛑 Spegnimento sistema...")
        self.running = False
        
        if self.logger:
            self.logger.log_system_event("system_shutdown", "Spegnimento sistema")
        
        if self.rfid_manager:
            self.rfid_manager.stop_reading()
            self.rfid_manager.cleanup()
        
        if self.manual_control:
            self.manual_control.cleanup()
        
        if self.offline_manager:
            if self.offline_manager.is_online and not self.offline_manager.offline_queue.empty():
                print("📤 Sync finale...")
                self.offline_manager.force_sync()
            self.offline_manager.cleanup()
        
        if self.mqtt_client:
            self.mqtt_client.publish_status("offline")
            self.mqtt_client.disconnect()
        
        if self.relay_manager:
            self.relay_manager.reset_all_to_initial_state()
            self.relay_manager.cleanup()
        
        if self.logger:
            self.logger.log_system_event("system_stop", "Sistema spento")
        
        print("👋 Sistema spento!")
        sys.exit(0)

def main():
    """Funzione principale"""
    try:
        # Verifica permessi
        import os
        if os.geteuid() != 0:
            print("❌ Eseguire con sudo")
            print("💡 sudo python3 main.py")
            sys.exit(1)
        
        # Avvia sistema
        system = AccessControlSystem()
        system.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Interruzione tastiera")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Errore critico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()