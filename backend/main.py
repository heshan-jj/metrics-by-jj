"""
FastAPI Backend & WebSocket Hub for Metrics by JJ.
Serves real-time hardware telemetry and the dashboard web application.
"""

import asyncio
import os
import json
import logging
from typing import Set
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .metrics import collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI(
    title="Metrics by JJ",
    description="Real-time Windows hardware and system telemetry engine",
    version="1.0.0"
)

# Allow private network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        dead = []
        payload = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

manager = ConnectionManager()

# Background broadcast loop
@app.on_event("startup")
async def start_broadcaster():
    async def metrics_loop():
        # Prime psutil cpu measurement
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        while True:
            try:
                if manager.active_connections:
                    # Run metrics collection in thread pool to avoid blocking async loop
                    data = await asyncio.to_thread(collector.collect)
                    await manager.broadcast(data)
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
            await asyncio.sleep(1.0)

    asyncio.create_task(metrics_loop())

@app.get("/api/snapshot")
async def get_snapshot():
    """Get a single real-time snapshot of all hardware & system metrics."""
    data = await asyncio.to_thread(collector.collect)
    return data

@app.get("/api/system")
async def get_system_info():
    """Get system static info (hostname, IPs, OS, architecture, CPUs)."""
    return collector.static_info

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial snapshot immediately upon connect
        initial_data = await asyncio.to_thread(collector.collect)
        await websocket.send_text(json.dumps(initial_data))
        
        while True:
            # Handle incoming ping / config messages from frontend client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Serve Frontend
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>Metrics by JJ</h1><p>Frontend file not found.</p>", status_code=404)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
