#!/usr/bin/env python3
"""
🧪 Test REALE Flusso Intelligente con Endpoint e MQTT
====================================================

Test completo del flusso intelligente con:
- Server MQTT reale
- Endpoint HTTP reali (/api/sync-gate, /api/gate-verification)
- Database cache SQLite
- Carte reali dal sistema
- Logging completo

Questo test si connette ai servizi reali e verifica il comportamento end-to-end.
"""

import sys
import os
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

class RealWorldTester:
    """Tester con endpoint e MQTT reali"""
    
    def __init__(self):
        # Carica configurazione reale
        from rfid_gate.config.settings import load_env_file, RFIDGateConfig
        load_env_file()
        
        self.config = RFIDGateConfig.from_env()
        self.test_results = []
        
        print(f"🔧 CONFIGURAZIONE REALE")
        print(f"   MQTT Server: {self.config.mqtt.broker}:{self.config.mqtt.port}")
        print(f"   Cache Server: {self.config.sync.cache_sync_server_url}")
        print(f"   Gate Server: {self.config.sync.server_url}")
        print(f"   Tornello ID: {self.config.system.tornello_id}")
    
    async def test_real_system_startup(self):
        """Testa avvio sistema reale completo"""
        print(f"\n🚀 TEST AVVIO SISTEMA REALE")
        print("=" * 35)
        
        try:
            from rfid_gate.core.access_control import AccessControlSystem
            
            # Crea sistema con configurazione reale
            access_system = AccessControlSystem()
            
            print("📋 Inizializzazione sistema...")
            success = await access_system.initialize()
            
            if success:
                print("✅ Sistema inizializzato correttamente")
                
                # Verifica componenti attivi
                if access_system.sync_manager:
                    print("✅ SyncManager attivo")
                    
                    # Test connettività
                    connectivity = await access_system.sync_manager.check_connectivity()
                    print(f"🌐 Connettività server: {'✅' if connectivity else '❌'}")
                
                if access_system.mqtt_client:
                    print("✅ MQTT Client creato")
                    is_connected = access_system.mqtt_client.is_connected()
                    print(f"📡 MQTT connesso: {'✅' if is_connected else '❌'}")
                
                # Test con carta reale
                await self.test_real_card_scenarios(access_system)
                
                # Spegni sistema
                await access_system.shutdown()
                print("✅ Sistema spento correttamente")
                
                return True
            else:
                print("❌ Inizializzazione sistema fallita")
                return False
                
        except Exception as e:
            print(f"❌ Errore test sistema: {e}")
            return False
    
    async def test_real_card_scenarios(self, access_system):
        """Testa scenari con carte reali"""
        print(f"\n📱 TEST SCENARI CARTE REALI")
        print("=" * 30)
        
        # Carte di test (usa carte che sai essere nel sistema)
        test_cards = [
            {
                'uid': '5B0948B5',  # Carta che hai usato nei log
                'name': 'Carta Test 1',
                'expected': 'cache_hit_or_refresh'
            },
            {
                'uid': 'AAAA1111',  # Carta inesistente
                'name': 'Carta Inesistente',
                'expected': 'fallback_deny'
            },
            {
                'uid': 'BBBB2222',  # Altra carta test
                'name': 'Carta Test 2', 
                'expected': 'cache_or_fallback'
            }
        ]
        
        for card_info in test_cards:
            await self.test_single_card_flow(access_system, card_info)
            await asyncio.sleep(2)  # Pausa tra test
    
    async def test_single_card_flow(self, access_system, card_info):
        """Testa il flusso completo per una singola carta"""
        uid = card_info['uid']
        print(f"\n📇 TEST CARTA: {uid} ({card_info['name']})")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Simula evento carta (come se fosse letta dal lettore RFID)
            from rfid_gate.hardware.readers.base import CardEvent
            
            card_event = CardEvent(
                uid=uid,
                uid_formatted=uid,
                timestamp=time.time(),
                reader_id="test_reader_in",
                direction="in",
                reader_type="test",
                metadata={"test": True}
            )
            
            print(f"📱 Carta letta: {uid}")
            print(f"🕐 Timestamp: {datetime.fromtimestamp(card_event.timestamp)}")
            
            # Test del nuovo flusso intelligente
            decision = await access_system._authenticate_card(card_event)
            
            auth_time = time.time() - start_time
            
            print(f"⚖️ Decisione: {decision}")
            print(f"⏱️ Tempo autenticazione: {auth_time*1000:.1f}ms")
            
            # Registra risultato
            result = {
                'card_uid': uid,
                'card_name': card_info['name'],
                'decision': decision.value,
                'auth_time_ms': auth_time * 1000,
                'timestamp': datetime.now().isoformat(),
                'expected': card_info['expected']
            }
            
            self.test_results.append(result)
            
            # Analizza risultato
            if decision.value in ['grant', 'deny']:
                print(f"✅ Decisione valida: {decision.value}")
            else:
                print(f"⚠️ Decisione inaspettata: {decision.value}")
            
            return result
            
        except Exception as e:
            print(f"❌ Errore test carta {uid}: {e}")
            
            error_result = {
                'card_uid': uid,
                'card_name': card_info['name'],
                'decision': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.test_results.append(error_result)
            return error_result
    
    async def test_direct_endpoints(self):
        """Testa endpoint diretti HTTP"""
        print(f"\n🔗 TEST ENDPOINT DIRETTI")
        print("=" * 25)
        
        # Test cache refresh endpoint
        await self.test_cache_refresh_endpoint()
        
        # Test gate verification endpoint  
        await self.test_gate_verification_endpoint()
    
    async def test_cache_refresh_endpoint(self):
        """Testa GET /api/sync-gate"""
        import aiohttp
        
        test_uid = "5B0948B5"  # Carta che dovrebbe esistere
        url = f"{self.config.sync.cache_sync_server_url}{self.config.sync.cache_sync_endpoint}"
        
        print(f"\n🔄 TEST CACHE REFRESH")
        print(f"   URL: {url}")
        print(f"   Card: {test_uid}")
        
        try:
            params = {'card_uid': test_uid}
            
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    request_time = time.time() - start_time
                    
                    print(f"   Status: {response.status}")
                    print(f"   Tempo: {request_time*1000:.1f}ms")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Risposta OK: {data}")
                        
                        # Analizza risposta
                        if 'card_data' in data:
                            card_data = data['card_data']
                            print(f"   📋 Customer ID: {card_data.get('customer_id')}")
                            print(f"   📋 Nome: {card_data.get('customer_name')}")
                            print(f"   📋 Whitelist: {card_data.get('in_white_list')}")
                        
                        return True
                    else:
                        error = await response.text()
                        print(f"   ❌ Errore {response.status}: {error}")
                        return False
                        
        except Exception as e:
            print(f"   ❌ Eccezione: {e}")
            return False
    
    async def test_gate_verification_endpoint(self):
        """Testa POST /api/gate-verification"""
        import aiohttp
        
        test_uid = "5B0948B5"
        # Usa configurazione server per gate-verification
        server_url = self.config.sync.server_url  # Server principale
        endpoint = "/api/gate-verification"
        url = f"{server_url}{endpoint}"
        
        print(f"\n🚪 TEST GATE VERIFICATION")
        print(f"   URL: {url}")
        print(f"   Card: {test_uid}")
        
        try:
            payload = {
                "uid": test_uid,
                "identificativo_tornello": self.config.system.tornello_id,
                "direction": "in"
            }
            
            print(f"   Payload: {payload}")
            
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    request_time = time.time() - start_time
                    
                    print(f"   Status: {response.status}")
                    print(f"   Tempo: {request_time*1000:.1f}ms")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Risposta OK: {data}")
                        
                        # Analizza risposta
                        authorized = data.get('authorized', False)
                        message = data.get('message', '')
                        print(f"   🔐 Autorizzato: {authorized}")
                        print(f"   💬 Messaggio: {message}")
                        
                        if 'card_data' in data:
                            card_data = data['card_data']
                            print(f"   📋 Dati carta ricevuti: {len(card_data)} campi")
                        
                        return True
                    else:
                        error = await response.text()
                        print(f"   ❌ Errore {response.status}: {error}")
                        return False
                        
        except Exception as e:
            print(f"   ❌ Eccezione: {e}")
            return False
    
    async def test_mqtt_real_connection(self):
        """Testa connessione MQTT reale"""
        print(f"\n📡 TEST CONNESSIONE MQTT REALE")
        print("=" * 35)
        
        try:
            from rfid_gate.network.mqtt import AsyncMQTTClient
            
            # Crea client MQTT
            mqtt_client = AsyncMQTTClient(self.config)
            
            print(f"🔧 Configurazione MQTT:")
            print(f"   Host: {self.config.mqtt.broker}")
            print(f"   Port: {self.config.mqtt.port}")
            print(f"   Username: {self.config.mqtt.username}")
            print(f"   Client ID: {getattr(self.config.mqtt, 'client_id', 'auto-generated')}")
            
            # Test connessione
            print(f"\n📡 Tentativo connessione...")
            
            # Simula invio messaggio
            from rfid_gate.network.mqtt import CardReadMessage
            
            test_message = CardReadMessage(
                card_uid="TEST001",
                direction="in",
                timestamp=time.time(),
                reader_type="test",
                tornello_id=self.config.system.tornello_id,
                auth_required=True
            )
            
            # Test invio (questo dovrebbe connettersi al broker reale)
            success = await mqtt_client.send_card_read(test_message)
            
            print(f"📤 Invio messaggio test: {'✅' if success else '❌'}")
            
            if success:
                print("✅ MQTT connessione e invio riusciti")
            else:
                print("⚠️ MQTT invio fallito (normale se broker offline)")
            
            # Cleanup
            await mqtt_client.cleanup()
            
            return success
            
        except Exception as e:
            print(f"❌ Errore MQTT: {e}")
            return False
    
    def print_final_report(self):
        """Stampa report finale completo"""
        print(f"\n📊 REPORT FINALE TEST REALI")
        print("=" * 35)
        
        if not self.test_results:
            print("❌ Nessun risultato da riportare")
            return
        
        # Statistiche
        total_tests = len(self.test_results)
        successful = len([r for r in self.test_results if r.get('decision') not in ['error']])
        errors = total_tests - successful
        
        print(f"📈 STATISTICHE:")
        print(f"   Test totali: {total_tests}")
        print(f"   Successi: {successful}")
        print(f"   Errori: {errors}")
        print(f"   Success rate: {100*successful/total_tests:.1f}%")
        
        # Performance
        auth_times = [r.get('auth_time_ms', 0) for r in self.test_results if 'auth_time_ms' in r]
        if auth_times:
            avg_time = sum(auth_times) / len(auth_times)
            min_time = min(auth_times)
            max_time = max(auth_times)
            
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Tempo medio: {avg_time:.1f}ms")
            print(f"   Tempo min: {min_time:.1f}ms")
            print(f"   Tempo max: {max_time:.1f}ms")
        
        # Dettagli per carta
        print(f"\n📋 DETTAGLI PER CARTA:")
        for result in self.test_results:
            uid = result['card_uid']
            decision = result['decision']
            time_ms = result.get('auth_time_ms', 0)
            
            status = "✅" if decision not in ['error'] else "❌"
            print(f"   {status} {uid}: {decision} ({time_ms:.1f}ms)")
        
        # Salva report su file
        self.save_report_to_file()
    
    def save_report_to_file(self):
        """Salva report su file JSON"""
        try:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'test_type': 'real_world_intelligent_flow',
                'config': {
                    'mqtt_host': self.config.mqtt.broker,
                    'mqtt_port': self.config.mqtt.port,
                    'cache_server': self.config.sync.cache_sync_server_url,
                    'gate_server': self.config.sync.server_url,
                    'tornello_id': self.config.system.tornello_id
                },
                'results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'successful': len([r for r in self.test_results if r.get('decision') not in ['error']]),
                    'avg_auth_time_ms': sum([r.get('auth_time_ms', 0) for r in self.test_results]) / len(self.test_results) if self.test_results else 0
                }
            }
            
            filename = f"real_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Report salvato: {filename}")
            
        except Exception as e:
            print(f"❌ Errore salvataggio report: {e}")

async def main():
    """Test principale con endpoint e MQTT reali"""
    
    print("🧪 TEST REALE FLUSSO INTELLIGENTE")
    print("🌐 CON ENDPOINT E MQTT REALI")
    print("=" * 50)
    
    tester = RealWorldTester()
    
    # 1. Test endpoint diretti
    print(f"🔗 FASE 1: Test endpoint HTTP...")
    await tester.test_direct_endpoints()
    
    # 2. Test connessione MQTT
    print(f"\n📡 FASE 2: Test MQTT...")
    await tester.test_mqtt_real_connection()
    
    # 3. Test sistema completo
    print(f"\n🚀 FASE 3: Test sistema completo...")
    await tester.test_real_system_startup()
    
    # 4. Report finale
    tester.print_final_report()
    
    print(f"\n🎉 TEST REALI COMPLETATI!")
    print(f"Verifica i log del server per controllare che ci sia UN SOLO log per carta.")

if __name__ == "__main__":
    asyncio.run(main())