"""
Servidor FastAPI + WebSocket para visualización de señales PPG en tiempo real.

Este servidor soporta:
- Lectura directa del puerto serial
- Recepción de datos desde la app Tkinter
- Transmisión WebSocket a múltiples clientes
- Filtrado Butterworth configurable
- Autenticación por contraseña
- Monitoreo de calidad de transmisión
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Set
import time
import csv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Importar módulos locales
from config import *
from serial_reader import SerialReader
from signal_processor import SignalProcessor
from auth_manager import AuthManager
from quality_monitor import QualityMonitor

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Modelos Pydantic
# ============================================================================

class AuthRequest(BaseModel):
    """Modelo para solicitud de autenticación."""
    password: str


class FilterConfig(BaseModel):
    """Modelo para configuración del filtro."""
    lowcut: float = DEFAULT_FILTER_LOW
    highcut: float = DEFAULT_FILTER_HIGH
    order: int = DEFAULT_FILTER_ORDER
    enabled: bool = FILTER_ENABLED


class DataPoint(BaseModel):
    """Modelo para punto de datos recibido desde Tkinter."""
    timestamp: float
    value: float


# ============================================================================
# Aplicación FastAPI
# ============================================================================

app = FastAPI(
    title="PPG WebSocket Server",
    description="Servidor de visualización en tiempo real de señales PPG",
    version="1.0.0"
)

# Montar carpeta static
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ============================================================================
# Estado Global del Servidor
# ============================================================================

class ServerState:
    """Estado global del servidor."""
    
    def __init__(self):
        # Componentes principales
        self.auth_manager = AuthManager(PASSWORD, SESSION_TIMEOUT_HOURS)
        self.signal_processor = SignalProcessor(SAMPLE_RATE, BUFFER_SIZE)
        self.quality_monitor = QualityMonitor(QUALITY_WINDOW_SECONDS)
        
        # Configurar filtro por defecto
        self.signal_processor.configure_filter(
            lowcut=DEFAULT_FILTER_LOW,
            highcut=DEFAULT_FILTER_HIGH,
            order=DEFAULT_FILTER_ORDER,
            enabled=FILTER_ENABLED
        )
        
        # Serial reader (opcional)
        self.serial_reader: SerialReader = None
        self.serial_task: asyncio.Task = None
        
        # Clientes WebSocket conectados: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Modo de lectura actual
        self.data_source_mode = DATA_SOURCE_MODE
        
        # Crear directorio de uploads si no existe
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        logger.info("ServerState inicializado")
    
    async def start_serial_reading(self):
        """Inicia la lectura del puerto serial."""
        if self.serial_reader is not None:
            logger.warning("Serial reader ya está activo")
            return False
        
        try:
            self.serial_reader = SerialReader(SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT)
            
            if not self.serial_reader.connect():
                logger.error("No se pudo conectar al puerto serial")
                self.serial_reader = None
                return False
            
            # Iniciar lectura asíncrona
            self.serial_task = asyncio.create_task(
                self.serial_reader.read_loop(self.on_serial_data)
            )
            
            logger.info(f"Lectura serial iniciada en {SERIAL_PORT}")
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando lectura serial: {e}")
            self.serial_reader = None
            return False
    
    async def stop_serial_reading(self):
        """Detiene la lectura del puerto serial."""
        if self.serial_reader:
            self.serial_reader.disconnect()
            
            if self.serial_task:
                self.serial_task.cancel()
                try:
                    await self.serial_task
                except asyncio.CancelledError:
                    pass
            
            self.serial_reader = None
            self.serial_task = None
            logger.info("Lectura serial detenida")
    
    async def on_serial_data(self, timestamp: float, value: float):
        """Callback cuando se reciben datos del serial."""
        await self.process_and_broadcast(timestamp, value)
    
    async def process_and_broadcast(self, timestamp: float, raw_value: float):
        """Procesa datos y los transmite a todos los clientes."""
        # Procesar con filtro
        _, raw, filtered = self.signal_processor.process_sample(timestamp, raw_value)
        
        # Obtener número de secuencia
        seq = self.quality_monitor.get_next_seq()
        
        # Crear mensaje
        message = {
            "seq": seq,
            "timestamp": timestamp,
            "raw": raw,
            "filtered": filtered,
            "server_time": time.time()
        }
        
        # Transmitir a todos los clientes conectados
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                # Registrar envío
                self.quality_monitor.record_packet_sent(client_id, seq)
                
                # Enviar mensaje
                await websocket.send_json(message)
                
            except Exception as e:
                logger.warning(f"Error enviando a {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Limpiar clientes desconectados
        for client_id in disconnected_clients:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                self.quality_monitor.unregister_client(client_id)


# Estado global
state = ServerState()


# ============================================================================
# Rutas HTTP
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Sirve el dashboard principal."""
    html_file = static_path / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h1>Dashboard no disponible</h1><p>Falta archivo index.html</p>")


@app.get("/diagnostics", response_class=HTMLResponse)
async def get_diagnostics():
    """Sirve la página de diagnóstico de calidad."""
    html_file = static_path / "diagnostics.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h1>Diagnóstico no disponible</h1><p>Falta archivo diagnostics.html</p>")


@app.post("/auth")
async def authenticate(request: AuthRequest):
    """Endpoint de autenticación."""
    token = state.auth_manager.authenticate(request.password)
    
    if token:
        return {"success": True, "token": token}
    else:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")


@app.get("/filter/config")
async def get_filter_config():
    """Obtiene la configuración actual del filtro."""
    return state.signal_processor.get_filter_config()


@app.post("/filter/config")
async def set_filter_config(config: FilterConfig):
    """Configura los parámetros del filtro."""
    try:
        result = state.signal_processor.configure_filter(
            lowcut=config.lowcut,
            highcut=config.highcut,
            order=config.order,
            enabled=config.enabled
        )
        logger.info(f"Filtro reconfigurado: {result}")
        return {"success": True, "config": result}
    except Exception as e:
        logger.error(f"Error configurando filtro: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/data/push")
async def push_data(data: DataPoint):
    """Endpoint para que Tkinter envíe datos."""
    await state.process_and_broadcast(data.timestamp, data.value)
    return {"success": True}


@app.post("/data/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Sube un archivo CSV para análisis offline."""
    try:
        # Validar tamaño
        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        
        if size_mb > MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo muy grande. Máximo: {MAX_UPLOAD_SIZE_MB} MB"
            )
        
        # Guardar archivo
        filename = f"{int(time.time())}_{file.filename}"
        filepath = Path(UPLOAD_DIR) / filename
        
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Parsear CSV
        data_points = []
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    try:
                        timestamp = float(row[0])
                        value = float(row[1])
                        data_points.append({"timestamp": timestamp, "value": value})
                    except ValueError:
                        continue
        
        logger.info(f"CSV cargado: {filename}, {len(data_points)} puntos")
        
        return {
            "success": True,
            "filename": filename,
            "points": len(data_points),
            "data": data_points
        }
        
    except Exception as e:
        logger.error(f"Error subiendo CSV: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/quality/stats")
async def get_quality_stats():
    """Obtiene estadísticas de calidad de todos los clientes."""
    return state.quality_monitor.get_all_stats()


@app.get("/quality/report/{client_id}")
async def get_quality_report(client_id: str):
    """Obtiene reporte de calidad de un cliente específico."""
    report = state.quality_monitor.get_quality_report(client_id)
    
    if report is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return report


@app.get("/status")
async def get_server_status():
    """Obtiene el estado general del servidor."""
    serial_stats = None
    if state.serial_reader:
        serial_stats = state.serial_reader.get_stats()
    
    return {
        "active_connections": len(state.active_connections),
        "serial_active": state.serial_reader is not None,
        "serial_stats": serial_stats,
        "data_source_mode": state.data_source_mode,
        "filter_config": state.signal_processor.get_filter_config(),
        "buffer_size": state.signal_processor.get_buffer_size(),
        "quality_stats": state.quality_monitor.get_all_stats()
    }


# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    """Endpoint WebSocket para streaming de datos."""
    
    # Validar token
    if not state.auth_manager.validate_token(token):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    # Validar límite de clientes
    if len(state.active_connections) >= MAX_CLIENTS:
        await websocket.close(code=1008, reason="Max clients reached")
        return
    
    # Aceptar conexión
    await websocket.accept()
    
    # Generar ID único para el cliente
    client_id = f"client_{len(state.active_connections)}_{int(time.time())}"
    
    # Registrar cliente
    state.active_connections[client_id] = websocket
    state.quality_monitor.register_client(client_id)
    
    logger.info(f"Cliente conectado: {client_id}")
    
    try:
        # Enviar configuración inicial
        await websocket.send_json({
            "type": "config",
            "client_id": client_id,
            "filter_config": state.signal_processor.get_filter_config(),
            "sample_rate": SAMPLE_RATE
        })
        
        # Mantener conexión abierta y recibir ACKs
        while True:
            try:
                # Esperar mensajes del cliente (ACKs, cambios de configuración, etc.)
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                
                # Procesar ACK
                if data.get("type") == "ack":
                    seq = data.get("seq")
                    client_time = data.get("client_time", time.time())
                    state.quality_monitor.record_ack_received(client_id, seq, client_time)
                
            except asyncio.TimeoutError:
                # Timeout esperando mensaje, continuar
                continue
            except WebSocketDisconnect:
                break
            
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado: {client_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket {client_id}: {e}")
    finally:
        # Limpiar cliente
        if client_id in state.active_connections:
            del state.active_connections[client_id]
        state.quality_monitor.unregister_client(client_id)


# ============================================================================
# Eventos de Inicio/Cierre
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio del servidor."""
    logger.info("=== Servidor WebSocket PPG iniciando ===")
    logger.info(f"Modo de fuente de datos: {state.data_source_mode}")
    
    # Intentar iniciar lectura serial si el modo lo permite
    if state.data_source_mode in ["serial", "auto"]:
        success = await state.start_serial_reading()
        
        if not success and state.data_source_mode == "auto":
            logger.info("Modo auto: Serial no disponible, esperando datos de Tkinter")
    
    logger.info(f"Servidor listo en http://{WS_HOST}:{WS_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre del servidor."""
    logger.info("=== Servidor WebSocket PPG cerrando ===")
    
    # Cerrar todas las conexiones WebSocket
    for client_id, websocket in list(state.active_connections.items()):
        try:
            await websocket.close()
        except:
            pass
    
    # Detener lectura serial
    await state.stop_serial_reading()
    
    logger.info("Servidor cerrado")


# ============================================================================
# Punto de Entrada
# ============================================================================

if __name__ == "__main__":
    # Ejecutar servidor con uvicorn
    uvicorn.run(
        "server:app",
        host=WS_HOST,
        port=WS_PORT,
        log_level=LOG_LEVEL.lower(),
        reload=False  # Desactivar reload en producción
    )
