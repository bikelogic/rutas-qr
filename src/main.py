"""
Script principal para procesamiento de rutas de entrega BikeLogic

Este script permite elegir entre dos métodos de optimización:
1. TSP (Traveling Salesman Problem) - Viajante de comercio
2. Line Distance - Distancia a línea de ruta
"""

import sys
from sheets_manager import crear_manager_sheets
from address_cleaner import procesar_direcciones
from geocoding import geocode_and_store_fast, get_cache_stats
from zone_manager import separar_por_zonas, agregar_punto_inicio, obtener_estadisticas_zonas
from tsp_solver import procesar_zonas_con_tsp
from line_distance_solver import procesar_zonas_con_linea
from config import GOOGLE_MAPS_API_KEY


def mostrar_menu():
    """Muestra el menú de opciones al usuario."""
    print("\n" + "="*60)
    print("  BIKELOGIC - SISTEMA DE OPTIMIZACIÓN DE RUTAS")
    print("="*60)
    print("\nSeleccione el método de optimización:")
    print("  1. TSP (Viajante de Comercio) - Ruta más corta")
    print("  2. Línea de Ruta - Ordenar según línea predefinida")
    print("  3. Salir")
    print("-"*60)


def solicitar_opcion():
    """
    Solicita al usuario que seleccione una opción.
    
    Returns:
        int: Opción seleccionada (1, 2 o 3)
    """
    while True:
        try:
            opcion = input("\nIngrese su opción (1, 2 o 3): ").strip()
            opcion_num = int(opcion)
            if opcion_num in [1, 2, 3]:
                return opcion_num
            else:
                print("❌ Opción inválida. Por favor ingrese 1, 2 o 3.")
        except ValueError:
            print("❌ Por favor ingrese un número válido.")


def procesar_rutas(metodo='tsp'):
    """
    Función principal que procesa las rutas según el método seleccionado.
    
    Args:
        metodo (str): 'tsp' o 'line' para elegir el método de optimización
    """
    print("\n" + "="*60)
    print(f"  PROCESANDO CON MÉTODO: {metodo.upper()}")
    print("="*60)
    
    # 1. Conexión con Google Sheets
    print("\n[1/7] Conectando con Google Sheets...")
    sheets_manager = crear_manager_sheets()
    print("  ✓ Conectado exitosamente")
    
    # 2. Leer datos del spreadsheet
    print("\n[2/7] Leyendo direcciones, códigos postales y códigos de barras...")
    direcciones_raw, codigos_postales, codigos_barras = sheets_manager.leer_direcciones_y_codigos()
    print(f"  ✓ {len(direcciones_raw)} direcciones leídas")
    print(f"  ✓ {len(codigos_barras)} códigos de barras leídos")
    
    # 3. Limpiar y procesar direcciones
    print("\n[3/7] Limpiando y procesando direcciones...")
    direcciones_completas = procesar_direcciones(direcciones_raw, codigos_postales)
    print(f"  ✓ Direcciones procesadas correctamente")
    
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
    
    # 6. Optimizar rutas según método seleccionado
    print(f"\n[6/7] Optimizando rutas con método {metodo.upper()}...")
    if metodo == 'tsp':
        zonas_ordenadas = procesar_zonas_con_tsp(zonas_dict)
    else:  # metodo == 'line'
        zonas_ordenadas = procesar_zonas_con_linea(zonas_dict)
    print("  ✓ Rutas optimizadas correctamente")
    
    # Contar totales
    total_ordenadas = sum(len(dirs) for dirs in zonas_ordenadas.values())
    print(f"  ✓ {total_ordenadas} puntos de entrega únicos (optimizados)")
    
    # 7. Escribir resultados en Google Sheets
    print("\n[7/7] Escribiendo resultados en Google Sheets...")
    sheets_manager.limpiar_columnas_resultados()
    # Escribir direcciones: si es método 'line', incluir todos los puntos
    # Si es método 'tsp', excluir el punto de inicio/fin (depósito)
    excluir_deposito = (metodo == 'tsp')
    sheets_manager.escribir_resultados_por_zona(zonas_ordenadas, excluir_inicio_fin=excluir_deposito)
    sheets_manager.escribir_no_encontradas(not_found_addresses)
    
    print("\n" + "="*60)
    print("  ✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*60)
    print("\nLos resultados han sido escritos en el Google Spreadsheet.")
    print("Columnas de resultados:")
    print("  - Columna I: Direcciones Zona Indust")
    print("  - Columna J: Códigos de barras Zona Indust")
    print("  - Columna K: Direcciones Zona Centre")
    print("  - Columna L: Códigos de barras Zona Centre")
    print("  - Columna M: Direcciones Zona Altres")
    print("  - Columna N: Códigos de barras Zona Altres")
    print("  - Columna O: No encontradas")


def main():
    """Función principal del programa."""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + " "*15 + "BIKELOGIC - RUTAS" + " "*25 + "║")
    print("║" + " "*10 + "Sistema de Optimización de Entregas" + " "*12 + "║")
    print("║" + " "*58 + "║")
    print("╚" + "═"*58 + "╝")
    
    while True:
        mostrar_menu()
        opcion = solicitar_opcion()
        
        if opcion == 1:
            print("\n🚴 Has seleccionado: TSP (Viajante de Comercio)")
            confirmacion = input("¿Deseas continuar? (s/n): ").strip().lower()
            if confirmacion == 's':
                try:
                    procesar_rutas(metodo='tsp')
                except Exception as e:
                    print(f"\n❌ ERROR: {str(e)}")
                    print("Por favor revisa la configuración y vuelve a intentar.")
            
        elif opcion == 2:
            print("\n🚴 Has seleccionado: Línea de Ruta")
            confirmacion = input("¿Deseas continuar? (s/n): ").strip().lower()
            if confirmacion == 's':
                try:
                    procesar_rutas(metodo='line')
                except Exception as e:
                    print(f"\n❌ ERROR: {str(e)}")
                    print("Por favor revisa la configuración y vuelve a intentar.")
        
        elif opcion == 3:
            print("\n👋 Saliendo del programa...")
            sys.exit(0)
        
        # Preguntar si desea procesar otra ruta
        continuar = input("\n¿Deseas procesar otra ruta? (s/n): ").strip().lower()
        if continuar != 's':
            print("\n👋 Saliendo del programa...")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        sys.exit(1)
