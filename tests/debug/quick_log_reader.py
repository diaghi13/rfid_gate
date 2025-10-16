#!/usr/bin/env python3
"""
📋 Quick Log Reader per RFID Gate
===============================
Tool rapido per leggere e filtrare i log del sistema.
"""

import os
import json
from datetime import datetime
from pathlib import Path

def read_system_logs():
    """Leggi log di sistema"""
    log_path = Path("/Users/davidedonghi/Apps/_micro services/rfid_gate/logs/system.log")
    
    if log_path.exists():
        print("📄 Log Sistema (ultimi 20 righe):")
        print("-" * 50)
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.strip())
    else:
        print("❌ File system.log non trovato")

def read_access_logs():
    """Leggi log accessi JSON"""
    log_path = Path("/Users/davidedonghi/Apps/_micro services/rfid_gate/logs/access_log.json")
    
    if log_path.exists():
        print("\n📊 Log Accessi (ultimi 5):")
        print("-" * 50)
        
        try:
            with open(log_path, 'r') as f:
                for line in f.readlines()[-5:]:
                    try:
                        data = json.loads(line.strip())
                        timestamp = data.get('timestamp', 'N/A')
                        card_uid = data.get('card_uid', 'N/A')
                        decision = data.get('decision', 'N/A')
                        direction = data.get('direction', 'N/A')
                        print(f"   {timestamp} | {card_uid} | {decision} | {direction}")
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"❌ Errore lettura access log: {e}")
    else:
        print("\n❌ File access_log.json non trovato")

def search_cache_refresh_logs():
    """Cerca log relativi a cache refresh"""
    log_path = Path("/Users/davidedonghi/Apps/_micro services/rfid_gate/logs/system.log")
    
    if log_path.exists():
        print("\n🔍 Ricerca Cache Refresh nei log:")
        print("-" * 50)
        
        keywords = ['cache', 'refresh', 'Cache aggiornata', 'negata dalla cache', 'refresh server']
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
            
        found = False
        for line in lines:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    print(f"   {line.strip()}")
                    found = True
                    break
        
        if not found:
            print("   ❌ Nessun log di cache refresh trovato")
            print("   📝 Questo conferma che cache refresh non viene attivata")
    else:
        print("\n❌ File system.log non trovato")

def show_recent_terminal_output():
    """Mostra come vedere output terminale"""
    print("\n🖥️  Per vedere log in tempo reale:")
    print("-" * 50)
    print("Se il sistema è in esecuzione, usa:")
    print("   tail -f logs/system.log")
    print("   Oppure osserva l'output del terminale dove gira main.py")
    print()
    print("Per cercare cache refresh:")
    print("   grep -i cache logs/system.log")
    print("   grep -i refresh logs/system.log")

def main():
    """Leggi tutti i log disponibili"""
    print("📋 RFID Gate - Quick Log Reader")
    print("=" * 50)
    
    # Log di sistema
    read_system_logs()
    
    # Log accessi
    read_access_logs()
    
    # Cerca cache refresh
    search_cache_refresh_logs()
    
    # Istruzioni terminale
    show_recent_terminal_output()
    
    print("\n🎯 COSA CERCARE:")
    print("- '🔄 Carta XXXXXXXX negata dalla cache - tentativo refresh server...'")
    print("- '💾 Cache aggiornata per XXXXXXXX'") 
    print("- '❌ Cache ancora nega XXXXXXXX dopo refresh'")
    print("- '📭 Cache refresh per XXXXXXXX non ha trovato aggiornamenti'")

if __name__ == "__main__":
    main()