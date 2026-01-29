/**
 * Cliente JavaScript para Dashboard PPG en Tiempo Real
 * 
 * Maneja:
 * - Conexión WebSocket
 * - Autenticación
 * - Visualización con Plotly.js
 * - Control de filtros
 * - Gestión de datos (guardar/cargar CSV)
 * - Monitoreo de calidad
 */

// ============================================================================
// Estado Global
// ============================================================================

const state = {
    ws: null,
    token: null,
    clientId: null,
    isConnected: false,
    isPaused: false,
    
    // Buffers de datos
    timeData: [],
    rawData: [],
    filteredData: [],
    maxPoints: 10000, // Máximo de puntos en buffer
    
    // Configuración
    windowSeconds: 10,
    signalView: 'both', // 'both', 'raw', 'filtered'
    autoScaleY: true,
    
    // Métricas de calidad
    packetsReceived: 0,
    lastSeq: null,
    packetsLost: 0,
    latencies: [],
    
    // Timestamps
    lastUpdate: Date.now(),
    startTime: null,
};

// ============================================================================
// Inicialización
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard iniciando...');
    
    // Configurar event listeners
    setupEventListeners();
    
    // Inicializar gráfico
    initChart();
    
    // Cargar configuración del filtro
    loadFilterConfig();
});

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Autenticación
    document.getElementById('btn-connect').addEventListener('click', authenticate);
    document.getElementById('password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') authenticate();
    });
    
    // Filtros
    document.getElementById('btn-update-filter').addEventListener('click', updateFilter);
    document.getElementById('signal-view').addEventListener('change', (e) => {
        state.signalView = e.target.value;
        updateChart();
    });
    
    // Visualización
    document.getElementById('btn-play-pause').addEventListener('click', togglePause);
    document.getElementById('window-seconds').addEventListener('change', (e) => {
        state.windowSeconds = parseInt(e.target.value);
    });
    document.getElementById('autoscale-y').addEventListener('change', (e) => {
        state.autoScaleY = e.target.checked;
    });
    
    // Gestión de datos
    document.getElementById('btn-save-data').addEventListener('click', saveDataToCSV);
    document.getElementById('btn-load-data').addEventListener('click', loadDataFromCSV);
    
    // Diagnóstico
    document.getElementById('btn-diagnostics').addEventListener('click', () => {
        window.open('/diagnostics', '_blank');
    });
}

// ============================================================================
// Autenticación
// ============================================================================

async function authenticate() {
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('auth-error');
    
    if (!password) {
        showError(errorDiv, 'Por favor ingrese una contraseña');
        return;
    }
    
    try {
        const response = await fetch('/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password })
        });
        
        if (!response.ok) {
            throw new Error('Contraseña incorrecta');
        }
        
        const data = await response.json();
        state.token = data.token;
        
        // Ocultar sección de autenticación
        document.getElementById('auth-section').style.display = 'none';
        
        // Mostrar otras secciones
        document.getElementById('filter-section').style.display = 'block';
        document.getElementById('view-section').style.display = 'block';
        document.getElementById('data-section').style.display = 'block';
        document.getElementById('quality-section').style.display = 'block';
        
        // Conectar WebSocket
        connectWebSocket();
        
    } catch (error) {
        showError(errorDiv, error.message);
    }
}

// ============================================================================
// WebSocket
// ============================================================================

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?token=${state.token}`;
    
    console.log('Conectando a WebSocket:', wsUrl);
    
    state.ws = new WebSocket(wsUrl);
    
    state.ws.onopen = () => {
        console.log('WebSocket conectado');
        state.isConnected = true;
        state.startTime = Date.now();
        updateConnectionStatus(true);
    };
    
    state.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    state.ws.onerror = (error) => {
        console.error('Error de WebSocket:', error);
        updateConnectionStatus(false);
    };
    
    state.ws.onclose = () => {
        console.log('WebSocket cerrado');
        state.isConnected = false;
        updateConnectionStatus(false);
    };
}

function handleWebSocketMessage(data) {
    if (data.type === 'config') {
        // Mensaje de configuración inicial
        state.clientId = data.client_id;
        console.log('Cliente ID:', state.clientId);
        return;
    }
    
    // Mensaje de datos
    const { seq, timestamp, raw, filtered, server_time } = data;
    
    // Detectar pérdidas de paquetes
    if (state.lastSeq !== null) {
        const expectedSeq = state.lastSeq + 1;
        if (seq > expectedSeq) {
            const lost = seq - expectedSeq;
            state.packetsLost += lost;
            console.warn(`Paquetes perdidos: ${lost} (esperado: ${expectedSeq}, recibido: ${seq})`);
        }
    }
    state.lastSeq = seq;
    state.packetsReceived++;
    
    // Calcular latencia (aproximada)
    const clientTime = Date.now() / 1000;
    const latency = (clientTime - server_time) * 1000; // ms
    state.latencies.push(latency);
    if (state.latencies.length > 100) {
        state.latencies.shift();
    }
    
    // Enviar ACK al servidor
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({
            type: 'ack',
            seq: seq,
            client_time: clientTime
        }));
    }
    
    // Agregar datos a buffers
    if (!state.isPaused) {
        state.timeData.push(timestamp);
        state.rawData.push(raw);
        state.filteredData.push(filtered);
        
        // Limitar tamaño del buffer
        if (state.timeData.length > state.maxPoints) {
            state.timeData.shift();
            state.rawData.shift();
            state.filteredData.shift();
        }
        
        // Actualizar gráfico (con throttling)
        const now = Date.now();
        if (now - state.lastUpdate > 50) { // Actualizar máximo cada 50ms
            updateChart();
            updateInfoBar();
            updateQualityIndicators();
            state.lastUpdate = now;
        }
    }
}

// ============================================================================
// Gráficos con Plotly.js
// ============================================================================

function initChart() {
    const layout = {
        title: 'Señal PPG en Tiempo Real',
        xaxis: {
            title: 'Tiempo (s)',
            showgrid: true,
        },
        yaxis: {
            title: 'Amplitud',
            showgrid: true,
        },
        margin: { t: 50, r: 50, b: 50, l: 50 },
        hovermode: 'closest',
        showlegend: true,
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    };
    
    Plotly.newPlot('chart', [], layout, config);
}

function updateChart() {
    if (state.timeData.length === 0) return;
    
    // Filtrar datos por ventana de tiempo
    const currentTime = state.timeData[state.timeData.length - 1];
    const startTime = currentTime - state.windowSeconds;
    
    const filteredIndices = state.timeData
        .map((t, i) => ({ t, i }))
        .filter(({ t }) => t >= startTime)
        .map(({ i }) => i);
    
    const windowTime = filteredIndices.map(i => state.timeData[i]);
    const windowRaw = filteredIndices.map(i => state.rawData[i]);
    const windowFiltered = filteredIndices.map(i => state.filteredData[i]);
    
    // Preparar trazas según la vista seleccionada
    const traces = [];
    
    if (state.signalView === 'both' || state.signalView === 'raw') {
        traces.push({
            x: windowTime,
            y: windowRaw,
            type: 'scatter',
            mode: 'lines',
            name: 'Señal Cruda',
            line: { color: '#3498db', width: 1 },
        });
    }
    
    if (state.signalView === 'both' || state.signalView === 'filtered') {
        traces.push({
            x: windowTime,
            y: windowFiltered,
            type: 'scatter',
            mode: 'lines',
            name: 'Señal Filtrada',
            line: { color: '#e74c3c', width: 2 },
        });
    }
    
    // Actualizar layout
    const layout = {
        xaxis: { 
            range: [startTime, currentTime],
            title: 'Tiempo (s)',
        },
        yaxis: {
            title: 'Amplitud',
            autorange: state.autoScaleY,
        },
    };
    
    Plotly.react('chart', traces, layout);
}

// ============================================================================
// Control de Filtros
// ============================================================================

async function loadFilterConfig() {
    try {
        const response = await fetch('/filter/config');
        const config = await response.json();
        
        document.getElementById('filter-enabled').checked = config.enabled;
        document.getElementById('filter-lowcut').value = config.lowcut;
        document.getElementById('filter-highcut').value = config.highcut;
        document.getElementById('filter-order').value = config.order;
        
    } catch (error) {
        console.error('Error cargando configuración de filtro:', error);
    }
}

async function updateFilter() {
    const config = {
        enabled: document.getElementById('filter-enabled').checked,
        lowcut: parseFloat(document.getElementById('filter-lowcut').value),
        highcut: parseFloat(document.getElementById('filter-highcut').value),
        order: parseInt(document.getElementById('filter-order').value),
    };
    
    try {
        const response = await fetch('/filter/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            throw new Error('Error actualizando filtro');
        }
        
        const result = await response.json();
        console.log('Filtro actualizado:', result);
        alert('Filtro actualizado correctamente');
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error actualizando filtro: ' + error.message);
    }
}

// ============================================================================
// Controles de Visualización
// ============================================================================

function togglePause() {
    state.isPaused = !state.isPaused;
    const btn = document.getElementById('btn-play-pause');
    btn.textContent = state.isPaused ? '▶️ Reproducir' : '⏸️ Pausar';
}

// ============================================================================
// Gestión de Datos
// ============================================================================

function saveDataToCSV() {
    if (state.timeData.length === 0) {
        alert('No hay datos para guardar');
        return;
    }
    
    // Crear contenido CSV
    let csv = 'timestamp,raw,filtered\n';
    for (let i = 0; i < state.timeData.length; i++) {
        csv += `${state.timeData[i]},${state.rawData[i]},${state.filteredData[i]}\n`;
    }
    
    // Crear blob y descargar
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ppg_data_${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('Datos guardados:', state.timeData.length, 'puntos');
}

async function loadDataFromCSV() {
    const fileInput = document.getElementById('file-upload');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Por favor seleccione un archivo CSV');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/data/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Error cargando archivo');
        }
        
        const result = await response.json();
        console.log('Archivo cargado:', result);
        
        // Cargar datos en buffers
        state.timeData = result.data.map(d => d.timestamp);
        state.rawData = result.data.map(d => d.value);
        state.filteredData = [...state.rawData]; // Por ahora, copiar raw
        
        // Pausar para analizar
        state.isPaused = true;
        document.getElementById('btn-play-pause').textContent = '▶️ Reproducir';
        
        updateChart();
        alert(`Cargados ${result.points} puntos de datos`);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error cargando archivo: ' + error.message);
    }
}

// ============================================================================
// Actualización de UI
// ============================================================================

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (connected) {
        statusElement.textContent = '🟢 Conectado';
        statusElement.className = 'status-connected';
    } else {
        statusElement.textContent = '🔴 Desconectado';
        statusElement.className = 'status-disconnected';
    }
}

function updateInfoBar() {
    document.getElementById('info-samples').textContent = `Muestras: ${state.timeData.length}`;
    
    if (state.timeData.length > 1) {
        const duration = state.timeData[state.timeData.length - 1] - state.timeData[0];
        const rate = state.timeData.length / duration;
        document.getElementById('info-rate').textContent = `Tasa: ${rate.toFixed(1)} Hz`;
        
        const currentTime = state.timeData[state.timeData.length - 1];
        document.getElementById('info-time').textContent = `Tiempo: ${currentTime.toFixed(1)}s`;
    }
}

function updateQualityIndicators() {
    // Tasa de pérdida
    const totalPackets = state.packetsReceived + state.packetsLost;
    const lossRate = totalPackets > 0 ? (state.packetsLost / totalPackets) * 100 : 0;
    
    document.getElementById('stat-loss').textContent = `${lossRate.toFixed(2)}%`;
    document.getElementById('stat-packets').textContent = state.packetsReceived;
    
    // Latencia promedio
    if (state.latencies.length > 0) {
        const avgLatency = state.latencies.reduce((a, b) => a + b, 0) / state.latencies.length;
        document.getElementById('stat-latency').textContent = `${avgLatency.toFixed(1)} ms`;
    }
    
    // Indicador de calidad
    const qualityDiv = document.getElementById('quality-indicator');
    const icon = qualityDiv.querySelector('.quality-icon');
    const text = qualityDiv.querySelector('.quality-text');
    
    if (lossRate < 1.0) {
        icon.textContent = '🟢';
        text.textContent = 'Excelente';
        text.style.color = '#27ae60';
    } else if (lossRate < 5.0) {
        icon.textContent = '🟡';
        text.textContent = 'Buena';
        text.style.color = '#f39c12';
    } else {
        icon.textContent = '🔴';
        text.textContent = 'Deficiente';
        text.style.color = '#e74c3c';
    }
}

// ============================================================================
// Utilidades
// ============================================================================

function showError(element, message) {
    element.textContent = message;
    element.style.display = 'block';
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}
