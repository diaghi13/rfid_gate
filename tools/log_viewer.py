#!/usr/bin/env python3
"""
Utilità per visualizzare e analizzare i log degli accessi
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from logger import AccessLogger
from config import Config

def main():
    parser = argparse.ArgumentParser(description="Visualizzatore Log Sistema RFID")
    parser.add_argument("--stats", "-s", type=int, default=7, 
                       help="Mostra statistiche degli ultimi N giorni (default: 7)")
    parser.add_argument("--tail", "-t", type=int, default=0,
                       help="Mostra gli ultimi N accessi")
    parser.add_argument("--card", "-c", type=str,
                       help="Filtra per UID card specifica")
    parser.add_argument("--today", action="store_true",
                       help="Mostra solo gli accessi di oggi")
    parser.add_argument("--authorized", action="store_true",
                       help="Mostra solo gli accessi autorizzati")
    parser.add_argument("--denied", action="store_true", 
                       help="Mostra solo gli accessi negati")
    parser.add_argument("--export", "-e", type=str,
                       help="Esporta log in formato CSV o JSON")
    parser.add_argument("--cleanup", action="store_true",
                       help="Pulisce i log più vecchi di 30 giorni")
    
    args = parser.parse_args()
    
    # Inizializza il logger
    logger = AccessLogger(Config.LOG_DIRECTORY)
    
    if args.cleanup:
        print("🧹 Pulizia log vecchi...")
        logger.cleanup_old_logs(30)
        return
    
    if args.export:
        print(f"📤 Esportazione log in formato {args.export}...")
        export_file = logger.export_logs(format_type=args.export)
        if export_file:
            print(f"✅ Export completato: {export_file}")
        return
    
    if args.stats > 0:
        logger.print_stats(args.stats)
    
    if args.tail > 0:
        show_recent_accesses(logger, args.tail, args)
    
    if args.today:
        show_today_accesses(logger, args)

def show_recent_accesses(logger, count, filters):
    """Mostra gli accessi più recenti"""
    try:
        import csv
        
        log_file = os.path.join(logger.log_dir, "access_log.csv")
        if not os.path.exists(log_file):
            print("❌ Nessun log trovato")
            return
        
        accesses = []
        with open(log_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Applica filtri
                if filters.card and row['card_uid'] != filters.card:
                    continue
                if filters.authorized and row['authorized'].lower() != 'true':
                    continue
                if filters.denied and row['authorized'].lower() != 'false':
                    continue
                
                accesses.append(row)
        
        # Prendi gli ultimi N
        recent = accesses[-count:] if len(accesses) >= count else accesses
        
        print(f"\n📋 Ultimi {len(recent)} accessi:")
        print("="*80)
        
        for access in recent:
            timestamp = datetime.fromisoformat(access['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
            status = "✅" if access['authorized'].lower() == 'true' else "❌"
            relay = "⚡" if access['relay_activated'].lower() == 'true' else "🔴"
            
            print(f"{timestamp} | {status} | {relay} | {access['card_uid']} | {access['auth_message']}")
        
        print("="*80)
        
    except Exception as e:
        print(f"❌ Errore lettura log: {e}")

def show_today_accesses(logger, filters):
    """Mostra gli accessi di oggi"""
    try:
        import csv
        
        log_file = os.path.join(logger.log_dir, "access_log.csv")
        if not os.path.exists(log_file):
            print("❌ Nessun log trovato")
            return
        
        today = datetime.now().date()
        today_accesses = []
        
        with open(log_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    access_date = datetime.fromisoformat(row['timestamp']).date()
                    if access_date != today:
                        continue
                    
                    # Applica filtri
                    if filters.card and row['card_uid'] != filters.card:
                        continue
                    if filters.authorized and row['authorized'].lower() != 'true':
                        continue
                    if filters.denied and row['authorized'].lower() != 'false':
                        continue
                    
                    today_accesses.append(row)
                    
                except Exception:
                    continue
        
        print(f"\n📅 Accessi di oggi ({today.strftime('%d/%m/%Y')}):")
        print("="*80)
        
        if not today_accesses:
            print("Nessun accesso registrato oggi.")
            return
        
        for access in today_accesses:
            timestamp = datetime.fromisoformat(access['timestamp']).strftime('%H:%M:%S')
            status = "✅ AUTORIZZATO" if access['authorized'].lower() == 'true' else "❌ NEGATO"
            relay = "⚡ Relè ON" if access['relay_activated'].lower() == 'true' else "🔴 Relè OFF"
            
            print(f"{timestamp} | {access['card_uid']} | {status} | {relay}")
            if access['auth_message']:
                print(f"         └─ 💬 {access['auth_message']}")
        
        print("="*80)
        print(f"📊 Totale accessi oggi: {len(today_accesses)}")
        
        authorized_today = sum(1 for a in today_accesses if a['authorized'].lower() == 'true')
        denied_today = len(today_accesses) - authorized_today
        
        print(f"✅ Autorizzati: {authorized_today}")
        print(f"❌ Negati: {denied_today}")
        
    except Exception as e:
        print(f"❌ Errore lettura log: {e}")

if __name__ == "__main__":
    main()