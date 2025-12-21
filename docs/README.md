# BikeLogic - Sistema de Optimización de Rutas

Sistema modular para optimización de rutas de entrega en bicicleta, con dos métodos de ordenación disponibles.

## 📁 Estructura del Proyecto

```
PythonBike/
├── config.py                    # Configuración y constantes
├── address_cleaner.py           # Limpieza y normalización de direcciones
├── geocoding.py                 # Geocodificación con Google Maps API
├── zone_manager.py              # Gestión de zonas geográficas
├── tsp_solver.py                # Algoritmo del Viajante de Comercio
├── line_distance_solver.py      # Algoritmo de distancia a línea
├── sheets_manager.py            # Gestión de Google Sheets
├── main.py                      # Script principal
├── bike.py                      # [Script original - mantener como respaldo]
├── key1.json                    # Credenciales Google Sheets API
└── README.md                    # Este archivo
```

## 🚀 Métodos de Optimización

### 1. TSP (Traveling Salesman Problem)
Calcula la ruta más corta que visita todas las direcciones usando el algoritmo del viajante de comercio.

**Ventajas:**
- Minimiza la distancia total recorrida
- Ruta óptima matemáticamente

**Cuándo usar:**
- Cuando la prioridad es minimizar kilómetros
- Áreas sin orden específico de entrega

### 2. Distancia a Línea de Ruta
Ordena los paquetes según su proximidad a una línea predefinida que representa la ruta deseada.

**Ventajas:**
- Sigue un camino lógico y predecible
- Respeta el flujo natural de las calles
- Fácil de seguir para el repartidor

**Cuándo usar:**
- Cuando hay una ruta preferida o conocida
- Para mantener un orden específico de zonas
- Cuando se desea seguir calles principales

## ⚙️ Configuración

### 1. Google Maps API
Edita `config.py` y actualiza tu API key:
```python
GOOGLE_MAPS_API_KEY = 'tu_api_key_aqui'
```

### 2. Google Sheets API
Asegúrate de tener el archivo `key1.json` con las credenciales de servicio.

### 3. Geocodificación Rápida (NUEVO) ⚡

El sistema ahora incluye **geocodificación optimizada** con:

- **Caché persistente**: Las direcciones ya geocodificadas se guardan en `geocoding_cache.json`
- **Procesamiento paralelo**: Múltiples direcciones se geocodifican simultáneamente
- **Velocidad 5-10x más rápida**: Especialmente en ejecuciones subsiguientes

**Primera ejecución:**
- 100 direcciones: ~30-45 segundos (con paralelo)
- 200 direcciones: ~60-90 segundos

**Ejecuciones posteriores (con caché):**
- 100 direcciones: ~5-10 segundos (si ya están en caché)
- 200 direcciones: ~10-20 segundos

**Gestión del caché:**
```bash
# Ver estadísticas y gestionar caché
python cache_manager.py
```

### 4. Líneas de Ruta (solo para método de línea)
En `config.py`, ajusta las líneas de ruta para cada zona:
```python
ZONE_ROUTE_LINES = {
    'Indust': [
        (41.47855, 2.07228),  # Inicio
        (41.48500, 2.08000),  # Punto intermedio
        (41.47682, 2.10226)   # Final
    ],
    # ... más zonas
}
```

**Cómo definir líneas de ruta:**
1. Identifica los puntos clave de tu ruta ideal
2. Obtén las coordenadas (lat, lon) de estos puntos
3. Ordénalos desde el inicio hasta el final de la ruta
4. Puedes usar 2 o más puntos por zona

## 📦 Instalación

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install requests geopy shapely ortools numpy scipy
```

## 🎯 Uso

### Ejecutar el programa
```bash
python main.py
```

### Menú interactivo
1. Selecciona el método (TSP o Línea)
2. Confirma la ejecución
3. El programa procesará automáticamente:
   - Lectura de Google Sheets
   - Limpieza de direcciones
   - Geocodificación
   - Separación por zonas
   - Optimización de rutas
   - Escritura de resultados

### Resultados
Los resultados se escriben en el Google Spreadsheet en las columnas:
- **Columna I:** Zona Indust
- **Columna J:** Zona Centre
- **Columna K:** Zona MiraEst
- **Columna L:** Zona Mira
- **Columna M:** Sin zona
- **Columna N:** Direcciones no encontradas

## 🔧 Módulos

### config.py
Contiene todas las constantes, API keys y configuraciones del proyecto.

### address_cleaner.py
Funciones para limpiar y normalizar direcciones antes de geocodificar.

### geocoding.py
Geocodificación usando Google Maps API con manejo de duplicados y errores.

**NUEVO - Optimizaciones de rendimiento:**
- ⚡ **Caché persistente**: Guarda geocodificaciones en archivo JSON
- 🚀 **Procesamiento paralelo**: Hasta 10 peticiones simultáneas
- 📊 **Estadísticas**: Función para ver hits/misses del caché
- 🔧 **Gestión**: Herramientas para limpiar caché si es necesario

```python
# Uso rápido (recomendado)
from geocoding import geocode_and_store_fast
geocoded, not_found = geocode_and_store_fast(direcciones, max_workers=10)

# Uso tradicional (compatible)
from geocoding import geocode_and_store
geocoded, not_found = geocode_and_store(direcciones, use_cache=True, use_parallel=True)
```

### zone_manager.py
Separación de direcciones en zonas geográficas usando polígonos de Shapely.

### tsp_solver.py
Implementación del problema del viajante de comercio usando Google OR-Tools.

### line_distance_solver.py
Algoritmo personalizado que ordena paquetes según su distancia a una línea de ruta.

**Funcionamiento:**
1. Define una línea con múltiples puntos (inicio → fin)
2. Para cada paquete, calcula:
   - Su distancia perpendicular a la línea
   - Su posición a lo largo de la línea (0 = inicio, 1 = fin)
3. Ordena por posición a lo largo de la línea

### sheets_manager.py
Clase para gestionar todas las operaciones con Google Sheets (lectura/escritura).

### main.py
Script principal con menú interactivo para elegir el método de optimización.

### cache_manager.py (NUEVO) 🆕
Utilidad para gestionar el caché de geocodificación:
- Ver estadísticas del caché
- Listar direcciones guardadas
- Limpiar caché si es necesario

## 📊 Comparación de Métodos

| Característica | TSP | Línea de Ruta |
|----------------|-----|---------------|
| Distancia total | ⭐⭐⭐ Óptima | ⭐⭐ Buena |
| Predictibilidad | ⭐⭐ Variable | ⭐⭐⭐ Alta |
| Facilidad seguimiento | ⭐⭐ Media | ⭐⭐⭐ Fácil |
| Configuración | ⭐⭐⭐ Simple | ⭐⭐ Requiere líneas |
| Velocidad cálculo | ⭐⭐ Más lento | ⭐⭐⭐ Rápido |

## 🛠️ Personalización

### Optimizar velocidad de geocodificación

```python
# En main.py o tu script, ajusta max_workers
from geocoding import geocode_and_store_fast

# Más rápido (más peticiones paralelas)
geocoded, not_found = geocode_and_store_fast(direcciones, max_workers=15)

# Más conservador (menos carga en API)
geocoded, not_found = geocode_and_store_fast(direcciones, max_workers=5)
```

**Nota**: Google Maps tiene límites de peticiones por segundo. Si recibes errores 429 (too many requests), reduce `max_workers`.

### Agregar nuevas zonas
1. Define el polígono en `config.py` → `ZONE_POLYGONS`
2. Define la línea de ruta en `ZONE_ROUTE_LINES`
3. Actualiza las columnas destino en `sheets_manager.py`

### Ajustar el algoritmo de línea
Modifica las funciones en `line_distance_solver.py`:
- `distancia_punto_a_linea()` - Cálculo de distancia
- `posicion_en_linea()` - Cálculo de posición
- `calcular_posicion_en_ruta_multi_segmento()` - Lógica para múltiples segmentos

## 📝 Notas Importantes

1. **API Limits:** Google Maps tiene límites de uso. El script usa procesamiento paralelo optimizado.
2. **Caché**: Primera ejecución es más lenta, siguientes son mucho más rápidas gracias al caché.
3. **Líneas de Ruta:** Deben definirse con cuidado para que representen el camino real.
4. **Respaldo:** El archivo original `bike.py` se mantiene como respaldo.
5. **Archivo de caché**: `geocoding_cache.json` se crea automáticamente. Puedes eliminarlo si quieres refrescar geocodificaciones.

## 🐛 Solución de Problemas

**Error de geocodificación:**
- Verifica tu API key de Google Maps
- Revisa los límites de uso de la API
- Si recibes error 429, reduce `max_workers` en la configuración

**Geocodificaciones incorrectas:**
- Elimina el caché: `python cache_manager.py` → opción 4
- O manualmente elimina el archivo `geocoding_cache.json`

**Proceso muy lento en primera ejecución:**
- Normal: la geocodificación toma tiempo
- Siguientes ejecuciones serán mucho más rápidas con el caché
- Considera usar `max_workers` más alto (10-15) si tu API lo permite

**Direcciones mal ordenadas (método línea):**
- Ajusta las líneas de ruta en `config.py`
- Agrega más puntos intermedios para mayor precisión

**Error de conexión a Sheets:**
- Verifica el archivo `key1.json`
- Confirma los permisos de la cuenta de servicio

## 📄 Licencia

Proyecto interno de BikeLogic para optimización de rutas de entrega.
