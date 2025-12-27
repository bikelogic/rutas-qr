"""
Módulo para limpieza de direcciones usando modelo T5 entrenado

Optimizaciones:
1. Lookup en Correccions.csv (instantáneo, sin cargar modelo)
2. Cache de sesión para direcciones repetidas del mismo día
3. Solo carga el modelo si hay direcciones nuevas
"""
import os
from pathlib import Path
import re

# Variables globales
_model = None
_tokenizer = None
_lookup_dict = None
_lookup_loaded = False
_session_cache = {}  # Cache de direcciones procesadas en esta sesión


def _normalizar_key(texto):
    """Normaliza texto para búsqueda en lookup"""
    texto = texto.upper().strip()
    reemplazos = {'À':'A','Á':'A','È':'E','É':'E','Í':'I','Ò':'O','Ó':'O','Ú':'U','Ü':'U','Ñ':'N','Ç':'C'}
    for o, r in reemplazos.items():
        texto = texto.replace(o, r)
    return re.sub(r'\s+', ' ', texto)


def _cargar_lookup():
    """Carga solo el diccionario de lookup (rápido, sin modelo)"""
    global _lookup_dict, _lookup_loaded
    
    if _lookup_loaded:
        return _lookup_dict
    
    lookup_path = Path(__file__).parent.parent / "data" / "Correccions.csv"
    _lookup_dict = {}
    
    if lookup_path.exists():
        import pandas as pd
        df = pd.read_csv(lookup_path)
        df.columns = ['raw', 'processed']
        
        for _, row in df.iterrows():
            key = _normalizar_key(str(row['raw']))
            _lookup_dict[key] = row['processed']
        
        print(f"  📚 Lookup dict cargado: {len(_lookup_dict)} entradas conocidas")
    
    _lookup_loaded = True
    return _lookup_dict


def _cargar_modelo():
    """Carga el modelo T5 (solo cuando es necesario)"""
    global _model, _tokenizer
    
    if _model is not None:
        return _model, _tokenizer
    
    try:
        from transformers import T5Tokenizer, T5ForConditionalGeneration
        import torch
        
        model_path = Path(__file__).parent.parent / "models" / "address_model4"
        
        if not model_path.exists():
            raise FileNotFoundError(f"No se encontró el modelo en: {model_path}")
        
        print(f"  📦 Cargando modelo IA (para direcciones nuevas)...")
        
        _tokenizer = T5Tokenizer.from_pretrained("t5-small")
        _model = T5ForConditionalGeneration.from_pretrained(str(model_path))
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = _model.to(device)
        _model.eval()
        
        print(f"  ✅ Modelo cargado en {device.upper()}")
        
        return _model, _tokenizer
        
    except ImportError as e:
        print(f"  ❌ Error: Falta librería. Instala con: pip install transformers torch")
        raise e


def limpiar_direccion_con_modelo(direccion):
    """
    Limpia una dirección. Orden de prioridad:
    1. Cache de sesión (direcciones ya procesadas hoy)
    2. Lookup en Correccions.csv (instantáneo)
    3. Modelo IA (solo si no se encuentra en anteriores)
    
    Args:
        direccion (str): Dirección sin procesar
        
    Returns:
        tuple: (dirección_limpia, fuente) donde fuente es 'cache', 'lookup' o 'modelo'
    """
    import torch
    global _session_cache
    
    key = _normalizar_key(direccion)
    
    # 1. Buscar en cache de sesión (direcciones repetidas del mismo día)
    if key in _session_cache:
        return _session_cache[key], 'cache'
    
    # 2. Buscar en lookup (Correccions.csv)
    lookup_dict = _cargar_lookup()
    if key in lookup_dict:
        resultado = lookup_dict[key]
        _session_cache[key] = resultado  # Guardar en cache
        return resultado, 'lookup'
    
    # 3. Usar modelo IA (carga el modelo si no está cargado)
    model, tokenizer = _cargar_modelo()
    device = next(model.parameters()).device
    
    input_text = "normalizar: " + direccion
    inputs = tokenizer(
        input_text, 
        return_tensors="pt", 
        max_length=256, 
        truncation=True
    ).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_length=128, 
            num_beams=4,
            early_stopping=True
        )
    
    resultado = tokenizer.decode(outputs[0], skip_special_tokens=True)
    _session_cache[key] = resultado  # Guardar en cache
    return resultado, 'modelo'


def _procesar_batch_con_modelo(direcciones_batch):
    """
    Procesa un lote de direcciones con el modelo IA de forma eficiente.
    
    Args:
        direcciones_batch (list): Lista de direcciones a procesar
        
    Returns:
        list: Lista de direcciones procesadas
    """
    import torch
    global _session_cache
    
    if not direcciones_batch:
        return []
    
    model, tokenizer = _cargar_modelo()
    device = next(model.parameters()).device
    
    # Preparar inputs para todo el batch
    input_texts = ["normalizar: " + dir for dir in direcciones_batch]
    
    # Tokenizar todo el batch de una vez
    inputs = tokenizer(
        input_texts,
        return_tensors="pt",
        max_length=256,
        truncation=True,
        padding=True  # Importante para batch
    ).to(device)
    
    # Generar todas las salidas de una vez
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=4,
            early_stopping=True
        )
    
    # Decodificar resultados
    resultados = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    
    # Guardar en cache
    for direccion, resultado in zip(direcciones_batch, resultados):
        key = _normalizar_key(direccion)
        _session_cache[key] = resultado
    
    return resultados


def procesar_direcciones_con_modelo(direcciones_raw, mostrar_comparativa=True, batch_size=16):
    """
    Procesa una lista de direcciones usando lookup + modelo IA.
    Optimizado con procesamiento por lotes (batch) para mayor velocidad.
    
    Args:
        direcciones_raw (list): Lista de direcciones sin procesar
        mostrar_comparativa (bool): Si True, imprime antes/después
        batch_size (int): Número de direcciones a procesar por lote (default: 16)
        
    Returns:
        list: Lista de direcciones procesadas
    """
    global _session_cache
    _session_cache = {}  # Limpiar cache al inicio de cada procesamiento
    
    print("\n  🤖 Procesando direcciones...")
    
    # Primero cargar lookup (rápido)
    lookup_dict = _cargar_lookup()
    
    # Separar direcciones: las que están en lookup/cache vs las que necesitan modelo
    direcciones_procesadas = [None] * len(direcciones_raw)  # Pre-alocar lista
    direcciones_para_modelo = []  # (índice, dirección)
    stats = {'cache': 0, 'lookup': 0, 'modelo': 0}
    
    # Primera pasada: resolver lookup y cache
    for i, direccion_raw in enumerate(direcciones_raw):
        key = _normalizar_key(direccion_raw)
        
        # Buscar en cache de sesión
        if key in _session_cache:
            direcciones_procesadas[i] = _session_cache[key]
            stats['cache'] += 1
        # Buscar en lookup
        elif key in lookup_dict:
            resultado = lookup_dict[key]
            _session_cache[key] = resultado
            direcciones_procesadas[i] = resultado
            stats['lookup'] += 1
        else:
            # Marcar para procesar con modelo
            direcciones_para_modelo.append((i, direccion_raw))
    
    # Segunda pasada: procesar con modelo en lotes (batch)
    if direcciones_para_modelo:
        print(f"  ⚡ Procesando {len(direcciones_para_modelo)} direcciones nuevas en lotes de {batch_size}...")
        
        # Procesar en batches
        for batch_start in range(0, len(direcciones_para_modelo), batch_size):
            batch_end = min(batch_start + batch_size, len(direcciones_para_modelo))
            batch_items = direcciones_para_modelo[batch_start:batch_end]
            
            # Extraer solo las direcciones del batch
            batch_direcciones = [item[1] for item in batch_items]
            
            # Procesar batch completo
            resultados_batch = _procesar_batch_con_modelo(batch_direcciones)
            
            # Asignar resultados a sus posiciones originales
            for (idx, direccion_raw), resultado in zip(batch_items, resultados_batch):
                direcciones_procesadas[idx] = resultado
                stats['modelo'] += 1
            
            print(f"     ✓ Lote {batch_start//batch_size + 1}: {len(batch_items)} direcciones procesadas")
    
    # Mostrar comparativa si está habilitado
    if mostrar_comparativa:
        print("\n" + "="*80)
        print("  COMPARATIVA DE DIRECCIONES (RAW → PROCESADA)")
        print("="*80)
        
        for i, (direccion_raw, direccion_procesada) in enumerate(zip(direcciones_raw, direcciones_procesadas)):
            key = _normalizar_key(direccion_raw)
            # Determinar fuente
            if key in lookup_dict:
                fuente = 'lookup'
            elif any(idx == i for idx, _ in direcciones_para_modelo):
                fuente = 'modelo'
            else:
                fuente = 'cache'
            
            icono = {'cache': '♻️', 'lookup': '📚', 'modelo': '🤖'}[fuente]
            print(f"\n  [{i+1}] {icono} ANTES:  {direccion_raw}")
            print(f"      DESPUÉS: {direccion_procesada}")
        
        print("\n" + "="*80)
    
    # Mostrar estadísticas
    print(f"\n  📊 Estadísticas de procesamiento:")
    print(f"     ♻️  Cache (repetidas): {stats['cache']}")
    print(f"     📚 Lookup (conocidas): {stats['lookup']}")
    print(f"     🤖 Modelo IA (nuevas): {stats['modelo']}")
    
    if stats['modelo'] == 0:
        print(f"     ⚡ ¡No fue necesario cargar el modelo IA!")
    elif stats['modelo'] > 0:
        print(f"     ⚡ Procesadas en lotes de {batch_size} (mucho más rápido)")
    
    return direcciones_procesadas
