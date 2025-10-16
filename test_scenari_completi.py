#!/usr/bin/env python3
"""
🧪 Test Completo Scenari Reali - Flusso Intelligente
===================================================

Testa tutti i casi del flusso intelligente con endpoint reali:

📱 CASO 1: Carta in cache → Cache auth + MQTT parallelo
📱 CASO 2: Carta NON in cache → Cache refresh → Fallback diretto (NO MQTT)  
📱 CASO 3: Carta scaduta → Cache refresh → Cache auth + MQTT parallelo
🔓 WHITELIST: Bypass completo con accesso sempre garantito

Monitora endpoint reali, performance e log server.
"""

import sys
import os
import asyncio
import time
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Aggiungi il path del progetto
sys.path.append(str(Path(__file__).parent))

class IntelligentFlowTester:
    """Tester completo per il flusso intelligente"""
    
    def __init__(self):
        # Configurazione endpoint dal .env
        from rfid_gate.config.settings import load_env_file
        load_env_file()
        
        self.cache_server_url = os.getenv('CACHE_SYNC_SERVER_URL', 'http://localhost:8000')
        self.cache_refresh_endpoint = os.getenv('CACHE_REFRESH_SINGLE_CARD_ENDPOINT', '/api/sync-gate')
        self.gate_verification_endpoint = os.getenv('GATE_VERIFICATION_ENDPOINT', '/api/gate-verification')
        
        self.results = {}
        self.performance_stats = {}
        
        print(f"🔧 CONFIGURAZIONE TEST")
        print(f"   Cache server: {self.cache_server_url}")
        print(f"   Cache refresh: {self.cache_refresh_endpoint}")
        print(f"   Gate verification: {self.gate_verification_endpoint}")
    
    async def test_cache_hit_scenario(self):
        """
        📱 CASO 1: Carta in Cache
        - Carta presente e valida in cache locale
        - Accesso immediato da cache
        - MQTT parallelo per logging server
        """
        print(f"\n📱 CASO 1: TEST CACHE HIT")
        print("=" * 30)
        
        test_card = "CACHE001"  # Carta che dovrebbe essere in cache
        start_time = time.time()
        
        try:
            # Simula il flusso del access_control.py
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import RFIDGateConfig
            
            config = RFIDGateConfig.from_env()
            sync_manager = SyncManager(
                config=config.sync,
                tornello_id=config.system.tornello_id
            )
            await sync_manager.start_background_sync()
            
            # 1. Check cache locale
            cache_result = await sync_manager.validate_card_offline(test_card, "in")
            cache_time = time.time() - start_time
            
            print(f"⏱️ Cache check: {cache_time*1000:.1f}ms")
            print(f"📋 Cache result: {cache_result}")
            
            if cache_result['authorized']:
                print(f"✅ CASO 1 CONFERMATO: Carta {test_card} in cache")
                
                # 2. Simula MQTT parallelo (non bloccante)
                mqtt_start = time.time()
                mqtt_success = await self._simulate_mqtt_parallel(test_card, "in")
                mqtt_time = time.time() - mqtt_start
                
                print(f"📡 MQTT parallelo: {mqtt_time*1000:.1f}ms - {'✅' if mqtt_success else '❌'}")
                
                # 3. Log locale
                await sync_manager.log_access(
                    card_uid=test_card,
                    direction="in", 
                    result="authorized",
                    reason=f"{cache_result['reason']} | Cache",
                    customer_id=cache_result.get('customer_id'),
                    reader_type="test"
                )
                
                total_time = time.time() - start_time
                
                self.results['caso_1'] = {
                    'success': True,
                    'cache_time_ms': cache_time * 1000,
                    'mqtt_time_ms': mqtt_time * 1000,
                    'total_time_ms': total_time * 1000,
                    'authorized': True,
                    'source': 'cache'
                }
                
                print(f"✅ CASO 1 COMPLETATO: {total_time*1000:.1f}ms totali")
                print(f"   → Cache: {cache_time*1000:.1f}ms")
                print(f"   → MQTT: {mqtt_time*1000:.1f}ms (parallelo)")
                
            else:
                print(f"❌ CASO 1 FALLITO: Carta {test_card} non in cache o non valida")
                self.results['caso_1'] = {
                    'success': False,
                    'reason': cache_result.get('reason', 'Cache miss')
                }
            
            await sync_manager.cleanup()
            
        except Exception as e:
            print(f"❌ Errore CASO 1: {e}")
            self.results['caso_1'] = {'success': False, 'error': str(e)}
    
    async def test_cache_miss_scenario(self):
        """
        📱 CASO 2: Carta NON in Cache
        - Carta non presente in cache locale
        - Cache refresh: GET /api/sync-gate
        - Se non trovata: Fallback diretto POST /api/gate-verification
        - NO MQTT parallelo per evitare duplicati
        """
        print(f"\n📱 CASO 2: TEST CACHE MISS + FALLBACK DIRETTO")
        print("=" * 45)
        
        test_card = "MISS001"  # Carta che non dovrebbe essere in cache
        start_time = time.time()
        
        try:
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import RFIDGateConfig
            
            config = RFIDGateConfig.from_env()
            sync_manager = SyncManager(
                config=config.sync,
                tornello_id=config.system.tornello_id
            )
            await sync_manager.start_background_sync()
            
            # 1. Check cache locale (dovrebbe fallire)
            cache_result = await sync_manager.validate_card_offline(test_card, "in")
            cache_time = time.time() - start_time
            
            print(f"⏱️ Cache check: {cache_time*1000:.1f}ms")
            print(f"📋 Cache result: {cache_result}")
            
            if not cache_result['authorized']:
                print(f"✅ Cache miss confermato per {test_card}")
                
                # 2. Cache refresh: GET /api/sync-gate
                refresh_start = time.time()
                refresh_success = await self._test_cache_refresh(test_card)
                refresh_time = time.time() - refresh_start
                
                print(f"🔄 Cache refresh: {refresh_time*1000:.1f}ms - {'✅' if refresh_success else '❌'}")
                
                if not refresh_success:
                    print(f"📭 Cache refresh non ha trovato {test_card}")
                    
                    # 3. Fallback diretto: POST /api/gate-verification
                    fallback_start = time.time()
                    fallback_result = await self._test_direct_gate_verification(test_card, "in")
                    fallback_time = time.time() - fallback_start
                    
                    print(f"🔗 Fallback diretto: {fallback_time*1000:.1f}ms")
                    print(f"📋 Fallback result: {fallback_result}")
                    
                    # 4. NO MQTT parallelo (importante per evitare duplicati)
                    print(f"❌ NO MQTT parallelo (prevenzione duplicati)")
                    
                    # 5. Log locale
                    if fallback_result.get('authorized'):
                        await sync_manager.log_access(
                            card_uid=test_card,
                            direction="in",
                            result="authorized", 
                            reason=f"{fallback_result['reason']} | Fallback",
                            customer_id=fallback_result.get('customer_id'),
                            reader_type="test"
                        )
                    
                    total_time = time.time() - start_time
                    
                    self.results['caso_2'] = {
                        'success': True,
                        'cache_time_ms': cache_time * 1000,
                        'refresh_time_ms': refresh_time * 1000,
                        'fallback_time_ms': fallback_time * 1000,
                        'total_time_ms': total_time * 1000,
                        'authorized': fallback_result.get('authorized', False),
                        'source': 'fallback_direct',
                        'no_mqtt': True
                    }
                    
                    print(f"✅ CASO 2 COMPLETATO: {total_time*1000:.1f}ms totali")
                    print(f"   → Cache miss: {cache_time*1000:.1f}ms")
                    print(f"   → Cache refresh: {refresh_time*1000:.1f}ms") 
                    print(f"   → Fallback diretto: {fallback_time*1000:.1f}ms")
                    print(f"   → Autorizzato: {fallback_result.get('authorized', False)}")
                    
                else:
                    # Cache refresh ha funzionato - dovrebbe essere CASO 3
                    print(f"🔄 Cache refresh riuscito - questo diventa CASO 3")
                    
            else:
                print(f"⚠️ CASO 2 SKIP: Carta {test_card} in realtà è in cache")
                
            await sync_manager.cleanup()
            
        except Exception as e:
            print(f"❌ Errore CASO 2: {e}")
            self.results['caso_2'] = {'success': False, 'error': str(e)}
    
    async def test_cache_refresh_scenario(self):
        """
        📱 CASO 3: Carta Scaduta/Rinnovata
        - Carta in cache ma scaduta
        - Cache refresh: GET /api/sync-gate trova dati aggiornati
        - Cache viene aggiornata
        - Autenticazione da cache aggiornata
        - MQTT parallelo per logging
        """
        print(f"\n📱 CASO 3: TEST CACHE REFRESH + ACCESSO")
        print("=" * 40)
        
        test_card = "REFRESH001"  # Carta che potrebbe essere scaduta ma rinnovabile
        start_time = time.time()
        
        try:
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import RFIDGateConfig
            
            config = RFIDGateConfig.from_env()
            sync_manager = SyncManager(
                config=config.sync,
                tornello_id=config.system.tornello_id
            )
            await sync_manager.start_background_sync()
            
            # 1. Check cache locale (potrebbe essere scaduta)
            cache_result_1 = await sync_manager.validate_card_offline(test_card, "in")
            cache_time = time.time() - start_time
            
            print(f"⏱️ Cache check iniziale: {cache_time*1000:.1f}ms")
            print(f"📋 Cache result iniziale: {cache_result_1}")
            
            # 2. Simula cache refresh anche se carta valida (per testare il flusso)
            refresh_start = time.time()
            refresh_success = await self._test_cache_refresh(test_card)
            refresh_time = time.time() - refresh_start
            
            print(f"🔄 Cache refresh: {refresh_time*1000:.1f}ms - {'✅' if refresh_success else '❌'}")
            
            if refresh_success:
                # 3. Ricontrolla cache dopo refresh
                cache_result_2 = await sync_manager.validate_card_offline(test_card, "in")
                recheck_time = time.time() - refresh_start - refresh_time
                
                print(f"⏱️ Cache recheck: {recheck_time*1000:.1f}ms")
                print(f"📋 Cache result dopo refresh: {cache_result_2}")
                
                if cache_result_2['authorized']:
                    print(f"✅ CASO 3 CONFERMATO: Cache refresh risolto per {test_card}")
                    
                    # 4. MQTT parallelo per logging
                    mqtt_start = time.time()
                    mqtt_success = await self._simulate_mqtt_parallel(test_card, "in")
                    mqtt_time = time.time() - mqtt_start
                    
                    print(f"📡 MQTT parallelo: {mqtt_time*1000:.1f}ms - {'✅' if mqtt_success else '❌'}")
                    
                    # 5. Log locale
                    await sync_manager.log_access(
                        card_uid=test_card,
                        direction="in",
                        result="authorized",
                        reason=f"{cache_result_2['reason']} | Cache Refreshed",
                        customer_id=cache_result_2.get('customer_id'),
                        reader_type="test"
                    )
                    
                    total_time = time.time() - start_time
                    
                    self.results['caso_3'] = {
                        'success': True,
                        'cache_time_ms': cache_time * 1000,
                        'refresh_time_ms': refresh_time * 1000,
                        'recheck_time_ms': recheck_time * 1000,
                        'mqtt_time_ms': mqtt_time * 1000,
                        'total_time_ms': total_time * 1000,
                        'authorized': True,
                        'source': 'cache_refreshed'
                    }
                    
                    print(f"✅ CASO 3 COMPLETATO: {total_time*1000:.1f}ms totali")
                    print(f"   → Cache iniziale: {cache_time*1000:.1f}ms")
                    print(f"   → Cache refresh: {refresh_time*1000:.1f}ms")
                    print(f"   → Cache recheck: {recheck_time*1000:.1f}ms")
                    print(f"   → MQTT parallelo: {mqtt_time*1000:.1f}ms")
                    
            await sync_manager.cleanup()
            
        except Exception as e:
            print(f"❌ Errore CASO 3: {e}")
            self.results['caso_3'] = {'success': False, 'error': str(e)}
    
    async def test_whitelist_scenario(self):
        """
        🔓 WHITELIST: Bypass Completo
        - Carta in whitelist
        - Accesso garantito sempre (bypass IN/OUT)
        - MQTT parallelo per logging
        - Priorità assoluta su tutto
        """
        print(f"\n🔓 WHITELIST: TEST BYPASS COMPLETO")
        print("=" * 35)
        
        test_card = "WHITE001"  # Carta whitelist
        start_time = time.time()
        
        try:
            from rfid_gate.network.sync_manager import SyncManager
            from rfid_gate.config.settings import RFIDGateConfig
            
            config = RFIDGateConfig.from_env()
            sync_manager = SyncManager(
                config=config.sync,
                tornello_id=config.system.tornello_id
            )
            await sync_manager.start_background_sync()
            
            # 1. Check whitelist (simula il flusso access_control.py)
            cache_result = await sync_manager.validate_card_offline(test_card, "in")
            cache_time = time.time() - start_time
            
            print(f"⏱️ Cache check: {cache_time*1000:.1f}ms")
            print(f"📋 Cache result: {cache_result}")
            
            # Verifica se è whitelist
            subscription_info = cache_result.get('subscription_info', {})
            is_whitelist = (
                subscription_info.get('in_white_list', False) or 
                subscription_info.get('type') == 'whitelist'
            )
            
            if is_whitelist:
                print(f"🔓 WHITELIST CONFERMATA per {test_card}")
                print(f"   → Bypass IN/OUT: ✅")
                print(f"   → Accesso garantito: ✅")
                
                # 2. MQTT parallelo per logging (non per autorizzazione)
                mqtt_start = time.time()
                mqtt_success = await self._simulate_mqtt_parallel(test_card, "in")
                mqtt_time = time.time() - mqtt_start
                
                print(f"📡 MQTT parallelo: {mqtt_time*1000:.1f}ms - {'✅' if mqtt_success else '❌'}")
                
                # 3. Log locale whitelist
                await sync_manager.log_access(
                    card_uid=test_card,
                    direction="in",
                    result="authorized",
                    reason="Carta in whitelist - accesso sempre autorizzato (bypass IN/OUT)",
                    customer_id=cache_result.get('customer_id'),
                    reader_type="test"
                )
                
                total_time = time.time() - start_time
                
                self.results['whitelist'] = {
                    'success': True,
                    'cache_time_ms': cache_time * 1000,
                    'mqtt_time_ms': mqtt_time * 1000,
                    'total_time_ms': total_time * 1000,
                    'authorized': True,
                    'source': 'whitelist',
                    'bypass_in_out': True
                }
                
                print(f"✅ WHITELIST COMPLETATA: {total_time*1000:.1f}ms totali")
                print(f"   → Cache check: {cache_time*1000:.1f}ms")
                print(f"   → MQTT parallelo: {mqtt_time*1000:.1f}ms")
                print(f"   → Bypass completo: ✅")
                
            else:
                print(f"❌ WHITELIST: Carta {test_card} non in whitelist")
                self.results['whitelist'] = {
                    'success': False,
                    'reason': 'Not in whitelist'
                }
            
            await sync_manager.cleanup()
            
        except Exception as e:
            print(f"❌ Errore WHITELIST: {e}")
            self.results['whitelist'] = {'success': False, 'error': str(e)}
    
    async def _simulate_mqtt_parallel(self, card_uid: str, direction: str) -> bool:
        """Simula invio MQTT parallelo (non-bloccante)"""
        try:
            # Simula latenza MQTT
            await asyncio.sleep(0.1)  # 100ms simulated
            print(f"📡 MQTT simulato per {card_uid} ({direction})")
            return True
        except Exception as e:
            print(f"❌ MQTT error: {e}")
            return False
    
    async def _test_cache_refresh(self, card_uid: str) -> bool:
        """Testa cache refresh reale: GET /api/sync-gate"""
        try:
            url = f"{self.cache_server_url}{self.cache_refresh_endpoint}"
            params = {'card_uid': card_uid}
            
            print(f"🔄 Cache refresh: GET {url}?card_uid={card_uid}")
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Cache refresh OK: {data}")
                        return data.get('success', False)
                    else:
                        error = await response.text()
                        print(f"❌ Cache refresh error {response.status}: {error}")
                        return False
                        
        except Exception as e:
            print(f"❌ Cache refresh exception: {e}")
            return False
    
    async def _test_direct_gate_verification(self, card_uid: str, direction: str) -> Dict:
        """Testa fallback diretto: POST /api/gate-verification"""
        try:
            url = f"{self.cache_server_url}{self.gate_verification_endpoint}"
            payload = {
                "uid": card_uid,
                "identificativo_tornello": "tornello_test",
                "direction": direction
            }
            
            print(f"🔗 Gate verification: POST {url}")
            print(f"📤 Payload: {payload}")
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Gate verification OK: {data}")
                        return {
                            'authorized': data.get('authorized', False),
                            'reason': data.get('message', 'Gate verification response'),
                            'card_data': data.get('card_data', {}),
                            'customer_id': data.get('card_data', {}).get('customer_id')
                        }
                    else:
                        error = await response.text()
                        print(f"❌ Gate verification error {response.status}: {error}")
                        return {
                            'authorized': False,
                            'reason': f'Gate verification error: HTTP {response.status}'
                        }
                        
        except Exception as e:
            print(f"❌ Gate verification exception: {e}")
            return {
                'authorized': False,
                'reason': f'Gate verification exception: {str(e)}'
            }
    
    def print_final_results(self):
        """Stampa risultati finali completi"""
        print(f"\n📊 RISULTATI FINALI TEST SCENARI")
        print("=" * 40)
        
        for scenario, result in self.results.items():
            print(f"\n{scenario.upper()}:")
            if result.get('success'):
                print(f"   ✅ Successo")
                if 'total_time_ms' in result:
                    print(f"   ⏱️ Tempo totale: {result['total_time_ms']:.1f}ms")
                if 'authorized' in result:
                    print(f"   🔐 Autorizzato: {result['authorized']}")
                if 'source' in result:
                    print(f"   📍 Source: {result['source']}")
                if result.get('no_mqtt'):
                    print(f"   📡 MQTT: ❌ (prevenzione duplicati)")
                elif 'mqtt_time_ms' in result:
                    print(f"   📡 MQTT: ✅ ({result['mqtt_time_ms']:.1f}ms parallelo)")
            else:
                print(f"   ❌ Fallito")
                if 'error' in result:
                    print(f"   🔴 Errore: {result['error']}")
                if 'reason' in result:
                    print(f"   🔴 Motivo: {result['reason']}")
        
        # Performance summary
        print(f"\n⚡ PERFORMANCE SUMMARY:")
        cache_times = [r.get('cache_time_ms', 0) for r in self.results.values() if r.get('success')]
        if cache_times:
            avg_cache = sum(cache_times) / len(cache_times)
            print(f"   📄 Cache avg: {avg_cache:.1f}ms")
            
        total_times = [r.get('total_time_ms', 0) for r in self.results.values() if r.get('success')]
        if total_times:
            avg_total = sum(total_times) / len(total_times)  
            print(f"   🎯 Total avg: {avg_total:.1f}ms")
        
        # Success rate
        successful = len([r for r in self.results.values() if r.get('success')])
        total = len(self.results)
        print(f"   📈 Success rate: {successful}/{total} ({100*successful/total:.0f}%)")

async def main():
    """Test principale"""
    
    print("🧪 TEST COMPLETO SCENARI FLUSSO INTELLIGENTE")
    print("=" * 50)
    
    tester = IntelligentFlowTester()
    
    # Test tutti gli scenari
    await tester.test_cache_hit_scenario()
    await tester.test_cache_miss_scenario()
    await tester.test_cache_refresh_scenario()
    await tester.test_whitelist_scenario()
    
    # Risultati finali
    tester.print_final_results()
    
    print(f"\n🎉 TEST SCENARI COMPLETATI!")
    print(f"Verifica che ogni scenario produca UN SOLO log server")
    print(f"e che MQTT parallelo funzioni correttamente.")

if __name__ == "__main__":
    asyncio.run(main())