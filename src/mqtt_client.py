#!/usr/bin/env python3
"""
Client MQTT per l'invio dei dati delle card RFID
Supporta connessioni TLS sicure
"""

import json
import time
import ssl
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from config import Config

class MQTTClient:
    """Classe per gestire la comunicazione MQTT con autenticazione server"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_retries = 3
        
        # Sistema di autenticazione
        self.auth_responses = {}  # Dizionario per memorizzare le risposte di auth
        self.auth_lock = threading.Lock()
        self.pending_auths = {}  # Richieste di auth in attesa
    
    def initialize(self):
        """Inizializza il client MQTT"""
        try:
            print("🌐 Configurazione client MQTT...")
            
            # Crea il client MQTT
            self.client = mqtt.Client()
            
            # Configura autenticazione
            if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
                self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)
                print(f"🔐 Autenticazione configurata per: {Config.MQTT_USERNAME}")
            
            # Configura TLS se richiesto
            if Config.MQTT_USE_TLS:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.client.tls_set_context(context)
                print("🔒 TLS configurato")
            
            # Imposta i callback
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            self.client.on_message = self._on_message
            self.client.on_log = self._on_log
            
            print("✅ Client MQTT inizializzato")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione MQTT: {e}")
            return False
    
    def connect(self):
        """Connette al broker MQTT"""
        if not self.client:
            print("❌ Client MQTT non inizializzato")
            return False
        
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔌 Tentativo connessione {attempt}/{self.max_retries} a {Config.MQTT_BROKER}:{Config.MQTT_PORT}...")
                
                self.client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
                self.client.loop_start()
                
                # Aspetta la connessione
                timeout = 10
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.is_connected:
                    print("✅ Connesso al broker MQTT!")
                    return True
                else:
                    print(f"⏱️ Timeout connessione (tentativo {attempt})")
                    
            except Exception as e:
                print(f"❌ Errore connessione tentativo {attempt}: {e}")
            
            if attempt < self.max_retries:
                print(f"⏳ Aspetto 3 secondi prima del prossimo tentativo...")
                time.sleep(3)
        
        print("❌ Impossibile connettersi al broker MQTT")
        return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback per la connessione MQTT"""
        if rc == 0:
            self.is_connected = True
            print("🟢 MQTT: Connesso al broker!")
            
            # Sottoscrive al topic di autenticazione se abilitata
            if Config.AUTH_ENABLED:
                auth_topic = Config.get_auth_response_topic()
                client.subscribe(auth_topic, qos=1)
                print(f"📬 Sottoscritto al topic: {auth_topic}")
        else:
            self.is_connected = False
            error_messages = {
                1: "Versione protocollo incorretta",
                2: "Client ID non valido",
                3: "Server non disponibile",
                4: "Username/password errati",
                5: "Non autorizzato"
            }
            error_msg = error_messages.get(rc, f"Errore sconosciuto ({rc})")
            print(f"🔴 MQTT: Errore connessione - {error_msg}")
    
    def _on_message(self, client, userdata, msg):
        """Callback per i messaggi ricevuti"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            print(f"📬 Messaggio ricevuto su {topic}")
            
            # Gestisce risposte di autenticazione
            if topic == Config.get_auth_response_topic():
                self._handle_auth_response(payload)
            
        except Exception as e:
            print(f"❌ Errore elaborazione messaggio: {e}")
    
    def _handle_auth_response(self, payload):
        """Gestisce le risposte di autenticazione dal server"""
        try:
            card_uid = payload.get('card_uid')
            authorized = payload.get('authorized', False)
            message = payload.get('message', '')
            
            if card_uid:
                with self.auth_lock:
                    self.auth_responses[card_uid] = {
                        'authorized': authorized,
                        'message': message,
                        'timestamp': time.time()
                    }
                
                status = "✅ AUTORIZZATO" if authorized else "❌ NEGATO"
                print(f"🔐 Risposta auth per {card_uid}: {status}")
                if message:
                    print(f"💬 Messaggio: {message}")
            
        except Exception as e:
            print(f"❌ Errore gestione risposta auth: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback per la disconnessione MQTT"""
        self.is_connected = False
        if rc != 0:
            print("🟡 MQTT: Disconnessione inaspettata")
        else:
            print("🟡 MQTT: Disconnesso dal broker")
    
    def _on_publish(self, client, userdata, mid):
        """Callback per la pubblicazione MQTT"""
        print(f"📤 MQTT: Messaggio inviato (ID: {mid})")
    
    def _on_log(self, client, userdata, level, buf):
        """Callback per i log MQTT (opzionale, per debug)"""
        # Decommentare per vedere i log dettagliati
        # print(f"🐛 MQTT Log: {buf}")
        pass
    
    def publish_card_data_and_wait_auth(self, card_info):
        """
        Pubblica i dati della card e aspetta l'autorizzazione dal server
        Args: card_info (dict) - Informazioni della card
        Returns: dict - Risultato dell'autenticazione
        """
        if not self.is_connected:
            print("❌ MQTT non connesso, impossibile inviare dati")
            return {'authorized': False, 'error': 'MQTT disconnesso'}
        
        card_uid = card_info.get('uid_formatted')
        
        # Se l'autenticazione è disabilitata, autorizza sempre
        if not Config.AUTH_ENABLED:
            print("🔓 Autenticazione disabilitata - Accesso automatico")
            self.publish_card_data(card_info)
            return {'authorized': True, 'message': 'Autenticazione disabilitata'}
        
        try:
            print(f"🔐 Richiesta autenticazione per card: {card_uid}")
            
            # Rimuove eventuali risposte precedenti
            with self.auth_lock:
                if card_uid in self.auth_responses:
                    del self.auth_responses[card_uid]
            
            # Pubblica la richiesta di autenticazione
            if not self.publish_card_data(card_info):
                return {'authorized': False, 'error': 'Errore invio richiesta'}
            
            # Aspetta la risposta del server
            print(f"⏳ Attendo risposta server (timeout: {Config.AUTH_TIMEOUT}s)...")
            
            start_time = time.time()
            while (time.time() - start_time) < Config.AUTH_TIMEOUT:
                with self.auth_lock:
                    if card_uid in self.auth_responses:
                        response = self.auth_responses[card_uid]
                        del self.auth_responses[card_uid]  # Pulisce la risposta
                        return response
                
                time.sleep(0.1)  # Controlla ogni 100ms
            
            # Timeout scaduto
            print("⏰ Timeout autenticazione scaduto")
            return {'authorized': False, 'error': 'Timeout autenticazione'}
            
        except Exception as e:
            print(f"❌ Errore processo autenticazione: {e}")
            return {'authorized': False, 'error': str(e)}
    def publish_card_data(self, card_info):
        """
        Pubblica i dati della card sul topic MQTT
        Args: card_info (dict) - Informazioni della card
        """
        if not self.is_connected:
            print("❌ MQTT non connesso, impossibile inviare dati")
            return False
        
        try:
            # Prepara il topic
            topic = Config.get_mqtt_topic("badge")
            
            # Prepara il payload
            payload = {
                "card_uid": card_info.get('uid_formatted'),
                "identificativo_tornello": Config.TORNELLO_ID,
                "direzione": Config.DIREZIONE,
                "timestamp": datetime.now().isoformat(),
                "raw_id": str(card_info.get('raw_id')),
                "card_data": card_info.get('data'),
                "hex_id": card_info.get('uid_hex'),
                "auth_required": Config.AUTH_ENABLED
            }
            
            # Converte in JSON
            json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
            
            print(f"\n📡 Invio dati MQTT:")
            print(f"📍 Topic: {topic}")
            print(f"📦 Payload:")
            print(json_payload)
            
            # Pubblica il messaggio
            result = self.client.publish(topic, json_payload, qos=1, retain=False)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("✅ Messaggio MQTT inviato con successo!")
                return True
            else:
                print(f"❌ Errore invio MQTT: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Errore preparazione/invio messaggio MQTT: {e}")
            return False
    
    def publish_status(self, status="online"):
        """
        Pubblica lo stato del sistema
        Args: status (str) - Stato del sistema
        """
        if not self.is_connected:
            return False
        
        try:
            topic = Config.get_mqtt_topic("status")
            payload = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "tornello_id": Config.TORNELLO_ID
            }
            
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ Errore invio status: {e}")
            return False
    
    def disconnect(self):
        """Disconnette dal broker MQTT"""
        try:
            if self.is_connected:
                self.publish_status("offline")
                time.sleep(0.5)  # Aspetta che il messaggio venga inviato
            
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                
            self.is_connected = False
            print("🌐 MQTT disconnesso")
            
        except Exception as e:
            print(f"⚠️ Errore disconnessione MQTT: {e}")
    
    def get_status(self):
        """Restituisce lo stato della connessione MQTT"""
        return {
            'connected': self.is_connected,
            'broker': Config.MQTT_BROKER,
            'port': Config.MQTT_PORT,
            'username': Config.MQTT_USERNAME,
            'tls_enabled': Config.MQTT_USE_TLS,
            'topic': Config.get_mqtt_topic("badge")
        }
    
    def __del__(self):
        """Destructor - disconnette automaticamente"""
        self.disconnect()