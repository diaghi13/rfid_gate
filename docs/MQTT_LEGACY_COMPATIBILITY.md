# 🔄 MQTT Legacy Compatibility & Future Migration Guide

## 📋 Situazione Attuale

Il sistema refactored mantiene **compatibilità completa** con il payload MQTT legacy per assicurare che il backend esistente continui a funzionare senza modifiche.

### 🎯 Payload Legacy Mantenuto

```json
{
  "card_uid": "E298C6EB",
  "identificativo_tornello": "GATE001",
  "direzione": "in",
  "timestamp": "2024-01-15T10:30:00.123456",
  "raw_id": "0xE298C6EB",
  "card_data": { "sector1": "test" },
  "hex_id": "0xE298C6EB",
  "auth_required": true,
  "reader_id": "mfrc522"
}
```

## ✨ Campi Futuri (Commentati)

Nelle dataclass `CardReadMessage` e `AuthRequest` sono presenti campi futuri commentati per una migrazione graduale:

### 📤 CardReadMessage - Campi Futuri

```python
# tornello_id: str = None              # ✨ FUTURO: Nome moderno per identificativo_tornello
# direction: str = None                # ✨ FUTURO: Nome moderno per direzione
# reader_type: str = None              # ✨ FUTURO: Tipo specifico reader ("mfrc522", "pn532")
# raw_uid: Optional[str] = None        # ✨ FUTURO: Nome moderno per raw_id
# uid_hex: Optional[str] = None        # ✨ FUTURO: Nome moderno per hex_id
# metadata: Dict[str, Any] = None      # ✨ FUTURO: Metadata aggiuntivi strutturati
# message_id: str = None               # ✨ FUTURO: ID messaggio univoco per tracking
# retry_count: int = 0                 # ✨ FUTURO: Contatore retry per resilienza
# priority: int = 0                    # ✨ FUTURO: Priorità messaggio (0=normale, 1=alta)
# source_version: str = "2.0"          # ✨ FUTURO: Versione protocollo per compatibilità
```

### 🔐 AuthRequest - Campi Futuri

```python
# tornello_id: str = None              # ✨ FUTURO: Nome moderno per identificativo_tornello
# direction: str = None                # ✨ FUTURO: Nome moderno per direzione
# request_id: str = None               # ✨ FUTURO: ID richiesta univoco per tracking
# timeout: int = 30                    # ✨ FUTURO: Timeout specifico per questa richiesta
# priority: int = 0                    # ✨ FUTURO: Priorità richiesta (0=normale, 1=alta)
# retry_count: int = 0                 # ✨ FUTURO: Contatore retry
# correlation_id: str = None           # ✨ FUTURO: ID correlazione per tracing distribuito
# client_version: str = "2.0"          # ✨ FUTURO: Versione client per compatibilità
# auth_method: str = "default"         # ✨ FUTURO: Metodo auth ("default", "biometric", "pin")
# metadata: Dict[str, Any] = None      # ✨ FUTURO: Metadata aggiuntivi per context
```

## 🗺️ Roadmap di Migrazione

### 📦 v1.0 - Legacy Compatibility (Attuale)

- ✅ Payload identico al sistema legacy
- ✅ Campi futuri commentati ma preservati
- ✅ Zero breaking changes per backend
- ✅ Test di compatibilità completi

### 🔄 v2.0 - Hybrid Mode (Futuro)

**Obiettivo**: Supportare entrambi i formati durante la transizione

#### Backend Changes Required:

```javascript
// Endpoint che accetta entrambi i formati
app.post("/api/card_read", (req, res) => {
  const payload = req.body;

  // Detect format version
  const isLegacy = payload.hasOwnProperty("identificativo_tornello");
  const isModern = payload.hasOwnProperty("tornello_id");

  if (isLegacy) {
    // Handle legacy format
    const tornelloId = payload.identificativo_tornello;
    const direction = payload.direzione;
    // ...
  } else if (isModern) {
    // Handle modern format
    const tornelloId = payload.tornello_id;
    const direction = payload.direction;
    // ...
  }
});
```

#### Client Changes:

```python
# Decommentare campi futuri nelle dataclass
@dataclass
class CardReadMessage:
    # Legacy fields (maintain)
    card_uid: str
    identificativo_tornello: str  # Keep for compatibility
    direzione: str               # Keep for compatibility

    # Modern fields (uncomment)
    tornello_id: str = None      # ✅ Modern name
    direction: str = None        # ✅ Modern name

    def to_hybrid_payload(self) -> Dict[str, Any]:
        """Send both legacy and modern fields during transition"""
        return {
            # Legacy format
            "card_uid": self.card_uid,
            "identificativo_tornello": self.identificativo_tornello,
            "direzione": self.direzione,

            # Modern format (additional)
            "tornello_id": self.tornello_id or self.identificativo_tornello,
            "direction": self.direction or self.direzione,
            "format_version": "2.0"
        }
```

### 🚀 v3.0 - Modern Only (Futuro Distante)

**Obiettivo**: Solo formato moderno, deprecazione completa legacy

#### Payload Moderno Target:

```json
{
  "card_uid": "E298C6EB",
  "tornello_id": "GATE001", // ← Modern name
  "direction": "in", // ← Modern name
  "timestamp": "2024-01-15T10:30:00.123456",
  "reader_type": "mfrc522", // ← More specific
  "raw_uid": "0xE298C6EB", // ← Modern name
  "metadata": {
    // ← Structured metadata
    "card_data": { "sector1": "test" },
    "hex_id": "0xE298C6EB"
  },
  "message_id": "a1b2c3d4", // ← Unique tracking
  "retry_count": 0,
  "priority": 0,
  "source_version": "3.0"
}
```

## 🔧 Migration Steps

### Step 1: Prepare Backend (v2.0)

1. Update backend to accept both legacy and modern field names
2. Add format detection logic
3. Implement gradual migration tracking
4. Deploy backend changes

### Step 2: Enable Hybrid Mode (v2.0)

1. Uncomment future fields in dataclass
2. Update `send_card_read` to send both formats
3. Add `format_version` field to track migration
4. Test with both formats

### Step 3: Monitor & Migrate (v2.0)

1. Monitor backend logs for format usage
2. Gradually switch clients to modern format
3. Track migration progress
4. Ensure 100% backend compatibility

### Step 4: Deprecate Legacy (v3.0)

1. Remove legacy field support from backend
2. Update client to send only modern format
3. Remove legacy fields from dataclass
4. Clean up migration code

## 🧪 Testing Strategy

### Compatibility Tests

```python
def test_legacy_compatibility():
    """Ensure legacy payload is identical"""
    # Test current implementation

def test_hybrid_mode():
    """Test both formats work"""
    # Test v2.0 implementation

def test_modern_only():
    """Test modern format only"""
    # Test v3.0 implementation
```

### Backend Integration Tests

- Test legacy client → legacy backend ✅
- Test hybrid client → legacy backend ✅
- Test hybrid client → hybrid backend ✅
- Test modern client → modern backend ✅

## 📊 Benefits of This Approach

1. **Zero Downtime**: Gradual migration without service interruption
2. **Risk Mitigation**: Fallback to legacy format if issues arise
3. **Flexibility**: Can pause/resume migration at any step
4. **Future Proof**: Modern format ready for new features
5. **Maintainability**: Clear separation between legacy and modern code

## 🎯 Current Status

- ✅ **Legacy Compatibility**: 100% compatible with existing backend
- ✅ **Future Fields**: Preserved and documented in code
- ✅ **Migration Plan**: Complete roadmap defined
- ✅ **Testing**: Compatibility tests implemented

**The system is ready for testing and can be migrated to modern format when needed!**
