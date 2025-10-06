#!/usr/bin/env python3
"""
Controllo apertura manuale - Versione corretta
"""
import json
import time
import threading
from datetime import datetime
from config import Config

class ManualControl:
    """Controllo manuale del tornello"""
    
    def __init__(self, mqtt_client=None, relay_manager=None, logger=None):
        self.mqtt_client = mqtt_client
        self.relay_manager = relay_manager
        self.logger = logger
        self.is_enabled = Config.MANUAL_OPEN_ENABLED
        
        self._lock = threading.Lock()
        
        # Statistiche
        self.stats = {
            'manual_opens': 0,
            'last_manual_open': None,
            'failed_attempts': 0
        }
    
    def initialize(self):
        """Inizializza controllo manuale"""
        if not self.is_enabled:
            print("Controllo manuale disabilitato")
            return False
        
        try:
            # Sottoscrivi MQTT se disponibile
            if self.mqtt_client and self.mqtt_client.is_connected:
                manual_topic = Config.get_manual_open_topic()
                self.mqtt_client.client.subscribe(manual_topic, qos=1)
                self.mqtt_client.client.message_callback_add(manual_topic, self._on_manual_command)
                print(f"✅ Sottoscritto topic manual: {manual_topic}")
            
            print("✅ Controllo manuale inizializzato")
            return True
            
        except Exception as e:
            print(f"❌ Errore controllo manuale: {e}")
            return False
    
    def _on_manual_command(self, client, userdata, msg):
        """Callback comandi MQTT"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            print(f"🔓 Comando manuale ricevuto: {payload.get('command_id', 'N/A')}")
            self._process_manual_command(payload)
        except Exception as e:
            print(f"❌ Errore elaborazione comando: {e}")
    
    def _process_manual_command(self, payload):
        """Elabora comando manuale"""
        try:
            command_id = payload.get('command_id', f"manual_{int(time.time())}")
            direction = payload.get('direction', 'in')
            duration = payload.get('duration', Config.RELAY_IN_ACTIVE_TIME)
            user_id = payload.get('user_id', 'unknown')
            auth_token = payload.get('auth_token', '')
            
            # Verifica autorizzazione
            if Config.MANUAL_OPEN_AUTH_REQUIRED:
                if not self._verify_auth(auth_token):
                    self._send_response(command_id, False, "Auth fallita", user_id)
                    return
            
            # Esegui apertura
            success = self._execute_open(direction, duration, user_id)
            
            # Risposta
            if success:
                self._send_response(command_id, True, "Apertura OK", user_id)
            else:
                self._send_response(command_id, False, "Errore apertura", user_id)
            
        except Exception as e:
            print(f"❌ Errore processo comando: {e}")
            self._send_response(
                payload.get('command_id', 'unknown'), 
                False, 
                f"Errore: {str(e)}", 
                payload.get('user_id', 'unknown')
            )
    
    def _verify_auth(self, token):
        """Verifica token"""
        if not token or len(token) < 8:
            return False
        return True
    
    def _execute_open(self, direction, duration, user_id):
        """Esegue apertura manuale"""
        try:
            with self._lock:
                if not self.relay_manager:
                    print("❌ Relay Manager non disponibile")
                    return False
                
                available_relays = self.relay_manager.get_active_relays()
                
                if direction not in available_relays:
                    if available_relays:
                        direction = available_relays[0]
                        print(f"⚠️ Uso relè alternativo: {direction}")
                    else:
                        print("❌ Nessun relè disponibile")
                        return False
                
                print(f"🔓 Apertura manuale: {direction.upper()}, {duration}s, user: {user_id}")
                
                # Attiva relè (il nuovo controller gestisce già i thread duplicati)
                success = self.relay_manager.activate_relay(direction, duration)
                
                if success:
                    self.stats['manual_opens'] += 1
                    self.stats['last_manual_open'] = datetime.now().isoformat()
                    
                    print(f"✅ Apertura manuale completata")
                    
                    if self.logger:
                        self.logger.log_system_event(
                            "manual_open_success",
                            f"Apertura manuale - User: {user_id}, Dir: {direction}, Durata: {duration}s"
                        )
                    
                    return True
                else:
                    self.stats['failed_attempts'] += 1
                    print(f"❌ Errore attivazione relè")
                    return False
                
        except Exception as e:
            print(f"❌ Errore esecuzione apertura: {e}")
            self.stats['failed_attempts'] += 1
            return False
    
    def _send_response(self, command_id, success, message, user_id):
        """Invia risposta MQTT"""
        if not self.mqtt_client or not self.mqtt_client.is_connected:
            print("⚠️ MQTT non disponibile per risposta")
            return
        
        try:
            response_topic = Config.get_manual_response_topic()
            
            response_payload = {
                'command_id': command_id,
                'success': success,
                'message': message,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'tornello_id': Config.TORNELLO_ID
            }
            
            json_payload = json.dumps(response_payload, ensure_ascii=False)
            
            result = self.mqtt_client.client.publish(response_topic, json_payload, qos=1)
            
            if result.rc == 0:
                print(f"📤 Risposta inviata: {success}")
            else:
                print(f"❌ Errore invio risposta: {result.rc}")
                
        except Exception as e:
            print(f"❌ Errore invio risposta: {e}")
    
    def manual_open_local(self, direction='in', duration=None, user_id='local'):
        """Apertura manuale locale"""
        if not self.is_enabled:
            print("❌ Controllo manuale disabilitato")
            return False
        
        duration = duration or Config.RELAY_IN_ACTIVE_TIME
        
        print(f"🔓 Apertura locale: {direction}, {duration}s")
        
        success = self._execute_open(direction, duration, user_id)
        
        if success:
            print("✅ Apertura locale completata")
        else:
            print("❌ Apertura locale fallita")
        
        return success
    
    def get_status(self):
        """Status controllo manuale"""
        return {
            'enabled': self.is_enabled,
            'mqtt_available': self.mqtt_client is not None and self.mqtt_client.is_connected,
            'relay_available': self.relay_manager is not None,
            'stats': self.stats.copy(),
            'config': {
                'auth_required': Config.MANUAL_OPEN_AUTH_REQUIRED,
                'timeout': Config.MANUAL_OPEN_TIMEOUT,
                'topic': Config.get_manual_open_topic() if Config.MANUAL_OPEN_ENABLED else None,
                'response_topic': Config.get_manual_response_topic() if Config.MANUAL_OPEN_ENABLED else None
            }
        }
    
    def get_stats(self):
        """Statistiche"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistiche"""
        with self._lock:
            self.stats = {
                'manual_opens': 0,
                'last_manual_open': None,
                'failed_attempts': 0
            }
    
    def cleanup(self):
        """Cleanup"""
        try:
            print("🧹 Cleanup controllo manuale...")
            
            if self.mqtt_client and self.mqtt_client.is_connected:
                manual_topic = Config.get_manual_open_topic()
                self.mqtt_client.client.unsubscribe(manual_topic)
            
        except Exception as e:
            print(f"⚠️ Errore cleanup controllo manuale: {e}")