"""
Módulo para resolver el problema del viajante de comercio (TSP)
usando Google OR-Tools
"""
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model(coordinates):
    """
    Crea el modelo de datos para el problema TSP.
    
    Args:
        coordinates (list): Lista de coordenadas (lat, lon)
        
    Returns:
        dict: Modelo de datos con locations, num_vehicles y depot
    """
    data = {}
    data['locations'] = coordinates
    data['num_vehicles'] = 1
    data['depot'] = 0  # Punto de inicio arbitrario (no es depósito real)
    return data


def compute_euclidean_distance_matrix(locations):
    """
    Crea la matriz de distancia euclidiana entre puntos.
    
    Args:
        locations (list): Lista de tuplas (lat, lon)
        
    Returns:
        dict: Matriz de distancias {from_index: {to_index: distance}}
    """
    distances = {}
    
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Distancia euclidiana escalada
                distances[from_counter][to_counter] = int(
                    ((float(from_node[0]) - float(to_node[0])) ** 2 + 
                     (float(from_node[1]) - float(to_node[1])) ** 2) ** 0.5 * 100000
                )
    
    return distances


def solve_tsp_problem(geocoded_addresses):
    """
    Resuelve el problema del viajante de comercio para una lista de direcciones.
    
    Args:
        geocoded_addresses (list): Lista de tuplas [(coords, address, codigos_barras), ...]
        
    Returns:
        list: Lista de tuplas ordenadas según la ruta óptima [(coords, address, codigos_barras), ...]
    """
    if not geocoded_addresses:
        return []
    
    # Extraer solo las coordenadas para el problema TSP
    # Manejar tuplas de 2 o 3 elementos
    coordinates = [item[0] for item in geocoded_addresses]
    
    # Instanciar el modelo de datos
    data = create_data_model(coordinates)
    distance_matrix = compute_euclidean_distance_matrix(data['locations'])
    data['distance_matrix'] = distance_matrix
    
    # Crear el modelo de enrutamiento
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'], 
        data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)
    
    # Definir el callback de distancia
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Configuración de búsqueda
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    # Solución del problema
    solution = routing.SolveWithParameters(search_parameters)
    
    # Lista para guardar el orden de las direcciones (tuplas completas)
    ordered_addresses = []
    
    if solution:
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            ordered_addresses.append(geocoded_addresses[node_index])
            index = solution.Value(routing.NextVar(index))
        
        # No añadir el punto final de retorno - solo puntos de entrega
    
    return ordered_addresses


def procesar_zonas_con_tsp(zonas_dict):
    """
    Procesa todas las zonas usando el algoritmo TSP.
    
    Args:
        zonas_dict (dict): Diccionario de zonas con direcciones
        
    Returns:
        dict: Diccionario con direcciones ordenadas por zona
    """
    zonas_ordenadas = {}
    
    for zona_name, direcciones in zonas_dict.items():
        if direcciones:
            print(f"Procesando zona {zona_name} con TSP ({len(direcciones)} direcciones)...")
            zonas_ordenadas[zona_name] = solve_tsp_problem(direcciones)
        else:
            zonas_ordenadas[zona_name] = []
    
    return zonas_ordenadas
