# Guía de Instalación Rápida - BikeLogic

## 🚀 Instalación en 3 Pasos

### Paso 1: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Verificar instalación

```bash
python test_system.py
```

Deberías ver algo como:
```
✓ PASÓ - Importaciones
✓ PASÓ - Configuración
✓ PASÓ - Limpieza de direcciones
✓ PASÓ - Detección de zonas
✓ PASÓ - Distancia a línea
✓ PASÓ - Estructura de archivos

Total: 6/6 tests pasados
🎉 ¡Todos los tests pasaron! El sistema está listo para usar.
```

### Paso 3: Ejecutar el programa

```bash
python main.py
```

## 📋 Requisitos Previos

- Python 3.8 o superior
- Archivo `key1.json` con credenciales de Google Sheets API
- API Key de Google Maps configurada en `config.py`

## 🔧 Solución de Problemas

### Error: "No module named 'X'"
Instala las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "FileNotFoundError: key1.json"
Asegúrate de que el archivo de credenciales esté en la carpeta del proyecto.

### Error en geocodificación
Verifica tu API Key de Google Maps en `config.py`:
```python
GOOGLE_MAPS_API_KEY = 'tu_api_key_aqui'
```

## 📚 Estructura del Proyecto

```
PythonBike/
├── config.py                    # Configuración (EDITA AQUÍ las líneas de ruta)
├── address_cleaner.py           # Limpieza de direcciones
├── geocoding.py                 # Geocodificación
├── zone_manager.py              # Gestión de zonas
├── tsp_solver.py                # Algoritmo TSP
├── line_distance_solver.py      # Algoritmo de línea
├── sheets_manager.py            # Google Sheets
├── main.py                      # Script principal ← EJECUTA ESTO
├── test_system.py               # Tests de validación
├── ejemplos.py                  # Ejemplos de uso
├── requirements.txt             # Dependencias
├── README.md                    # Documentación completa
├── INSTALL.md                   # Esta guía
├── key1.json                    # Credenciales (no incluir en git)
└── bike.py                      # Script original (respaldo)
```

## 🎯 Uso Básico

1. Ejecuta `python main.py`
2. Elige el método (1: TSP, 2: Línea)
3. Confirma con 's'
4. Espera a que termine el proceso
5. Revisa los resultados en Google Sheets

## 📝 Personalización

### Ajustar líneas de ruta (método línea)

Edita `config.py` en la sección `ZONE_ROUTE_LINES`:

```python
ZONE_ROUTE_LINES = {
    'Indust': [
        (41.47855, 2.07228),  # Inicio (tu depósito)
        (41.48500, 2.08000),  # Punto intermedio 1
        (41.48800, 2.08500),  # Punto intermedio 2
        (41.47682, 2.10226)   # Final de la ruta
    ],
    # ... otras zonas
}
```

**Tips para definir líneas:**
- Usa 3-5 puntos por zona
- Sigue el orden real de tu ruta
- Más puntos = mayor precisión
- Menos puntos = más rápido

### Cambiar columnas de salida

Edita en `sheets_manager.py` la función `escribir_resultados_por_zona`:

```python
columnas_destino = {
    'Indust': 'i2',     # ← Cambia estas columnas
    'Centre': 'j2',
    'MiraEst': 'k2',
    'Mira': 'l2',
    'sin_zona': 'm2'
}
```

## 🆘 Soporte

Si tienes problemas:

1. Ejecuta `python test_system.py` para diagnosticar
2. Revisa `README.md` para documentación completa
3. Consulta `ejemplos.py` para ver cómo usar cada módulo

## ⚡ Quick Start (Instalación Express)

```bash
# 1. Instalar todo
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests geopy shapely ortools numpy scipy

# 2. Verificar
python test_system.py

# 3. Ejecutar
python main.py
```

¡Listo! 🎉
