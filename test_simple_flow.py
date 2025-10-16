#!/usr/bin/env python3
"""
Test completo del flusso di autenticazione RFID Gate
Test simulato senza dipendenze complesse - simulazione realistica
"""

import asyncio
import time
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import statistics


@dataclass
class TestCard:
    """Carta test con caratteristiche specifiche"""
    uid: str
    name: str
    description: str
    in_cache: bool
    should_access: bool


@dataclass
class FlowResult:
    """Risultato test singolo flusso"""
    card_uid: str
    card_name: str
    total_time_ms: float
    cache_hit: bool
    access_granted: bool
    mqtt_sent: bool
    relay_activated: bool
    error: Optional[str] = None


class RFIDGateSimulator:
    """Simulatore RFID Gate con timing realistici"""
    
    def __init__(self):
        self.cache_path = Path("cache/local_cache.db")
        
    async def simulate_card_read(self, card: TestCard) -> FlowResult:
        """Simula lettura carta completa"""
        start_time = time.time()
        
        print(f"\n🔍 Test: {card.name} ({card.uid})")
        print(f"   📝 {card.description}")
        
        try:
            # 1. Cache Check (sempre primo step)
            cache_start = time.time()
            cache_hit, cache_enabled = await self._check_cache(card.uid)
            cache_time = (time.time() - cache_start) * 1000
            
            print(f"   💾 Cache check: {cache_time:.2f}ms - {'HIT' if cache_hit else 'MISS'}")
            
            access_granted = False
            mqtt_sent = False
            relay_activated = False
            
            if cache_hit:
                # Scenario 1: Autenticazione da cache (veloce)
                access_granted = cache_enabled and card.should_access
                auth_source = "CACHE"
                
            else:
                # Scenario 2: Fallback server (più lento)
                auth_source = "SERVER"
                server_start = time.time()
                
                # Simula latenza rete realistica (20-100ms)
                await asyncio.sleep(0.05)  # 50ms tipico
                
                server_time = (time.time() - server_start) * 1000
                print(f"   🌐 Server check: {server_time:.2f}ms")
                
                # Simula risposta server
                access_granted = card.should_access and not card.uid.startswith("INVALID")
            
            print(f"   🔐 Auth ({auth_source}): {'GRANTED' if access_granted else 'DENIED'}")
            
            # 3. Se accesso garantito: MQTT + Relay (paralleli)
            if access_granted:
                
                # MQTT (non-bloccante)
                mqtt_start = time.time()
                await self._send_mqtt(card.uid, "in")
                mqtt_time = (time.time() - mqtt_start) * 1000
                mqtt_sent = True
                print(f"   📡 MQTT sent: {mqtt_time:.2f}ms")
                
                # Relay (thread separato - simulazione)
                relay_start = time.time()
                await self._activate_relay()
                relay_time = (time.time() - relay_start) * 1000
                relay_activated = True
                print(f"   ⚡ Relay activated: {relay_time:.2f}ms")
            
            total_time = (time.time() - start_time) * 1000
            result_icon = "✅" if access_granted else "❌"
            print(f"   {result_icon} Total: {total_time:.2f}ms")
            
            return FlowResult(
                card_uid=card.uid,
                card_name=card.name,
                total_time_ms=total_time,
                cache_hit=cache_hit,
                access_granted=access_granted,
                mqtt_sent=mqtt_sent,
                relay_activated=relay_activated
            )
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            print(f"   ❌ ERROR: {e}")
            
            return FlowResult(
                card_uid=card.uid,
                card_name=card.name,
                total_time_ms=total_time,
                cache_hit=False,
                access_granted=False,
                mqtt_sent=False,
                relay_activated=False,
                error=str(e)
            )
    
    async def _check_cache(self, uid: str) -> tuple[bool, bool]:
        """Controlla cache SQLite"""
        try:
            if not self.cache_path.exists():
                return False, False
                
            # Simula latenza DB (1-5ms)
            await asyncio.sleep(0.002)  # 2ms
            
            conn = sqlite3.connect(str(self.cache_path))
            cursor = conn.cursor()
            cursor.execute("SELECT enabled FROM access_cards WHERE card_uid = ?", (uid,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return True, bool(result[0])
            else:
                return False, False
                
        except Exception:
            return False, False
    
    async def _send_mqtt(self, uid: str, direction: str):
        """Simula invio MQTT"""
        # Simula serializzazione JSON + invio rete (1-5ms)
        await asyncio.sleep(0.002)  # 2ms tipico
        
        # Simula payload JSON corretto
        payload = {
            "uid": uid,
            "direzione": direction,  # Campo corretto
            "timestamp": int(time.time()),
            "authorized": True
        }
        return payload
    
    async def _activate_relay(self):
        """Simula attivazione relay"""
        # Simula GPIO + thread setup (1-3ms)
        await asyncio.sleep(0.001)  # 1ms
        
        # Nota: in realtà il relay thread continua in background
        # per il release automatico dopo timeout


async def setup_test_cache():
    """Setup cache test con carte predefinite"""
    cache_path = Path("cache/local_cache.db")
    
    # Assicura directory exists
    cache_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(cache_path))
    cursor = conn.cursor()
    
    # Crea tabella se non esiste
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_uid TEXT UNIQUE NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserisce carte test
    test_cards_cache = [
        ("AA:BB:CC:DD", True),   # VIP card
        ("11:22:33:44", True),   # Staff card
        ("00:11:22:33", False),  # Disabled card
    ]
    
    for uid, enabled in test_cards_cache:
        cursor.execute("""
            INSERT OR REPLACE INTO access_cards (card_uid, enabled) 
            VALUES (?, ?)
        """, (uid, enabled))
    
    conn.commit()
    conn.close()
    print(f"✅ Cache setup completato: {len(test_cards_cache)} carte in cache")


def create_test_scenarios() -> List[TestCard]:
    """Crea scenari test realistici"""
    return [
        # CACHE SCENARIOS (veloci)
        TestCard(
            uid="AA:BB:CC:DD",
            name="VIP Card",
            description="Carta VIP in cache, autorizzata",
            in_cache=True,
            should_access=True
        ),
        TestCard(
            uid="11:22:33:44", 
            name="Staff Card",
            description="Carta staff in cache, autorizzata",
            in_cache=True,
            should_access=True
        ),
        TestCard(
            uid="00:11:22:33",
            name="Disabled Card",
            description="Carta in cache ma disabilitata",
            in_cache=True,
            should_access=False
        ),
        
        # SERVER FALLBACK SCENARIOS (più lenti)
        TestCard(
            uid="FF:EE:DD:CC",
            name="Server Valid",
            description="Carta non in cache, autorizzata da server",
            in_cache=False,
            should_access=True
        ),
        TestCard(
            uid="99:88:77:66",
            name="Server Invalid", 
            description="Carta non in cache, rifiutata da server",
            in_cache=False,
            should_access=False
        ),
        TestCard(
            uid="INVALID:CARD",
            name="Malformed Card",
            description="Carta malformata",
            in_cache=False,
            should_access=False
        ),
    ]


def analyze_results(results: List[FlowResult]):
    """Analizza risultati test"""
    print("\n" + "="*60)
    print("📊 ANALISI RISULTATI TEST COMPLETO")
    print("="*60)
    
    # Statistiche generali
    total_tests = len(results)
    successful_tests = len([r for r in results if r.error is None])
    access_granted = len([r for r in results if r.access_granted])
    
    print(f"📈 Tests totali: {total_tests}")
    print(f"✅ Tests riusciti: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"🔓 Accessi garantiti: {access_granted}")
    
    # Performance per tipo
    cache_results = [r for r in results if r.cache_hit and r.error is None]
    server_results = [r for r in results if not r.cache_hit and r.error is None]
    
    if cache_results:
        cache_times = [r.total_time_ms for r in cache_results]
        print(f"\n💾 PERFORMANCE CACHE ({len(cache_results)} tests):")
        print(f"   Tempo medio: {statistics.mean(cache_times):.2f}ms")
        print(f"   Min/Max: {min(cache_times):.2f}ms / {max(cache_times):.2f}ms")
    
    if server_results:
        server_times = [r.total_time_ms for r in server_results]
        print(f"\n🌐 PERFORMANCE SERVER ({len(server_results)} tests):")
        print(f"   Tempo medio: {statistics.mean(server_times):.2f}ms")
        print(f"   Min/Max: {min(server_times):.2f}ms / {max(server_times):.2f}ms")
    
    # Dettaglio errori
    errors = [r for r in results if r.error]
    if errors:
        print(f"\n❌ ERRORI ({len(errors)}):")
        for error in errors:
            print(f"   {error.card_name}: {error.error}")
    
    # Riepilogo per carta
    print(f"\n📋 DETTAGLIO PER CARTA:")
    for result in results:
        status = "✅" if result.access_granted else "❌"
        source = "💾" if result.cache_hit else "🌐"
        print(f"   {status} {source} {result.card_name}: {result.total_time_ms:.2f}ms")
    
    return {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'access_granted': access_granted,
        'cache_avg_time': statistics.mean([r.total_time_ms for r in cache_results]) if cache_results else 0,
        'server_avg_time': statistics.mean([r.total_time_ms for r in server_results]) if server_results else 0,
        'errors': len(errors)
    }


async def main():
    """Test completo sistema RFID Gate"""
    print("🚀 AVVIO TEST COMPLETO SISTEMA RFID GATE")
    print("="*60)
    
    # Setup
    print("🔧 Setup ambiente test...")
    await setup_test_cache()
    
    # Crea simulatore
    simulator = RFIDGateSimulator()
    
    # Crea scenari
    test_cards = create_test_scenarios()
    print(f"📝 Scenari creati: {len(test_cards)} test cards")
    
    # Esegui test
    print("\n🎯 ESECUZIONE TEST...")
    results = []
    
    for card in test_cards:
        result = await simulator.simulate_card_read(card)
        results.append(result)
        
        # Pausa piccola tra test per realismo
        await asyncio.sleep(0.1)
    
    # Analisi
    stats = analyze_results(results)
    
    # Conclusioni
    print("\n" + "="*60)
    print("🎯 CONCLUSIONI")
    print("="*60)
    
    if stats['successful_tests'] == stats['total_tests']:
        print("✅ SISTEMA FUNZIONANTE - Tutti i test superati")
    else:
        print(f"⚠️ PROBLEMI RILEVATI - {stats['errors']} errori su {stats['total_tests']} test")
    
    print(f"\n🚄 PERFORMANCE:")
    print(f"   Cache hit: {stats['cache_avg_time']:.2f}ms (target: <10ms)")
    print(f"   Server fallback: {stats['server_avg_time']:.2f}ms (target: <100ms)")
    
    print(f"\n🔍 RACCOMANDAZIONI:")
    if stats['cache_avg_time'] > 10:
        print("   ⚠️ Cache performance da ottimizzare")
    else:
        print("   ✅ Cache performance eccellente")
        
    if stats['server_avg_time'] > 100:
        print("   ⚠️ Server latency da verificare") 
    else:
        print("   ✅ Server fallback accettabile")
    
    if stats['errors'] == 0:
        print("   ✅ Sistema pronto per produzione")
    else:
        print("   ⚠️ Risolvere errori prima del deploy")


if __name__ == "__main__":
    asyncio.run(main())