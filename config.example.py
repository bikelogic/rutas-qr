"""
Archivo de ejemplo de configuración.
Copia este archivo como 'config.py' y rellena con tus datos.
"""

# Configuración de Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY_FILE = 'key1.json'  # Ruta a tu archivo de credenciales de Google
SPREADSHEET_ID = 'TU_SPREADSHEET_ID_AQUI'  # ID de tu Google Sheets

# Configuración de Google Maps API
GOOGLE_MAPS_API_KEY = 'TU_API_KEY_DE_GOOGLE_MAPS_AQUI'

# Configuración de ciudad por defecto
DEFAULT_CITY = "SANT CUGAT DEL VALLES"

# Punto de inicio/depósito
DEPOT_COORDS = (41.47855, 2.07228)  # (latitud, longitud)
DEPOT_ADDRESS = "CARRER DE SOLSONA 22, SANT CUGAT DEL VALLES 08173"

# Definición de polígonos para las zonas (lista de coordenadas)
ZONE_POLYGONS = {
    'Indust': [
        (41.47965, 2.07387), (41.49077, 2.07591), (41.49193, 2.08694), 
        (41.47682, 2.10226), (41.47181, 2.09789), (41.47386, 2.09179), 
        (41.47603, 2.0909), (41.47589, 2.08279)
    ],
    
    'Centre': [
        (41.47965, 2.07387), (41.47589, 2.08279), (41.47603, 2.0909), 
        (41.47386, 2.09179), (41.47181, 2.09789), (41.45823, 2.08887), 
        (41.46548, 2.07734), (41.46705, 2.07794), (41.46837, 2.07834), 
        (41.47356, 2.07736)
    ],
    
    'MiraEst': [
        (41.47965, 2.07387), (41.47356, 2.07736), (41.46837, 2.07834), 
        (41.46705, 2.07794), (41.464, 2.07437), (41.45739, 2.08844), 
        (41.45, 2.08671), (41.45296, 2.06534), (41.45903, 2.0647), 
        (41.47744, 2.06418), (41.47699, 2.04356), (41.50087, 2.05476), 
        (41.50133, 2.07809), (41.49077, 2.07591)
    ],
    
    'Mira': [
        (41.47699, 2.04356), (41.47744, 2.06418), (41.45903, 2.0647), 
        (41.45296, 2.06534), (41.45264, 2.0254), (41.47495, 2.02771)
    ]
}

# Definición de líneas de ruta para cada zona
ZONE_ROUTE_LINES = {
    'Indust': [
        (41.47855, 2.07228),  # DEPOT
        (41.47984, 2.07411),
        (41.4769, 2.08276),
        (41.47755, 2.08434),
        (41.48003, 2.08117),
        (41.48145, 2.08552),
        (41.48341, 2.08415),
        (41.485, 2.08743),
        (41.48167, 2.09179),
        (41.47942, 2.09157),
        (41.47696, 2.09584),
        (41.47596, 2.09546),
        (41.47575, 2.09775),
        (41.4737, 2.09726),
        (41.47402, 2.09166),
        (41.47632, 2.09048),
        (41.47707, 2.08803)
    ],
    'Centre': [
        (41.47855, 2.07228),
        (41.47000, 2.08500),
        (41.46000, 2.08500)
    ],
    'MiraEst': [
        (41.47855, 2.07228),
        (41.47000, 2.06500),
        (41.45500, 2.07000)
    ],
    'Mira': [
        (41.47855, 2.07228),
        (41.46500, 2.05000),
        (41.45500, 2.03500)
    ]
}
