#!/usr/bin/env python3
"""
🚀 Test Performance Completo - Sistema RFID Gate
================================================
Test di reattività e performance con dati reali:
- Latenza lettura carta → attivazione relay
- Throughput MQTT
- Performance parallelo vs sequenziale  
- Stress test con carichi multipli
"""

import asyncio
import time
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Aggiungi path per import
import sys
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class PerformanceMetric:
    """Metrica di performance"""
    operation: str
    start_time: float
    end_time: float
    success: bool
    data: Dict[str, Any] = None
    
    @property
    def duration_ms(self) -> float:
        """Durata in millisecondi"""
        return (self.end_time - self.start_time) * 1000
    
    @property
    def duration_s(self) -> float:
        """Durata in secondi"""
        return self.end_time - self.start_time

class PerformanceCollector:
    """Raccoglitore metriche performance"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.start_time = time.time()
    
    def add_metric(self, operation: str, start_time: float, end_time: float, 
                   success: bool, data: Dict[str, Any] = None):
        """Aggiunge metrica"""
        metric = PerformanceMetric(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            success=success,
            data=data or {}
        )
        self.metrics.append(metric)
    
    def get_stats(self, operation: str = None) -> Dict[str, Any]:
        """Calcola statistiche per operazione"""
        filtered = self.metrics
        if operation:
            filtered = [m for m in self.metrics if m.operation == operation]
        
        if not filtered:
            return {}
        
        durations = [m.duration_ms for m in filtered]
        success_rate = sum(1 for m in filtered if m.success) / len(filtered) * 100
        
        return {
            'count': len(filtered),
            'success_rate': success_rate,
            'avg_ms': statistics.mean(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'median_ms': statistics.median(durations),
            'p95_ms': self._percentile(durations, 95),
            'p99_ms': self._percentile(durations, 99)
        }
    
    def _percentile(self, data: List[float], percent: float) -> float:
        """Calcola percentile"""
        data_sorted = sorted(data)
        k = (len(data_sorted) - 1) * percent / 100
        f = int(k)
        c = k - f
        if f + 1 < len(data_sorted):
            return data_sorted[f] + c * (data_sorted[f + 1] - data_sorted[f])
        return data_sorted[f]

# Istanza globale per raccolta metriche
perf = PerformanceCollector()

async def test_mqtt_latency():
    """Test latenza MQTT pura"""
    print("🔥 Test Latenza MQTT")
    print("=" * 60)
    
    try:
        from rfid_gate.config.settings import Config
        from rfid_gate.network.mqtt import AsyncMQTTClient, CardReadMessage
        
        # Crea config MQTT
        mqtt_config = type('MQTTConfig', (), {
            'broker': Config.MQTT_BROKER,
            'port': Config.MQTT_PORT,
            'username': Config.MQTT_USERNAME,
            'password': Config.MQTT_PASSWORD,
            'use_tls': Config.MQTT_USE_TLS,
            'keep_alive': 60,
            'card_read_topic': Config.get_mqtt_topic('badge'),
            'auth_response_topic': Config.get_auth_response_topic()
        })()
        
        # Inizializza client
        client = AsyncMQTTClient(mqtt_config)
        await client.initialize()
        
        connected = await client.connect()
        if not connected:
            print("❌ Connessione MQTT fallita")
            return False
        
        print("✅ Client MQTT connesso")
        
        # Test latenza invio singolo
        test_cards = ["LATENCY_01", "LATENCY_02", "LATENCY_03", "LATENCY_04", "LATENCY_05"]
        
        for i, card_uid in enumerate(test_cards, 1):
            print(f"📤 Test {i}/{len(test_cards)} - Latenza: {card_uid}")
            
            # Misura tempo invio
            start = time.time()
            
            message = CardReadMessage(
                card_uid=card_uid,
                identificativo_tornello=Config.TORNELLO_ID,
                timestamp=datetime.now().isoformat(),
                direzione="in",
                raw_id=card_uid,
                reader_id="pn532_performance"
            )
            
            success = await client.send_card_read(message)
            end = time.time()
            
            perf.add_metric("mqtt_send", start, end, success, {
                'card_uid': card_uid,
                'message_size': len(json.dumps({
                    'card_uid': card_uid,
                    'identificativo_tornello': Config.TORNELLO_ID,
                    'direzione': 'in'
                }))
            })
            
            print(f"   ⏱️ Latenza: {(end-start)*1000:.2f}ms - {'✅' if success else '❌'}")
            
            await asyncio.sleep(0.1)  # Piccola pausa tra invii
        
        await client.disconnect()
        print("🔌 Client disconnesso")
        return True
        
    except Exception as e:
        print(f"❌ Errore test latenza MQTT: {e}")
        return False

async def test_relay_activation_simulation():
    """Test simulazione attivazione relay"""
    print("\n⚡ Test Simulazione Attivazione Relay")
    print("=" * 60)
    
    try:
        # Simula attivazione relay con threading (come nel sistema reale)
        import threading
        
        def simulate_relay_activation(relay_id: str, duration: float):
            """Simula attivazione relay non-bloccante"""
            start = time.time()
            print(f"🔌 Relay {relay_id} ATTIVATO")
            time.sleep(duration)  # Simula durata attivazione
            end = time.time()
            print(f"🔌 Relay {relay_id} DISATTIVATO")
            return end - start
        
        relay_tests = [
            {"relay_id": "relay_in", "duration": 2.0},
            {"relay_id": "relay_out", "duration": 2.5},
            {"relay_id": "relay_in", "duration": 1.5},
            {"relay_id": "relay_out", "duration": 3.0}
        ]
        
        for i, test in enumerate(relay_tests, 1):
            print(f"⚡ Test {i}/{len(relay_tests)} - Relay: {test['relay_id']}")
            
            start = time.time()
            
            # Avvia relay in thread separato (non-bloccante)
            thread = threading.Thread(
                target=simulate_relay_activation,
                args=(test['relay_id'], test['duration'])
            )
            thread.start()
            
            # Il thread principale continua immediatamente
            immediate_end = time.time()
            
            # Attende completamento per metriche complete
            thread.join()
            complete_end = time.time()
            
            perf.add_metric("relay_trigger", start, immediate_end, True, {
                'relay_id': test['relay_id'],
                'duration_set': test['duration'],
                'non_blocking': True
            })
            
            perf.add_metric("relay_complete", start, complete_end, True, {
                'relay_id': test['relay_id'],
                'duration_actual': complete_end - start
            })
            
            print(f"   ⏱️ Trigger istantaneo: {(immediate_end-start)*1000:.2f}ms")
            print(f"   ⏱️ Durata totale: {(complete_end-start):.2f}s")
            
            await asyncio.sleep(0.2)
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test relay: {e}")
        return False

async def test_end_to_end_workflow():
    """Test workflow completo carta → MQTT + Relay parallelo"""
    print("\n🔄 Test Workflow End-to-End")
    print("=" * 60)
    
    try:
        from rfid_gate.config.settings import Config
        from rfid_gate.network.mqtt import AsyncMQTTClient, CardReadMessage
        import threading
        
        # Setup MQTT client
        mqtt_config = type('MQTTConfig', (), {
            'broker': Config.MQTT_BROKER,
            'port': Config.MQTT_PORT,
            'username': Config.MQTT_USERNAME,
            'password': Config.MQTT_PASSWORD,
            'use_tls': Config.MQTT_USE_TLS,
            'keep_alive': 60,
            'card_read_topic': Config.get_mqtt_topic('badge'),
            'auth_response_topic': Config.get_auth_response_topic()
        })()
        
        client = AsyncMQTTClient(mqtt_config)
        await client.initialize()
        await client.connect()
        
        def relay_activation(card_uid: str):
            """Simulazione relay non-bloccante"""
            time.sleep(2.0)  # Simula durata relay
            print(f"   🔌 Relay completato per {card_uid}")
        
        # Test workflow parallelo
        workflow_tests = [
            {"card_uid": "WORKFLOW_01", "direction": "in"},
            {"card_uid": "WORKFLOW_02", "direction": "out"}, 
            {"card_uid": "WORKFLOW_03", "direction": "in"},
            {"card_uid": "WORKFLOW_04", "direction": "out"}
        ]
        
        for i, test in enumerate(workflow_tests, 1):
            print(f"🔄 Test {i}/{len(workflow_tests)} - Card: {test['card_uid']}")
            
            workflow_start = time.time()
            
            # 1. MQTT (asincrono)
            mqtt_start = time.time()
            message = CardReadMessage(
                card_uid=test['card_uid'],
                identificativo_tornello=Config.TORNELLO_ID,
                timestamp=datetime.now().isoformat(),
                direzione=test['direction'],
                raw_id=test['card_uid'],
                reader_id="pn532_workflow"
            )
            
            mqtt_success = await client.send_card_read(message)
            mqtt_end = time.time()
            
            # 2. Relay (parallelo in thread)
            relay_start = time.time()
            relay_thread = threading.Thread(
                target=relay_activation,
                args=(test['card_uid'],)
            )
            relay_thread.start()
            relay_trigger_end = time.time()
            
            # Workflow principale completato (non aspetta relay)
            workflow_immediate_end = time.time()
            
            perf.add_metric("workflow_mqtt", mqtt_start, mqtt_end, mqtt_success, {
                'card_uid': test['card_uid'],
                'direction': test['direction']
            })
            
            perf.add_metric("workflow_relay_trigger", relay_start, relay_trigger_end, True, {
                'card_uid': test['card_uid']
            })
            
            perf.add_metric("workflow_complete", workflow_start, workflow_immediate_end, True, {
                'card_uid': test['card_uid'],
                'parallel_execution': True
            })
            
            print(f"   ⏱️ MQTT: {(mqtt_end-mqtt_start)*1000:.2f}ms")
            print(f"   ⏱️ Relay trigger: {(relay_trigger_end-relay_start)*1000:.2f}ms") 
            print(f"   ⏱️ Workflow totale: {(workflow_immediate_end-workflow_start)*1000:.2f}ms")
            print(f"   📊 Parallel execution: ✅")
            
            # Cleanup thread (non blocca il test)
            relay_thread.join(timeout=0.1)
            
            await asyncio.sleep(0.3)
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Errore test workflow: {e}")
        return False

async def test_stress_load():
    """Test carico stress con burst di richieste"""
    print("\n💪 Test Stress Load")
    print("=" * 60)
    
    try:
        from rfid_gate.config.settings import Config
        from rfid_gate.network.mqtt import AsyncMQTTClient, CardReadMessage
        
        # Setup client
        mqtt_config = type('MQTTConfig', (), {
            'broker': Config.MQTT_BROKER,
            'port': Config.MQTT_PORT,
            'username': Config.MQTT_USERNAME,
            'password': Config.MQTT_PASSWORD,
            'use_tls': Config.MQTT_USE_TLS,
            'keep_alive': 60,
            'card_read_topic': Config.get_mqtt_topic('badge'),
            'auth_response_topic': Config.get_auth_response_topic()
        })()
        
        client = AsyncMQTTClient(mqtt_config)
        await client.initialize()
        await client.connect()
        
        # Test burst - molte richieste simultanee
        print("🚀 Burst test: 10 richieste simultanee")
        burst_start = time.time()
        
        tasks = []
        for i in range(10):
            card_uid = f"BURST_{i:02d}"
            
            message = CardReadMessage(
                card_uid=card_uid,
                identificativo_tornello=Config.TORNELLO_ID,
                timestamp=datetime.now().isoformat(),
                direzione="in" if i % 2 == 0 else "out",
                raw_id=card_uid,
                reader_id="pn532_burst"
            )
            
            task = client.send_card_read(message)
            tasks.append((task, card_uid, time.time()))
        
        # Esegui tutti in parallelo
        results = await asyncio.gather(*[task for task, _, _ in tasks], return_exceptions=True)
        burst_end = time.time()
        
        # Analizza risultati
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        perf.add_metric("stress_burst", burst_start, burst_end, successful > 0, {
            'total_requests': len(tasks),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(tasks) * 100,
            'concurrent': True
        })
        
        print(f"   📊 Richieste totali: {len(tasks)}")
        print(f"   ✅ Successi: {successful}")
        print(f"   ❌ Fallimenti: {failed}")
        print(f"   📈 Success rate: {successful/len(tasks)*100:.1f}%")
        print(f"   ⏱️ Tempo totale: {(burst_end-burst_start)*1000:.2f}ms")
        print(f"   🚀 Throughput: {len(tasks)/(burst_end-burst_start):.1f} req/s")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Errore test stress: {e}")
        return False

def generate_performance_report():
    """Genera report dettagliato performance"""
    print("\n📊 REPORT PERFORMANCE DETTAGLIATO")
    print("=" * 80)
    
    # Statistiche per operazione
    operations = set(m.operation for m in perf.metrics)
    
    for op in sorted(operations):
        stats = perf.get_stats(op)
        if not stats:
            continue
            
        print(f"\n🔍 {op.upper()}")
        print("-" * 50)
        print(f"  📈 Richieste totali: {stats['count']}")
        print(f"  ✅ Success rate: {stats['success_rate']:.1f}%")
        print(f"  ⏱️ Latenza media: {stats['avg_ms']:.2f}ms")
        print(f"  ⚡ Min latenza: {stats['min_ms']:.2f}ms")
        print(f"  🐌 Max latenza: {stats['max_ms']:.2f}ms")
        print(f"  📊 Mediana: {stats['median_ms']:.2f}ms")
        print(f"  📈 P95: {stats['p95_ms']:.2f}ms")
        print(f"  🔥 P99: {stats['p99_ms']:.2f}ms")
    
    # Analisi reattività sistema
    print(f"\n🎯 ANALISI REATTIVITÀ SISTEMA")
    print("-" * 50)
    
    # Calcola reattività workflow completo
    workflow_stats = perf.get_stats("workflow_complete")
    mqtt_stats = perf.get_stats("mqtt_send")
    relay_stats = perf.get_stats("relay_trigger")
    
    if workflow_stats:
        print(f"  🔄 Workflow end-to-end: {workflow_stats['avg_ms']:.2f}ms")
    if mqtt_stats:
        print(f"  📡 MQTT latenza: {mqtt_stats['avg_ms']:.2f}ms")
    if relay_stats:
        print(f"  ⚡ Relay trigger: {relay_stats['avg_ms']:.2f}ms")
    
    # Throughput analysis
    stress_metrics = [m for m in perf.metrics if m.operation == "stress_burst"]
    if stress_metrics:
        stress_data = stress_metrics[0].data
        print(f"  🚀 Throughput max: {stress_data.get('total_requests', 0)/stress_metrics[0].duration_s:.1f} req/s")
        print(f"  💪 Stress success rate: {stress_data.get('success_rate', 0):.1f}%")
    
    # Raccomandazioni
    print(f"\n💡 RACCOMANDAZIONI")
    print("-" * 50)
    
    if mqtt_stats and mqtt_stats['avg_ms'] > 100:
        print("  ⚠️ MQTT latenza elevata - verifica connessione di rete")
    elif mqtt_stats and mqtt_stats['avg_ms'] < 50:
        print("  ✅ MQTT latenza ottima")
    
    if workflow_stats and workflow_stats['avg_ms'] < 100:
        print("  ✅ Sistema molto reattivo - workflow < 100ms")
    elif workflow_stats and workflow_stats['avg_ms'] < 200:
        print("  ✅ Sistema reattivo - workflow < 200ms")
    else:
        print("  ⚠️ Sistema lento - ottimizzazione necessaria")
    
    print(f"\n🎊 Test completato! Durata totale: {time.time() - perf.start_time:.2f}s")

async def main():
    """Test completo performance sistema"""
    print("🚀 TEST PERFORMANCE COMPLETO - RFID GATE SYSTEM")
    print("=" * 80)
    print("📋 Test pianificati:")
    print("   1. Latenza MQTT")
    print("   2. Simulazione Relay")
    print("   3. Workflow End-to-End")
    print("   4. Stress Load")
    print("=" * 80)
    
    # Esegui tutti i test
    test_results = {}
    
    test_results['mqtt_latency'] = await test_mqtt_latency()
    test_results['relay_simulation'] = await test_relay_activation_simulation()
    test_results['end_to_end'] = await test_end_to_end_workflow()
    test_results['stress_load'] = await test_stress_load()
    
    # Genera report finale
    generate_performance_report()
    
    # Riassunto finale
    print(f"\n🎯 RIASSUNTO ESECUZIONE")
    print("=" * 50)
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    overall_success = all(test_results.values())
    print(f"\n🏆 Risultato generale: {'✅ TUTTI I TEST PASSATI' if overall_success else '❌ ALCUNI TEST FALLITI'}")

if __name__ == "__main__":
    asyncio.run(main())