// URL del CSV público de Google Sheets
// El formato correcto para obtener CSV es: /pub?gid=0&single=true&output=csv
const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSMUbPSH39x9bMdABa6O-S0up-GSRvZ7XmOJaxKhFgDhTYoLY-W4MIGuZyqWbLPQbZ7m6vB8VoHNLxq/pub?gid=0&single=true&output=csv';

let sheetData = [];
let isScanning = false;
let lastScannedCode = '';
let scanHistory = [];
let isShowingResult = false; // Para mantener el resultado visible 3 segundos

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
    
    // Buscar el código en todas las celdas
    for (let rowIndex = 0; rowIndex < sheetData.length; rowIndex++) {
        const row = sheetData[rowIndex];
        for (let colIndex = 0; colIndex < row.length; colIndex++) {
            const cellValue = row[colIndex].toString().trim();
            const normalizedCell = cellValue.toLowerCase();
            
            // Múltiples estrategias de búsqueda
            const exactMatch = normalizedCell === normalizedBarcode;
            const cellContainsBarcode = normalizedCell.includes(normalizedBarcode);
            const barcodeContainsCell = normalizedBarcode.includes(normalizedCell) && normalizedCell.length > 3;
            // También comparar sin ceros a la izquierda
            const numericMatch = parseInt(normalizedBarcode) === parseInt(normalizedCell) && !isNaN(parseInt(normalizedBarcode));
            
            if (exactMatch || cellContainsBarcode || barcodeContainsCell || numericMatch) {
                // ¡Encontrado!
                const displayRow = rowIndex + 1; // Las filas empiezan en 1
                const displayCol = getColumnLetter(colIndex + 1);
                
                rowNumEl.textContent = displayRow;
                colNumEl.textContent = displayCol;
                scannedCodeEl.className = 'value found';
                
                cellContentEl.innerHTML = `✅ <strong>Encontrado!</strong><br>Contenido celda: "${cellValue}"`;
                cellContentEl.style.display = 'block';
                
                statusEl.textContent = `✅ ¡ENCONTRADO! Fila ${displayRow}, Columna ${displayCol}`;
                statusEl.className = 'status success';
                
                // Añadir al historial
                addToHistory(barcode, displayRow, displayCol);
                
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
                }, 3000);
                
                console.log('¡Encontrado en fila', displayRow, 'columna', displayCol);
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
    colNumEl.textContent = '-';
    scannedCodeEl.className = 'value not-found';
    cellContentEl.innerHTML = `❌ Código "${barcode}" no encontrado en la hoja<br><small>Datos cargados: ${sheetData.length} filas</small>`;
    cellContentEl.style.display = 'block';
    
    statusEl.textContent = `❌ Código no encontrado`;
    statusEl.className = 'status error';
    
    addToHistory(barcode, 'N/A', 'N/A');
    
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

function addToHistory(code, row, col) {
    const historyList = document.getElementById('historyList');
    
    // Limpiar mensaje inicial si es el primer escaneo
    if (scanHistory.length === 0) {
        historyList.innerHTML = '';
    }
    
    scanHistory.unshift({ code, row, col, time: new Date() });
    
    // Mantener solo los últimos 10
    if (scanHistory.length > 10) {
        scanHistory.pop();
    }
    
    // Renderizar historial
    historyList.innerHTML = scanHistory.map(item => `
        <div class="history-item">
            <span class="code">${item.code}</span>
            <span class="pos">${item.row === 'N/A' ? '❌' : `Fila ${item.row}, Col ${item.col}`}</span>
        </div>
    `).join('');
}

function startScanner() {
    if (isScanning) return;
    
    const statusEl = document.getElementById('status');
    statusEl.textContent = '📷 Iniciando cámara...';
    statusEl.className = 'status loading';

    Quagga.init({
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: document.querySelector('#interactive'),
            constraints: {
                width: { min: 640 },
                height: { min: 480 },
                facingMode: "environment" // Cámara trasera
            },
        },
        locator: {
            patchSize: "medium",
            halfSample: true
        },
        numOfWorkers: navigator.hardwareConcurrency || 4,
        frequency: 10,
        decoder: {
            readers: [
                "code_128_reader",
                "ean_reader",
                "ean_8_reader",
                "code_39_reader",
                "code_39_vin_reader",
                "codabar_reader",
                "upc_reader",
                "upc_e_reader",
                "i2of5_reader"
            ]
        },
        locate: true
    }, function(err) {
        if (err) {
            console.error('Error iniciando QuaggaJS:', err);
            statusEl.textContent = '❌ Error al acceder a la cámara. Permite el acceso.';
            statusEl.className = 'status error';
            return;
        }
        
        Quagga.start();
        isScanning = true;
        
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('scanLine').style.display = 'block';
        
        statusEl.textContent = '🔍 Escaneando... Apunta al código de barras';
        statusEl.className = 'status success';
    });

    // Evento cuando detecta un código
    Quagga.onDetected(function(result) {
        const code = result.codeResult.code;
        
        // Evitar escaneos mientras se muestra el resultado (3 segundos)
        if (isShowingResult) return;
        
        // Evitar escaneos duplicados consecutivos
        if (code === lastScannedCode) return;
        lastScannedCode = code;
        
        console.log('Código detectado:', code);
        
        // Buscar en la hoja
        searchInSheet(code);
        
        // Reset después de 3 segundos para permitir nuevo escaneo del mismo código
        setTimeout(() => {
            lastScannedCode = '';
        }, 3000);
    });

    // Dibujar rectángulo de detección
    Quagga.onProcessed(function(result) {
        const drawingCtx = Quagga.canvas.ctx.overlay;
        const drawingCanvas = Quagga.canvas.dom.overlay;

        if (result) {
            if (result.boxes) {
                drawingCtx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);
                result.boxes.filter(box => box !== result.box).forEach(box => {
                    Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, { 
                        color: "rgba(0, 212, 255, 0.5)", 
                        lineWidth: 2 
                    });
                });
            }

            if (result.box) {
                Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, { 
                    color: "#00ff88", 
                    lineWidth: 3 
                });
            }

            if (result.codeResult && result.codeResult.code) {
                Quagga.ImageDebug.drawPath(result.line, { x: 'x', y: 'y' }, drawingCtx, { 
                    color: '#ff0000', 
                    lineWidth: 3 
                });
            }
        }
    });
}

function stopScanner() {
    if (!isScanning) return;
    
    Quagga.stop();
    isScanning = false;
    
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('scanLine').style.display = 'none';
    
    const statusEl = document.getElementById('status');
    statusEl.textContent = 'Cámara detenida. Presiona "Iniciar Cámara" para continuar.';
    statusEl.className = 'status';
}

// Limpiar al cerrar
window.addEventListener('beforeunload', () => {
    if (isScanning) {
        Quagga.stop();
    }
});
