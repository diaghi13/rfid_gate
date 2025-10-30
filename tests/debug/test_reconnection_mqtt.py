#!/usr/bin/env python3
"""
🔍 Test Riconnessione MQTT - Diagnosi problema dopo riavvio broker
================================================================
Questo script testa e monitora la riconnessione MQTT automatica
"""

import os
import ssl
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Carica .env
def load_env():
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# Configurazione
MQTT_CONFIG = {
    'broker': os.getenv('MQTT_BROKER', 'mqbrk.ddns.net'),
    'port': int(os.getenv('MQTT_PORT', '8883')),
    'username': os.getenv('MQTT_USERNAME', 'palestraUser'),
    'password': os.getenv('MQTT_PASSWORD', '28dade03$'),
    'use_tls': os.getenv('MQTT_USE_TLS', 'True').lower() == 'true',
    'keep_alive': int(os.getenv('MQTT_KEEP_ALIVE', '60'))
}

class MQTTReconnectionTester:
    """Testa la riconnessione automatica MQTT"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.connection_count = 0
        self.disconnection_count = 0
        self.last_connection_time = None
        self.last_disconnection_time = None
        self.reconnection_attempts = 0
        self.max_reconnection_attempts = 10  # Più di default (3)
        self.reconnection_delay = 2.0  # Più veloce
        
    def setup_client(self):
        """Configura client MQTT"""
        try:
            import paho.mqtt.client as mqtt
            
            self.client = mqtt.Client()
            self.client.username_pw_set(MQTT_CONFIG['username'], MQTT_CONFIG['password'])
            
            # TLS
            if MQTT_CONFIG['use_tls']:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.client.tls_set_context(context)
            
            # Callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            return True
            
        except ImportError:
            print("❌ paho-mqtt non installato")
            return False
        except Exception as e:
            print(f"❌ Errore setup client: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback connessione"""
        if rc == 0:
            self.connected = True
            self.connection_count += 1
            self.last_connection_time = datetime.now()
            print(f"✅ CONNESSO #{self.connection_count} - {self.last_connection_time.strftime('%H:%M:%S')}")
            
            # Reset tentativi riconnessione
            self.reconnection_attempts = 0
            
            # Subscribe test topic
            client.subscribe("gate/+/response")
            
        else:
            print(f"❌ Connessione fallita: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback disconnessione"""
        self.connected = False
        self.disconnection_count += 1
        self.last_disconnection_time = datetime.now()
        
        disconnect_reason = {
            0: "Disconnessione normale",
            1: "Protocollo non supportato", 
            2: "Client ID non valido",
            3: "Server non disponibile",
            4: "Credenziali non valide",
            5: "Non autorizzato",
            7: "Timeout connessione"
        }.get(rc, f"Errore sconosciuto ({rc})")
        
        print(f"🔌 DISCONNESSO #{self.disconnection_count} - {self.last_disconnection_time.strftime('%H:%M:%S')}")
        print(f"   Motivo: {disconnect_reason}")
        
        # Avvia riconnessione se non volontaria
        if rc != 0:
            asyncio.create_task(self._auto_reconnect())
    
    def _on_message(self, client, userdata, msg):
        """Callback messaggio ricevuto"""
        try:
            print(f"📨 MSG: {msg.topic} - {msg.payload.decode()[:50]}...")
        except:
            print(f"📨 MSG: {msg.topic} - [binary]")
    
    async def _auto_reconnect(self):
        """Riconnessione automatica migliorata"""
        if self.reconnection_attempts >= self.max_reconnection_attempts:
            print(f"❌ Superato limite riconnessioni ({self.max_reconnection_attempts})")
            return
        
        self.reconnection_attempts += 1
        print(f"🔄 Tentativo riconnessione #{self.reconnection_attempts}/{self.max_reconnection_attempts}")
        
        await asyncio.sleep(self.reconnection_delay)
        
        try:
            self.client.connect_async(
                MQTT_CONFIG['broker'],
                MQTT_CONFIG['port'], 
                MQTT_CONFIG['keep_alive']
            )
            self.client.loop_start()
            
        except Exception as e:
            print(f"❌ Errore riconnessione: {e}")
            # Riprova con delay incrementale
            self.reconnection_delay = min(self.reconnection_delay * 1.5, 30)
            await asyncio.sleep(1)
            asyncio.create_task(self._auto_reconnect())
    
    async def connect(self):
        """Connessione iniziale"""
        try:
            print(f"🔌 Connessione a {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
            
            self.client.connect_async(
                MQTT_CONFIG['broker'],
                MQTT_CONFIG['port'],
                MQTT_CONFIG['keep_alive']
            )
            self.client.loop_start()
            
            # Attendi connessione
            for _ in range(50):  # 5 secondi max
                if self.connected:
                    return True
                await asyncio.sleep(0.1)
            
            print("⏰ Timeout connessione iniziale")
            return False
            
        except Exception as e:
            print(f"❌ Errore connessione: {e}")
            return False
    
    def get_status(self):
        """Stato corrente"""
        return {
            'connected': self.connected,
            'connections': self.connection_count,
            'disconnections': self.disconnection_count,
            'reconnection_attempts': self.reconnection_attempts,
            'last_connection': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'last_disconnection': self.last_disconnection_time.isoformat() if self.last_disconnection_time else None
        }
    
    async def send_test_message(self):
        """Invia messaggio di test"""
        if not self.connected:
            print("❌ Non connesso - impossibile inviare messaggio")
            return False
            
        test_msg = {
            "card_uid": f"TEST_{int(time.time())}",
            "identificativo_tornello": "tornello_01",
            "timestamp": datetime.now().isoformat(),
            "test": True,
            "reconnection_test": True
        }
        
        try:
            result = self.client.publish(
                "gate/tornello_01/badge",
                json.dumps(test_msg),
                qos=1
            )
            
            if result.rc == 0:
                print(f"📤 Messaggio test inviato: {test_msg['card_uid']}")
                return True
            else:
                print(f"❌ Errore invio: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Errore invio messaggio: {e}")
            return False
    
    def stop(self):
        """Ferma client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

async def test_reconnection_behavior():
    """Test completo comportamento riconnessione"""
    print("🧪 TEST COMPORTAMENTO RICONNESSIONE MQTT")
    print("=" * 60)
    print("Questo test verifica come il sistema si comporta dopo:")
    print("- Riavvio del broker")
    print("- Perdita di connessione temporanea")
    print("- Multiple disconnessioni")
    print()
    
    tester = MQTTReconnectionTester()
    
    # Setup
    if not tester.setup_client():
        return False
    
    # Connessione iniziale
    print("1️⃣ CONNESSIONE INIZIALE")
    success = await tester.connect()
    if not success:
        print("❌ Connessione iniziale fallita")
        return False
    
    print(f"✅ Connesso! Status: {json.dumps(tester.get_status(), indent=2)}")
    
    # Test invio messaggi ogni 10 secondi per 2 minuti
    print("\\n2️⃣ MONITORAGGIO CONTINUO (2 minuti)")
    print("Inviando messaggi ogni 10 secondi...")
    print("🔔 PROVA A RIAVVIARE IL BROKER DURANTE QUESTO TEST!")
    print()
    
    start_time = time.time()
    message_count = 0
    
    while time.time() - start_time < 120:  # 2 minuti
        # Status ogni ciclo
        status = tester.get_status()
        uptime = int(time.time() - start_time)
        
        print(f"⏱️ [{uptime:03d}s] Conn: {status['connected']} | " + 
              f"Tot Conn: {status['connections']} | " +
              f"Tot Disc: {status['disconnections']} | " +
              f"Retry: {status['reconnection_attempts']}")
        
        # Prova invio messaggio
        if await tester.send_test_message():
            message_count += 1
        
        await asyncio.sleep(10)
    
    # Risultati finali  
    print("\\n" + "=" * 60)
    print("📊 RISULTATI FINALI:")
    final_status = tester.get_status()
    
    print(f"🔌 Connessioni totali: {final_status['connections']}")
    print(f"🔄 Disconnessioni totali: {final_status['disconnections']}")
    print(f"♻️ Tentativi riconnessione: {final_status['reconnection_attempts']}")
    print(f"📤 Messaggi inviati: {message_count}")
    print(f"✅ Stato finale: {'CONNESSO' if final_status['connected'] else 'DISCONNESSO'}")
    
    if final_status['disconnections'] > 0:
        if final_status['connected']:
            print("🎉 RICONNESSIONE AUTOMATICA FUNZIONA!")
        else:
            print("❌ PROBLEMA: Riconnessione fallita")
    
    # Cleanup
    tester.stop()
    
    return final_status['connected']

async def main():
    """Funzione principale"""
    print("🚀 DIAGNOSI RICONNESSIONE MQTT")
    print("Identificazione problema dopo riavvio broker")
    print()
    
    success = await test_reconnection_behavior()
    
    if success:
        print("\\n✅ SISTEMA MQTT RESILIENTE")
    else:
        print("\\n❌ PROBLEMI DI RICONNESSIONE IDENTIFICATI")
        print("\\n🔧 POSSIBILI SOLUZIONI:")
        print("1. Aumentare max_retries nel codice (attualmente 3)")
        print("2. Implementare reset periodico dei tentativi")  
        print("3. Aggiungere monitoraggio heartbeat")
        print("4. Usare reconnect_delay progressivo")

if __name__ == "__main__":
    asyncio.run(main())