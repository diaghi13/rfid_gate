#!/usr/bin/env python3
"""
Client MQTT per l'invio dei dati delle card RFID
Supporta connessioni TLS sicure
"""

import json
import time
import ssl
from datetime import datetime
import paho.mqtt.client as mqtt
from config import Config

class MQTTClient:
    """Classe per gestire la comunicazione MQTT"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_retries = 3
    
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
                "hex_id": card_info.get('uid_hex')
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