#!/usr/bin/env python3
"""
Test della logica corretta del flusso intelligente secondo le specifiche aggiornate:

📱 CASO 1: Carta in cache
   → Carta letta → autenticazione cache → apertura relè
   → Log: UNA entry di autorizzazione
   → In parallelo dopo validazione cache: MQTT → broker → gate-verification (non uso risposta)

📱 CASO 2: Carta NON in cache  
   → Carta letta → carta non trovata
   → Cache refresh: GET /api/sync-gate?card_uid=XXX
   → Se trova dati → autenticazione cache e aggiorna dati → MQTT parallelo
   → Se ancora non trova: chiamata /api/gate-verification (senza MQTT parallelo)
   → Log: UNA entry di autorizzazione finale

📱 CASO 3: Carta con abbonamento scaduto
   → Carta letta → abbonamento scaduto o non esistente  
   → Cache refresh: GET /api/sync-gate?card_uid=XXX
   → Se trova rinnovo → autenticazione cache → aggiorna cache
   → Log: UNA entry con nuovo abbonamento
   → In parallelo dopo autenticazione cache: MQTT → broker (non uso risposta)
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any

# Aggiungi il percorso del modulo RFID Gate
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class TestResult:
    """Risultato di un test"""
    case_name: str
    passed: bool
    details: str
    expected_mqtt_parallel: bool
    actual_mqtt_parallel: bool
    log_entries: int

def create_mock_config():
    """Crea una configurazione mock per i test"""
    from rfid_gate.config.settings import RFIDGateConfig
    from rfid_gate.core.events import SystemMode
    
    config = MagicMock()
    config.sync.enabled = True
    config.sync.cache_sync_server_url = "https://gymme-newaction.ddns.net"
    config.auth.enabled = True
    config.system.bidirectional_mode = True
    config.system.tornello_id = "tornello_01"
    
    return config

def create_mock_card_event(uid: str, direction: str = "in"):
    """Crea un evento carta mock"""
    from rfid_gate.core.events import CardEvent
    
    event = MagicMock()
    event.uid_formatted = uid
    event.direction = direction
    event.reader_type = "pn532"
    event.metadata = {}
    
    return event

async def test_caso_1_carta_in_cache():
    """
    CASO 1: Carta in cache
    - Deve autorizzare da cache
    - Deve fare MQTT parallelo
    - Deve loggare UNA entry
    """
    print("🧪 TEST CASO 1: Carta in cache")
    
    from rfid_gate.core.access_control import AccessControl
    from rfid_gate.core.events import SystemMode, AccessDecision
    
    # Setup mock
    config = create_mock_config()
    access_control = AccessControl(config)
    access_control.mode = SystemMode.ONLINE
    
    # Mock sync_manager per carta in cache
    mock_sync_manager = AsyncMock()
    mock_sync_manager.validate_card_offline.return_value = {
        'authorized': True,
        'reason': 'Carta valida in cache',
        'customer_id': 'customer_123',
        'customer_name': 'Test User'
    }
    access_control.sync_manager = mock_sync_manager
    
    # Mock MQTT client per tracciare chiamate parallele
    mock_mqtt_client = AsyncMock()
    mock_mqtt_client.is_connected.return_value = True
    access_control.mqtt_client = mock_mqtt_client
    
    # Mock metodi di logging
    access_control._log_authorized_access = AsyncMock()
    access_control._send_parallel_mqtt_logging = AsyncMock()
    
    # Test
    card_event = create_mock_card_event("12345678")
    result = await access_control._authenticate_card(card_event)
    
    # Verifiche
    assert result == AccessDecision.GRANT, "CASO 1 deve autorizzare"
    assert access_control._send_parallel_mqtt_logging.called, "CASO 1 deve fare MQTT parallelo"
    assert access_control._log_authorized_access.called, "CASO 1 deve loggare"
    
    return TestResult(
        case_name="CASO 1: Carta in cache",
        passed=True,
        details="✅ Autorizzata da cache con MQTT parallelo",
        expected_mqtt_parallel=True,
        actual_mqtt_parallel=access_control._send_parallel_mqtt_logging.called,
        log_entries=1 if access_control._log_authorized_access.called else 0
    )

async def test_caso_2_carta_non_in_cache():
    """
    CASO 2: Carta NON in cache
    - Cache refresh fallisce  
    - Deve chiamare gate-verification diretto
    - NON deve fare MQTT parallelo
    - Deve loggare UNA entry
    """
    print("🧪 TEST CASO 2: Carta NON in cache → Fallback diretto")
    
    from rfid_gate.core.access_control import AccessControl
    from rfid_gate.core.events import SystemMode, AccessDecision
    
    # Setup mock
    config = create_mock_config()
    access_control = AccessControl(config)
    access_control.mode = SystemMode.ONLINE
    
    # Mock sync_manager per carta NON in cache
    mock_sync_manager = AsyncMock()
    mock_sync_manager.validate_card_offline.return_value = {
        'authorized': False,
        'reason': 'Carta non trovata in cache'
    }
    access_control.sync_manager = mock_sync_manager
    
    # Mock MQTT client 
    mock_mqtt_client = AsyncMock()
    mock_mqtt_client.is_connected.return_value = True
    access_control.mqtt_client = mock_mqtt_client
    
    # Mock cache refresh che fallisce
    with patch('rfid_gate.network.cache_refresh_strategy.CacheRefreshManager') as MockRefresh:
        mock_refresh_instance = AsyncMock()
        mock_refresh_instance.handle_denied_card_refresh.return_value = False  # Cache refresh fallisce
        MockRefresh.return_value = mock_refresh_instance
        
        # Mock direct gate verification che autorizza
        access_control._direct_gate_verification = AsyncMock(return_value={
            'authorized': True,
            'reason': 'Gate-verification autorizza',
            'card_data': {'customer_id': 'customer_456'}
        })
        
        # Mock metodi di logging
        access_control._log_authorized_access = AsyncMock()
        access_control._send_parallel_mqtt_logging = AsyncMock()
        
        # Test
        card_event = create_mock_card_event("87654321")
        result = await access_control._authenticate_card(card_event)
        
        # Verifiche
        assert result == AccessDecision.GRANT, "CASO 2 deve autorizzare tramite gate-verification"
        assert not access_control._send_parallel_mqtt_logging.called, "CASO 2 NON deve fare MQTT parallelo"
        assert access_control._log_authorized_access.called, "CASO 2 deve loggare"
        assert access_control._direct_gate_verification.called, "CASO 2 deve chiamare gate-verification"
        
        return TestResult(
            case_name="CASO 2: Carta NON in cache → Fallback diretto", 
            passed=True,
            details="✅ Autorizzata da gate-verification SENZA MQTT parallelo",
            expected_mqtt_parallel=False,
            actual_mqtt_parallel=access_control._send_parallel_mqtt_logging.called,
            log_entries=1 if access_control._log_authorized_access.called else 0
        )

async def test_caso_3_abbonamento_scaduto_rinnovato():
    """
    CASO 3: Carta con abbonamento scaduto → Cache refresh trova rinnovo
    - Cache refresh trova dati aggiornati
    - Deve autorizzare da cache aggiornata
    - Deve fare MQTT parallelo
    - Deve loggare UNA entry
    """
    print("🧪 TEST CASO 3: Abbonamento scaduto → Cache refresh trova rinnovo")
    
    from rfid_gate.core.access_control import AccessControl
    from rfid_gate.core.events import SystemMode, AccessDecision
    
    # Setup mock
    config = create_mock_config()
    access_control = AccessControl(config)
    access_control.mode = SystemMode.ONLINE
    
    # Mock sync_manager 
    mock_sync_manager = AsyncMock()
    # Prima chiamata: abbonamento scaduto
    # Seconda chiamata (dopo refresh): abbonamento rinnovato
    mock_sync_manager.validate_card_offline.side_effect = [
        {
            'authorized': False,
            'reason': 'Abbonamento scaduto'
        },
        {
            'authorized': True,
            'reason': 'Abbonamento rinnovato',
            'customer_id': 'customer_789',
            'customer_name': 'Renewed User'
        }
    ]
    access_control.sync_manager = mock_sync_manager
    
    # Mock MQTT client
    mock_mqtt_client = AsyncMock()
    mock_mqtt_client.is_connected.return_value = True
    access_control.mqtt_client = mock_mqtt_client
    
    # Mock cache refresh che trova rinnovo
    with patch('rfid_gate.network.cache_refresh_strategy.CacheRefreshManager') as MockRefresh:
        mock_refresh_instance = AsyncMock()
        mock_refresh_instance.handle_denied_card_refresh.return_value = True  # Cache refresh trova rinnovo
        MockRefresh.return_value = mock_refresh_instance
        
        # Mock metodi di logging
        access_control._log_authorized_access = AsyncMock()
        access_control._send_parallel_mqtt_logging = AsyncMock()
        
        # Test
        card_event = create_mock_card_event("11223344")
        result = await access_control._authenticate_card(card_event)
        
        # Verifiche
        assert result == AccessDecision.GRANT, "CASO 3 deve autorizzare dopo cache refresh"
        assert access_control._send_parallel_mqtt_logging.called, "CASO 3 deve fare MQTT parallelo"
        assert access_control._log_authorized_access.called, "CASO 3 deve loggare"
        assert mock_refresh_instance.handle_denied_card_refresh.called, "CASO 3 deve fare cache refresh"
        
        return TestResult(
            case_name="CASO 3: Abbonamento scaduto → Rinnovato",
            passed=True,
            details="✅ Autorizzata dopo cache refresh CON MQTT parallelo",
            expected_mqtt_parallel=True,
            actual_mqtt_parallel=access_control._send_parallel_mqtt_logging.called,
            log_entries=1 if access_control._log_authorized_access.called else 0
        )

async def test_payload_gate_verification():
    """Test che il payload per gate-verification sia corretto"""
    print("🧪 TEST Payload gate-verification")
    
    from rfid_gate.core.access_control import AccessControl
    
    config = create_mock_config()
    access_control = AccessControl(config)
    
    # Mock aiohttp per catturare il payload
    with patch('aiohttp.ClientSession') as MockSession:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'authorized': True,
            'message': 'Customer unlocked successfully',
            'identificativo_tornello': 'tornello_1'
        }
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        MockSession.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Test
        result = await access_control._direct_gate_verification("632D3903", "out")
        
        # Verifica che il payload sia corretto
        call_args = mock_session.post.call_args
        expected_payload = {
            "uid": "632D3903",
            "direction": "out", 
            "gate_id": "tornello_01"
        }
        
        assert call_args[1]['json'] == expected_payload, f"Payload errato: {call_args[1]['json']}"
        
        return TestResult(
            case_name="Payload gate-verification",
            passed=True,
            details="✅ Payload corretto secondo specifiche",
            expected_mqtt_parallel=False,
            actual_mqtt_parallel=False,
            log_entries=0
        )

async def main():
    """Esegue tutti i test della logica corretta"""
    print("=" * 80)
    print("🧪 TEST LOGICA FLUSSO INTELLIGENTE CORRETTA")
    print("=" * 80)
    
    tests = [
        test_caso_1_carta_in_cache,
        test_caso_2_carta_non_in_cache,
        test_caso_3_abbonamento_scaduto_rinnovato,
        test_payload_gate_verification
    ]
    
    results = []
    
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
            print(f"✅ {result.case_name}: PASSED")
            print(f"   📝 {result.details}")
            print(f"   📡 MQTT parallelo - Atteso: {result.expected_mqtt_parallel}, Effettivo: {result.actual_mqtt_parallel}")
            print(f"   📄 Log entries: {result.log_entries}")
            print()
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            results.append(TestResult(
                case_name=test_func.__name__,
                passed=False,
                details=str(e),
                expected_mqtt_parallel=False,
                actual_mqtt_parallel=False,
                log_entries=0
            ))
            print()
    
    # Riassunto
    print("=" * 80)
    print("📊 RIASSUNTO TEST")
    print("=" * 80)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        mqtt_ok = "✅" if result.expected_mqtt_parallel == result.actual_mqtt_parallel else "❌"
        print(f"{status} {result.case_name} - MQTT: {mqtt_ok}")
    
    print(f"\n🎯 Risultato finale: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 TUTTI I TEST PASSATI! Logica flusso intelligente corretta.")
    else:
        print("⚠️ Alcuni test falliti. Controllare la logica.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)