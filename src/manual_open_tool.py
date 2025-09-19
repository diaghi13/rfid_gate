#!/usr/bin/env python3
"""
Tool per testare e comandare l'apertura manuale del tornello
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime

# Aggiungi src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from mqtt_client import MQTTClient
from manual_control import ManualControl
from relay_manager import RelayManager
from logger import AccessLogger

def send_remote_command(direction='in', duration=2, user_id='admin', auth_token='admin123456'):
    """Invia comando di apertura manuale via MQTT"""
    print("📡 INVIO COMANDO REMOTO")
    print("=" * 40)
    
    # Inizializza MQTT
    try:
        mqtt_client = MQTTClient()
        if not mqtt_client.initialize():
            print("❌ Errore inizializzazione MQTT Client")
            return False
        
        if not mqtt_client.connect():
            print("❌ Errore connessione MQTT")
            return False
        
        print("✅ Connesso al broker MQTT")
        
        # Prepara comando
        command_id = f"cmd_{int(time.time())}"
        manual_topic = Config.get_manual_open_topic()
        
        command_payload = {
            'command_id': command_id,
            'direction': direction,
            'duration': duration,
            'user_id': user_id,
            'auth_token': auth_token,
            'timestamp': datetime.now().isoformat(),
            'source': 'manual_tool'
        }
        
        print(f"📤 Invio comando:")
        print(f"   Topic: {manual_topic}")
        print(f"   Direction: {direction}")
        print(f"   Duration: {duration}s")
        print(f"   User: {user_id}")
        print(f"   Command ID: {command_id}")
        
        # Invia comando
        json_payload = json.dumps(command_payload, ensure_ascii=False, indent=2)
        result = mqtt_client.client.publish(manual_topic, json_payload, qos=1)
        
        if result.rc == 0:
            print("✅ Comando inviato con successo!")
            
            # Aspetta risposta per qualche secondo
            print("⏳ Attendo risposta...")
            time.sleep(5)
            
        else:
            print(f"❌ Errore invio comando: {result.rc}")
            return False
        
        mqtt_client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def send_local_command(direction='in', duration=2, user_id='local'):
    """Esegue apertura manuale locale"""
    print("🔧 APERTURA MANUALE LOCALE")
    print("=" * 40)
    
    try:
        # Inizializza componenti necessari
        logger = AccessLogger(Config.LOG_DIRECTORY)
        
        # Inizializza Relay Manager
        relay_manager = RelayManager()
        if not relay_manager.initialize():
            print("❌ Errore inizializzazione Relay Manager")
            return False
        
        # Crea Manual Control senza MQTT
        manual_control = ManualControl(None, relay_manager, logger)
        manual_control.is_enabled = True  # Forza abilitazione per test locale
        
        # Esegui apertura
        success = manual_control.manual_open_local(direction, duration, user_id)
        
        # Cleanup
        relay_manager.cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def test_manual_system():
    """Testa il sistema di apertura manuale"""
    print("🧪 TEST SISTEMA APERTURA MANUALE")
    print("=" * 50)
    
    try:
        # Test configurazione
        print("1️⃣ Test configurazioni:")
        print(f"   MANUAL_OPEN_ENABLED: {Config.MANUAL_OPEN_ENABLED}")
        print(f"   MANUAL_OPEN_AUTH_REQUIRED: {Config.MANUAL_OPEN_AUTH_REQUIRED}")
        print(f"   MANUAL_OPEN_TIMEOUT: {Config.MANUAL_OPEN_TIMEOUT}")
        print(f"   Manual topic: {Config.get_manual_open_topic()}")
        print(f"   Response topic: {Config.get_manual_response_topic()}")
        
        if not Config.MANUAL_OPEN_ENABLED:
            print("❌ Apertura manuale disabilitata nel config!")
            return False
        
        # Test MQTT (se disponibile)
        print("\n2️⃣ Test connessione MQTT...")
        mqtt_available = False
        try:
            mqtt_client = MQTTClient()
            if mqtt_client.initialize() and mqtt_client.connect():
                print("✅ MQTT disponibile per comandi remoti")
                mqtt_available = True
                mqtt_client.disconnect()
            else:
                print("⚠️ MQTT non disponibile - solo comandi locali")
        except Exception as e:
            print(f"⚠️ MQTT non disponibile: {e}")
        
        # Test Relay Manager
        print("\n3️⃣ Test Relay Manager...")
        relay_manager = RelayManager()
        if relay_manager.initialize():
            available_relays = relay_manager.get_active_relays()
            print(f"✅ Relay Manager OK - Relè disponibili: {available_relays}")
            relay_manager.cleanup()
        else:
            print("❌ Relay Manager non funziona")
            return False
        
        # Test Manual Control
        print("\n4️⃣ Test Manual Control...")
        logger = AccessLogger(Config.LOG_DIRECTORY)
        manual_control = ManualControl(None, None, logger)
        
        status = manual_control.get_status()
        print(f"✅ Manual Control - Status: {status}")
        
        print("\n✅ Tutti i test completati!")
        print(f"\nCapacità sistema:")
        print(f"   🔧 Comandi locali: ✅ Disponibili")
        print(f"   📡 Comandi remoti: {'✅ Disponibili' if mqtt_available else '❌ Non disponibili'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        return False

def monitor_manual_responses():
    """Monitora le risposte ai comandi manuali"""
    print("👁️ MONITOR RISPOSTE APERTURA MANUALE")
    print("=" * 50)
    print("Premi Ctrl+C per interrompere\n")
    
    try:
        mqtt_client = MQTTClient()
        if not mqtt_client.initialize() or not mqtt_client.connect():
            print("❌ Impossibile connettersi a MQTT")
            return
        
        # Sottoscrivi al topic delle risposte
        response_topic = Config.get_manual_response_topic()
        mqtt_client.client.subscribe(response_topic, qos=1)
        
        def on_response(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                timestamp = payload.get('timestamp', 'N/A')
                success = payload.get('success', False)
                message = payload.get('message', 'N/A')
                user_id = payload.get('user_id', 'N/A')
                command_id = payload.get('command_id', 'N/A')
                
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"{timestamp} | {status} | User: {user_id} | ID: {command_id}")
                print(f"   Message: {message}")
                print("-" * 60)
                
            except Exception as e:
                print(f"Errore parsing risposta: {e}")
        
        mqtt_client.client.message_callback_add(response_topic, on_response)
        
        print(f"📬 In ascolto su topic: {response_topic}")
        print("Aspettando risposte...\n")
        
        # Loop di ascolto
        mqtt_client.client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Monitor interrotto")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        try:
            mqtt_client.disconnect()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description="Tool Apertura Manuale Tornello")
    parser.add_argument("--remote", "-r", action="store_true", help="Invia comando remoto via MQTT")
    parser.add_argument("--local", "-l", action="store_true", help="Esegui apertura locale")
    parser.add_argument("--test", "-t", action="store_true", help="Testa il sistema")
    parser.add_argument("--monitor", "-m", action="store_true", help="Monitora risposte")
    
    parser.add_argument("--direction", "-d", default="in", choices=["in", "out"], help="Direzione (default: in)")
    parser.add_argument("--duration", default=2, type=int, help="Durata in secondi (default: 2)")
    parser.add_argument("--user", "-u", default="admin", help="User ID (default: admin)")
    parser.add_argument("--token", default="admin123456", help="Token auth (default: admin123456)")
    
    args = parser.parse_args()
    
    if args.test:
        test_manual_system()
    elif args.monitor:
        monitor_manual_responses()
    elif args.remote:
        send_remote_command(args.direction, args.duration, args.user, args.token)
    elif args.local:
        send_local_command(args.direction, args.duration, args.user)
    else:
        print("🔓 TOOL APERTURA MANUALE TORNELLO")
        print("=" * 40)
        print("Opzioni:")
        print("  --test    : Test del sistema")
        print("  --local   : Apertura locale")
        print("  --remote  : Comando remoto MQTT")
        print("  --monitor : Monitor risposte")
        print()
        print("Esempi:")
        print("  python3 manual_open_tool.py --local")
        print("  python3 manual_open_tool.py --remote --direction in --duration 3")
        print("  python3 manual_open_tool.py --test")

if __name__ == "__main__":
    main()