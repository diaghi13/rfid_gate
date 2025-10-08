#!/usr/bin/env python3
"""
🚀 Server Web UI RFID Gate - Versione Demo
==========================================
Server FastAPI semplificato per la gestione della configurazione RFID Gate
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importa ConfigManager
from config_manager import ConfigManager

app = FastAPI(title="RFID Gate Web UI", version="1.0.0")

# Monta file statici e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inizializza ConfigManager
config_manager = ConfigManager()

@app.get("/")
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/config")
async def config_page(request: Request):
    """Config page"""
    return templates.TemplateResponse("config.html", {"request": request})

@app.get("/control")
async def control_page(request: Request):
    """Control page"""
    return templates.TemplateResponse("control.html", {"request": request})

@app.get("/logs")
async def logs_page(request: Request):
    """Logs page"""
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/api/config")
async def get_config():
    """Ottieni configurazione corrente"""
    try:
        config = config_manager.load_env_config()
        return {"status": "success", "data": config}
    except Exception as e:
        logger.error(f"Errore caricamento config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def save_config(config_data: Dict[str, Any]):
    """Salva configurazione"""
    try:
        # Valida configurazione
        validation_result = config_manager.validate_config(config_data)
        if not validation_result["valid"]:
            return {
                "status": "error", 
                "message": "Validazione fallita",
                "errors": validation_result["errors"]
            }
        
        # Salva configurazione
        success = config_manager.save_env_config(config_data)
        if success:
            return {"status": "success", "message": "Configurazione salvata"}
        else:
            raise HTTPException(status_code=500, detail="Errore salvataggio")
            
    except Exception as e:
        logger.error(f"Errore salvataggio config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backup/list")
async def list_backups():
    """Lista backup disponibili"""
    try:
        backups = config_manager.list_backups()
        return {"status": "success", "data": backups}
    except Exception as e:
        logger.error(f"Errore lista backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup/restore/{backup_filename}")
async def restore_backup(backup_filename: str):
    """Ripristina backup"""
    try:
        success = config_manager.restore_backup(backup_filename)
        if success:
            return {"status": "success", "message": f"Backup {backup_filename} ripristinato"}
        else:
            raise HTTPException(status_code=500, detail="Errore ripristino backup")
    except Exception as e:
        logger.error(f"Errore ripristino backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Status sistema"""
    return {
        "status": "success",
        "data": {
            "server": "running",
            "config_manager": "active",
            "timestamp": datetime.now().isoformat()
        }
    }

if __name__ == "__main__":
    print("🚀 Avvio Server Web UI RFID Gate")
    print("📡 URL: http://localhost:8080")
    print("🔧 Gestione configurazione attiva")
    print("💾 File .env: configurazione reale")
    print("📂 Backup automatici abilitati")
    print("\n" + "="*50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info"
    )