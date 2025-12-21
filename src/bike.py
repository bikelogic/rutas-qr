from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import linear_sum_assignment
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import requests
import time
from shapely.geometry import Point, Polygon
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY = 'key1.json'

SPREADSHEET_ID = '1loHNAzKgu7f11ctn7vv-4Nn9Bbkxz-1vHqO8DbZbvJw'

creds = None
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Hoja 1!c2:c300').execute()

values = result.get('values', [])

direcciones = [item[0] for item in values if item]


'''
-------------------------------------------------------------------------------------
SEPARACIO SEGONS POLIGONS
-------------------------------------------------------------------------------------
'''

poligono_zona1 = Polygon([(41.47965, 2.07387), (41.49077, 2.07591), (41.49193, 2.08694), (41.47682, 2.10226), (41.47181, 2.09789), (41.47386, 2.09179), (41.47603, 2.0909), (41.47589, 2.08279)])
poligono_zona2 = Polygon([(41.47965, 2.07387), (41.47589, 2.08279), (41.47603, 2.0909), (41.47386, 2.09179), (41.47181, 2.09789), (41.45823, 2.08887), (41.46548, 2.07734), (41.46705, 2.07794), (41.46837, 2.07834), (41.47356, 2.07736)])
poligono_zona3 = Polygon([(41.47965, 2.07387), (41.47356, 2.07736), (41.46837, 2.07834), (41.46705, 2.07794), (41.464, 2.07437), (41.45739, 2.08844), (41.45, 2.08671), (41.45296, 2.06534), (41.45903, 2.0647), (41.47744, 2.06418), (41.47699, 2.04356), (41.50087, 2.05476), (41.50133, 2.07809), (41.49077, 2.07591)])
poligono_zona4 = Polygon([(41.47699, 2.04356), (41.47744, 2.06418), (41.45903, 2.0647), (41.45296, 2.06534), (41.45264, 2.0254), (41.47495, 2.02771)])

def determinar_zona(coord):
    punto = Point(coord)
    if poligono_zona1.contains(punto):
        return 'Indust'
    elif poligono_zona2.contains(punto):
        return 'Centre'
    elif poligono_zona3.contains(punto):
        return 'MiraEst'
    elif poligono_zona4.contains(punto):
        return 'Mira'
    else:
        return 'sin_zona'
    
def separar_por_zonas(geocoded_addresses):
    direcciones_Indust = []
    direcciones_Centre = []
    direcciones_MiraEst = []
    direcciones_Mira = []
    direcciones_sin_zona = []
    
    for item in geocoded_addresses:
        coords, address = item
        zona = determinar_zona(coords)
        if zona == 'Indust':
            direcciones_Indust.append(item)
        elif zona == 'Centre':
            direcciones_Centre.append(item)
        elif zona == 'MiraEst':
            direcciones_MiraEst.append(item)
        elif zona == 'Mira':
            direcciones_Mira.append(item)
        elif zona == 'Mira':
            direcciones_sin_zona.append(item)
            
    return direcciones_Indust, direcciones_Centre, direcciones_MiraEst, direcciones_Mira, direcciones_sin_zona


'''
-------------------------------------------------------------------------------------
NETEJA D'ADRECES-------------------------------------------------------------------------------------
'''
def limpiar_direccion_con_reglas(direccion):
    direccion = re.sub(r'(?<![A-Za-z])n(?![A-Za-z])', '', direccion)
    direccion = re.sub(r'(?<![A-Za-z])N(?![A-Za-z])', '', direccion)
    numeros = [int(num) for num in re.findall(r'(?<=\D-)\b\d+\b|(?<!-)\b\d+\b(?![ºª])', direccion) if len(num) <= 3]
    palabras_a_eliminar = r'\b(CASA|LOCAL|PISO|NUM|BLOQUE|MICROGESTIO, S.L. )\b'
    caracteres_especiales = r'[()&%-+`^\'\[\]]'  # Añade aquí todos los caracteres especiales que quieras eliminar
    direccion = re.sub(palabras_a_eliminar, '', direccion, flags=re.IGNORECASE)
    direccion = re.sub(caracteres_especiales, '', direccion)
    numero_mayor = max(numeros) if numeros else None
    if numero_mayor is not None:
        # Encontrar y reemplazar caracteres especiales
        direccion = re.sub(r'[ºª]', '', direccion)
        # Determinar la posición del número más grande
        posicion_numero_mayor = direccion.find(str(numero_mayor))
        # Si el número más grande está al inicio, reconstruir la dirección moviendo el número al final
        if posicion_numero_mayor == 0:
            # Eliminar el número al inicio
            direccion_sin_numero = re.sub(r'^\d+\s*', '', direccion)
            # Añadir el número al final
            direccion_final = f"{direccion_sin_numero} {numero_mayor}"
        else:
            # Si el número no está al inicio, proceder como antes
            direccion_nueva = re.sub(r'\d+', lambda match: str(match.group()) if int(match.group()) == numero_mayor else "", direccion, count=1)
            indice_numero_mayor = direccion_nueva.find(str(numero_mayor)) + len(str(numero_mayor))
            direccion_final = direccion_nueva[:indice_numero_mayor].strip()
        return direccion_final
    else:
        # Si no hay números válidos, solo limpiar caracteres especiales
        direccion = re.sub(r'[ºª]', '', direccion).strip()
        # Eliminar cualquier texto no deseado después de un número, si existe
        return re.sub(r'(?<=\d)\s*[^\d\n]+$', '', direccion)
    

# Limpiar y normalizar cada dirección
direcciones_limpia = [limpiar_direccion_con_reglas(direccion) for direccion in direcciones]

result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Hoja 1!a2:a300').execute()

values = result.get('values', [])

codigos_postales = [item[0] for item in values if item]


ciudad = "SANT CUGAT DEL VALLES"
direcciones_completas = []
for i, direccion in enumerate(direcciones_limpia):
    if "VALLDOREIX" in direccion:
        ciudad_actual = "VALLDOREIX"
    else:
        ciudad_actual = ciudad
    direccion_completa = f"{direccion}, {ciudad_actual} {codigos_postales[i]}"
    direcciones_completas.append(direccion_completa)
    


'''
-------------------------------------------------------------------------------------
GEOCODIFICACIO AMB GOOGLE MAPS
-------------------------------------------------------------------------------------
'''

def geocode_with_google_maps(address, google_maps_api_key):
    """Geocodifica una dirección usando Google Maps Geocoding API."""
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": google_maps_api_key}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lon = data['results'][0]['geometry']['location']['lng']
            return (lat, lon)
    return None

def geocode_and_store(addresses, google_maps_api_key='YOUR_GOOGLE_MAPS_API_KEY'):
    """Geocodifica una lista de direcciones y almacena las que se pudieron geocodificar y las que no."""
    geocoded_addresses_dict = {}
    not_found_addresses = []
    
    for address in addresses:
        coords = geocode_with_google_maps(address, google_maps_api_key)
        if coords:
            if coords not in geocoded_addresses_dict:
                geocoded_addresses_dict[coords] = []
            geocoded_addresses_dict[coords].append(address)
        else:
            not_found_addresses.append([address])
        time.sleep(0.3)  # Para evitar sobrepasar los límites de la cuota de la API

    # Convertir el diccionario a una lista de coordenadas con la primera dirección asociada
    geocoded_addresses = [(coords, addresses[0]) for coords, addresses in geocoded_addresses_dict.items()]
    return geocoded_addresses, not_found_addresses

google_maps_api_key = 'AIzaSyCNieUGcoASX7yT2h2gRS1DxT0XlSN1yFU'


'''
-------------------------------------------------------------------------------------
VIATJANT DE COMERÇ
-------------------------------------------------------------------------------------
'''
def create_data_model(coordinates):
    """Stores the data for the problem."""
    data = {}
    # Assumption: 'coordinates' includes the start/end location at 'start_end_index'
    data['locations'] = coordinates  # Location coordinates
    data['num_vehicles'] = 1  # Number of vehicles in the problem
    data['depot'] = 0  # Index of the start/end location
    return data

def compute_euclidean_distance_matrix(locations):
    """Crea la matriz de distancia euclidiana entre puntos."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Distancia euclidiana
                distances[from_counter][to_counter] = (int(
                    ((float(from_node[0]) - float(to_node[0])) ** 2 + 
                     (float(from_node[1]) - float(to_node[1])) ** 2) ** 0.5 * 100000))
    return distances

def print_solution(manager, routing, solution):
    """Imprime la solución."""
    index = routing.Start(0)
    plan_output = 'Ruta:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += f' {manager.IndexToNode(index)} ->'
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += ' {}\n'.format(manager.IndexToNode(index))


def solve_tsp_problem(geocoded_addresses):
    # Extraer solo las coordenadas para el problema TSP
    coordinates = [coords for coords, address in geocoded_addresses]
    
    # Instanciar el modelo de datos
    data = create_data_model(coordinates)
    distance_matrix = compute_euclidean_distance_matrix(data['locations'])
    data['distance_matrix'] = distance_matrix
    
    # Crear el modelo de enrutamiento
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # Definir el callback de distancia
    transit_callback_index = routing.RegisterTransitCallback(
        lambda from_index, to_index: data['distance_matrix'][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
    )
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Configuración de búsqueda
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    # Solución del problema
    solution = routing.SolveWithParameters(search_parameters)

    # Lista para guardar el orden de las direcciones
    ordered_addresses = []

    if solution:
        index = routing.Start(0)
        while not routing.IsEnd(index):
            ordered_addresses.append(geocoded_addresses[manager.IndexToNode(index)][1])
            index = solution.Value(routing.NextVar(index))
        # Añade el punto de retorno al inicio para completar el ciclo
        ordered_addresses.append(geocoded_addresses[manager.IndexToNode(index)][1])

    return ordered_addresses


geocoded_addresses, not_found_addresses = geocode_and_store(direcciones_completas, google_maps_api_key)
if not geocoded_addresses:
    print("No se pudieron geocodificar direcciones para esta ruta.")
    
direcciones_Indust, direcciones_Centre, direcciones_MiraEst, direcciones_Mira, direcciones_sin_zona = separar_por_zonas(geocoded_addresses)
direcciones_Indust.insert(0, ((41.47855, 2.07228), "CARRER DE SOLSONA 22, SANT CUGAT DEL VALLES 08173"))
direcciones_Centre.insert(0,((41.47855, 2.07228), "CARRER DE SOLSONA 22, SANT CUGAT DEL VALLES 08173"))
direcciones_MiraEst.insert(0,((41.47855, 2.07228), "CARRER DE SOLSONA 22, SANT CUGAT DEL VALLES 08173"))
direcciones_Mira.insert(0,((41.47855, 2.07228), "CARRER DE SOLSONA 22, SANT CUGAT DEL VALLES 08173"))
direcciones_sin_zona.insert(0,((41.47855, 2.07228), "CARRER DE SOLSONA 22, SANT CUGAT DEL VALLES 08173"))

ordered_Indust = solve_tsp_problem(direcciones_Indust)
ordered_Centre = solve_tsp_problem(direcciones_Centre)
ordered_MiraEst = solve_tsp_problem(direcciones_MiraEst)
ordered_Mira = solve_tsp_problem(direcciones_Mira)
ordered_sin_zona = solve_tsp_problem(direcciones_sin_zona)

list_of_Indust = [[item] for item in ordered_Indust]
list_of_Centre = [[item] for item in ordered_Centre]
list_of_MiraEst = [[item] for item in ordered_MiraEst]
list_of_Mira = [[item] for item in ordered_Mira]
list_of_sin_zona = [[item] for item in ordered_sin_zona]



result = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                               range='i2',
                               valueInputOption='USER_ENTERED',
                               body={'values':list_of_Indust[1:-1]}).execute()

result = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                               range='j2',
                               valueInputOption='USER_ENTERED',
                               body={'values':list_of_Centre[1:-1]}).execute()
result = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                               range='k2',
                               valueInputOption='USER_ENTERED',
                               body={'values':list_of_MiraEst[1:-1]}).execute()
result = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                               range='l2',
                               valueInputOption='USER_ENTERED',
                               body={'values':list_of_Mira[1:-1]}).execute()
result = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                               range='m2',
                               valueInputOption='USER_ENTERED',
                               body={'values':list_of_sin_zona[1:-1]}).execute()

if not_found_addresses:
    range_to_write = 'Hoja 1!n2'  # Ajusta según el nombre de tu hoja y la celda inicial
    body = {
        'values': not_found_addresses
    }
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_to_write,
        valueInputOption='USER_ENTERED',
        body=body).execute()
    print(f"{len(not_found_addresses)} direcciones no encontradas fueron añadidas a la hoja.")
