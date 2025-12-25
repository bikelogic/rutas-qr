"""
Script principal para procesamiento de rutas de entrega BikeLogic

Optimiza rutas usando distancia a línea de ruta predefinida.
Limpieza de direcciones con modelo IA (T5 fine-tuned).
"""

import sys
from sheets_manager import crear_manager_sheets
from address_model_cleaner import procesar_direcciones_con_modelo
from geocoding import geocode_and_store_fast, get_cache_stats
from zone_manager import separar_por_zonas, obtener_estadisticas_zonas
from line_distance_solver import procesar_zonas_con_linea
from config import GOOGLE_MAPS_API_KEY


def procesar_rutas():
    """
    Función principal que procesa las rutas.
    Usa método Línea de Ruta + Limpieza IA.
    """
    print("\n" + "="*60)
    print("  PROCESANDO RUTAS")
    print("  Método: LÍNEA DE RUTA + LIMPIEZA IA")
    print("="*60)
    
    # 1. Conexión con Google Sheets
    print("\n[1/7] Conectando con Google Sheets...")
    sheets_manager = crear_manager_sheets()
    print("  ✓ Conectado exitosamente")
    
    # 2. Leer datos del spreadsheet (columna A: códigos, columna D: direcciones)
    print("\n[2/7] Leyendo códigos de barras (A) y direcciones (D)...")
    direcciones_raw, codigos_barras = sheets_manager.leer_direcciones_completas()
    print(f"  ✓ {len(direcciones_raw)} direcciones leídas")
    print(f"  ✓ {len(codigos_barras)} códigos de barras leídos")
    
    # 3. Limpiar direcciones con modelo IA
    print("\n[3/7] Limpiando direcciones con modelo IA...")
    
    direcciones_completas = procesar_direcciones_con_modelo(
        direcciones_raw, 
        mostrar_comparativa=True  # Mostrar antes/después
    )
    print(f"  ✓ {len(direcciones_completas)} direcciones procesadas")
    
    # 4. Geocodificar direcciones
    print("\n[4/7] Geocodificando direcciones (esto puede tardar varios minutos)...")
    
    # Mostrar estadísticas del caché si existe
    cache_stats = get_cache_stats()
    if cache_stats['exists']:
        print(f"  📦 Caché disponible: {cache_stats['geocoded']} direcciones previamente geocodificadas")
    
    # Usar geocodificación rápida (con caché y paralelo)
    # Retorna 2 valores: direcciones únicas y no encontradas
    geocoded_addresses, not_found_addresses = geocode_and_store_fast(
        direcciones_completas,
        GOOGLE_MAPS_API_KEY,
        max_workers=10,  # 10 hilos en paralelo
        codigos_barras=codigos_barras  # Pasar códigos de barras
    )
    
    print(f"  ✓ {len(geocoded_addresses)} puntos únicos de entrega geocodificados")
    
    if not_found_addresses:
        print(f"  ⚠ {len(not_found_addresses)} direcciones no encontradas")
    
    if not geocoded_addresses:
        print("\n❌ ERROR: No se pudieron geocodificar direcciones. Abortando proceso.")
        return
    
    # 5. Separar por zonas
    print("\n[5/7] Separando direcciones por zonas...")
    zonas_dict = separar_por_zonas(geocoded_addresses)
    # zonas_dict = agregar_punto_inicio(zonas_dict)  # Comentado: el depósito no es punto de visita
    
    # Mostrar estadísticas
    stats = obtener_estadisticas_zonas(zonas_dict)
    print(f"  ✓ Direcciones separadas por zona:")
    for zona, count in stats.items():
        if zona != 'total':
            print(f"     - {zona}: {count} direcciones")
    print(f"     TOTAL: {stats['total']} direcciones")
    
    # 6. Optimizar rutas con método línea
    print("\n[6/7] Optimizando rutas con método LÍNEA...")
    zonas_ordenadas = procesar_zonas_con_linea(zonas_dict)
    print("  ✓ Rutas optimizadas correctamente")
    
    # Contar totales
    total_ordenadas = sum(len(dirs) for dirs in zonas_ordenadas.values())
    print(f"  ✓ {total_ordenadas} puntos de entrega únicos (optimizados)")
    
    # 7. Escribir resultados en Google Sheets
    print("\n[7/7] Escribiendo resultados en Google Sheets...")
    sheets_manager.limpiar_columnas_resultados()
    sheets_manager.escribir_resultados_por_zona(zonas_ordenadas, excluir_inicio_fin=False)
    sheets_manager.escribir_no_encontradas(not_found_addresses)
    
    print("\n" + "="*60)
    print("  ✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*60)
    print("\nLos resultados han sido escritos en el Google Spreadsheet.")
    print("Columnas de resultados:")
    print("  - Columna F-G: Zona Fàbriques (direcciones + códigos)")
    print("  - Columna I-J: Zona Centre (direcciones + códigos)")
    print("  - Columna L-M: Zona Mirasol (direcciones + códigos)")
    print("  - Columna O-P: Fuera de polígonos (direcciones + códigos)")
    print("  - Columna Q: No encontradas")


def main():
    """Función principal del programa."""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + " "*15 + "BIKELOGIC - RUTAS" + " "*25 + "║")
    print("║" + " "*10 + "Sistema de Optimización de Entregas" + " "*12 + "║")
    print("║" + " "*58 + "║")
    print("╚" + "═"*58 + "╝")
    
    try:
        procesar_rutas()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("Por favor revisa la configuración y vuelve a intentar.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        sys.exit(1)
