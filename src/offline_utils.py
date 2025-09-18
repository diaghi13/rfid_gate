#!/usr/bin/env python3
"""
Utilità per gestire il sistema offline e la sincronizzazione
"""

import sys
import argparse
import json
import os
from datetime import datetime
from config import Config
from offline_manager import OfflineManager
from mqtt_client import MQTTClient
from logger import AccessLogger

def main():
    parser = argparse.ArgumentParser(description="Utilità Gestione Sistema Offline")
    parser.add_argument("--status", "-s", action="store_true",
                       help="Mostra stato sistema offline")
    parser.add_argument("--queue", "-q", action="store_true",
                       help="Mostra coda elementi offline")
    parser.add_argument("--sync", action="store_true",
                       help="Forza sincronizzazione immediate")
    parser.add_argument("--clear", action="store_true",
                       help="Pulisce coda offline (ATTENZIONE: cancella dati!)")
    parser.add_argument("--test-connection", "-t", action="store_true",
                       help="Testa connessione internet e MQTT")
    parser.add_argument("--export", "-e", type=str,
                       help="Esporta coda offline in file")
    parser.add_argument("--stats", action="store_true",
                       help="Mostra statistiche offline dettagliate")
    
    args = parser.parse_args()
    
    # Inizializza componenti base
    logger = AccessLogger(Config.LOG_DIRECTORY)
    
    if args.test_connection:
        test_connection()
        return
    
    # Inizializza offline manager
    mqtt_client = None
    try:
        mqtt_client = MQTTClient()
        mqtt_client.initialize()
        mqtt_client.connect()
    except Exception as e:
        print(f"⚠️ MQTT non disponibile: {e}")
    
    offline_manager = OfflineManager(mqtt_client, logger)
    offline_manager.initialize()
    
    if args.status:
        show_status(offline_manager)
    
    if args.queue:
        show_queue(offline_manager)
    
    if args.sync:
        force_sync(offline_manager)
    
    if args.clear:
        clear_queue(offline_manager)
    
    if args.export:
        export_queue(offline_manager, args.export)
    
    if args.stats:
        show_detailed_stats(offline_manager, logger)
    
    # Cleanup
    if offline_manager:
        offline_manager.cleanup()
    if mqtt_client:
        mqtt_client.disconnect()

def test_connection():
    """Testa la connessione internet e MQTT"""
    print("🔍 Test connessione...")
    
    try:
        # Test connessione internet generica
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("✅ Connessione internet: OK")
    except Exception as e:
        print(f"❌ Connessione internet: FALLITA ({e})")
        return
    
    try:
        # Test connessione MQTT
        socket.create_connection((Config.MQTT_BROKER, Config.MQTT_PORT), timeout=5)
        print(f"✅ Connessione MQTT ({Config.MQTT_BROKER}:{Config.MQTT_PORT}): OK")
    except Exception as e:
        print(f"❌ Connessione MQTT: FALLITA ({e})")
        return
    
    try:
        # Test completo MQTT con autenticazione
        mqtt_client = MQTTClient()
        mqtt_client.initialize()
        if mqtt_client.connect():
            print("✅ Autenticazione MQTT: OK")
            mqtt_client.disconnect()
        else:
            print("❌ Autenticazione MQTT: FALLITA")
    except Exception as e:
        print(f"❌ Test MQTT completo: FALLITO ({e})")

def show_status(offline_manager):
    """Mostra lo status del sistema offline"""
    status = offline_manager.get_status()
    
    print("\n📊 STATUS SISTEMA OFFLINE")
    print("="*50)
    print(f"🌐 Modalità offline: {'Abilitata' if status['enabled'] else 'Disabilitata'}")
    print(f"🔌 Connessione: {'Online' if status['online'] else 'Offline'}")
    print(f"🚪 Accesso offline: {'Consentito' if status['allow_offline_access'] else 'Negato'}")
    print(f"🔄 Sync automatica: {'Attiva' if status['sync_enabled'] else 'Disattiva'}")
    print(f"📦 Elementi in coda: {status['queue_size']}")
    
    if status['last_connection_check']:
        last_check = datetime.fromtimestamp(status['last_connection_check'])
        print(f"🕐 Ultimo check connessione: {last_check.strftime('%H:%M:%S - %d/%m/%Y')}")
    
    stats = status['stats']
    print(f"\n📈 Statistiche:")
    print(f"   🔢 Accessi offline totali: {stats['total_offline_accesses']}")
    print(f"   📤 In attesa di sync: {stats['pending_sync']}")
    print(f"   🔍 Check connessione: {stats['connection_checks']}")
    
    if stats['last_sync_attempt']:
        print(f"   ⏰ Ultimo tentativo sync: {stats['last_sync_attempt']}")
    if stats['last_successful_sync']:
        print(f"   ✅ Ultimo sync riuscito: {stats['last_successful_sync']}")

def show_queue(offline_manager):
    """Mostra il contenuto della coda offline"""
    print("\n📦 CODA ELEMENTI OFFLINE")
    print("="*60)
    
    if offline_manager.offline_queue.empty():
        print("📭 Coda vuota - Nessun elemento in attesa di sincronizzazione")
        return
    
    # Estrai elementi per visualizzazione (senza rimuoverli)
    queue_items = []
    temp_items = []
    
    while not offline_manager.offline_queue.empty():
        try:
            item = offline_manager.offline_queue.get_nowait()
            queue_items.append(item)
            temp_items.append(item)
        except:
            break
    
    # Rimetti tutto nella coda
    for item in temp_items:
        offline_manager.offline_queue.put(item)
    
    print(f"📊 Totale elementi: {len(queue_items)}")
    print("-" * 60)
    
    for i, item in enumerate(queue_items[:10], 1):  # Mostra solo primi 10
        card_info = item['card_info']
        timestamp = datetime.fromisoformat(item['timestamp'])
        
        print(f"{i:2d}. {timestamp.strftime('%d/%m %H:%M:%S')} | "
              f"{card_info.get('uid_formatted', 'N/A'):10s} | "
              f"{card_info.get('direction', 'N/A'):3s} | "
              f"Tentativi: {item.get('sync_attempts', 0)}")
    
    if len(queue_items) > 10:
        print(f"    ... e altri {len(queue_items) - 10} elementi")

def force_sync(offline_manager):
    """Forza una sincronizzazione immediata"""
    print("\n🔄 SINCRONIZZAZIONE FORZATA")
    print("="*40)
    
    if not offline_manager.is_online:
        print("❌ Impossibile sincronizzare: sistema offline")
        print("💡 Controllare la connessione internet e riprovare")
        return
    
    if offline_manager.offline_queue.empty():
        print("📭 Nessun elemento da sincronizzare")
        return
    
    queue_size_before = offline_manager.offline_queue.qsize()
    print(f"📤 Inizio sincronizzazione di {queue_size_before} elementi...")
    
    offline_manager.sync_offline_data()
    
    queue_size_after = offline_manager.offline_queue.qsize()
    synced_count = queue_size_before - queue_size_after
    
    print(f"\n📊 Risultato sincronizzazione:")
    print(f"   ✅ Sincronizzati: {synced_count}")
    print(f"   ⏳ Rimanenti: {queue_size_after}")
    
    if queue_size_after > 0:
        print(f"   💡 {queue_size_after} elementi non sincronizzati (potrebbero essere ritentati)")

def clear_queue(offline_manager):
    """Pulisce la coda offline"""
    print("\n🧹 PULIZIA CODA OFFLINE")
    print("="*40)
    
    queue_size = offline_manager.offline_queue.qsize()
    
    if queue_size == 0:
        print("📭 Coda già vuota")
        return
    
    print(f"⚠️  ATTENZIONE: Stai per cancellare {queue_size} elementi dalla coda!")
    print("   Questi dati NON potranno essere recuperati.")
    
    confirm = input("\nConfermi la cancellazione? (scrivi 'CONFERMA' per procedere): ")
    
    if confirm == "CONFERMA":
        offline_manager.clear_offline_queue()
        print("✅ Coda offline pulita")
    else:
        print("❌ Operazione annullata")

def export_queue(offline_manager, filename):
    """Esporta la coda offline in un file"""
    print(f"\n📤 EXPORT CODA OFFLINE → {filename}")
    print("="*50)
    
    if offline_manager.offline_queue.empty():
        print("📭 Coda vuota - Nessun dato da esportare")
        return
    
    # Estrai elementi per export
    queue_items = []
    temp_items = []
    
    while not offline_manager.offline_queue.empty():
        try:
            item = offline_manager.offline_queue.get_nowait()
            queue_items.append(item)
            temp_items.append(item)
        except:
            break
    
    # Rimetti tutto nella coda
    for item in temp_items:
        offline_manager.offline_queue.put(item)
    
    # Prepara dati per export
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'total_items': len(queue_items),
        'tornello_id': Config.TORNELLO_ID,
        'queue_data': queue_items
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Export completato: {len(queue_items)} elementi salvati in {filename}")
        
    except Exception as e:
        print(f"❌ Errore durante export: {e}")

def show_detailed_stats(offline_manager, logger):
    """Mostra statistiche dettagliate"""
    print("\n📈 STATISTICHE DETTAGLIATE SISTEMA OFFLINE")
    print("="*60)
    
    # Status offline manager
    status = offline_manager.get_status()
    stats = status['stats']
    
    print("🌐 Sistema Offline:")
    print(f"   📊 Accessi offline totali: {stats['total_offline_accesses']}")
    print(f"   📦 In coda per sync: {stats['pending_sync']}")
    print(f"   🔍 Controlli connessione: {stats['connection_checks']}")
    
    # Statistiche dai log
    try:
        log_stats = logger.get_access_stats(30)  # Ultimi 30 giorni
        
        print(f"\n📋 Statistiche Accessi (30 giorni):")
        print(f"   🔢 Totale tentativi: {log_stats.get('total_attempts', 0)}")
        print(f"   ✅ Autorizzati: {log_stats.get('authorized', 0)}")
        print(f"   ❌ Negati: {log_stats.get('denied', 0)}")
        print(f"   🏷️  Card uniche: {log_stats.get('unique_cards', 0)}")
        print(f"   ⚡ Attivazioni relè: {log_stats.get('relay_activations', 0)}")
        
        if log_stats.get('avg_auth_time'):
            print(f"   ⏱️  Tempo auth medio: {log_stats['avg_auth_time']:.1f}ms")
        
        # Analizza pattern temporali
        by_hour = log_stats.get('by_hour', {})
        if by_hour:
            most_active_hour = max(by_hour, key=by_hour.get)
            print(f"   🕐 Ora più attiva: {most_active_hour}:00 ({by_hour[most_active_hour]} accessi)")
        
    except Exception as e:
        print(f"⚠️ Errore lettura statistiche log: {e}")
    
    # Analisi file coda offline
    queue_file_path = os.path.join(Config.LOG_DIRECTORY, Config.OFFLINE_STORAGE_FILE)
    if os.path.exists(queue_file_path):
        try:
            file_size = os.path.getsize(queue_file_path)
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(queue_file_path))
            
            print(f"\n💾 File Coda Offline:")
            print(f"   📁 Path: {queue_file_path}")
            print(f"   📏 Dimensione: {file_size} bytes")
            print(f"   🕐 Ultima modifica: {file_mod_time.strftime('%H:%M:%S - %d/%m/%Y')}")
            
        except Exception as e:
            print(f"⚠️ Errore analisi file coda: {e}")

if __name__ == "__main__":
    main()