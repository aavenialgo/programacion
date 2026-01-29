"""
Ejemplo de integración del servidor WebSocket con la aplicación Tkinter existente.

Este módulo muestra cómo enviar datos desde la app Tkinter al servidor WebSocket
para que puedan ser visualizados por clientes remotos.

Uso:
    1. Iniciar el servidor WebSocket
    2. Importar este módulo en la app Tkinter
    3. Crear instancia de TkinterWebSocketBridge
    4. Llamar send_data() cuando se reciban datos del serial
"""

import requests
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TkinterWebSocketBridge:
    """
    Puente entre la aplicación Tkinter y el servidor WebSocket.
    
    Envía datos capturados por Tkinter al servidor WebSocket de forma asíncrona
    para no bloquear la interfaz de usuario.
    """
    
    def __init__(self, server_url: str = "http://localhost:8765", enabled: bool = True):
        """
        Inicializa el puente de integración.
        
        Args:
            server_url: URL del servidor WebSocket
            enabled: Si False, deshabilita el envío de datos (modo standalone)
        """
        self.server_url = server_url
        self.enabled = enabled
        self.push_endpoint = f"{server_url}/data/push"
        
        # Estadísticas
        self.packets_sent = 0
        self.errors_count = 0
        
        # Test de conectividad inicial
        if self.enabled:
            self._test_connection()
    
    def _test_connection(self):
        """Prueba la conectividad con el servidor."""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=1.0)
            if response.ok:
                logger.info(f"✓ Servidor WebSocket detectado en {self.server_url}")
            else:
                logger.warning(f"Servidor WebSocket responde pero con error: {response.status_code}")
        except requests.exceptions.RequestException:
            logger.warning(f"Servidor WebSocket no disponible en {self.server_url}")
            logger.info("Los datos no se enviarán al servidor WebSocket (modo standalone)")
            self.enabled = False
    
    def send_data(self, timestamp: float, value: float):
        """
        Envía un punto de datos al servidor WebSocket.
        
        Args:
            timestamp: Tiempo relativo en segundos
            value: Valor crudo de la señal
        
        Esta función es no-bloqueante y retorna inmediatamente.
        """
        if not self.enabled:
            return
        
        # Enviar en hilo separado para no bloquear la UI
        thread = threading.Thread(
            target=self._send_async,
            args=(timestamp, value),
            daemon=True
        )
        thread.start()
    
    def _send_async(self, timestamp: float, value: float):
        """Envío asíncrono de datos (ejecutado en hilo separado)."""
        try:
            response = requests.post(
                self.push_endpoint,
                json={"timestamp": timestamp, "value": value},
                timeout=0.1  # Timeout corto para no acumular retrasos
            )
            
            if response.ok:
                self.packets_sent += 1
            else:
                self.errors_count += 1
                if self.errors_count % 100 == 0:
                    logger.warning(f"Error enviando datos al WebSocket: {response.status_code}")
                    
        except requests.exceptions.Timeout:
            self.errors_count += 1
            # No loguear timeouts individuales para no saturar logs
            
        except requests.exceptions.RequestException as e:
            self.errors_count += 1
            if self.errors_count % 100 == 0:
                logger.error(f"Error de conexión con WebSocket server: {e}")
    
    def get_stats(self) -> dict:
        """Retorna estadísticas de envío."""
        return {
            "enabled": self.enabled,
            "packets_sent": self.packets_sent,
            "errors_count": self.errors_count,
            "server_url": self.server_url
        }
    
    def enable(self):
        """Habilita el envío de datos."""
        self.enabled = True
        self._test_connection()
    
    def disable(self):
        """Deshabilita el envío de datos."""
        self.enabled = False


# ============================================================================
# Ejemplo de uso en la aplicación Tkinter existente
# ============================================================================

def example_integration():
    """
    Ejemplo de cómo integrar en src/ui/serial_reader.py o similar.
    """
    
    # 1. Crear instancia del bridge (hacer esto en __init__)
    websocket_bridge = TkinterWebSocketBridge(
        server_url="http://localhost:8765",
        enabled=True  # Puede ser configurable desde la UI
    )
    
    # 2. En el callback de datos del serial (ejemplo simplificado)
    def on_serial_data_received(line: str):
        """Callback cuando se reciben datos del puerto serial."""
        
        # Parsear datos (formato: "tiempo,valor" o similar)
        try:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                timestamp = float(parts[0])
                value = float(parts[1])
                
                # Procesar en Tkinter (código existente)
                # ... tu código actual de procesamiento ...
                
                # Enviar al servidor WebSocket
                websocket_bridge.send_data(timestamp, value)
                
        except (ValueError, IndexError):
            pass  # Ignorar líneas mal formadas
    
    # 3. Opcional: Agregar botón en la UI para habilitar/deshabilitar
    def toggle_websocket_streaming():
        """Toggle de streaming a WebSocket desde la UI."""
        if websocket_bridge.enabled:
            websocket_bridge.disable()
            print("WebSocket streaming deshabilitado")
        else:
            websocket_bridge.enable()
            print("WebSocket streaming habilitado")
    
    # 4. Opcional: Mostrar estadísticas en la UI
    def show_websocket_stats():
        """Muestra estadísticas de envío."""
        stats = websocket_bridge.get_stats()
        print(f"WebSocket Stats:")
        print(f"  - Habilitado: {stats['enabled']}")
        print(f"  - Paquetes enviados: {stats['packets_sent']}")
        print(f"  - Errores: {stats['errors_count']}")
        print(f"  - Servidor: {stats['server_url']}")


# ============================================================================
# Integración alternativa: Modo observador
# ============================================================================

class TkinterDataObserver:
    """
    Observador que se puede agregar a la app Tkinter sin modificar código existente.
    
    Uso:
        observer = TkinterDataObserver()
        # Cada vez que se procesen datos:
        observer.notify(timestamp, value)
    """
    
    def __init__(self):
        self.bridge = TkinterWebSocketBridge()
        self.observers = []
    
    def notify(self, timestamp: float, value: float):
        """Notifica nuevos datos a todos los observadores."""
        # Enviar al WebSocket
        self.bridge.send_data(timestamp, value)
        
        # Notificar a otros observadores si los hay
        for observer_func in self.observers:
            try:
                observer_func(timestamp, value)
            except Exception as e:
                logger.error(f"Error en observer: {e}")
    
    def add_observer(self, func):
        """Agrega un observador adicional."""
        self.observers.append(func)


if __name__ == "__main__":
    """Prueba de integración."""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Prueba de Integración Tkinter-WebSocket ===\n")
    
    # Crear bridge
    bridge = TkinterWebSocketBridge(server_url="http://localhost:8765")
    
    # Simular envío de datos
    import time
    import random
    
    print("Enviando 10 puntos de datos de prueba...")
    for i in range(10):
        timestamp = i * 0.01  # 100 Hz
        value = -68000 + random.randint(-1000, 1000)
        
        bridge.send_data(timestamp, value)
        print(f"  [{i+1}/10] t={timestamp:.3f}s, v={value:.1f}")
        time.sleep(0.01)
    
    # Esperar a que terminen los envíos
    time.sleep(0.5)
    
    # Mostrar estadísticas
    stats = bridge.get_stats()
    print(f"\n=== Estadísticas ===")
    print(f"Paquetes enviados: {stats['packets_sent']}")
    print(f"Errores: {stats['errors_count']}")
    print(f"Estado: {'Activo' if stats['enabled'] else 'Inactivo'}")
