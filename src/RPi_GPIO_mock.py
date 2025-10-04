"""
Mock RPi.GPIO per macOS - Simula GPIO di Raspberry Pi
"""

# Costanti GPIO
BCM = "BCM"
BOARD = "BOARD"
IN = "IN"
OUT = "OUT"
HIGH = 1
LOW = 0
PUD_UP = "PUD_UP"
PUD_DOWN = "PUD_DOWN"
RISING = "RISING"
FALLING = "FALLING"
BOTH = "BOTH"

# Stato simulato dei pin
_pin_states = {}
_pin_modes = {}
_pin_setup = {}

def setmode(mode):
    """Imposta modalità numerazione pin (simulato)"""
    print(f"🎮 [GPIO Mock] Modalità pin impostata: {mode}")

def setup(pin, mode, **kwargs):
    """Configura pin GPIO (simulato)"""
    _pin_setup[pin] = mode
    _pin_modes[pin] = mode
    if mode == OUT:
        _pin_states[pin] = LOW
    print(f"🎮 [GPIO Mock] Pin {pin} configurato come {mode}")

def output(pin, state):
    """Imposta output pin (simulato)"""
    if pin in _pin_setup and _pin_setup[pin] == OUT:
        _pin_states[pin] = state
        state_str = "HIGH" if state == HIGH else "LOW"
        print(f"🎮 [GPIO Mock] Pin {pin} → {state_str}")
    else:
        print(f"⚠️ [GPIO Mock] Pin {pin} non configurato come output")

def input(pin):
    """Legge input pin (simulato)"""
    state = _pin_states.get(pin, LOW)
    return state

def cleanup():
    """Cleanup GPIO (simulato)"""
    global _pin_states, _pin_modes, _pin_setup
    _pin_states.clear()
    _pin_modes.clear()
    _pin_setup.clear()
    print("🎮 [GPIO Mock] Cleanup completato")

def setwarnings(flag):
    """Abilita/disabilita warning (simulato)"""
    pass

def add_event_detect(pin, edge, callback=None, bouncetime=None):
    """Aggiunge rilevamento eventi (simulato)"""
    print(f"🎮 [GPIO Mock] Event detect su pin {pin}, edge: {edge}")

def remove_event_detect(pin):
    """Rimuove rilevamento eventi (simulato)"""
    print(f"🎮 [GPIO Mock] Rimosso event detect pin {pin}")

def wait_for_edge(pin, edge, timeout=None):
    """Aspetta evento su pin (simulato)"""
    print(f"🎮 [GPIO Mock] Attesa evento pin {pin}, edge: {edge}")
    return None

def get_pin_state(pin):
    """Ottiene stato pin (funzione aggiuntiva per debug)"""
    return _pin_states.get(pin, LOW)

def get_pin_mode(pin):
    """Ottiene modalità pin (funzione aggiuntiva per debug)"""
    return _pin_modes.get(pin, None)

def list_configured_pins():
    """Lista pin configurati (funzione aggiuntiva per debug)"""
    return list(_pin_setup.keys())

# Compatibilità con import as GPIO
class GPIO:
    """Classe per compatibilità 'import RPi.GPIO as GPIO'"""
    BCM = BCM
    BOARD = BOARD
    IN = IN
    OUT = OUT
    HIGH = HIGH
    LOW = LOW
    PUD_UP = PUD_UP
    PUD_DOWN = PUD_DOWN
    RISING = RISING
    FALLING = FALLING
    BOTH = BOTH
    
    @staticmethod
    def setmode(mode):
        return setmode(mode)
    
    @staticmethod
    def setup(pin, mode, **kwargs):
        return setup(pin, mode, **kwargs)
    
    @staticmethod
    def output(pin, state):
        return output(pin, state)
    
    @staticmethod
    def input(pin):
        return input(pin)
    
    @staticmethod
    def cleanup():
        return cleanup()
    
    @staticmethod
    def setwarnings(flag):
        return setwarnings(flag)
    
    @staticmethod
    def add_event_detect(pin, edge, callback=None, bouncetime=None):
        return add_event_detect(pin, edge, callback, bouncetime)
    
    @staticmethod
    def remove_event_detect(pin):
        return remove_event_detect(pin)
    
    @staticmethod
    def wait_for_edge(pin, edge, timeout=None):
        return wait_for_edge(pin, edge, timeout)