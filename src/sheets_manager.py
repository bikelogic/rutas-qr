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
    
    def leer_direcciones_y_codigos(self):
        """
        Lee direcciones, códigos postales y códigos de barras del spreadsheet.
        
        Returns:
            tuple: (direcciones, codigos_postales, codigos_barras)
        """
        direcciones = self.leer_columna('Hoja 1!c2:c300')
        codigos_postales = self.leer_columna('Hoja 1!a2:a300')
        codigos_barras = self.leer_columna('Hoja 1!d2:d300')
        
        return direcciones, codigos_postales, codigos_barras
    
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
                'Indust': ('i2', 'j2'),
                'Centre': ('k2', 'l2'),
                'Altres': ('m2', 'n2')
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
    
    def escribir_no_encontradas(self, not_found_addresses, rango='o2'):
        """
        Escribe las direcciones que no se pudieron geocodificar.
        
        Args:
            not_found_addresses (list): Lista de direcciones no encontradas
            rango (str): Rango inicial donde escribir (ahora columna O)
            
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
            columnas (list): Lista de rangos a limpiar ej: ['i2:i300', 'j2:j300']
        """
        if columnas is None:
            # Nuevas columnas: I-J (Indust), K-L (Centre), M-N (Altres), O (No encontradas)
            columnas = ['i2:i300', 'j2:j300', 'k2:k300', 'l2:l300', 'm2:m300', 'n2:n300', 'o2:o300']
        
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
