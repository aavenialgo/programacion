"""
Monitoreo de calidad de transmisión WebSocket.

Rastrea métricas como latencia, jitter, pérdida de paquetes, etc.
"""
import time
from collections import deque
from typing import Dict, Optional
import logging
import statistics

logger = logging.getLogger(__name__)


class QualityMonitor:
    """
    Monitor de calidad para conexiones WebSocket.
    
    Rastrea métricas por cliente para diagnosticar problemas de red.
    """
    
    def __init__(self, window_seconds: int = 60):
        """
        Inicializa el monitor de calidad.
        
        Args:
            window_seconds: Ventana de tiempo para estadísticas históricas
        """
        self.window_seconds = window_seconds
        
        # Métricas por cliente: {client_id: ClientMetrics}
        self.clients: Dict[str, 'ClientMetrics'] = {}
        
        # Contador global de paquetes enviados
        self.global_seq = 0
        
        logger.info(f"QualityMonitor inicializado (ventana: {window_seconds}s)")
    
    def register_client(self, client_id: str):
        """
        Registra un nuevo cliente.
        
        Args:
            client_id: Identificador único del cliente
        """
        if client_id not in self.clients:
            self.clients[client_id] = ClientMetrics(
                client_id=client_id,
                window_seconds=self.window_seconds
            )
            logger.info(f"Cliente registrado: {client_id}")
    
    def unregister_client(self, client_id: str):
        """
        Elimina un cliente del registro.
        
        Args:
            client_id: Identificador del cliente
        """
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Cliente no registrado: {client_id}")
    
    def get_next_seq(self) -> int:
        """
        Obtiene el siguiente número de secuencia global.
        
        Returns:
            int: Número de secuencia
        """
        self.global_seq += 1
        return self.global_seq
    
    def record_packet_sent(self, client_id: str, seq: int):
        """
        Registra un paquete enviado a un cliente.
        
        Args:
            client_id: ID del cliente
            seq: Número de secuencia del paquete
        """
        if client_id in self.clients:
            self.clients[client_id].record_packet_sent(seq)
    
    def record_ack_received(self, client_id: str, seq: int, client_time: float):
        """
        Registra el ACK de un paquete recibido del cliente.
        
        Args:
            client_id: ID del cliente
            seq: Número de secuencia confirmado
            client_time: Timestamp del cliente cuando recibió el paquete
        """
        if client_id in self.clients:
            self.clients[client_id].record_ack_received(seq, client_time)
    
    def get_client_stats(self, client_id: str) -> Optional[dict]:
        """
        Obtiene estadísticas de un cliente específico.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            dict: Estadísticas del cliente o None si no existe
        """
        if client_id in self.clients:
            return self.clients[client_id].get_stats()
        return None
    
    def get_all_stats(self) -> dict:
        """
        Obtiene estadísticas de todos los clientes.
        
        Returns:
            dict: Estadísticas globales y por cliente
        """
        client_stats = {
            client_id: client.get_stats()
            for client_id, client in self.clients.items()
        }
        
        return {
            "global_seq": self.global_seq,
            "active_clients": len(self.clients),
            "clients": client_stats
        }
    
    def get_quality_report(self, client_id: str) -> Optional[dict]:
        """
        Genera un reporte de calidad legible para un cliente.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            dict: Reporte de calidad con indicadores y recomendaciones
        """
        stats = self.get_client_stats(client_id)
        if not stats:
            return None
        
        loss_rate = stats['loss_rate']
        
        # Determinar nivel de calidad
        if loss_rate < 1.0:
            quality_level = "excellent"
            quality_indicator = "🟢"
            quality_text = "Excelente"
        elif loss_rate < 5.0:
            quality_level = "good"
            quality_indicator = "🟡"
            quality_text = "Buena"
        else:
            quality_level = "poor"
            quality_indicator = "🔴"
            quality_text = "Deficiente"
        
        return {
            "client_id": client_id,
            "quality_level": quality_level,
            "quality_indicator": quality_indicator,
            "quality_text": quality_text,
            "loss_rate": loss_rate,
            "latency_avg": stats['latency_avg'],
            "latency_max": stats['latency_max'],
            "jitter": stats['jitter'],
            "packets_sent": stats['packets_sent'],
            "packets_received": stats['packets_received'],
            "packets_lost": stats['packets_lost']
        }


class ClientMetrics:
    """Métricas de calidad para un cliente individual."""
    
    def __init__(self, client_id: str, window_seconds: int = 60):
        """
        Inicializa las métricas del cliente.
        
        Args:
            client_id: Identificador del cliente
            window_seconds: Ventana de tiempo para historial
        """
        self.client_id = client_id
        self.window_seconds = window_seconds
        
        # Contadores
        self.packets_sent = 0
        self.packets_received = 0
        
        # Paquetes pendientes: {seq: send_time}
        self.pending_packets: Dict[int, float] = {}
        
        # Historial de latencias (en ms)
        self.latency_history = deque(maxlen=1000)
        
        # Historial temporal para calcular tasa de pérdida
        # [(timestamp, sent, received)]
        self.history = deque(maxlen=60)  # 60 segundos de historial
        
        self.connection_start = time.time()
        self.last_packet_time = None
    
    def record_packet_sent(self, seq: int):
        """Registra un paquete enviado."""
        send_time = time.time()
        self.packets_sent += 1
        self.pending_packets[seq] = send_time
        self.last_packet_time = send_time
        
        # Limpiar paquetes pendientes antiguos (>10 segundos)
        cutoff_time = send_time - 10.0
        old_seqs = [s for s, t in self.pending_packets.items() if t < cutoff_time]
        for seq in old_seqs:
            del self.pending_packets[seq]
    
    def record_ack_received(self, seq: int, client_time: float):
        """Registra ACK de paquete recibido."""
        self.packets_received += 1
        
        # Calcular latencia si el paquete está en pendientes
        if seq in self.pending_packets:
            send_time = self.pending_packets[seq]
            latency_ms = (time.time() - send_time) * 1000  # Convertir a ms
            self.latency_history.append(latency_ms)
            del self.pending_packets[seq]
    
    def get_stats(self) -> dict:
        """Calcula y retorna estadísticas actuales."""
        # Calcular tasa de pérdida
        packets_lost = max(0, self.packets_sent - self.packets_received - len(self.pending_packets))
        
        if self.packets_sent > 0:
            loss_rate = (packets_lost / self.packets_sent) * 100
        else:
            loss_rate = 0.0
        
        # Calcular latencia
        if self.latency_history:
            latency_avg = statistics.mean(self.latency_history)
            latency_min = min(self.latency_history)
            latency_max = max(self.latency_history)
            
            # Calcular jitter (desviación estándar de latencia)
            if len(self.latency_history) > 1:
                jitter = statistics.stdev(self.latency_history)
            else:
                jitter = 0.0
        else:
            latency_avg = 0.0
            latency_min = 0.0
            latency_max = 0.0
            jitter = 0.0
        
        # Tiempo de conexión
        uptime = time.time() - self.connection_start
        
        return {
            "client_id": self.client_id,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packets_lost": packets_lost,
            "packets_pending": len(self.pending_packets),
            "loss_rate": round(loss_rate, 2),
            "latency_avg": round(latency_avg, 2),
            "latency_min": round(latency_min, 2),
            "latency_max": round(latency_max, 2),
            "jitter": round(jitter, 2),
            "uptime_seconds": round(uptime, 2),
            "last_packet_time": self.last_packet_time
        }


if __name__ == "__main__":
    # Ejemplo de uso
    import random
    
    # Crear monitor
    monitor = QualityMonitor(window_seconds=60)
    
    # Registrar clientes
    client1 = "client_001"
    client2 = "client_002"
    
    monitor.register_client(client1)
    monitor.register_client(client2)
    
    # Simular envío de paquetes
    print("=== Simulando transmisión de paquetes ===\n")
    
    for i in range(100):
        seq = monitor.get_next_seq()
        
        # Enviar a ambos clientes
        monitor.record_packet_sent(client1, seq)
        monitor.record_packet_sent(client2, seq)
        
        # Simular recepción con pérdida ocasional
        # Cliente 1: 99% de éxito
        if random.random() > 0.01:
            time.sleep(random.uniform(0.001, 0.005))  # Simular latencia de red
            monitor.record_ack_received(client1, seq, time.time())
        
        # Cliente 2: 95% de éxito (peor conexión)
        if random.random() > 0.05:
            time.sleep(random.uniform(0.001, 0.010))
            monitor.record_ack_received(client2, seq, time.time())
        
        time.sleep(0.01)  # 100Hz
    
    # Mostrar estadísticas
    print("\n=== Estadísticas Cliente 1 ===")
    stats1 = monitor.get_client_stats(client1)
    for key, value in stats1.items():
        print(f"{key}: {value}")
    
    print("\n=== Estadísticas Cliente 2 ===")
    stats2 = monitor.get_client_stats(client2)
    for key, value in stats2.items():
        print(f"{key}: {value}")
    
    # Reportes de calidad
    print("\n=== Reporte de Calidad Cliente 1 ===")
    report1 = monitor.get_quality_report(client1)
    print(f"{report1['quality_indicator']} {report1['quality_text']}")
    print(f"Pérdida: {report1['loss_rate']}%")
    print(f"Latencia promedio: {report1['latency_avg']:.2f} ms")
    
    print("\n=== Reporte de Calidad Cliente 2 ===")
    report2 = monitor.get_quality_report(client2)
    print(f"{report2['quality_indicator']} {report2['quality_text']}")
    print(f"Pérdida: {report2['loss_rate']}%")
    print(f"Latencia promedio: {report2['latency_avg']:.2f} ms")
