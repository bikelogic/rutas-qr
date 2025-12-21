"""
Módulo para ordenar paquetes según su distancia a una línea de ruta
"""
import numpy as np
from config import ZONE_ROUTE_LINES


def calcular_distancia_y_posicion(punto, linea_inicio, linea_fin):
    """
    Calcula tanto la distancia perpendicular como la posición de un punto respecto a una línea.
    Esta función optimiza el cálculo haciendo ambas operaciones en una sola pasada.
    
    Args:
        punto (tuple): Coordenadas del punto (lat, lon)
        linea_inicio (tuple): Punto inicial de la línea (lat, lon)
        linea_fin (tuple): Punto final de la línea (lat, lon)
        
    Returns:
        tuple: (distancia, posicion_relativa)
            - distancia: Distancia perpendicular del punto a la línea
            - posicion_relativa: Posición relativa (0-1, puede ser <0 o >1 si está fuera)
    """
    # Convertir a arrays numpy para cálculos vectoriales
    p = np.array(punto)
    l1 = np.array(linea_inicio)
    l2 = np.array(linea_fin)
    
    # Vector de la línea
    linea_vec = l2 - l1
    linea_len = np.linalg.norm(linea_vec)
    
    if linea_len == 0:
        # Si la línea tiene longitud 0, retorna distancia al punto y posición 0
        return np.linalg.norm(p - l1), 0
    
    # Vector normalizado de la línea
    linea_unitvec = linea_vec / linea_len
    
    # Vector del punto inicial al punto
    punto_vec = p - l1
    
    # Proyección del punto sobre la línea (distancia a lo largo de la línea)
    proyeccion = np.dot(punto_vec, linea_unitvec)
    
    # Posición relativa (normalizada 0-1)
    posicion_relativa = proyeccion / linea_len
    
    # Punto más cercano en la línea
    if proyeccion < 0:
        # Antes del inicio de la línea
        punto_cercano = l1
    elif proyeccion > linea_len:
        # Después del fin de la línea
        punto_cercano = l2
    else:
        # Dentro de la línea
        punto_cercano = l1 + proyeccion * linea_unitvec
    
    # Distancia perpendicular
    distancia = np.linalg.norm(p - punto_cercano)
    
    return distancia, posicion_relativa

def calcular_posicion_en_ruta_multi_segmento(punto, linea_puntos):
    """
    Calcula la posición de un punto a lo largo de una ruta con múltiples segmentos.
    
    Args:
        punto (tuple): Coordenadas del punto (lat, lon)
        linea_puntos (list): Lista de puntos que definen la ruta [(lat1, lon1), (lat2, lon2), ...]
        
    Returns:
        tuple: (posicion_en_ruta, distancia_minima)
            - posicion_en_ruta: Posición acumulada a lo largo de toda la ruta
            - distancia_minima: Distancia perpendicular mínima a cualquier segmento
    """
    if len(linea_puntos) < 2:
        return 0, float('inf')
    
    distancia_minima = float('inf')
    posicion_en_ruta = 0
    longitud_acumulada = 0
    
    # Calcular longitud total de la ruta
    longitud_total = 0
    for i in range(len(linea_puntos) - 1):
        seg_vec = np.array(linea_puntos[i + 1]) - np.array(linea_puntos[i])
        longitud_total += np.linalg.norm(seg_vec)
    
    # Encontrar el segmento más cercano
    for i in range(len(linea_puntos) - 1):
        inicio_seg = linea_puntos[i]
        fin_seg = linea_puntos[i + 1]
        
        # Longitud de este segmento
        seg_vec = np.array(fin_seg) - np.array(inicio_seg)
        longitud_segmento = np.linalg.norm(seg_vec)
        
        # Calcular distancia y posición en este segmento (optimizado en una sola llamada)
        dist, pos_rel = calcular_distancia_y_posicion(punto, inicio_seg, fin_seg)
        
        # Si este segmento está más cerca
        if dist < distancia_minima:
            distancia_minima = dist
            # Calcular posición absoluta en la ruta
            if pos_rel < 0:
                posicion_en_ruta = longitud_acumulada
            elif pos_rel > 1:
                posicion_en_ruta = longitud_acumulada + longitud_segmento
            else:
                posicion_en_ruta = longitud_acumulada + pos_rel * longitud_segmento
        
        longitud_acumulada += longitud_segmento
    
    # Normalizar la posición (0-1)
    if longitud_total > 0:
        posicion_normalizada = posicion_en_ruta / longitud_total
    else:
        posicion_normalizada = 0
    
    return posicion_normalizada, distancia_minima


def ordenar_por_linea(geocoded_addresses, linea_puntos):
    """
    Ordena direcciones según su posición a lo largo de una línea de ruta.
    
    Args:
        geocoded_addresses (list): Lista de tuplas [(coords, address), ...]
        linea_puntos (list): Lista de puntos que definen la ruta
        
    Returns:
        list: Lista de direcciones ordenadas
    """
    if not geocoded_addresses:
        return []
    
    if len(linea_puntos) < 2:
        print(f"  ⚠️ Línea de ruta tiene menos de 2 puntos, retornando orden original")
        return [address for _, address in geocoded_addresses]
    
    # Calcular posición de cada dirección a lo largo de la línea
    direcciones_con_posicion = []
    direcciones_problematicas = []
    
    for coords, address in geocoded_addresses:
        try:
            posicion, distancia = calcular_posicion_en_ruta_multi_segmento(coords, linea_puntos)
            
            # Verificar que los valores sean válidos
            if posicion is None or distancia is None or not isinstance(posicion, (int, float)) or not isinstance(distancia, (int, float)):
                print(f"  ⚠️ Valores inválidos para '{address[:50]}...': pos={posicion}, dist={distancia}")
                direcciones_problematicas.append((float('inf'), float('inf'), address))
            else:
                direcciones_con_posicion.append((posicion, distancia, address))
        except Exception as e:
            print(f"  ⚠️ Error procesando '{address[:50]}...': {e}")
            # Colocar al final si hay error
            direcciones_problematicas.append((float('inf'), float('inf'), address))
    
    # Ordenar por posición a lo largo de la línea (menor posición = más cerca del inicio)
    direcciones_con_posicion.sort(key=lambda x: x[0])
    
    # Extraer solo las direcciones ordenadas
    direcciones_ordenadas = [address for _, _, address in direcciones_con_posicion]
    
    # Añadir direcciones problemáticas al final
    if direcciones_problematicas:
        print(f"  ⚠️ {len(direcciones_problematicas)} direcciones colocadas al final por error en procesamiento")
        direcciones_ordenadas.extend([address for _, _, address in direcciones_problematicas])
    
    return direcciones_ordenadas


def procesar_zonas_con_linea(zonas_dict, lineas_por_zona=None):
    """
    Procesa todas las zonas usando el algoritmo de distancia a línea.
    
    Args:
        zonas_dict (dict): Diccionario de zonas con direcciones
        lineas_por_zona (dict): Diccionario con líneas de ruta por zona
                                Si es None, usa ZONE_ROUTE_LINES de config
        
    Returns:
        dict: Diccionario con direcciones ordenadas por zona
    """
    if lineas_por_zona is None:
        lineas_por_zona = ZONE_ROUTE_LINES
    
    zonas_ordenadas = {}
    
    for zona_name, direcciones in zonas_dict.items():
        if direcciones and zona_name in lineas_por_zona:
            print(f"Procesando zona {zona_name} con línea de ruta ({len(direcciones)} direcciones)...")
            linea = lineas_por_zona[zona_name]
            
            # Mostrar info de entrada
            print(f"  Direcciones de entrada:")
            for i, (coords, address) in enumerate(direcciones[:3], 1):
                print(f"    {i}. {address[:60]}... → {coords}")
            if len(direcciones) > 3:
                print(f"    ... y {len(direcciones) - 3} más")
            
            # Ordenar
            resultado = ordenar_por_linea(direcciones, linea)
            zonas_ordenadas[zona_name] = resultado
            
            # Verificar resultado
            if len(resultado) != len(direcciones):
                print(f"  ⚠️ ADVERTENCIA: Entrada={len(direcciones)}, Salida={len(resultado)}")
            else:
                print(f"  ✓ Ordenadas correctamente: {len(resultado)} direcciones")
        elif direcciones:
            # Si no hay línea definida para la zona, mantener el orden original
            print(f"  ⚠️ Zona {zona_name}: No hay línea de ruta definida, manteniendo orden original")
            zonas_ordenadas[zona_name] = [address for _, address in direcciones]
        else:
            zonas_ordenadas[zona_name] = []
    
    return zonas_ordenadas


def visualizar_ordenacion(geocoded_addresses, linea_puntos, titulo="Ordenación"):
    """
    Función auxiliar para visualizar cómo se ordenan los puntos (opcional).
    Útil para debugging y validación.
    
    Args:
        geocoded_addresses (list): Lista de tuplas [(coords, address), ...]
        linea_puntos (list): Lista de puntos que definen la ruta
        titulo (str): Título para la visualización
    """
    print(f"\n=== {titulo} ===")
    print(f"Línea de ruta: {len(linea_puntos)} puntos")
    
    for coords, address in geocoded_addresses:
        posicion, distancia = calcular_posicion_en_ruta_multi_segmento(coords, linea_puntos)
        print(f"  Posición: {posicion:.3f}, Distancia: {distancia:.6f} - {address[:50]}...")
