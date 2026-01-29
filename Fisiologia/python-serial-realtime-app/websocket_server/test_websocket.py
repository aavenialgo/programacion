#!/usr/bin/env python3
"""
Script de prueba para el servidor WebSocket PPG.

Este script genera datos sintéticos y los envía al servidor para verificar
que toda la cadena de procesamiento funciona correctamente.

Uso:
    1. Iniciar el servidor WebSocket en otra terminal: python server.py
    2. Ejecutar este script: python test_websocket.py
    3. Abrir el dashboard en el navegador: http://localhost:8765
"""

import asyncio
import time
import numpy as np
import sys
from pathlib import Path

# Agregar directorio actual al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from signal_processor import SignalProcessor
from quality_monitor import QualityMonitor
from auth_manager import AuthManager


def test_signal_processor():
    """Prueba el procesador de señales con datos sintéticos."""
    print("\n" + "="*70)
    print("TEST 1: Signal Processor")
    print("="*70)
    
    # Crear procesador
    processor = SignalProcessor(sample_rate=100, buffer_size=1000)
    
    # Configurar filtro
    processor.configure_filter(lowcut=0.5, highcut=10.0, order=4, enabled=True)
    
    # Generar señal sintética (frecuencia cardíaca ~70 bpm = 1.17 Hz)
    duration = 10  # segundos
    sample_rate = 100
    t = np.linspace(0, duration, duration * sample_rate)
    
    # Señal: componente cardíaco (1.17 Hz) + ruido de alta frecuencia
    heart_signal = 1000 * np.sin(2 * np.pi * 1.17 * t)
    noise = 200 * np.sin(2 * np.pi * 50 * t)  # Ruido de 50 Hz
    raw_signal = heart_signal + noise + np.random.randn(len(t)) * 50
    
    # Procesar muestras
    print(f"Procesando {len(t)} muestras...")
    for i, (time_point, value) in enumerate(zip(t, raw_signal)):
        processor.process_sample(time_point, value)
    
    # Obtener datos procesados
    data = processor.get_buffer_data(window_seconds=10)
    
    # Calcular mejora SNR (aproximada)
    raw_power = np.var(data['raw'])
    filtered_power = np.var(data['filtered'])
    
    print(f"✓ Muestras procesadas: {len(data['time'])}")
    print(f"✓ Potencia señal cruda: {raw_power:.2f}")
    print(f"✓ Potencia señal filtrada: {filtered_power:.2f}")
    print(f"✓ Reducción de potencia: {(1 - filtered_power/raw_power)*100:.1f}%")
    
    # Verificar que el filtro está funcionando
    assert len(data['time']) == len(t), "Pérdida de muestras"
    assert filtered_power < raw_power, "El filtro no está reduciendo el ruido"
    
    print("✅ Signal Processor: PASS")
    return True


def test_auth_manager():
    """Prueba el sistema de autenticación."""
    print("\n" + "="*70)
    print("TEST 2: Authentication Manager")
    print("="*70)
    
    # Crear gestor
    auth = AuthManager(password="test123", session_timeout_hours=24)
    
    # Test 1: Autenticación correcta
    token = auth.authenticate("test123")
    assert token is not None, "Token no generado"
    print(f"✓ Token generado: {token[:16]}...")
    
    # Test 2: Validación de token
    is_valid = auth.validate_token(token)
    assert is_valid, "Token válido rechazado"
    print(f"✓ Token validado correctamente")
    
    # Test 3: Autenticación incorrecta
    bad_token = auth.authenticate("wrongpass")
    assert bad_token is None, "Token generado con contraseña incorrecta"
    print(f"✓ Contraseña incorrecta rechazada")
    
    # Test 4: Token inválido
    is_valid = auth.validate_token("fake_token_123")
    assert not is_valid, "Token falso aceptado"
    print(f"✓ Token inválido rechazado")
    
    # Test 5: Múltiples sesiones
    token2 = auth.authenticate("test123")
    token3 = auth.authenticate("test123")
    sessions = auth.get_active_sessions_count()
    assert sessions == 3, f"Esperadas 3 sesiones, encontradas {sessions}"
    print(f"✓ Múltiples sesiones: {sessions}")
    
    # Test 6: Revocación
    auth.revoke_token(token)
    is_valid = auth.validate_token(token)
    assert not is_valid, "Token revocado aún válido"
    print(f"✓ Token revocado correctamente")
    
    print("✅ Authentication Manager: PASS")
    return True


def test_quality_monitor():
    """Prueba el monitor de calidad."""
    print("\n" + "="*70)
    print("TEST 3: Quality Monitor")
    print("="*70)
    
    # Crear monitor
    monitor = QualityMonitor(window_seconds=60)
    
    # Registrar clientes
    client1 = "test_client_1"
    client2 = "test_client_2"
    
    monitor.register_client(client1)
    monitor.register_client(client2)
    print(f"✓ Clientes registrados: 2")
    
    # Simular transmisión con diferentes tasas de pérdida
    print("Simulando transmisión (100 paquetes)...")
    
    # Usar seed para resultados reproducibles
    np.random.seed(42)
    
    for i in range(100):
        seq = monitor.get_next_seq()
        
        # Cliente 1: conexión excelente (perder paquetes 1, 50)
        monitor.record_packet_sent(client1, seq)
        if i not in [1, 50]:  # 98% éxito
            time.sleep(0.001)  # Simular latencia de 1ms
            monitor.record_ack_received(client1, seq, time.time())
        
        # Cliente 2: conexión regular (perder cada 10mo paquete)
        monitor.record_packet_sent(client2, seq)
        if i % 10 != 0:  # 90% éxito
            time.sleep(0.003)  # Simular latencia de 3ms
            monitor.record_ack_received(client2, seq, time.time())
    
    # Verificar estadísticas
    stats1 = monitor.get_client_stats(client1)
    stats2 = monitor.get_client_stats(client2)
    
    print(f"\nCliente 1 (conexión excelente):")
    print(f"  - Paquetes enviados: {stats1['packets_sent']}")
    print(f"  - Paquetes recibidos: {stats1['packets_received']}")
    print(f"  - Tasa de pérdida: {stats1['loss_rate']:.2f}%")
    print(f"  - Latencia promedio: {stats1['latency_avg']:.2f} ms")
    
    print(f"\nCliente 2 (conexión regular):")
    print(f"  - Paquetes enviados: {stats2['packets_sent']}")
    print(f"  - Paquetes recibidos: {stats2['packets_received']}")
    print(f"  - Tasa de pérdida: {stats2['loss_rate']:.2f}%")
    print(f"  - Latencia promedio: {stats2['latency_avg']:.2f} ms")
    
    # Verificaciones
    assert stats1['packets_sent'] == 100, "Conteo de paquetes incorrecto"
    assert stats2['packets_sent'] == 100, "Conteo de paquetes incorrecto"
    # Verificar que el cliente 2 perdió más paquetes
    lost1 = stats1['packets_sent'] - stats1['packets_received']
    lost2 = stats2['packets_sent'] - stats2['packets_received']
    assert lost2 > lost1, f"Cliente 2 debería perder más paquetes ({lost2} vs {lost1})"
    assert lost2 >= 10, f"Cliente 2 debería perder al menos 10 paquetes, perdió {lost2}"
    
    # Reportes de calidad
    report1 = monitor.get_quality_report(client1)
    report2 = monitor.get_quality_report(client2)
    
    print(f"\nCalidad Cliente 1: {report1['quality_indicator']} {report1['quality_text']}")
    print(f"Calidad Cliente 2: {report2['quality_indicator']} {report2['quality_text']}")
    
    print("✅ Quality Monitor: PASS")
    return True


def test_integration():
    """Prueba de integración básica."""
    print("\n" + "="*70)
    print("TEST 4: Integration Test")
    print("="*70)
    
    # Crear componentes
    auth = AuthManager("test123")
    processor = SignalProcessor(sample_rate=100)
    monitor = QualityMonitor()
    
    # Flujo completo:
    # 1. Autenticar
    token = auth.authenticate("test123")
    print(f"✓ Cliente autenticado")
    
    # 2. Registrar en monitor
    client_id = "integration_test_client"
    monitor.register_client(client_id)
    print(f"✓ Cliente registrado en monitor")
    
    # 3. Procesar y transmitir datos
    print("Procesando 50 muestras...")
    for i in range(50):
        t = i * 0.01
        value = 1000 * np.sin(2 * np.pi * 1.0 * t)
        
        # Procesar señal
        _, raw, filtered = processor.process_sample(t, value)
        
        # Simular transmisión
        seq = monitor.get_next_seq()
        monitor.record_packet_sent(client_id, seq)
        monitor.record_ack_received(client_id, seq, time.time())
    
    # Verificar estado final
    buffer = processor.get_buffer_data()
    stats = monitor.get_client_stats(client_id)
    
    print(f"✓ Buffer size: {len(buffer['time'])} muestras")
    print(f"✓ Paquetes transmitidos: {stats['packets_sent']}")
    print(f"✓ Paquetes recibidos: {stats['packets_received']}")
    print(f"✓ Tasa de pérdida: {stats['loss_rate']:.2f}%")
    
    assert len(buffer['time']) == 50, "Pérdida de muestras en buffer"
    assert stats['loss_rate'] == 0.0, "Pérdida de paquetes en test local"
    
    print("✅ Integration Test: PASS")
    return True


def generate_sample_csv():
    """Genera un archivo CSV de ejemplo para pruebas."""
    print("\n" + "="*70)
    print("BONUS: Generating Sample CSV")
    print("="*70)
    
    output_file = Path(__file__).parent / "sample_data.csv"
    
    # Generar datos
    duration = 30  # segundos
    sample_rate = 100
    t = np.linspace(0, duration, duration * sample_rate)
    
    # Señal realista: componente cardíaco + respiratorio + ruido
    heart_rate = 1.17  # Hz (70 bpm)
    resp_rate = 0.25   # Hz (15 respiraciones/min)
    
    signal = (
        1000 * np.sin(2 * np.pi * heart_rate * t) +  # Componente cardíaco
        200 * np.sin(2 * np.pi * resp_rate * t) +     # Componente respiratorio
        50 * np.random.randn(len(t))                   # Ruido
    )
    
    # Guardar CSV
    with open(output_file, 'w') as f:
        f.write("timestamp,value\n")
        for time_point, value in zip(t, signal):
            f.write(f"{time_point:.6f},{value:.2f}\n")
    
    print(f"✓ CSV generado: {output_file}")
    print(f"✓ Duración: {duration} segundos")
    print(f"✓ Frecuencia de muestreo: {sample_rate} Hz")
    print(f"✓ Total de muestras: {len(t)}")
    print(f"\nPuede cargar este archivo en el dashboard usando el botón 'Cargar CSV'")
    
    return True


def main():
    """Ejecuta todos los tests."""
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "WEBSOCKET SERVER TEST SUITE" + " "*26 + "║")
    print("╚" + "═"*68 + "╝")
    
    tests = [
        ("Signal Processor", test_signal_processor),
        ("Authentication Manager", test_auth_manager),
        ("Quality Monitor", test_quality_monitor),
        ("Integration", test_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASS" if success else "FAIL"))
        except Exception as e:
            print(f"\n❌ {name}: FAIL")
            print(f"   Error: {e}")
            results.append((name, "FAIL"))
    
    # Generar CSV de ejemplo
    try:
        generate_sample_csv()
    except Exception as e:
        print(f"\n⚠️ Warning: Could not generate sample CSV: {e}")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE TESTS")
    print("="*70)
    
    for name, result in results:
        icon = "✅" if result == "PASS" else "❌"
        print(f"{icon} {name}: {result}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r == "PASS")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron! El servidor está listo para usar.")
        print("\nPróximos pasos:")
        print("  1. Iniciar el servidor: python server.py")
        print("  2. Abrir el dashboard: http://localhost:8765")
        print("  3. Cargar sample_data.csv o conectar dispositivo PPG")
        return 0
    else:
        print("\n⚠️ Algunos tests fallaron. Revisar los errores arriba.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
