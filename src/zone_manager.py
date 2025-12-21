"""
Módulo para gestión de zonas geográficas mediante polígonos
"""
from shapely.geometry import Point, Polygon
from config import ZONE_POLYGONS, DEPOT_COORDS, DEPOT_ADDRESS


def determinar_zona(coord):
    """
    Determina a qué zona pertenece una coordenada.
    
    Args:
        coord (tuple): Tupla (latitud, longitud)
        
    Returns:
        str: Nombre de la zona o 'sin_zona' si no pertenece a ninguna
    """
    punto = Point(coord)
    
    for zone_name, zone_coords in ZONE_POLYGONS.items():
        poligono = Polygon(zone_coords)
        if poligono.contains(punto):
            return zone_name
    
    return 'sin_zona'


def separar_por_zonas(geocoded_addresses):
    """
    Separa las direcciones geocodificadas por zonas.
    
    Args:
        geocoded_addresses (list): Lista de tuplas [(coords, address), ...]
        
    Returns:
        dict: Diccionario con las direcciones separadas por zona
            {
                'Indust': [...],
                'Centre': [...],
                'MiraEst': [...],
                'Mira': [...],
                'sin_zona': [...]
            }
    """
    zonas = {
        'Indust': [],
        'Centre': [],
        'MiraEst': [],
        'Mira': [],
        'sin_zona': []
    }
    
    for item in geocoded_addresses:
        coords, address = item
        zona = determinar_zona(coords)
        zonas[zona].append(item)
    
    return zonas


def agregar_punto_inicio(zonas_dict, depot_coords=DEPOT_COORDS, depot_address=DEPOT_ADDRESS):
    """
    Agrega el punto de inicio (depósito) al principio de cada zona.
    
    Args:
        zonas_dict (dict): Diccionario de zonas con direcciones
        depot_coords (tuple): Coordenadas del depósito
        depot_address (str): Dirección del depósito
        
    Returns:
        dict: Diccionario con el punto de inicio agregado a cada zona
    """
    depot_item = (depot_coords, depot_address)
    
    for zona_name in zonas_dict:
        if zonas_dict[zona_name]:  # Solo si hay direcciones en la zona
            zonas_dict[zona_name].insert(0, depot_item)
    
    return zonas_dict


def obtener_estadisticas_zonas(zonas_dict):
    """
    Obtiene estadísticas sobre la distribución de direcciones por zona.
    
    Args:
        zonas_dict (dict): Diccionario de zonas con direcciones
        
    Returns:
        dict: Estadísticas por zona
    """
    stats = {}
    total = 0
    
    for zona_name, direcciones in zonas_dict.items():
        # Restar 1 si contiene el depósito
        count = len(direcciones)
        if count > 0 and direcciones[0][0] == DEPOT_COORDS:
            count -= 1
        
        stats[zona_name] = count
        total += count
    
    stats['total'] = total
    
    return stats
