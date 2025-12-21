"""
Módulo para limpieza y normalización de direcciones
"""
import re
from config import DEFAULT_CITY


def limpiar_direccion_con_reglas(direccion):
    """
    Limpia y normaliza una dirección siguiendo reglas específicas.
    
    Args:
        direccion (str): Dirección sin limpiar
        
    Returns:
        str: Dirección limpia y normalizada
    """
    # Eliminar 'n' y 'N' aisladas
    direccion = re.sub(r'(?<![A-Za-z])n(?![A-Za-z])', '', direccion)
    direccion = re.sub(r'(?<![A-Za-z])N(?![A-Za-z])', '', direccion)
    
    # Extraer números (máximo 3 dígitos)
    numeros = [int(num) for num in re.findall(r'(?<=\D-)\b\d+\b|(?<!-)\b\d+\b(?![ºª])', direccion) if len(num) <= 3]
    
    # Palabras a eliminar
    palabras_a_eliminar = r'\b(CASA|LOCAL|PISO|NUM|BLOQUE|MICROGESTIO, S.L. )\b'
    
    # Caracteres especiales a eliminar
    caracteres_especiales = r'[()&%-+`^\'\[\]]'
    
    direccion = re.sub(palabras_a_eliminar, '', direccion, flags=re.IGNORECASE)
    direccion = re.sub(caracteres_especiales, '', direccion)
    
    numero_mayor = max(numeros) if numeros else None
    
    if numero_mayor is not None:
        # Encontrar y reemplazar caracteres especiales
        direccion = re.sub(r'[ºª]', '', direccion)
        
        # Determinar la posición del número más grande
        posicion_numero_mayor = direccion.find(str(numero_mayor))
        
        # Si el número más grande está al inicio, moverlo al final
        if posicion_numero_mayor == 0:
            direccion_sin_numero = re.sub(r'^\d+\s*', '', direccion)
            direccion_final = f"{direccion_sin_numero} {numero_mayor}"
        else:
            direccion_nueva = re.sub(
                r'\d+', 
                lambda match: str(match.group()) if int(match.group()) == numero_mayor else "", 
                direccion, 
                count=1
            )
            indice_numero_mayor = direccion_nueva.find(str(numero_mayor)) + len(str(numero_mayor))
            direccion_final = direccion_nueva[:indice_numero_mayor].strip()
        
        return direccion_final
    else:
        # Si no hay números válidos, solo limpiar caracteres especiales
        direccion = re.sub(r'[ºª]', '', direccion).strip()
        return re.sub(r'(?<=\d)\s*[^\d\n]+$', '', direccion)


def construir_direcciones_completas(direcciones, codigos_postales, ciudad=DEFAULT_CITY):
    """
    Construye direcciones completas con código postal y ciudad.
    
    Args:
        direcciones (list): Lista de direcciones limpias
        codigos_postales (list): Lista de códigos postales
        ciudad (str): Ciudad por defecto
        
    Returns:
        list: Lista de direcciones completas
    """
    direcciones_completas = []
    
    for i, direccion in enumerate(direcciones):
        # Detectar si es Valldoreix
        if "VALLDOREIX" in direccion:
            ciudad_actual = "VALLDOREIX"
        else:
            ciudad_actual = ciudad
        
        direccion_completa = f"{direccion}, {ciudad_actual} {codigos_postales[i]}"
        direcciones_completas.append(direccion_completa)
    
    return direcciones_completas


def procesar_direcciones(direcciones_raw, codigos_postales):
    """
    Proceso completo de limpieza y construcción de direcciones.
    
    Args:
        direcciones_raw (list): Lista de direcciones sin procesar
        codigos_postales (list): Lista de códigos postales
        
    Returns:
        list: Lista de direcciones completas procesadas
    """
    # Limpiar direcciones
    direcciones_limpia = [limpiar_direccion_con_reglas(direccion) for direccion in direcciones_raw]
    
    # Construir direcciones completas
    direcciones_completas = construir_direcciones_completas(direcciones_limpia, codigos_postales)
    
    return direcciones_completas
