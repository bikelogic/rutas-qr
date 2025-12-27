"""
Módulo para gestión de Google Sheets
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import SCOPES, KEY_FILE, SPREADSHEET_ID


class SheetsManager:
    """Clase para gestionar operaciones con Google Sheets"""
    
    def __init__(self, key_file=KEY_FILE, spreadsheet_id=SPREADSHEET_ID):
        """
        Inicializa el gestor de Google Sheets.
        
        Args:
            key_file (str): Ruta al archivo de credenciales JSON
            spreadsheet_id (str): ID del spreadsheet de Google Sheets
        """
        self.spreadsheet_id = spreadsheet_id
        self.creds = service_account.Credentials.from_service_account_file(
            key_file, 
            scopes=SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet = self.service.spreadsheets()
    
    def leer_columna(self, rango):
        """
        Lee valores de una columna del spreadsheet.
        
        Args:
            rango (str): Rango en formato 'Hoja!A1:A100'
            
        Returns:
            list: Lista de valores (una sola columna)
        """
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=rango
        ).execute()
        
        values = result.get('values', [])
        # Aplanar lista si es necesario
        return [item[0] for item in values if item]
    
    def escribir_columna(self, rango, datos):
        """
        Escribe valores en una columna del spreadsheet.
        
        Args:
            rango (str): Rango inicial en formato 'Hoja!A1' o 'A1'
            datos (list): Lista de valores a escribir
            
        Returns:
            dict: Resultado de la operación
        """
        # Convertir lista simple a lista de listas para formato de Sheets
        if datos and not isinstance(datos[0], list):
            datos = [[item] for item in datos]
        
        result = self.sheet.values().update(
            spreadsheetId=self.spreadsheet_id,
            range=rango,
            valueInputOption='USER_ENTERED',
            body={'values': datos}
        ).execute()
        
        return result
    
    def leer_rango_filas(self, rango):
        """
        Lee valores de un rango de filas completo (múltiples columnas).
        
        Args:
            rango (str): Rango en formato 'Hoja!A1:E100'
            
        Returns:
            list: Lista de listas con los valores de cada fila
        """
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=rango
        ).execute()
        
        return result.get('values', [])
    
    def leer_direcciones_completas(self):
        """
        Lee direcciones completas de la columna E, códigos de barras de columna A,
        y columna D para filtrar filas que contengan 'Q-PRINTING'.
        
        Returns:
            tuple: (direcciones_completas, codigos_barras, filas_eliminadas)
                   filas_eliminadas es una lista de tuplas (fila_num, codigo, texto_d)
        """
        # Leer columnas A, D y E de una vez (A=códigos, D=filtro, E=direcciones)
        filas = self.leer_rango_filas('Hoja 1!a2:e1000')
        
        direcciones = []
        codigos_barras = []
        filas_eliminadas = []
        
        for i, fila in enumerate(filas):
            # Asegurar que la fila tiene suficientes columnas
            codigo = fila[0] if len(fila) > 0 else ''
            columna_d = fila[3] if len(fila) > 3 else ''  # Columna D (índice 3)
            direccion = fila[4] if len(fila) > 4 else ''  # Columna E (índice 4)
            
            # Verificar si contiene Q-PRINTING (case-insensitive)
            if 'Q-PRINTING' in str(columna_d).upper():
                filas_eliminadas.append((i + 2, codigo, columna_d))  # +2 porque empezamos en fila 2
                continue
            
            # Solo añadir si hay dirección
            if direccion:
                direcciones.append(direccion)
                codigos_barras.append(codigo)
        
        return direcciones, codigos_barras, filas_eliminadas
    
    def escribir_resultados_por_zona(self, zonas_ordenadas, columnas_destino=None, excluir_inicio_fin=True):
        """
        Escribe los resultados ordenados en columnas por zona.
        Ahora escribe direcciones y códigos de barras en columnas separadas.
        
        Args:
            zonas_ordenadas (dict): Diccionario con datos ordenados por zona
                                    Cada item es (coords, address, codigos_barras)
            columnas_destino (dict): Diccionario {zona: (col_dir, col_codigos)} 
                                     ej: {'Indust': ('i2', 'j2')}
                                     Si es None, usa las columnas por defecto
            excluir_inicio_fin (bool): Si True, excluye el primer y último punto (depósito)
                                       Si False, incluye todos los puntos
        
        Returns:
            dict: Resultado de las operaciones de escritura
        """
        if columnas_destino is None:
            columnas_destino = {
                'Indust': ('g2', 'h2'),
                'Centre': ('j2', 'k2'),
                'Mirasol': ('m2', 'n2'),
                'sin_zona': ('p2', 'q2')
            }
        
        resultados = {}
        
        for zona_name, items in zonas_ordenadas.items():
            if zona_name in columnas_destino and items:
                # Excluir primera y última dirección (depósito) solo si se solicita
                if excluir_inicio_fin:
                    if len(items) > 2:
                        datos_a_escribir = items[1:-1]
                    else:
                        datos_a_escribir = []
                else:
                    datos_a_escribir = items
                
                if datos_a_escribir:
                    col_dir, col_codigos = columnas_destino[zona_name]
                    
                    # Extraer direcciones y códigos de barras
                    direcciones = []
                    codigos = []
                    for item in datos_a_escribir:
                        # item puede ser (coords, address) o (coords, address, codigos_barras)
                        if len(item) >= 3:
                            coords, address, codigos_barras = item[0], item[1], item[2]
                        else:
                            coords, address = item[0], item[1]
                            codigos_barras = []
                        
                        direcciones.append(address)
                        # Unir múltiples códigos de barras con coma
                        codigos.append(', '.join(str(c) for c in codigos_barras) if codigos_barras else '')
                    
                    # Escribir direcciones
                    result_dir = self.escribir_columna(col_dir, direcciones)
                    # Escribir códigos de barras
                    result_cod = self.escribir_columna(col_codigos, codigos)
                    
                    resultados[zona_name] = {'direcciones': result_dir, 'codigos': result_cod}
                    print(f"  ✓ Zona {zona_name}: {len(direcciones)} direcciones en {col_dir}, códigos en {col_codigos}")
        
        return resultados
    
    def escribir_no_encontradas(self, not_found_addresses, rango='q2'):
        """
        Escribe las direcciones que no se pudieron geocodificar.
        
        Args:
            not_found_addresses (list): Lista de direcciones no encontradas
            rango (str): Rango inicial donde escribir (columna Q)
            
        Returns:
            dict: Resultado de la operación
        """
        if not not_found_addresses:
            print("  ✓ Todas las direcciones fueron geocodificadas correctamente")
            return None
        
        result = self.escribir_columna(f'Hoja 1!{rango}', not_found_addresses)
        print(f"  ⚠ {len(not_found_addresses)} direcciones no encontradas escritas en {rango}")
        
        return result
    
    def limpiar_columnas_resultados(self, columnas=None):
        """
        Limpia las columnas de resultados antes de escribir nuevos datos.
        
        Args:
            columnas (list): Lista de rangos a limpiar ej: ['d2:d1000', 'e2:e1000']
        """
        if columnas is None:
            # Columnas: F-G (Indust), I-J (Centre), L-M (Mirasol), O-P (sin_zona), Q (No encontradas)
            # Nota: R no se limpia (contiene datos permanentes)
            columnas = ['g2:g1000', 'h2:h1000', 'j2:j1000', 'k2:k1000', 'm2:m1000', 'n2:n1000', 'p2:p1000', 'q2:q1000']
        
        for columna in columnas:
            self.sheet.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f'Hoja 1!{columna}'
            ).execute()
        
        print(f"  ✓ Columnas de resultados limpiadas: {', '.join(columnas)}")


def crear_manager_sheets(key_file=KEY_FILE, spreadsheet_id=SPREADSHEET_ID):
    """
    Función auxiliar para crear un SheetsManager.
    
    Args:
        key_file (str): Ruta al archivo de credenciales
        spreadsheet_id (str): ID del spreadsheet
        
    Returns:
        SheetsManager: Instancia del gestor
    """
    return SheetsManager(key_file, spreadsheet_id)
