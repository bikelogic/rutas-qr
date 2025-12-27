"""
Módulo para geocodificación de direcciones usando Google Maps API
con caché persistente y procesamiento paralelo
"""
import time
import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from config import GOOGLE_MAPS_API_KEY

# Archivo de caché
CACHE_FILE = 'geocoding_cache.json'
_cache_lock = Lock()


def load_cache():
    """
    Carga el caché de geocodificaciones desde archivo.
    
    Returns:
        dict: Diccionario con direcciones ya geocodificadas
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠️ Error cargando caché: {e}")
            return {}
    return {}


def save_cache(cache):
    """
    Guarda el caché de geocodificaciones en archivo.
    
    Args:
        cache (dict): Diccionario con direcciones geocodificadas
    """
    try:
        with _cache_lock:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠️ Error guardando caché: {e}")


def get_from_cache(address, cache):
    """
    Busca una dirección en el caché.
    
    Args:
        address (str): Dirección a buscar
        cache (dict): Caché de geocodificaciones
        
    Returns:
        tuple: (lat, lon) o None si no está en caché
    """
    if address in cache:
        coords = cache[address]
        if coords and isinstance(coords, list) and len(coords) == 2:
            return tuple(coords)
    return None


def add_to_cache(address, coords, cache):
    """
    Añade una geocodificación al caché.
    
    Args:
        address (str): Dirección
        coords (tuple): Coordenadas (lat, lon) o None
        cache (dict): Caché de geocodificaciones
    """
    with _cache_lock:
        if coords:
            cache[address] = list(coords)
        else:
            cache[address] = None


def geocode_with_google_maps(address, google_maps_api_key=GOOGLE_MAPS_API_KEY):
    """
    Geocodifica una dirección usando Google Maps Geocoding API.
    
    Args:
        address (str): Dirección a geocodificar
        google_maps_api_key (str): API key de Google Maps
        
    Returns:
        tuple: (latitud, longitud) o None si no se pudo geocodificar
    """
    print(f"  🌐 API Google Maps: Geocodificando '{address[:60]}...'")
    
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": google_maps_api_key}
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lon = data['results'][0]['geometry']['location']['lng']
            print(f"     ✓ Encontrado: ({lat}, {lon})")
            return (lat, lon)
        else:
            print(f"     ✗ No encontrado (status: {data['status']})")
    else:
        print(f"     ✗ Error HTTP {response.status_code}")
    
    return None


def geocode_and_store(addresses, google_maps_api_key=GOOGLE_MAPS_API_KEY, delay=0.3, use_cache=True, use_parallel=False, max_workers=5, codigos_barras=None):
    """
    Geocodifica una lista de direcciones eliminando duplicados (mismas coordenadas).
    Solo mantiene la primera dirección por cada coordenada única, pero agrupa todos los códigos de barras.
    
    Args:
        addresses (list): Lista de direcciones a geocodificar
        google_maps_api_key (str): API key de Google Maps
        delay (float): Tiempo de espera entre llamadas a la API (segundos)
        use_cache (bool): Si True, usa caché persistente
        use_parallel (bool): Si True, usa procesamiento paralelo
        max_workers (int): Número máximo de hilos paralelos
        codigos_barras (list): Lista de códigos de barras asociados a cada dirección
        
    Returns:
        tuple: (geocoded_addresses, not_found_addresses)
            - geocoded_addresses: Lista única por coordenada [(coords, address, codigos_barras), ...]
            - not_found_addresses: Lista de direcciones no encontradas
    """
    geocoded_addresses_dict = {}  # {coords: {'address': str, 'codigos': list}}
    not_found_addresses = []
    
    # Si no hay códigos de barras, crear lista vacía
    if codigos_barras is None:
        codigos_barras = [''] * len(addresses)
    
    # Asegurar que las listas tengan el mismo tamaño
    while len(codigos_barras) < len(addresses):
        codigos_barras.append('')
    
    # Crear mapeo dirección -> lista de códigos de barras (acumulando duplicados)
    address_to_codigos = {}
    for addr, cod in zip(addresses, codigos_barras):
        if addr not in address_to_codigos:
            address_to_codigos[addr] = []
        if cod:  # Solo agregar si el código no está vacío
            address_to_codigos[addr].append(cod)
    
    # Cargar caché si está habilitado
    cache = load_cache() if use_cache else {}
    cache_hits = 0
    cache_misses = 0
    
    # Separar direcciones en caché y no caché
    addresses_to_geocode = []
    addresses_already_queued = set()  # Para evitar geocodificar la misma dirección múltiples veces
    
    for address in addresses:
        cached_coords = get_from_cache(address, cache) if use_cache else None
        codigos_list = address_to_codigos.get(address, [])
        
        if cached_coords:
            # Usar coordenadas del caché
            cache_hits += 1
            if cached_coords not in geocoded_addresses_dict:
                geocoded_addresses_dict[cached_coords] = {'address': address, 'codigos': []}
            # Agregar todos los códigos de barras de esta dirección
            for codigo in codigos_list:
                if codigo and codigo not in geocoded_addresses_dict[cached_coords]['codigos']:
                    geocoded_addresses_dict[cached_coords]['codigos'].append(codigo)
        else:
            # Solo añadir si no se ha añadido ya a la cola de geocodificación
            if address not in addresses_already_queued:
                cache_misses += 1
                addresses_to_geocode.append(address)
                addresses_already_queued.add(address)
    
    if use_cache and cache_hits > 0:
        print(f"  ✓ Caché: {cache_hits} direcciones recuperadas, {cache_misses} nuevas a geocodificar")
    
    # Geocodificar direcciones no encontradas en caché
    if addresses_to_geocode:
        if use_parallel and len(addresses_to_geocode) > 10:
            # Geocodificación paralela
            _geocode_parallel(
                addresses_to_geocode, 
                geocoded_addresses_dict, 
                not_found_addresses,
                cache,
                google_maps_api_key,
                max_workers,
                delay,
                address_to_codigos
            )
        else:
            # Geocodificación secuencial
            _geocode_sequential(
                addresses_to_geocode,
                geocoded_addresses_dict,
                not_found_addresses,
                cache,
                google_maps_api_key,
                delay,
                address_to_codigos
            )
    
    # Guardar caché actualizado
    if use_cache and addresses_to_geocode:
        save_cache(cache)
    
    # Detectar y reportar duplicados
    total_codigos = sum(len(data['codigos']) for data in geocoded_addresses_dict.values())
    puntos_unicos = len(geocoded_addresses_dict)
    
    if total_codigos > puntos_unicos:
        print(f"  📍 {total_codigos - puntos_unicos} direcciones con coordenadas duplicadas (mismo punto de entrega)")
    
    # Convertir el diccionario a una lista de tuplas (coords, address, codigos_barras)
    geocoded_addresses = [
        (coords, data['address'], data['codigos']) 
        for coords, data in geocoded_addresses_dict.items()
    ]
    
    return geocoded_addresses, not_found_addresses


def _geocode_sequential(addresses, geocoded_dict, not_found_list, cache, api_key, delay, address_to_codigos=None):
    """
    Geocodificación secuencial (una por una).
    
    Args:
        addresses (list): Direcciones a geocodificar
        geocoded_dict (dict): Diccionario de resultados
        not_found_list (list): Lista de no encontradas
        cache (dict): Caché
        api_key (str): API key
        delay (float): Delay entre llamadas
        address_to_codigos (dict): Mapeo dirección -> lista de códigos de barras
    """
    if address_to_codigos is None:
        address_to_codigos = {}
    
    for address in addresses:
        coords = geocode_with_google_maps(address, api_key)
        codigos_list = address_to_codigos.get(address, [])
        
        if coords:
            # Agrupar direcciones con las mismas coordenadas
            if coords not in geocoded_dict:
                geocoded_dict[coords] = {'address': address, 'codigos': []}
            # Agregar todos los códigos de esta dirección
            for codigo in codigos_list:
                if codigo and codigo not in geocoded_dict[coords]['codigos']:
                    geocoded_dict[coords]['codigos'].append(codigo)
            add_to_cache(address, coords, cache)
        else:
            not_found_list.append([address])
            add_to_cache(address, None, cache)
        
        # Esperar para no sobrepasar límites de la API
        if delay > 0:
            time.sleep(delay)


def _geocode_parallel(addresses, geocoded_dict, not_found_list, cache, api_key, max_workers, delay, address_to_codigos=None):
    """
    Geocodificación paralela usando ThreadPoolExecutor.
    
    Args:
        addresses (list): Direcciones a geocodificar
        geocoded_dict (dict): Diccionario de resultados
        not_found_list (list): Lista de no encontradas
        cache (dict): Caché
        api_key (str): API key
        max_workers (int): Número de hilos
        delay (float): Delay entre lotes
        address_to_codigos (dict): Mapeo dirección -> lista de códigos de barras
    """
    if address_to_codigos is None:
        address_to_codigos = {}
    
    def geocode_single(address):
        """Geocodifica una dirección individual"""
        coords = geocode_with_google_maps(address, api_key)
        return address, coords
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        future_to_address = {
            executor.submit(geocode_single, addr): addr 
            for addr in addresses
        }
        
        # Procesar resultados a medida que se completan
        for i, future in enumerate(as_completed(future_to_address)):
            address, coords = future.result()
            codigos_list = address_to_codigos.get(address, [])
            
            if coords:
                with _cache_lock:
                    if coords not in geocoded_dict:
                        geocoded_dict[coords] = {'address': address, 'codigos': []}
                    # Agregar todos los códigos de esta dirección
                    for codigo in codigos_list:
                        if codigo and codigo not in geocoded_dict[coords]['codigos']:
                            geocoded_dict[coords]['codigos'].append(codigo)
                add_to_cache(address, coords, cache)
            else:
                with _cache_lock:
                    not_found_list.append([address])
                add_to_cache(address, None, cache)
            
            # Pequeño delay cada cierto número de peticiones
            if delay > 0 and (i + 1) % max_workers == 0:
                time.sleep(delay)


def geocode_and_store_fast(addresses, google_maps_api_key=GOOGLE_MAPS_API_KEY, max_workers=10, codigos_barras=None):
    """
    Versión rápida de geocodificación con caché y paralelización habilitados.
    Recomendado para grandes volúmenes de direcciones.
    
    Args:
        addresses (list): Lista de direcciones
        google_maps_api_key (str): API key de Google Maps
        max_workers (int): Número de hilos paralelos (default: 10)
        codigos_barras (list): Lista de códigos de barras asociados a cada dirección
        
    Returns:
        tuple: (geocoded_addresses, not_found_addresses)
            - geocoded_addresses: Lista única por coordenada [(coords, address, codigos_barras), ...]
            - not_found_addresses: Lista de direcciones no encontradas
    """
    return geocode_and_store(
        addresses,
        google_maps_api_key=google_maps_api_key,
        delay=0.1,  # Delay reducido con paralelo
        use_cache=True,
        use_parallel=True,
        max_workers=max_workers,
        codigos_barras=codigos_barras
    )


def clear_cache():
    """
    Elimina el archivo de caché de geocodificaciones.
    Útil si las geocodificaciones antiguas son incorrectas.
    """
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print(f"  ✓ Caché eliminado: {CACHE_FILE}")
    else:
        print(f"  ℹ️ No existe archivo de caché")


def get_cache_stats():
    """
    Obtiene estadísticas sobre el caché.
    
    Returns:
        dict: Estadísticas del caché
    """
    cache = load_cache()
    
    total = len(cache)
    geocoded = sum(1 for v in cache.values() if v is not None)
    not_found = total - geocoded
    
    return {
        'total': total,
        'geocoded': geocoded,
        'not_found': not_found,
        'file': CACHE_FILE,
        'exists': os.path.exists(CACHE_FILE)
    }
