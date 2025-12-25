"""
Módulo para limpieza de direcciones usando modelo T5 entrenado
"""
import os
from pathlib import Path

# Variable global para cargar el modelo solo una vez
_model = None
_tokenizer = None
_lookup_dict = None


def _cargar_modelo():
    """Carga el modelo T5 y el diccionario de lookup (solo una vez)"""
    global _model, _tokenizer, _lookup_dict
    
    if _model is not None:
        return _model, _tokenizer, _lookup_dict
    
    try:
        from transformers import T5Tokenizer, T5ForConditionalGeneration
        import json
        import torch
        
        # Ruta al modelo (relativa a src/)
        model_path = Path(__file__).parent.parent / "models" / "address_model"
        
        if not model_path.exists():
            raise FileNotFoundError(f"No se encontró el modelo en: {model_path}")
        
        print(f"  📦 Cargando modelo desde {model_path}...")
        
        # Intentar cargar tokenizer desde modelo local primero
        try:
            # Usar tokenizer de t5-small original (más compatible)
            print("  🔄 Cargando tokenizer desde t5-small (Hugging Face)...")
            _tokenizer = T5Tokenizer.from_pretrained("t5-small")
            print("  ✅ Tokenizer cargado desde Hugging Face")
        except Exception as e:
            print(f"  ⚠️ Error cargando tokenizer: {e}")
            raise
        
        # Cargar el modelo local entrenado
        _model = T5ForConditionalGeneration.from_pretrained(str(model_path))
        
        # Usar GPU si está disponible
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = _model.to(device)
        _model.eval()
        
        print(f"  ✅ Modelo cargado en {device.upper()}")
        
        # Cargar lookup dict si existe
        lookup_path = Path(__file__).parent.parent / "data" / "Correccions.csv"
        _lookup_dict = {}
        
        if lookup_path.exists():
            import pandas as pd
            import re
            df = pd.read_csv(lookup_path)
            df.columns = ['raw', 'processed']
            
            for _, row in df.iterrows():
                key = _normalizar_key(str(row['raw']))
                _lookup_dict[key] = row['processed']
            
            print(f"  📚 Lookup dict cargado: {len(_lookup_dict)} entradas")
        
        return _model, _tokenizer, _lookup_dict
        
    except ImportError as e:
        print(f"  ❌ Error: Falta librería. Instala con: pip install transformers torch")
        raise e


def _normalizar_key(texto):
    """Normaliza texto para búsqueda en lookup"""
    import re
    texto = texto.upper().strip()
    reemplazos = {'À':'A','Á':'A','È':'E','É':'E','Í':'I','Ò':'O','Ó':'O','Ú':'U','Ü':'U','Ñ':'N','Ç':'C'}
    for o, r in reemplazos.items():
        texto = texto.replace(o, r)
    return re.sub(r'\s+', ' ', texto)


def limpiar_direccion_con_modelo(direccion):
    """
    Limpia una dirección usando el modelo T5 entrenado.
    Primero busca en el lookup dict (instantáneo), si no encuentra usa el modelo.
    
    Args:
        direccion (str): Dirección sin procesar
        
    Returns:
        str: Dirección limpia
    """
    import torch
    
    model, tokenizer, lookup_dict = _cargar_modelo()
    
    # Primero intentar lookup (instantáneo)
    key = _normalizar_key(direccion)
    if key in lookup_dict:
        return lookup_dict[key]
    
    # Si no está en lookup, usar modelo
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
    return resultado


def procesar_direcciones_con_modelo(direcciones_raw, mostrar_comparativa=True):
    """
    Procesa una lista de direcciones usando el modelo IA.
    
    Args:
        direcciones_raw (list): Lista de direcciones sin procesar
        mostrar_comparativa (bool): Si True, imprime antes/después
        
    Returns:
        list: Lista de direcciones procesadas
    """
    print("\n  🤖 Procesando direcciones con modelo IA...")
    
    # Cargar modelo (solo la primera vez)
    _cargar_modelo()
    
    direcciones_procesadas = []
    
    if mostrar_comparativa:
        print("\n" + "="*80)
        print("  COMPARATIVA DE DIRECCIONES (RAW → PROCESADA)")
        print("="*80)
    
    for i, direccion_raw in enumerate(direcciones_raw):
        direccion_procesada = limpiar_direccion_con_modelo(direccion_raw)
        direcciones_procesadas.append(direccion_procesada)
        
        if mostrar_comparativa:
            print(f"\n  [{i+1}] ANTES:  {direccion_raw}")
            print(f"      DESPUÉS: {direccion_procesada}")
    
    if mostrar_comparativa:
        print("\n" + "="*80)
    
    return direcciones_procesadas
