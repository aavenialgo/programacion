/**
 * Cliente JavaScript para Diagnóstico de Calidad
 * 
 * Obtiene y visualiza métricas detalladas de calidad de transmisión
 */

// ============================================================================
// Estado
// ============================================================================

const diagState = {
    clientId: null,
    updateInterval: null,
    historyData: {
        timestamps: [],
        lossRates: [],
        latencies: [],
        jitters: [],
    },
    maxHistoryPoints: 60, // 60 puntos (60 segundos si se actualiza cada segundo)
};

// ============================================================================
// Inicialización
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Diagnóstico iniciando...');
    
    // Obtener client_id de URL o localStorage
    const urlParams = new URLSearchParams(window.location.search);
    diagState.clientId = urlParams.get('client_id') || localStorage.getItem('client_id');
    
    if (diagState.clientId) {
        document.getElementById('info-client-id').textContent = diagState.clientId;
    }
    
    // Configurar event listeners
    setupEventListeners();
    
    // Inicializar gráfico
    initHistoryChart();
    
    // Iniciar actualización automática
    startAutoUpdate();
    
    // Primera actualización
    updateDiagnostics();
});

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    document.getElementById('btn-export-report').addEventListener('click', exportReport);
    document.getElementById('btn-reset-stats').addEventListener('click', resetStats);
    document.getElementById('btn-refresh').addEventListener('click', updateDiagnostics);
}

// ============================================================================
// Actualización de Datos
// ============================================================================

function startAutoUpdate() {
    // Actualizar cada segundo
    diagState.updateInterval = setInterval(() => {
        updateDiagnostics();
    }, 1000);
}

async function updateDiagnostics() {
    try {
        const response = await fetch('/quality/stats');
        if (!response.ok) {
            throw new Error('Error obteniendo estadísticas');
        }
        
        const data = await response.json();
        console.log('Estadísticas:', data);
        
        // Si no tenemos client_id, usar el primero disponible
        if (!diagState.clientId && data.clients) {
            const clientIds = Object.keys(data.clients);
            if (clientIds.length > 0) {
                diagState.clientId = clientIds[0];
                document.getElementById('info-client-id').textContent = diagState.clientId;
                localStorage.setItem('client_id', diagState.clientId);
            }
        }
        
        // Actualizar métricas
        if (diagState.clientId && data.clients[diagState.clientId]) {
            const stats = data.clients[diagState.clientId];
            updateMetrics(stats);
            updateHistoryChart(stats);
            updateRecommendations(stats);
        } else {
            showNoDataMessage();
        }
        
        // Actualizar timestamp
        document.getElementById('info-last-update').textContent = new Date().toLocaleTimeString();
        
    } catch (error) {
        console.error('Error actualizando diagnóstico:', error);
    }
}

// ============================================================================
// Actualización de Métricas
// ============================================================================

function updateMetrics(stats) {
    // Paquetes
    document.getElementById('metric-packets-sent').textContent = stats.packets_sent;
    document.getElementById('metric-packets-received').textContent = stats.packets_received;
    document.getElementById('metric-packets-lost').textContent = stats.packets_lost;
    
    // Tasa de pérdida
    document.getElementById('metric-loss-rate').textContent = `${stats.loss_rate}%`;
    
    // Indicador de calidad
    const indicator = document.getElementById('loss-indicator');
    const icon = indicator.querySelector('.quality-icon');
    const text = indicator.querySelector('.quality-text');
    
    if (stats.loss_rate < 1.0) {
        icon.textContent = '🟢';
        text.textContent = 'Excelente';
        text.style.color = '#27ae60';
    } else if (stats.loss_rate < 5.0) {
        icon.textContent = '🟡';
        text.textContent = 'Buena';
        text.style.color = '#f39c12';
    } else {
        icon.textContent = '🔴';
        text.textContent = 'Deficiente';
        text.style.color = '#e74c3c';
    }
    
    // Latencia
    document.getElementById('metric-latency-avg').textContent = `${stats.latency_avg} ms`;
    document.getElementById('metric-latency-min').textContent = `${stats.latency_min} ms`;
    document.getElementById('metric-latency-max').textContent = `${stats.latency_max} ms`;
    
    // Jitter
    document.getElementById('metric-jitter').textContent = `${stats.jitter} ms`;
    
    // Tiempo de conexión
    const uptime = formatUptime(stats.uptime_seconds);
    document.getElementById('info-uptime').textContent = uptime;
}

// ============================================================================
// Gráfico Histórico
// ============================================================================

function initHistoryChart() {
    const layout = {
        title: 'Métricas Históricas',
        xaxis: {
            title: 'Tiempo',
            showgrid: true,
        },
        yaxis: {
            title: 'Tasa de Pérdida (%)',
            showgrid: true,
            side: 'left',
        },
        yaxis2: {
            title: 'Latencia (ms)',
            overlaying: 'y',
            side: 'right',
        },
        margin: { t: 50, r: 80, b: 50, l: 80 },
        showlegend: true,
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
    };
    
    Plotly.newPlot('history-chart', [], layout, config);
}

function updateHistoryChart(stats) {
    // Agregar punto al historial
    const now = new Date();
    diagState.historyData.timestamps.push(now);
    diagState.historyData.lossRates.push(stats.loss_rate);
    diagState.historyData.latencies.push(stats.latency_avg);
    diagState.historyData.jitters.push(stats.jitter);
    
    // Limitar tamaño del historial
    if (diagState.historyData.timestamps.length > diagState.maxHistoryPoints) {
        diagState.historyData.timestamps.shift();
        diagState.historyData.lossRates.shift();
        diagState.historyData.latencies.shift();
        diagState.historyData.jitters.shift();
    }
    
    // Crear trazas
    const traces = [
        {
            x: diagState.historyData.timestamps,
            y: diagState.historyData.lossRates,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Tasa de Pérdida (%)',
            line: { color: '#e74c3c', width: 2 },
            marker: { size: 6 },
            yaxis: 'y',
        },
        {
            x: diagState.historyData.timestamps,
            y: diagState.historyData.latencies,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Latencia (ms)',
            line: { color: '#3498db', width: 2 },
            marker: { size: 6 },
            yaxis: 'y2',
        },
    ];
    
    Plotly.react('history-chart', traces);
}

// ============================================================================
// Recomendaciones
// ============================================================================

function updateRecommendations(stats) {
    const recommendations = [];
    
    // Analizar pérdida de paquetes
    if (stats.loss_rate > 5.0) {
        recommendations.push({
            icon: '🔴',
            text: 'Alta tasa de pérdida de paquetes. Verifique la calidad de su conexión de red.',
            severity: 'high'
        });
    } else if (stats.loss_rate > 1.0) {
        recommendations.push({
            icon: '🟡',
            text: 'Pérdida moderada de paquetes. Considere cerrar otras aplicaciones que usen la red.',
            severity: 'medium'
        });
    } else {
        recommendations.push({
            icon: '🟢',
            text: 'Calidad de conexión excelente. No se requieren acciones.',
            severity: 'low'
        });
    }
    
    // Analizar latencia
    if (stats.latency_avg > 100) {
        recommendations.push({
            icon: '⚠️',
            text: 'Latencia alta. Intente conectarse a una red más rápida o acérquese al router.',
            severity: 'high'
        });
    } else if (stats.latency_avg > 50) {
        recommendations.push({
            icon: 'ℹ️',
            text: 'Latencia moderada. La experiencia debería ser aceptable.',
            severity: 'medium'
        });
    }
    
    // Analizar jitter
    if (stats.jitter > 20) {
        recommendations.push({
            icon: '📊',
            text: 'Jitter alto detectado. La conexión puede ser inestable. Evite usar WiFi congestionado.',
            severity: 'high'
        });
    }
    
    // Mostrar recomendaciones
    const listElement = document.getElementById('recommendations-list');
    listElement.innerHTML = '';
    
    recommendations.forEach(rec => {
        const div = document.createElement('div');
        div.className = `recommendation recommendation-${rec.severity}`;
        div.innerHTML = `<span class="rec-icon">${rec.icon}</span> ${rec.text}`;
        listElement.appendChild(div);
    });
}

// ============================================================================
// Acciones
// ============================================================================

function exportReport() {
    const reportData = {
        client_id: diagState.clientId,
        timestamp: new Date().toISOString(),
        history: {
            timestamps: diagState.historyData.timestamps.map(t => t.toISOString()),
            lossRates: diagState.historyData.lossRates,
            latencies: diagState.historyData.latencies,
            jitters: diagState.historyData.jitters,
        },
        current_metrics: getCurrentMetrics(),
    };
    
    // Crear JSON
    const json = JSON.stringify(reportData, null, 2);
    
    // Descargar
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quality_report_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('Reporte exportado');
}

function resetStats() {
    if (confirm('¿Está seguro de que desea reiniciar las estadísticas?')) {
        // Limpiar historial
        diagState.historyData = {
            timestamps: [],
            lossRates: [],
            latencies: [],
            jitters: [],
        };
        
        // Actualizar gráfico
        Plotly.react('history-chart', []);
        
        console.log('Estadísticas reiniciadas');
    }
}

// ============================================================================
// Utilidades
// ============================================================================

function getCurrentMetrics() {
    return {
        packets_sent: document.getElementById('metric-packets-sent').textContent,
        packets_received: document.getElementById('metric-packets-received').textContent,
        packets_lost: document.getElementById('metric-packets-lost').textContent,
        loss_rate: document.getElementById('metric-loss-rate').textContent,
        latency_avg: document.getElementById('metric-latency-avg').textContent,
        latency_min: document.getElementById('metric-latency-min').textContent,
        latency_max: document.getElementById('metric-latency-max').textContent,
        jitter: document.getElementById('metric-jitter').textContent,
    };
}

function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function showNoDataMessage() {
    console.warn('No hay datos de cliente disponibles');
    
    // Mostrar mensaje en las métricas
    const metricsCards = document.querySelectorAll('.metric-card');
    metricsCards.forEach(card => {
        card.style.opacity = '0.5';
    });
}

// Limpiar al cerrar
window.addEventListener('beforeunload', () => {
    if (diagState.updateInterval) {
        clearInterval(diagState.updateInterval);
    }
});
