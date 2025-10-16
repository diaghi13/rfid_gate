#!/usr/bin/env python3
"""
🌐 Cache Refresh Strategy - Implementazione Endpoint Real-Time
=============================================================

OPZIONI DI IMPLEMENTAZIONE per verifica server real-time:

OPZIONE 1: Usa ENDPOINT ESISTENTE (se già hai backend)
OPZIONE 2: Crea NUOVO ENDPOINT specifico  
OPZIONE 3: Usa MQTT REQUEST/RESPONSE pattern
"""

import asyncio
import aiohttp
import time
from datetime import datetime


class RealTimeCardVerification:
    """Gestisce verifica carte real-time con diverse strategie"""
    
    def __init__(self, config):
        self.config = config
        
    # ========================================================================
    # OPZIONE 1: USA ENDPOINT ESISTENTE (modifica di /api/sync)
    # ========================================================================
    
    async def verify_single_card_existing_endpoint(self, card_uid: str) -> dict:
        """
        OPZIONE 1: Usa endpoint sync esistente con parametro singola carta
        
        Vantaggi:
        - Zero modifiche backend
        - Usa logica di autenticazione esistente
        - Compatibile con sistema attuale
        
        Backend modification needed:
        GET /api/sync?card_uid=AA:BB:CC:DD
        Response: {"success": true, "data": [card_data]}
        """
        try:
            url = f"{self.config.server_url}{self.config.sync_endpoint}"
            params = {
                'card_uid': card_uid,           # Filtra una sola carta
                'gate_id': self.config.gate_id, # Identifica tornello
                'refresh': 'true'               # Flag per forzare controllo DB
            }
            
            print(f"🌐 Verifica carta {card_uid} via endpoint esistente...")
            print(f"   URL: {url}?card_uid={card_uid}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.fallback_timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('success') and data.get('data'):
                            cards = data['data']
                            if cards and len(cards) > 0:
                                card_data = cards[0]
                                return {
                                    'found': True,
                                    'enabled': self._is_card_enabled(card_data),
                                    'customer_name': card_data.get('customer_name', 'Unknown'),
                                    'customer_id': card_data.get('customer_id'),
                                    'source': 'existing_sync_endpoint'
                                }
                        
                        # Carta non trovata o non autorizzata
                        return {'found': False, 'enabled': False, 'source': 'existing_sync_endpoint'}
                    else:
                        print(f"   ⚠️ HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            return None
    
    # ========================================================================
    # OPZIONE 2: NUOVO ENDPOINT DEDICATO (serve sviluppo backend)
    # ========================================================================
    
    async def verify_single_card_new_endpoint(self, card_uid: str) -> dict:
        """
        OPZIONE 2: Nuovo endpoint dedicato per verifiche real-time
        
        Vantaggi:
        - Performance ottimizzata
        - API pulita e specifica
        - Controllo granulare
        
        Backend development needed:
        GET /api/gate-verification/{card_uid}?gate_id=tornello_01
        Response: {
            "card_uid": "AA:BB:CC:DD",
            "authorized": true,
            "customer_name": "Mario Rossi", 
            "customer_id": 123,
            "subscription_status": "active",
            "expires_at": "2025-12-31T23:59:59Z"
        }
        """
        try:
            # Usa configurazione fallback dedicata
            url = f"{self.config.fallback_server_url}{self.config.fallback_endpoint}/{card_uid}"
            params = {
                'gate_id': self.config.gate_id,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"🆕 Verifica carta {card_uid} via endpoint dedicato...")
            print(f"   URL: {url}?gate_id={self.config.gate_id}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.fallback_timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'found': True,
                            'enabled': data.get('authorized', False),
                            'customer_name': data.get('customer_name', 'Unknown'),
                            'customer_id': data.get('customer_id'),
                            'subscription_status': data.get('subscription_status'),
                            'expires_at': data.get('expires_at'),
                            'source': 'dedicated_endpoint'
                        }
                    elif response.status == 404:
                        # Carta non trovata
                        return {'found': False, 'enabled': False, 'source': 'dedicated_endpoint'}
                    else:
                        print(f"   ⚠️ HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            return None
    
    # ========================================================================
    # OPZIONE 3: MQTT REQUEST/RESPONSE (usa MQTT esistente)
    # ========================================================================
    
    async def verify_single_card_mqtt(self, card_uid: str, mqtt_client) -> dict:
        """
        OPZIONE 3: Usa MQTT per verifiche real-time
        
        Vantaggi:
        - Usa infrastruttura MQTT esistente
        - Zero endpoint HTTP da creare
        - Supporta timeout personalizzati
        
        MQTT Pattern:
        Publish: gate/tornello_01/verify_request
        Subscribe: gate/tornello_01/verify_response
        """
        try:
            if not mqtt_client or not mqtt_client.is_connected():
                return None
            
            request_topic = f"gate/{self.config.gate_id}/verify_request"
            response_topic = f"gate/{self.config.gate_id}/verify_response" 
            
            print(f"📡 Verifica carta {card_uid} via MQTT...")
            print(f"   Request: {request_topic}")
            print(f"   Response: {response_topic}")
            
            # Prepara payload richiesta
            request_payload = {
                "card_uid": card_uid,
                "gate_id": self.config.gate_id,
                "timestamp": datetime.now().isoformat(),
                "request_id": f"verify_{int(time.time()*1000)}"  # ID univoco
            }
            
            # Setup listener per risposta
            response_received = asyncio.Event()
            response_data = {}
            
            def on_verify_response(topic, payload):
                nonlocal response_data
                try:
                    import json
                    data = json.loads(payload)
                    if data.get('card_uid') == card_uid:
                        response_data = data
                        response_received.set()
                except Exception:
                    pass
            
            # Subscribe temporaneo
            await mqtt_client.subscribe(response_topic, on_verify_response)
            
            # Invia richiesta
            await mqtt_client.publish(request_topic, request_payload)
            
            # Aspetta risposta con timeout
            try:
                await asyncio.wait_for(response_received.wait(), timeout=self.config.fallback_timeout)
                
                return {
                    'found': True,
                    'enabled': response_data.get('authorized', False),
                    'customer_name': response_data.get('customer_name', 'Unknown'),
                    'customer_id': response_data.get('customer_id'),
                    'source': 'mqtt_verification'
                }
                
            except asyncio.TimeoutError:
                print(f"   ⏱️ Timeout MQTT verification per {card_uid}")
                return None
                
        except Exception as e:
            print(f"   ❌ Errore MQTT: {e}")
            return None
    
    def _is_card_enabled(self, card_data: dict) -> bool:
        """Determina se carta è abilitata dalla risposta server"""
        # Logica compatibile con formato sync esistente
        if card_data.get('in_white_list'):
            return True
            
        # Controlla subscriptions attive
        subscriptions = card_data.get('active_subscriptions', [])
        if isinstance(subscriptions, list) and len(subscriptions) > 0:
            return True
            
        return False


# ========================================================================
# ESEMPI DI IMPLEMENTAZIONE BACKEND
# ========================================================================

def backend_examples():
    """
    Esempi di implementazione backend per ogni opzione
    """
    
    print("🔧 ESEMPI IMPLEMENTAZIONE BACKEND")
    print("="*60)
    
    print("""
📋 OPZIONE 1: Modifica endpoint esistente /api/sync

// Express.js / Node.js
app.get('/api/sync', async (req, res) => {
    const { card_uid, gate_id, refresh } = req.query;
    
    if (card_uid) {
        // Verifica singola carta
        const card = await db.getCard(card_uid);
        if (card) {
            return res.json({
                success: true,
                data: [card]  // Array con una sola carta
            });
        } else {
            return res.json({
                success: true,  
                data: []       // Array vuoto = carta non trovata
            });
        }
    }
    
    // Logica sync normale esistente...
});

// Python/Django
def sync_view(request):
    card_uid = request.GET.get('card_uid')
    
    if card_uid:
        try:
            card = Card.objects.get(uid=card_uid)
            return JsonResponse({
                'success': True,
                'data': [serialize_card(card)]
            })
        except Card.DoesNotExist:
            return JsonResponse({
                'success': True,
                'data': []
            })
    
    # Sync normale...
""")

    print("""
📋 OPZIONE 2: Nuovo endpoint dedicato

// Express.js / Node.js  
app.get('/api/gate-verification/:card_uid', async (req, res) => {
    const { card_uid } = req.params;
    const { gate_id } = req.query;
    
    try {
        const card = await db.getActiveCard(card_uid);
        
        if (card && card.isAuthorized(gate_id)) {
            return res.json({
                card_uid: card_uid,
                authorized: true,
                customer_name: card.customer_name,
                customer_id: card.customer_id,
                subscription_status: card.subscription_status,
                expires_at: card.expires_at
            });
        } else {
            return res.status(404).json({
                card_uid: card_uid,
                authorized: false,
                message: 'Card not found or unauthorized'
            });
        }
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
});

// Python/FastAPI
@app.get("/api/gate-verification/{card_uid}")
async def verify_card(card_uid: str, gate_id: str):
    card = await get_card_by_uid(card_uid)
    
    if card and is_authorized(card, gate_id):
        return {
            "card_uid": card_uid,
            "authorized": True,
            "customer_name": card.customer_name,
            "customer_id": card.customer_id,
            "subscription_status": card.subscription_status
        }
    else:
        raise HTTPException(404, "Card not authorized")
""")

    print("""
📋 OPZIONE 3: MQTT Handler (server-side)

// Node.js con MQTT
mqtt.on('message', async (topic, message) => {
    if (topic.endsWith('/verify_request')) {
        const request = JSON.parse(message.toString());
        const { card_uid, gate_id, request_id } = request;
        
        const card = await db.getCard(card_uid);
        const response = {
            card_uid,
            gate_id,
            request_id,
            authorized: card ? card.isActive() : false,
            customer_name: card?.customer_name || null,
            customer_id: card?.customer_id || null,
            timestamp: new Date().toISOString()
        };
        
        const responseTopic = topic.replace('verify_request', 'verify_response');
        mqtt.publish(responseTopic, JSON.stringify(response));
    }
});

// Python con paho-mqtt
def on_message(client, userdata, msg):
    if msg.topic.endswith('/verify_request'):
        request = json.loads(msg.payload.decode())
        card_uid = request['card_uid']
        
        card = get_card(card_uid)
        response = {
            'card_uid': card_uid,
            'authorized': card.is_active() if card else False,
            'customer_name': card.customer_name if card else None
        }
        
        response_topic = msg.topic.replace('verify_request', 'verify_response')
        client.publish(response_topic, json.dumps(response))
""")


async def test_verification_options():
    """Test delle tre opzioni"""
    print("🧪 TEST OPZIONI VERIFICA REAL-TIME")
    print("="*50)
    
    # Mock config
    class MockConfig:
        server_url = "http://localhost:3000"
        sync_endpoint = "/api/sync"
        fallback_server_url = "http://localhost:8000" 
        fallback_endpoint = "/api/gate-verification"
        fallback_timeout = 3
        gate_id = "tornello_01"
    
    config = MockConfig()
    verifier = RealTimeCardVerification(config)
    
    test_card = "AA:BB:CC:DD"
    
    print(f"\n🔍 Test carta: {test_card}")
    
    # Test Opzione 1
    print(f"\n1️⃣ Test endpoint esistente...")
    result1 = await verifier.verify_single_card_existing_endpoint(test_card)
    print(f"   Risultato: {result1}")
    
    # Test Opzione 2  
    print(f"\n2️⃣ Test endpoint dedicato...")
    result2 = await verifier.verify_single_card_new_endpoint(test_card)
    print(f"   Risultato: {result2}")
    
    # Test Opzione 3 richiederebbe MQTT client
    print(f"\n3️⃣ Test MQTT...")
    print("   (Richiede MQTT client attivo)")


if __name__ == "__main__":
    backend_examples()
    print("\n" + "="*60)
    asyncio.run(test_verification_options())