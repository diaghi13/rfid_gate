#!/usr/bin/env python3
"""
🧪 TEST REALE COMPLETO SISTEMA RFID GATE
========================================

Test end-to-end con:
- MQTT broker reale (mqbrk.ddns.net)
- Endpoint HTTP reali (gymme-newaction.ddns.net)
- Flusso intelligente completo
- Cache SQLite reale
- Logging completo

Questo test simula il comportamento reale del sistema.
"""

import sys
import os
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Carica configurazione
load_dotenv()

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

class RealSystemTester:
    """Tester completo con servizi reali"""
    
    def __init__(self):
        self.config = None
        self.access_control = None
        self.test_results = []
        
        print("🔧 INIZIALIZZAZIONE TEST REALE")
        print("=" * 40)
    
    async def setup_real_system(self):
        """Inizializza il sistema reale"""
        try:
            from rfid_gate.config.settings import RFIDGateConfig
            from rfid_gate.core.access_control import AccessControlSystem
            
            # Carica configurazione reale
            self.config = RFIDGateConfig.from_env()
            
            print(f"📡 MQTT Broker: {self.config.mqtt.broker}:{self.config.mqtt.port}")
            print(f"🌐 Cache Server: {self.config.sync.cache_sync_server_url}")
            print(f"🚪 Gate Server: {self.config.sync.server_url}")
            print(f"🏷️ Tornello ID: {self.config.system.tornello_id}")
            print()
            
            print("📡 MQTT Topics:")
            print(f"   📤 Badge (invio): {self.config.mqtt.card_read_topic}")
            print(f"   📥 Response (risposta): {self.config.mqtt.auth_response_topic}")
            print(f"   🔓 Manual Open: {self.config.mqtt.manual_open_topic}")
            print()
            
            # Inizializza sistema di controllo accessi
            print("🚀 Inizializzazione AccessControlSystem...")
            self.access_control = AccessControlSystem(self.config)
            
            # Avvia sistema
            print("⚡ Avvio sistema...")
            await self.access_control.start()
            
            # Aspetta un momento per la connessione
            await asyncio.sleep(2)
            
            print("✅ Sistema avviato e pronto!")
            return True
            
        except Exception as e:
            print(f"❌ Errore setup sistema: {e}")
            return False
    
    async def test_real_card_scenarios(self):
        """Test scenari reali con carte"""
        
        print("\n🃏 TEST SCENARI CARTE REALI")
        print("=" * 40)
        
        # Carte di test con scenari diversi
        test_cards = [
            {
                "uid": "632D3903",  # Carta reale trovata nei test precedenti
                "direction": "in",
                "description": "Carta DAVIDE DONGHI (reale nel sistema)",
                "expected_scenario": "CASO 1 o CASO 3"
            },
            {
                "uid": "A1B2C3D4", 
                "direction": "out",
                "description": "Carta test non esistente",
                "expected_scenario": "CASO 2"
            },
            {
                "uid": "12345678",
                "direction": "in", 
                "description": "Carta test generica",
                "expected_scenario": "CASO 2"
            }
        ]
        
        for i, card in enumerate(test_cards, 1):
            print(f"\n🧪 TEST {i}: {card['description']}")
            print(f"   UID: {card['uid']}")
            print(f"   Direzione: {card['direction']}")
            print(f"   Scenario atteso: {card['expected_scenario']}")
            print("-" * 50)
            
            # Simula evento carta
            start_time = time.time()
            
            try:
                from rfid_gate.core.events import CardEvent
                
                # Crea evento carta
                card_event = CardEvent(
                    uid_raw=bytes.fromhex(card['uid'].replace(' ', '')),
                    uid_formatted=card['uid'],
                    direction=card['direction'],
                    reader_id=f"reader_{card['direction']}",
                    reader_type="pn532",
                    timestamp=datetime.now(),
                    metadata={"test": True}
                )
                
                print(f"📋 Evento carta creato: {card_event.uid_formatted}")
                
                # Processo autenticazione attraverso il sistema reale
                decision = await self.access_control._authenticate_card(card_event)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # in ms
                
                print(f"⏱️ Tempo risposta: {response_time:.1f}ms")
                print(f"🎯 Decisione: {decision}")
                
                # Salva risultato
                result = {
                    "card_uid": card['uid'],
                    "direction": card['direction'],
                    "decision": str(decision),
                    "response_time_ms": response_time,
                    "description": card['description'],
                    "timestamp": datetime.now().isoformat()
                }
                
                self.test_results.append(result)
                
                if "GRANT" in str(decision):
                    print("✅ ACCESSO AUTORIZZATO")
                elif "DENY" in str(decision):
                    print("❌ ACCESSO NEGATO")
                else:
                    print(f"⚠️ DECISIONE: {decision}")
                    
            except Exception as e:
                print(f"❌ Errore test carta {card['uid']}: {e}")
                
                result = {
                    "card_uid": card['uid'],
                    "direction": card['direction'],
                    "decision": "ERROR",
                    "response_time_ms": 0,
                    "description": card['description'],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.test_results.append(result)
            
            print("=" * 50)
            
            # Pausa tra test
            await asyncio.sleep(1)
    
    async def test_mqtt_connectivity(self):
        """Test connettività MQTT"""
        
        print("\n📡 TEST CONNETTIVITÀ MQTT")
        print("-" * 30)
        
        try:
            if self.access_control.mqtt_client:
                is_connected = self.access_control.mqtt_client.is_connected()
                print(f"🔗 Stato connessione: {'✅ CONNESSO' if is_connected else '❌ DISCONNESSO'}")
                
                if is_connected:
                    print(f"📡 Broker: {self.config.mqtt.broker}:{self.config.mqtt.port}")
                    print(f"🔐 TLS: {'✅' if self.config.mqtt.use_tls else '❌'}")
                    print(f"👤 Username: {self.config.mqtt.username}")
                    return True
                else:
                    print("⚠️ MQTT non connesso")
                    return False
            else:
                print("❌ Client MQTT non inizializzato")
                return False
                
        except Exception as e:
            print(f"❌ Errore test MQTT: {e}")
            return False
    
    async def test_sync_manager(self):
        """Test sync manager e cache"""
        
        print("\n💾 TEST SYNC MANAGER E CACHE")
        print("-" * 35)
        
        try:
            if self.access_control.sync_manager:
                print("✅ Sync Manager inizializzato")
                
                # Test cache con carta reale
                test_uid = "632D3903"
                cache_result = await self.access_control.sync_manager.validate_card_offline(test_uid, "in")
                
                print(f"🔍 Test cache per {test_uid}:")
                print(f"   Autorizzato: {cache_result.get('authorized', False)}")
                print(f"   Motivo: {cache_result.get('reason', 'N/A')}")
                
                if cache_result.get('customer_id'):
                    print(f"   Customer ID: {cache_result['customer_id']}")
                    print(f"   Customer Name: {cache_result.get('customer_name', 'N/A')}")
                
                return True
            else:
                print("❌ Sync Manager non inizializzato")
                return False
                
        except Exception as e:
            print(f"❌ Errore test sync manager: {e}")
            return False
    
    async def generate_final_report(self):
        """Genera report finale del test"""
        
        print("\n📊 REPORT FINALE TEST REALE")
        print("=" * 50)
        
        if not self.test_results:
            print("❌ Nessun risultato test disponibile")
            return
        
        # Statistiche generali
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r['decision'] != 'ERROR'])
        granted_access = len([r for r in self.test_results if 'GRANT' in r['decision']])
        denied_access = len([r for r in self.test_results if 'DENY' in r['decision']])
        
        print(f"📈 STATISTICHE:")
        print(f"   Test totali: {total_tests}")
        print(f"   Test riusciti: {successful_tests}/{total_tests}")
        print(f"   Accessi autorizzati: {granted_access}/{total_tests}")
        print(f"   Accessi negati: {denied_access}/{total_tests}")
        
        if successful_tests > 0:
            avg_response_time = sum(r['response_time_ms'] for r in self.test_results if r['response_time_ms'] > 0) / successful_tests
            print(f"   Tempo medio risposta: {avg_response_time:.1f}ms")
        
        print()
        
        # Dettagli per carta
        print("📋 DETTAGLI PER CARTA:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result['decision'] != 'ERROR' else "❌"
            print(f"   {i}. {status} {result['card_uid']} ({result['direction']}) → {result['decision']}")
            if result['response_time_ms'] > 0:
                print(f"      ⏱️ {result['response_time_ms']:.1f}ms")
        
        print()
        
        # Analisi flusso intelligente
        print("🎯 ANALISI FLUSSO INTELLIGENTE:")
        
        # Stima scenari basata sui tempi di risposta e decisioni
        fast_responses = [r for r in self.test_results if r['response_time_ms'] < 50 and r['response_time_ms'] > 0]
        slow_responses = [r for r in self.test_results if r['response_time_ms'] >= 50]
        
        if fast_responses:
            print(f"   🚀 Risposte veloci (<50ms): {len(fast_responses)} → Probabili CASO 1 (Cache Hit)")
        
        if slow_responses:
            print(f"   🐌 Risposte lente (≥50ms): {len(slow_responses)} → Probabili CASO 2/3 (Network)")
        
        print()
        print("🎊 TEST REALE COMPLETATO!")
    
    async def cleanup(self):
        """Pulizia sistema"""
        try:
            if self.access_control:
                print("\n🧹 Pulizia sistema...")
                await self.access_control.stop()
                print("✅ Sistema fermato correttamente")
        except Exception as e:
            print(f"⚠️ Errore durante pulizia: {e}")

async def main():
    """Funzione principale test reale"""
    
    print("🚀 TEST REALE SISTEMA RFID GATE COMPLETO")
    print("=" * 60)
    print(f"⏰ Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = RealSystemTester()
    
    try:
        # Setup sistema
        if not await tester.setup_real_system():
            print("❌ Setup fallito, impossibile continuare")
            return False
        
        # Test connettività
        mqtt_ok = await tester.test_mqtt_connectivity()
        sync_ok = await tester.test_sync_manager()
        
        if not (mqtt_ok and sync_ok):
            print("⚠️ Alcuni servizi non funzionano, ma continuo con test carte...")
        
        # Test scenari carte
        await tester.test_real_card_scenarios()
        
        # Report finale
        await tester.generate_final_report()
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto dall'utente")
        return False
        
    except Exception as e:
        print(f"\n❌ Errore durante test: {e}")
        return False
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n🏁 Test {'✅ COMPLETATO' if success else '❌ FALLITO'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Errore critico: {e}")
        sys.exit(1)