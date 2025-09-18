#!/usr/bin/env python3
"""
Modulo per il controllo dell'apertura manuale del tornello
"""

import json
import time
import threading
from datetime import datetime
from config import Config

class ManualControl:
    """Classe per gestire l'apertura manuale del tornello"""
    
    def __init__(self, mqtt_client=None, relay_manager=None, logger=None):
        self.mqtt_client = mqtt_client
        self.relay_manager = relay_manager
        self.logger = logger
        self.is_enabled = Config.MANUAL_OPEN_ENABLED
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistiche
        self.stats = {
            'manual_opens': 0,
            'last_manual_open': None,
            'failed_attempts': 0
        }
    
    def initialize(self):
        """Inizializza il controllo manuale"""
        if not self.is_enabled:
            print("🔓 Controllo manuale disabilitato")
            return False
        
        try:
            print("🔓 Inizializzazione controllo manuale...")
            
            # Sottoscrivi al topic dei comandi manuali se MQTT disponibile
            if self.mqtt_client and self.mqtt_client.is_connected:
                manual_topic = Config.get_manual_open_topic()
                self.mqtt_client.client.subscribe(manual_topic, qos=1)
                print(f"📬 Sottoscritto al topic: {manual_topic}")
                
                # Registra il callback personalizzato
                self.mqtt_client.client.message_callback_add(manual_topic, self._on_manual_command)
            
            print("✅ Controllo manuale inizializzato")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione controllo manuale: {e}")
            return False
    
    def _on_manual_command(self, client, userdata, msg):
        """Callback per i comandi di apertura manuale via MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            print(f"🔓 Comando apertura manuale ricevuto su {topic}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            # Elabora il comando
            self._process_manual_command(payload)
            
        except Exception as e:
            print(f"❌ Errore elaborazione comando manuale: {e}")
            if self.logger:
                self.logger.log_system_event("manual_command_error", str(e), "error")
    
    def _process_manual_command(self, payload):
        """Elabora un comando di apertura manuale"""
        try:
            # Estrai parametri del comando
            command_id = payload.get('command_id', f"manual_{int(time.time())}")
            direction = payload.get('direction', 'in')
            duration = payload.get('duration', Config.RELAY_IN_ACTIVE_TIME)
            user_id = payload.get('user_id', 'unknown')
            auth_token = payload.get('auth_token', '')
            
            print(f"🔓 Elaborazione comando manuale:")
            print(f"   ID: {command_id}")
            print(f"   Direzione: {direction}")
            print(f"   Durata: {duration}s")
            print(f"   Utente: {user_id}")
            
            # Verifica autorizzazione se richiesta
            if Config.MANUAL_OPEN_AUTH_REQUIRED:
                if not self._verify_manual_auth(auth_token, user_id):
                    self._send_manual_response(command_id, False, "Autorizzazione fallita", user_id)
                    return
            
            # Esegui apertura
            success = self._execute_manual_open(direction, duration, command_id, user_id)
            
            # Invia risposta
            if success:
                self._send_manual_response(command_id, True, "Apertura eseguita con successo", user_id)
            else:
                self._send_manual_response(command_id, False, "Errore durante apertura", user_id)
            
        except Exception as e:
            print(f"❌ Errore elaborazione comando manuale: {e}")
            self._send_manual_response(
                payload.get('command_id', 'unknown'), 
                False, 
                f"Errore: {str(e)}", 
                payload.get('user_id', 'unknown')
            )
    
    def _verify_manual_auth(self, auth_token, user_id):
        """Verifica l'autorizzazione per l'apertura manuale"""
        # Implementazione semplice - in produzione usare sistema auth più robusto
        # Per ora accetta qualsiasi token non vuoto
        if not auth_token:
            print("❌ Token autorizzazione mancante")
            return False
        
        if len(auth_token) < 8:
            print("❌ Token autorizzazione troppo corto")
            return False
        
        print("✅ Autorizzazione manuale verificata")
        return True
    
    def _execute_manual_open(self, direction, duration, command_id, user_id):
        """Esegue l'apertura manuale del relè"""
        try:
            with self._lock:
                if not self.relay_manager:
                    print("❌ Relay Manager non disponibile")
                    return False
                
                # Verifica che il relè per la direzione sia disponibile
                available_relays = self.relay_manager.get_active_relays()
                
                if direction not in available_relays:
                    if available_relays:
                        direction = available_relays[0]  # Usa il primo disponibile
                        print(f"⚠️ Direzione richiesta non disponibile, uso {direction}")
                    else:
                        print("❌ Nessun relè disponibile")
                        return False
                
                print(f"🔓 APERTURA MANUALE - Direzione: {direction.upper()}, Durata: {duration}s")
                
                # Attiva il relè
                success = self.relay_manager.activate_relay(direction, duration)
                
                if success:
                    # Aggiorna statistiche
                    self.stats['manual_opens'] += 1
                    self.stats['last_manual_open'] = datetime.now().isoformat()
                    
                    # Log evento
                    if self.logger:
                        self.logger.log_system_event(
                            "manual_open_success",
                            f"Apertura manuale - User: {user_id}, Dir: {direction}, Durata: {duration}s, ID: {command_id}"
                        )
                    
                    print(f"✅ Apertura manuale eseguita con successo")
                    return True
                else:
                    self.stats['failed_attempts'] += 1
                    print(f"❌ Errore attivazione relè per apertura manuale")
                    return False
                
        except Exception as e:
            print(f"❌ Errore esecuzione apertura manuale: {e}")
            self.stats['failed_attempts'] += 1
            return False
    
    def _send_manual_response(self, command_id, success, message, user_id):
        """Invia risposta al comando di apertura manuale"""
        if not self.mqtt_client or not self.mqtt_client.is_connected:
            print("⚠️ MQTT non disponibile per inviare risposta")
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
            
            if result.rc == 0:  # MQTT_ERR_SUCCESS
                print(f"📤 Risposta apertura manuale inviata: {success}")
            else:
                print(f"❌ Errore invio risposta apertura manuale: {result.rc}")
                
        except Exception as e:
            print(f"❌ Errore invio risposta apertura manuale: {e}")
    
    def manual_open_local(self, direction='in', duration=None, user_id='local'):
        """Apertura manuale locale (senza MQTT)"""
        if not self.is_enabled:
            print("❌ Controllo manuale disabilitato")
            return False
        
        duration = duration or Config.RELAY_IN_ACTIVE_TIME
        command_id = f"local_{int(time.time())}"
        
        print(f"🔓 APERTURA MANUALE LOCALE")
        print(f"   Direzione: {direction}")
        print(f"   Durata: {duration}s")
        print(f"   Utente: {user_id}")
        
        success = self._execute_manual_open(direction, duration, command_id, user_id)
        
        if success:
            print("✅ Apertura manuale locale eseguita")
        else:
            print("❌ Apertura manuale locale fallita")
        
        return success
    
    def get_status(self):
        """Restituisce lo status del controllo manuale"""
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
        """Restituisce le statistiche dell'apertura manuale"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Resetta le statistiche"""
        with self._lock:
            self.stats = {
                'manual_opens': 0,
                'last_manual_open': None,
                'failed_attempts': 0
            }
        print("📊 Statistiche apertura manuale resettate")
    
    def cleanup(self):
        """Cleanup delle risorse"""
        try:
            print("🧹 Cleanup controllo manuale...")
            
            # Unsubscribe dai topic MQTT se necessario
            if self.mqtt_client and self.mqtt_client.is_connected:
                manual_topic = Config.get_manual_open_topic()
                self.mqtt_client.client.unsubscribe(manual_topic)
            
            print("🧹 Controllo manuale cleanup completato")
            
        except Exception as e:
            print(f"⚠️ Errore cleanup controllo manuale: {e}")