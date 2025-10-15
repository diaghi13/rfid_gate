#!/usr/bin/env python3
"""
🌐 RFID Gate Web UI - Main Application
====================================

Web interface moderna per gestione sistema RFID Gate.

Features:
- Dashboard real-time con WebSockets
- Controllo manuale tornello
- Gestione log e statistiche
- Configurazione sistema
- API REST completa
- Autenticazione sicura
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

# Add parent directory to path for RFID Gate imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import RFID Gate modules
from rfid_gate.config.settings import Config
# Note: AccessControlSystem e AccessLogger saranno implementati in futuro
# from rfid_gate import AccessControlSystem, RFIDGateConfig
# from rfid_gate.logging.logger import AccessLogger
from config_manager import ConfigManager

# ==============================================================================
# 🧪 MOCK CLASSES (temporanee fino all'implementazione completa)
# ==============================================================================

class MockAccessControlSystem:
    """Mock temporaneo per AccessControlSystem"""
    def __init__(self, config=None):
        self.config = config
        self.running = False
    
    def get_status(self):
        return {
            "running": self.running,
            "hardware": {
                "rfid_in": {"status": "connected", "type": "PN532"},
                "rfid_out": {"status": "connected", "type": "PN532"},
                "relay": {"status": "ready"},
                "gpio": {"status": "ready"}
            }
        }

class MockAccessLogger:
    """Mock temporaneo per AccessLogger"""
    def __init__(self):
        self.logs = []
    
    def get_recent_logs(self, limit=50):
        # Ritorna log di esempio
        return [
            {
                "timestamp": "2025-10-15T10:30:00",
                "uid": "04:1A:2B:3C",
                "customer_id": "CUST001",
                "direction": "in",
                "status": "authorized"
            }
        ]

# Istanze mock globali
AccessControlSystem = MockAccessControlSystem
AccessLogger = MockAccessLogger


# ==============================================================================
# 🔧 CONFIGURATION
# ==============================================================================

# JWT Configuration
SECRET_KEY = os.getenv("WEBUI_SECRET_KEY", "rfid_gate_web_ui_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Templates and static files
current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# Default admin user (change in production!)
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",  # Will be hashed
    "role": "admin"
}


# ==============================================================================
# 🚀 FASTAPI APP SETUP
# ==============================================================================

app = FastAPI(
    title="RFID Gate Web UI",
    description="Interface web per gestione sistema RFID Gate",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")


# ==============================================================================
# 🔐 AUTHENTICATION & SECURITY
# ==============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        # Modalità demo - accetta token demo per sviluppo
        if credentials.credentials == "demo-token-12345":
            return {
                "username": "admin",
                "role": "admin",  # Cambiato da "administrator" a "admin"
                "name": "Demo Admin"
            }
        
        # JWT normale
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "role": payload.get("role", "user")}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user (basic implementation)"""
    # In production, use proper database
    if username == DEFAULT_ADMIN["username"]:
        hashed_pwd = get_password_hash(DEFAULT_ADMIN["password"])
        if verify_password(password, hashed_pwd):
            return DEFAULT_ADMIN
    return None


# ==============================================================================
# 🌐 GLOBAL STATE & CONNECTIONS
# ==============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔗 WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global instances
manager = ConnectionManager()
rfid_system = None  # Optional[AccessControlSystem] = None - TODO: Implementare
access_logger = None  # Optional[AccessLogger] = None - TODO: Implementare


# ==============================================================================
# 🏠 WEB PAGES (HTML)
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with system overview"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    favicon_path = current_dir / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    else:
        # Ritorna un favicon vuoto se non esiste
        return Response(content="", media_type="image/x-icon")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/control", response_class=HTMLResponse)
async def control_page(request: Request):
    """Manual control page"""
    return templates.TemplateResponse("control.html", {"request": request})


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Access logs page"""
    return templates.TemplateResponse("logs.html", {"request": request})


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    return templates.TemplateResponse("config.html", {"request": request})


@app.get("/config/advanced", response_class=HTMLResponse)
async def config_advanced_page(request: Request):
    """Advanced configuration page with all 95+ settings"""
    return templates.TemplateResponse("config_advanced.html", {"request": request})


# ==============================================================================
# 🔑 AUTHENTICATION API
# ==============================================================================

@app.post("/api/auth/login")
async def login(request: Request):
    """User login endpoint"""
    try:
        form_data = await request.json()
        username = form_data.get("username")
        password = form_data.get("password")
        
        user = authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {"username": user["username"], "role": user["role"]}
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """User logout endpoint"""
    return {"message": "Logged out successfully"}


# ==============================================================================
# 📊 DASHBOARD API
# ==============================================================================

@app.get("/api/system/status")
async def get_system_status(current_user: dict = Depends(verify_token)):
    """Get current system status"""
    try:
        global rfid_system
        
        # Initialize system if needed
        if rfid_system is None:
            # Mock configuration per demo
            rfid_system = AccessControlSystem()
            rfid_system.running = True
        
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "running": True,
                "version": "2.0.0",
                "uptime": "00:45:23",
                "memory_usage": "45.2 MB"
            },
            "hardware": {
                "readers": [
                    {"id": "reader_1", "type": "PN532", "status": "connected", "last_read": "2 min ago"},
                    {"id": "reader_2", "type": "MFRC522", "status": "connected", "last_read": "5 min ago"}
                ],
                "relay": {"status": "ready", "last_activation": "10 min ago"},
                "gpio": {"status": "ok", "pins_active": 4}
            },
            "network": {
                "mqtt": {"connected": True, "broker": "mqtt.example.com"},
                "internet": {"connected": True, "latency": "45ms"},
                "offline_queue": {"items": 0}
            },
            "stats": {
                "today_accesses": 24,
                "authorized": 22,
                "denied": 2,
                "manual_opens": 3
            }
        }
        
        return status_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/logs/recent")
async def get_recent_logs(limit: int = 50, current_user: dict = Depends(verify_token)):
    """Get recent access logs"""
    try:
        # Mock data for now - integrate with real logger
        logs = []
        for i in range(min(limit, 20)):
            logs.append({
                "id": f"log_{i}",
                "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                "card_uid": f"A1B2C{i:03d}",
                "direction": "in" if i % 2 == 0 else "out",
                "authorized": i % 5 != 0,  # 80% authorized
                "user_name": f"User {i}" if i % 5 != 0 else None,
                "reader_id": "reader_1" if i % 2 == 0 else "reader_2"
            })
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 🎮 CONTROL API
# ==============================================================================

@app.post("/api/control/open")
async def manual_open(request: Request, current_user: dict = Depends(verify_token)):
    """Manual gate open"""
    try:
        data = await request.json()
        direction = data.get("direction", "in")
        duration = data.get("duration", 3)
        
        # Here integrate with your manual open system
        command = {
            "command_id": f"web_{current_user['username']}_{int(datetime.now().timestamp())}",
            "direction": direction,
            "duration": duration,
            "user_id": current_user["username"],
            "source": "web_ui",
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to WebSocket clients
        await manager.broadcast(f"manual_open:{direction}:{duration}")
        
        return {
            "success": True,
            "message": f"Gate opened {direction} for {duration} seconds",
            "command_id": command["command_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/control/status")
async def get_control_status(current_user: dict = Depends(verify_token)):
    """Get gate control status"""
    return {
        "gate": {
            "position": "closed",
            "locked": True,
            "last_action": "auto_close",
            "last_action_time": (datetime.now() - timedelta(minutes=2)).isoformat()
        },
        "permissions": {
            "can_open_in": True,
            "can_open_out": True,
            "can_emergency_open": current_user["role"] == "admin"
        }
    }


# ==============================================================================
# 🔧 CONFIGURATION API  
# ==============================================================================

@app.get("/api/config/all")
async def get_all_config(current_user: dict = Depends(verify_token)):
    """Get complete system configuration with all 95+ variables"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Inizializza ConfigManager
        config_manager = ConfigManager()
        
        # Carica configurazione attuale dal .env
        env_config = config_manager.load_env_config()
        
        # Organizza in sezioni per la Web UI
        sections = config_manager.get_config_sections()
        descriptions = config_manager.get_config_descriptions()
        
        # Restituisce tutte le configurazioni organizzate
        return {
            "success": True,
            "data": env_config,  # Tutte le variabili .env
            "sections": sections,  # Organizzazione per sezioni
            "descriptions": descriptions,  # Descrizioni user-friendly
            "total_configs": len(env_config),
            "message": f"Configurazione completa caricata con {len(env_config)} parametri"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel caricamento configurazione completa: {str(e)}"
        )

@app.post("/api/config/advanced")
async def update_advanced_config(request: Request, current_user: dict = Depends(verify_token)):
    """Update advanced configuration with all variables"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        config_updates = await request.json()
        
        # Inizializza ConfigManager
        config_manager = ConfigManager()
        
        # Carica configurazione attuale
        current_config = config_manager.load_env_config()
        
        # Applica gli aggiornamenti
        for key, value in config_updates.items():
            current_config[key] = str(value)
        
        # Valida la configurazione
        validation_errors = config_manager.validate_config(current_config)
        if validation_errors:
            return {
                "success": False,
                "errors": validation_errors,
                "message": f"Errori di validazione: {len(validation_errors)}"
            }
        
        # Salva la configurazione
        if config_manager.save_env_config(current_config):
            return {
                "success": True,
                "updated_fields": list(config_updates.keys()),
                "total_updated": len(config_updates),
                "message": f"Configurazione aggiornata con successo: {len(config_updates)} modifiche"
            }
        else:
            raise HTTPException(status_code=500, detail="Errore nel salvataggio file .env")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nell'aggiornamento configurazione avanzata: {str(e)}"
        )

@app.post("/api/config/backup")
async def create_config_backup(current_user: dict = Depends(verify_token)):
    """Create configuration backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        config_manager = ConfigManager()
        backup_file = config_manager._create_backup()
        
        return {
            "success": True,
            "backup_file": backup_file,
            "message": "Backup creato con successo"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nella creazione backup: {str(e)}"
        )

@app.get("/api/config")
async def get_config(current_user: dict = Depends(verify_token)):
    """Get system configuration"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Inizializza ConfigManager
        config_manager = ConfigManager()
        
        # Carica configurazione attuale dal .env
        env_config = config_manager.load_env_config()
        
        # Organizza in sezioni per la Web UI
        sections = config_manager.get_config_sections()
        
        # Mappa la configurazione nel formato atteso dalla Web UI
        config_data = {
            "readers": {
                "reader_1": {
                    "type": env_config.get("RFID_IN_READER_TYPE", "PN532"),
                    "interface": env_config.get("RFID_IN_PN532_INTERFACE", "I2C"),
                    "address": env_config.get("RFID_IN_PN532_I2C_ADDRESS", "0x24"),
                    "enabled": env_config.get("RFID_IN_ENABLE", "True").lower() == "true"
                },
                "reader_2": {
                    "type": env_config.get("RFID_OUT_READER_TYPE", "PN532"),
                    "interface": env_config.get("RFID_OUT_PN532_INTERFACE", "SPI"),
                    "bus": env_config.get("RFID_OUT_PN532_SPI_BUS", "0"),
                    "enabled": env_config.get("RFID_OUT_ENABLE", "True").lower() == "true"
                }
            },
            "network": {
                "mqtt_broker": env_config.get("MQTT_BROKER", ""),
                "mqtt_port": int(env_config.get("MQTT_PORT", "1883")),
                "mqtt_username": env_config.get("MQTT_USERNAME", ""),
                "mqtt_topic_prefix": env_config.get("MQTT_CARD_READ_TOPIC", "").replace("/card_read", ""),
                "mqtt_enabled": env_config.get("MQTT_BROKER", "") != ""
            },
            "security": {
                "require_authorization": env_config.get("AUTH_ENABLED", "True").lower() == "true",
                "log_all_attempts": env_config.get("LOG_LEVEL", "INFO") == "DEBUG",
                "offline_mode_enabled": env_config.get("OFFLINE_MODE_ENABLED", "True").lower() == "true",
                "auto_lock_timeout": int(env_config.get("AUTH_TIMEOUT", "10"))
            },
            "system": {
                "gate_open_duration": float(env_config.get("RELAY_OPEN_TIME", "3.0")),
                "read_timeout": int(env_config.get("AUTH_TIMEOUT", "5")),
                "relay_pin": int(env_config.get("RELAY_IN_PIN", "18")),
                "debug_mode": env_config.get("LOG_LEVEL", "INFO") == "DEBUG",
                "auto_restart": True,  # Non configurabile via .env
                "log_retention_days": int(env_config.get("LOG_RETENTION_DAYS", "30"))
            },
            "_raw_config": env_config,  # Configurazione grezza per debug
            "_sections": sections  # Sezioni organizzate
        }
        
        return config_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore caricamento configurazione: {str(e)}")


@app.post("/api/config")
async def update_config(request: Request, current_user: dict = Depends(verify_token)):
    """Update system configuration"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        config_data = await request.json()
        
        # Inizializza ConfigManager
        config_manager = ConfigManager()
        
        # Mappa la configurazione Web UI nel formato .env
        env_updates = {}
        
        # Readers configuration
        if "readers" in config_data:
            readers = config_data["readers"]
            
            if "reader_1" in readers:
                r1 = readers["reader_1"]
                env_updates["RFID_IN_READER_TYPE"] = r1.get("type", "PN532").lower()
                env_updates["RFID_IN_PN532_INTERFACE"] = r1.get("interface", "I2C").lower()
                env_updates["RFID_IN_PN532_I2C_ADDRESS"] = r1.get("address", "0x24")
                env_updates["RFID_IN_ENABLE"] = str(r1.get("enabled", True))
            
            if "reader_2" in readers:
                r2 = readers["reader_2"]
                env_updates["RFID_OUT_READER_TYPE"] = r2.get("type", "PN532").lower()
                env_updates["RFID_OUT_PN532_INTERFACE"] = r2.get("interface", "SPI").lower()
                env_updates["RFID_OUT_PN532_SPI_BUS"] = str(r2.get("bus", "0"))
                env_updates["RFID_OUT_ENABLE"] = str(r2.get("enabled", True))
        
        # Network configuration
        if "network" in config_data:
            network = config_data["network"]
            env_updates["MQTT_BROKER"] = network.get("mqtt_broker", "")
            env_updates["MQTT_PORT"] = str(network.get("mqtt_port", 1883))
            env_updates["MQTT_USERNAME"] = network.get("mqtt_username", "")
            
            # Password solo se fornita (non sovrascrive se vuota)
            if network.get("mqtt_password"):
                env_updates["MQTT_PASSWORD"] = network["mqtt_password"]
            
            # Topic prefix
            topic_prefix = network.get("mqtt_topic_prefix", "rfid_gate")
            env_updates["MQTT_CARD_READ_TOPIC"] = f"{topic_prefix}/card_read"
            env_updates["MQTT_AUTH_RESPONSE_TOPIC"] = f"{topic_prefix}/auth_response"
            env_updates["MQTT_MANUAL_OPEN_TOPIC"] = f"{topic_prefix}/manual_open"
        
        # Security configuration
        if "security" in config_data:
            security = config_data["security"]
            env_updates["AUTH_ENABLED"] = str(security.get("require_authorization", True))
            env_updates["OFFLINE_MODE_ENABLED"] = str(security.get("offline_mode_enabled", True))
            env_updates["AUTH_TIMEOUT"] = str(security.get("auto_lock_timeout", 10))
        
        # System configuration
        if "system" in config_data:
            system = config_data["system"]
            env_updates["RELAY_OPEN_TIME"] = str(system.get("gate_open_duration", 3.0))
            env_updates["RELAY_IN_PIN"] = str(system.get("relay_pin", 18))
            env_updates["LOG_RETENTION_DAYS"] = str(system.get("log_retention_days", 30))
            
            # Debug mode
            if system.get("debug_mode", False):
                env_updates["LOG_LEVEL"] = "DEBUG"
            else:
                env_updates["LOG_LEVEL"] = "INFO"
        
        # Valida la configurazione
        validation_errors = config_manager.validate_config(env_updates)
        if validation_errors:
            return JSONResponse(
                status_code=400,
                content={"success": False, "errors": validation_errors}
            )
        
        # Salva la configurazione nel file .env
        success = config_manager.save_env_config(env_updates, create_backup=True)
        
        if success:
            # Notifica aggiornamento via WebSocket
            await manager.broadcast({
                "type": "config_updated",
                "message": "Configurazione aggiornata con successo",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True, 
                "message": "Configurazione salvata nel file .env con successo",
                "backup_created": True,
                "updated_keys": list(env_updates.keys())
            }
        else:
            raise HTTPException(status_code=500, detail="Errore durante il salvataggio della configurazione")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore aggiornamento configurazione: {str(e)}")


@app.get("/api/config/backups")
async def get_config_backups(current_user: dict = Depends(verify_token)):
    """Get list of configuration backups"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        config_manager = ConfigManager()
        backups = config_manager.get_backup_list()
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/restore/{backup_filename}")
async def restore_config_backup(backup_filename: str, current_user: dict = Depends(verify_token)):
    """Restore configuration from backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        config_manager = ConfigManager()
        success = config_manager.restore_backup(backup_filename)
        
        if success:
            await manager.broadcast({
                "type": "config_restored",
                "message": f"Configurazione ripristinata da backup: {backup_filename}",
                "timestamp": datetime.now().isoformat()
            })
            
            return {"success": True, "message": "Configurazione ripristinata con successo"}
        else:
            raise HTTPException(status_code=500, detail="Errore durante il ripristino")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 📡 WEBSOCKET ENDPOINT
# ==============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==============================================================================
# 🚀 APPLICATION STARTUP
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    print("🌐 Starting RFID Gate Web UI...")
    print(f"📍 Dashboard: http://localhost:8080")
    print(f"📖 API Docs: http://localhost:8080/api/docs")
    print(f"🔑 Default login: admin / admin123")
    
    # Initialize RFID system connection here if needed
    global rfid_system, access_logger
    try:
        # Note: Uncomment when ready to integrate with real system
        # config = RFIDGateConfig()
        # rfid_system = AccessControlSystem(config) 
        # access_logger = AccessLogger()
        pass
    except Exception as e:
        print(f"⚠️ Could not initialize RFID system: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down RFID Gate Web UI...")
    
    global rfid_system
    if rfid_system:
        # Cleanup RFID system
        pass


# ==============================================================================
# 🏃 MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )