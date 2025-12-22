// URL pública del Google Sheet en formato CSV
const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSMUbPSH39x9bMdABa6O-S0up-GSRvZ7XmOJaxKhFgDhTYoLY-W4MIGuZyqWbLPQbZ7m6vB8VoHNLxq/pub?gid=0&single=true&output=csv';

let sheetData = [];
let isScanning = false;
let lastScannedCode = '';
let scanHistory = [];
let isShowingResult = false;
let html5QrCode = null;

// Sistema de validación - códigos de 10 dígitos se aceptan con menos lecturas
let codeBuffer = [];
const REQUIRED_READS_10_DIGITS = 2; // Solo 2 lecturas para códigos de 10 dígitos
const REQUIRED_READS_OTHER = 3; // 3 lecturas para otros códigos
const CODE_BUFFER_TIMEOUT = 2000;
let bufferResetTimer = null;

// Cargar datos del Google Sheets al iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadSheetData();
});

async function loadSheetData() {
    const statusEl = document.getElementById('status');
    statusEl.textContent = '⏳ Cargando datos de Google Sheets...';
    statusEl.className = 'status loading';

    try {
        const response = await fetch(SHEET_CSV_URL);
        if (!response.ok) {
            throw new Error('Error al cargar el CSV');
        }
        const csvText = await response.text();
        
        // Debug: mostrar las primeras líneas del CSV
        console.log('=== CSV RAW (primeras 500 chars) ===');
        console.log(csvText.substring(0, 500));
        
        sheetData = parseCSV(csvText);
        
        statusEl.textContent = `✅ Datos cargados: ${sheetData.length} filas`;
        statusEl.className = 'status success';
        
        document.getElementById('lastUpdate').textContent = 
            `Última actualización: ${new Date().toLocaleString('es-ES')}`;
        
        console.log('=== DATOS PARSEADOS ===');
        console.log('Total filas:', sheetData.length);
        console.log('Primeras 5 filas:', sheetData.slice(0, 5));
        
        // Mostrar todos los valores únicos de la primera columna (para debug)
        const col1Values = sheetData.map(row => row[0]).filter(v => v);
        console.log('Valores columna 1:', col1Values.slice(0, 20));
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        statusEl.textContent = '❌ Error al cargar datos. Intenta recargar.';
        statusEl.className = 'status error';
    }
}

function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const data = [];
    
    for (let i = 0; i < lines.length; i++) {
        const row = parseCSVLine(lines[i]);
        if (row.length > 0) {
            data.push(row);
        }
    }
    
    return data;
}

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current.trim());
    
    return result;
}

function searchInSheet(barcode) {
    const scannedCodeEl = document.getElementById('scannedCode');
    const rowNumEl = document.getElementById('rowNum');
    const colNumEl = document.getElementById('colNum');
    const cellContentEl = document.getElementById('cellContent');
    const statusEl = document.getElementById('status');
    
    scannedCodeEl.textContent = barcode;
    scannedCodeEl.className = 'value searching';
    
    // Normalizar el código de barras (quitar espacios, convertir a string)
    const normalizedBarcode = barcode.toString().trim().toLowerCase();
    
    // Debug: mostrar qué estamos buscando
    console.log('Buscando código:', barcode);
    console.log('Código normalizado:', normalizedBarcode);
    console.log('Total filas en datos:', sheetData.length);
    
    // Columnas de códigos de barras: J=9, L=11, N=13 (índices 0-based)
    const columnasCodigos = [9, 11, 13]; // J, L, N
    // Columnas de direcciones: I=8, K=10, M=12
    const columnasDirecciones = {
        9: 8,   // J (códigos Indust) -> I (direcciones Indust)
        11: 10, // L (códigos Centre) -> K (direcciones Centre)
        13: 12  // N (códigos Altres) -> M (direcciones Altres)
    };
    const coloresColumnas = {
        9: '#6366f1',   // J = Índigo (Indust)
        11: '#f59e0b',  // L = Ámbar (Centre)
        13: '#10b981'   // N = Verde (Altres)
    };
    const nombresZonas = {
        9: 'Indust',
        11: 'Centre',
        13: 'Altres'
    };
    
    // Buscar solo en las columnas de códigos de barras (J, L, N)
    for (let rowIndex = 0; rowIndex < sheetData.length; rowIndex++) {
        const row = sheetData[rowIndex];
        
        for (const colIndex of columnasCodigos) {
            if (colIndex >= row.length) continue;
            
            const cellValue = row[colIndex].toString().trim();
            if (!cellValue) continue;
            
            const normalizedCell = cellValue.toLowerCase();
            
            // Múltiples estrategias de búsqueda (el código puede estar separado por comas)
            const codigos = normalizedCell.split(',').map(c => c.trim());
            const encontrado = codigos.some(codigo => {
                const exactMatch = codigo === normalizedBarcode;
                const codigoContainsBarcode = codigo.includes(normalizedBarcode);
                const barcodeContainsCodigo = normalizedBarcode.includes(codigo) && codigo.length > 3;
                const numericMatch = parseInt(normalizedBarcode) === parseInt(codigo) && !isNaN(parseInt(normalizedBarcode));
                return exactMatch || codigoContainsBarcode || barcodeContainsCodigo || numericMatch;
            });
            
            if (encontrado) {
                // ¡Encontrado! - Mostrar número de fila -1 (porque la fila 1 es cabecera)
                const displayRow = rowIndex; // rowIndex ya es 0-based, la fila 2 del sheet es rowIndex 1
                const displayCol = getColumnLetter(colIndex + 1);
                const color = coloresColumnas[colIndex];
                const zona = nombresZonas[colIndex];
                
                // Obtener la dirección de la columna correspondiente
                const colDireccion = columnasDirecciones[colIndex];
                const direccion = row[colDireccion] ? row[colDireccion].toString().trim() : 'Dirección no disponible';
                
                // Mostrar el número de fila con el color correspondiente
                rowNumEl.textContent = displayRow;
                rowNumEl.style.color = color;
                colNumEl.textContent = zona;
                colNumEl.style.color = color;
                scannedCodeEl.className = 'value found';
                scannedCodeEl.style.color = color;
                
                cellContentEl.innerHTML = `✅ <strong>${zona}</strong> - Posición ${displayRow}<div class="address-info">📍 ${direccion}</div>`;
                cellContentEl.style.display = 'block';
                cellContentEl.style.color = color;
                
                statusEl.textContent = `✅ ${zona} - Posición ${displayRow}`;
                statusEl.className = 'status success';
                statusEl.style.color = color;
                
                // Añadir al historial con la dirección
                addToHistory(barcode, displayRow, zona, color, direccion);
                
                // Vibrar para feedback (patrón de éxito)
                if (navigator.vibrate) {
                    navigator.vibrate([100, 50, 100, 50, 200]);
                }
                
                // Bloquear nuevos escaneos por 3 segundos para que se vea el resultado
                isShowingResult = true;
                setTimeout(() => {
                    isShowingResult = false;
                    statusEl.textContent = '🔍 Escaneando... Apunta al código de barras';
                    statusEl.className = 'status success';
                    statusEl.style.color = '';
                }, 3000);
                
                console.log('¡Encontrado en fila', displayRow, 'zona', zona);
                return true;
            }
        }
    }
    
    // No encontrado - Mostrar debug info
    console.log('No encontrado. Mostrando primeras 5 filas de datos:');
    sheetData.slice(0, 5).forEach((row, i) => {
        console.log(`Fila ${i + 1}:`, row);
    });
    
    rowNumEl.textContent = '-';
    rowNumEl.style.color = '';
    colNumEl.textContent = '-';
    colNumEl.style.color = '';
    scannedCodeEl.className = 'value not-found';
    scannedCodeEl.style.color = '';
    cellContentEl.innerHTML = `❌ Código "${barcode}" no encontrado<br><small>Datos cargados: ${sheetData.length} filas</small>`;
    cellContentEl.style.display = 'block';
    cellContentEl.style.color = '';
    
    statusEl.textContent = `❌ Código no encontrado`;
    statusEl.className = 'status error';
    statusEl.style.color = '';
    
    // NO agregar al historial cuando no se encuentra
    
    // Vibrar para feedback (patrón de error)
    if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200]);
    }
    
    // Bloquear nuevos escaneos por 3 segundos
    isShowingResult = true;
    setTimeout(() => {
        isShowingResult = false;
        statusEl.textContent = '🔍 Escaneando... Apunta al código de barras';
        statusEl.className = 'status success';
    }, 3000);
    
    return false;
}

function getColumnLetter(colNum) {
    let letter = '';
    while (colNum > 0) {
        const remainder = (colNum - 1) % 26;
        letter = String.fromCharCode(65 + remainder) + letter;
        colNum = Math.floor((colNum - 1) / 26);
    }
    return letter;
}

function addToHistory(code, row, zona, color = '#00ff88', direccion = '') {
    const historyList = document.getElementById('historyList');
    
    // Limpiar mensaje inicial si es el primer escaneo
    if (scanHistory.length === 0) {
        historyList.innerHTML = '';
    }
    
    scanHistory.unshift({ code, row, zona, color, direccion, time: new Date() });
    
    // Mantener solo los últimos 10
    if (scanHistory.length > 10) {
        scanHistory.pop();
    }
    
    // Renderizar historial - solo mostrar encontrados
    historyList.innerHTML = scanHistory.map(item => `
        <div class="history-item">
            <div>
                <div class="code" style="font-weight: 600; margin-bottom: 4px;">${item.code}</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">${item.direccion}</div>
            </div>
            <span class="pos" style="color: ${item.color}; font-weight: 600;">${item.zona} - ${item.row}</span>
        </div>
    `).join('');
}

function startScanner() {
    if (isScanning) return;
    
    const statusEl = document.getElementById('status');
    statusEl.textContent = '📷 Iniciando cámara...';
    statusEl.className = 'status loading';

    // Crear instancia de html5-qrcode
    html5QrCode = new Html5Qrcode("interactive");
    
    const config = {
        fps: 20,
        // Sin qrbox - escanea toda la imagen para mayor flexibilidad
        aspectRatio: 1.777778,
        formatsToSupport: [
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.ITF,
            Html5QrcodeSupportedFormats.CODABAR,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E
        ],
        experimentalFeatures: {
            useBarCodeDetectorIfSupported: true
        },
        rememberLastUsedCamera: true,
        disableFlip: false
    };

    html5QrCode.start(
        { facingMode: "environment" },
        config,
        onScanSuccess,
        onScanFailure
    ).then(() => {
        isScanning = true;
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('scanLine').style.display = 'block';
        statusEl.textContent = '🔍 Escaneando... Apunta al código de barras';
        statusEl.className = 'status success';
        
        // Inicializar el track de video para la linterna después de un breve delay
        setTimeout(() => {
            initTorchSupport();
        }, 500);
    }).catch((err) => {
        console.error('Error iniciando cámara:', err);
        statusEl.textContent = '❌ Error al acceder a la cámara. Permite el acceso.';
        statusEl.className = 'status error';
    });
}

// Inicializar soporte de linterna
function initTorchSupport() {
    try {
        const videoElement = document.querySelector('#interactive video');
        if (videoElement && videoElement.srcObject) {
            videoTrack = videoElement.srcObject.getVideoTracks()[0];
            
            if (videoTrack) {
                const capabilities = videoTrack.getCapabilities ? videoTrack.getCapabilities() : {};
                console.log('Track de video obtenido:', videoTrack.label);
                console.log('Capacidades:', JSON.stringify(capabilities));
                
                // Habilitar botón de linterna
                document.getElementById('torchBtn').disabled = false;
                
                if (capabilities.torch) {
                    console.log('✅ Linterna soportada');
                } else {
                    console.log('⚠️ Torch no reportado en capacidades');
                }
            }
        } else {
            console.log('Video element no encontrado, reintentando...');
            setTimeout(initTorchSupport, 300);
        }
    } catch (err) {
        console.error('Error inicializando linterna:', err);
    }
}

function onScanSuccess(decodedText, decodedResult) {
    // Evitar escaneos mientras se muestra el resultado
    if (isShowingResult) return;
    
    // Limpiar código
    const cleanCode = decodedText.replace(/[^0-9A-Za-z]/g, '');
    
    // SIEMPRE aceptar códigos de exactamente 10 dígitos numéricos
    const is10Digits = /^\d{10}$/.test(cleanCode);
    
    console.log(`Detectado: ${cleanCode} (${cleanCode.length} chars, 10 dígitos: ${is10Digits})`);
    
    // Para códigos de 10 dígitos, procesarlos directamente con menos validación
    if (is10Digits) {
        addToCodeBuffer(cleanCode, true);
    } else if (cleanCode.length >= 6 && cleanCode.length <= 15) {
        addToCodeBuffer(cleanCode, false);
    }
}

function onScanFailure(error) {
    // Ignorar errores de escaneo silenciosamente (ocurren constantemente mientras busca)
}

// Sistema de validación con múltiples lecturas
function addToCodeBuffer(code, is10Digits) {
    if (bufferResetTimer) {
        clearTimeout(bufferResetTimer);
    }
    
    codeBuffer.push(code);
    
    // Límite del buffer
    if (codeBuffer.length > 10) {
        codeBuffer = codeBuffer.slice(-10);
    }
    
    // Contar ocurrencias
    const counts = {};
    codeBuffer.forEach(c => {
        counts[c] = (counts[c] || 0) + 1;
    });
    
    // Determinar cuántas lecturas se requieren
    const requiredReads = is10Digits ? REQUIRED_READS_10_DIGITS : REQUIRED_READS_OTHER;
    
    // Buscar código validado
    for (const [detectedCode, count] of Object.entries(counts)) {
        const isThisCode10Digits = /^\d{10}$/.test(detectedCode);
        const threshold = isThisCode10Digits ? REQUIRED_READS_10_DIGITS : REQUIRED_READS_OTHER;
        
        if (count >= threshold && detectedCode !== lastScannedCode) {
            console.log(`✅ Código validado: ${detectedCode} (${count}/${threshold} lecturas)`);
            
            lastScannedCode = detectedCode;
            codeBuffer = [];
            
            searchInSheet(detectedCode);
            
            setTimeout(() => {
                lastScannedCode = '';
            }, 3000);
            return;
        }
    }
    
    // Mostrar progreso
    const maxCount = Math.max(...Object.values(counts));
    const maxCode = Object.keys(counts).find(k => counts[k] === maxCount);
    const isMax10 = /^\d{10}$/.test(maxCode);
    const threshold = isMax10 ? REQUIRED_READS_10_DIGITS : REQUIRED_READS_OTHER;
    
    if (maxCount >= 1) {
        const statusEl = document.getElementById('status');
        const progress = Math.round((maxCount / threshold) * 100);
        statusEl.textContent = `🔍 Detectando: ${maxCode} (${Math.min(progress, 99)}%)`;
    }
    
    bufferResetTimer = setTimeout(() => {
        if (codeBuffer.length > 0) {
            console.log('Buffer reseteado');
            codeBuffer = [];
            const statusEl = document.getElementById('status');
            if (!isShowingResult) {
                statusEl.textContent = '🔍 Escaneando... Apunta al código de barras';
            }
        }
    }, CODE_BUFFER_TIMEOUT);
}

function stopScanner() {
    if (!isScanning || !html5QrCode) return;
    
    // Apagar linterna si está encendida
    if (isTorchOn) {
        isTorchOn = false;
        document.getElementById('torchBtn').classList.remove('torch-on');
    }
    videoTrack = null;
    
    html5QrCode.stop().then(() => {
        isScanning = false;
        html5QrCode = null;
        
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('torchBtn').disabled = true;
        document.getElementById('torchBtn').classList.remove('torch-on');
        document.getElementById('scanLine').style.display = 'none';
        
        const statusEl = document.getElementById('status');
        statusEl.textContent = 'Cámara detenida. Presiona "Iniciar Cámara" para continuar.';
        statusEl.className = 'status';
    }).catch(err => {
        console.error('Error deteniendo cámara:', err);
    });
}

// Función para activar/desactivar la linterna
let isTorchOn = false;
let videoTrack = null;

async function toggleTorch() {
    if (!isScanning) {
        console.log('Cámara no activa');
        return;
    }
    
    const torchBtn = document.getElementById('torchBtn');
    
    // Si no tenemos el track, intentar obtenerlo
    if (!videoTrack) {
        const videoElement = document.querySelector('#interactive video');
        if (videoElement && videoElement.srcObject) {
            videoTrack = videoElement.srcObject.getVideoTracks()[0];
        }
    }
    
    if (!videoTrack) {
        console.error('No se pudo obtener el track de video');
        return;
    }
    
    try {
        // Toggle el estado
        const newTorchState = !isTorchOn;
        
        console.log('Intentando poner linterna:', newTorchState);
        
        // Aplicar el constraint
        await videoTrack.applyConstraints({
            advanced: [{ torch: newTorchState }]
        });
        
        isTorchOn = newTorchState;
        torchBtn.classList.toggle('torch-on', isTorchOn);
        console.log('✅ Linterna:', isTorchOn ? 'ENCENDIDA' : 'APAGADA');
        
    } catch (err) {
        console.error('Error controlando linterna:', err.name, err.message);
        
        // Verificar capacidades
        if (videoTrack.getCapabilities) {
            const caps = videoTrack.getCapabilities();
            console.log('Capacidades torch:', caps.torch);
        }
    }
}

// Limpiar al cerrar
window.addEventListener('beforeunload', () => {
    if (isScanning && html5QrCode) {
        html5QrCode.stop();
    }
});

// ========== ENTRADA MANUAL DE CÓDIGO DE BARRAS ==========

function openManualInput() {
    const modal = document.getElementById('manualModal');
    const input = document.getElementById('manualCodeInput');
    modal.style.display = 'flex';
    input.value = '';
    input.focus();
}

function closeManualInput() {
    const modal = document.getElementById('manualModal');
    modal.style.display = 'none';
}

function submitManualCode() {
    const input = document.getElementById('manualCodeInput');
    const code = input.value.trim();
    
    if (code.length === 0) {
        input.style.borderColor = '#ef4444';
        input.placeholder = 'Introduce un código válido';
        setTimeout(() => {
            input.style.borderColor = '';
            input.placeholder = 'Ej: 1234567890';
        }, 2000);
        return;
    }
    
    // Cerrar modal
    closeManualInput();
    
    // Buscar el código
    console.log('Búsqueda manual:', code);
    searchInSheet(code);
}

// Cerrar modal con Escape o clic fuera
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeManualInput();
    }
    if (e.key === 'Enter' && document.getElementById('manualModal').style.display === 'flex') {
        submitManualCode();
    }
});

document.addEventListener('click', (e) => {
    const modal = document.getElementById('manualModal');
    if (e.target === modal) {
        closeManualInput();
    }
});
