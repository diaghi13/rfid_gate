#!/usr/bin/env python3
"""
🔧 ANALISI PROBLEMA: Doppia Chiamata MQTT + API REST
==================================================

PROBLEMA IDENTIFICATO:
L'utente riceve DUE log per la stessa carta:
1619 - "Carta autorizzata via fallback REST real-time | Local"  
1618 - "Accesso consentito - bypass per test"

CAUSA:
Il sistema fa DUE chiamate separate:
1. MQTT parallelo → broker → gate-verification (sempre)
2. API REST diretta → /api/gate-verification (se carta non in cache)

LOGICA CORRETTA RICHIESTA:
1. ✅ MQTT sempre (unica chiamata al broker)
2. ✅ Se tessera non trovata → /api/gate-sync?card_uid=xxx (per popolare cache)
3. ✅ Se tessera in cache ma senza abbonamento valido → /api/gate-sync?card_uid=xxx
4. ✅ Solo se trova qualcosa di attivo → poi MQTT

FLUSSO CORRETTO:
┌─ Carta letta
├─ MQTT → broker → gate-verification
├─ Se broker dice "carta non trovata":
│  ├─ Chiama /api/gate-sync?card_uid=xxx
│  ├─ Se trova dati attivi → aggiorna cache → ri-chiama MQTT
│  └─ Se non trova → nega accesso
└─ Fine (UNA sola chiamata al broker)
"""

def analyze_current_flow():
    """Analizza il flusso attuale problematico"""
    
    print("🚨 FLUSSO ATTUALE (PROBLEMATICO)")
    print("=" * 40)
    
    print("1. 📡 MQTT parallelo sempre attivo:")
    print("   → access_control.py:545 → send_auth_request_parallel()")
    print("   → broker riceve richiesta → gate-verification")
    print("   → PRIMO LOG: 'Accesso consentito - bypass per test'")
    
    print("\n2. 🔍 API REST fallback per carte non in cache:")
    print("   → sync_manager.py:456 → _check_realtime_fallback()")
    print("   → POST /api/gate-verification diretto")
    print("   → SECONDO LOG: 'Carta autorizzata via fallback REST real-time'")
    
    print("\n❌ RISULTATO: DUE CHIAMATE SEPARATE!")

def show_correct_flow():
    """Mostra il flusso corretto"""
    
    print("\n✅ FLUSSO CORRETTO RICHIESTO")
    print("=" * 35)
    
    print("1. 📡 MQTT unico sempre:")
    print("   → Carta letta → MQTT → broker → gate-verification")
    
    print("\n2. 🔄 Cache refresh intelligente:")
    print("   → Se broker risponde 'carta non trovata':")
    print("   → GET /api/gate-sync?card_uid=xxx")
    print("   → Se trova abbonamento attivo → aggiorna cache")
    print("   → Ri-chiama MQTT (ora carta in cache)")
    
    print("\n3. 📋 Cache check intelligente:")
    print("   → Se carta in cache ma abbonamento scaduto:")
    print("   → GET /api/gate-sync?card_uid=xxx")
    print("   → Se trova rinnovo → aggiorna cache → MQTT")
    
    print("\n✅ RISULTATO: UNA SOLA CHIAMATA GATE-VERIFICATION!")

def identify_needed_changes():
    """Identifica modifiche necessarie"""
    
    print("\n🔧 MODIFICHE NECESSARIE")
    print("=" * 25)
    
    print("1. ❌ RIMUOVI: _check_realtime_fallback()")
    print("   → sync_manager.py:1107")
    print("   → Chiamata API diretta a gate-verification")
    
    print("\n2. ✅ MODIFICA: Cache refresh strategy")
    print("   → Usa /api/gate-sync?card_uid=xxx invece")
    print("   → Solo per popolare cache, non per autorizzare")
    
    print("\n3. ✅ MODIFICA: Access control flow")
    print("   → Un solo path: MQTT → broker → gate-verification")
    print("   → Cache refresh come supporto, non autorizzazione")
    
    print("\n4. ✅ AGGIUNGI: Response handler MQTT")
    print("   → Se broker dice 'not found' → trigger cache refresh")
    print("   → Poi ri-prova MQTT con cache aggiornata")

def show_new_endpoint_usage():
    """Mostra uso corretto endpoint"""
    
    print("\n🌐 ENDPOINT USAGE CORRETTO")
    print("=" * 30)
    
    print("❌ ATTUALE (SBAGLIATO):")
    print("   POST /api/gate-verification")
    print("   → Autorizza direttamente (duplica MQTT)")
    
    print("\n✅ CORRETTO:")
    print("   GET /api/gate-sync?card_uid=5B0948B5")
    print("   → Ritorna dati carta/abbonamenti")
    print("   → Sistema aggiorna cache locale")
    print("   → Poi MQTT con cache aggiornata")
    
    print("\n📋 FLUSSO GATE-SYNC:")
    print("   1. Carta non in cache → /api/gate-sync")
    print("   2. Carta in cache, abbonamento scaduto → /api/gate-sync")
    print("   3. Se gate-sync trova abbonamento attivo:")
    print("      → Aggiorna cache → MQTT → broker → gate-verification")

def main():
    analyze_current_flow()
    show_correct_flow()
    identify_needed_changes()
    show_new_endpoint_usage()
    
    print("\n🎯 PRIORITÀ INTERVENTO:")
    print("=" * 25)
    print("1. Rimuovere _check_realtime_fallback()")
    print("2. Implementare cache refresh con /api/gate-sync")
    print("3. Un solo path MQTT → gate-verification")
    print("4. Eliminare duplicazione chiamate")

if __name__ == "__main__":
    main()