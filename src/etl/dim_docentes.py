import pandas as pd
import numpy as np
import warnings
from pathlib import Path

# --- IMPORTACIONES DE TU PROYECTO ---
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings
# Importamos tus nuevas herramientas de limpieza
from src.core.limpieza import limpiar_texto_general, corregir_dni, limpiar_celulares

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def dimension_docentes():  
    """
    🔄 PROCESO ETL: DIMENSIÓN DOCENTES
    Actualiza la base de datos de docentes combinando 'Docentes Activos' y 'RUT'.
    """
    copiar_archivo_onedrive('data_docentes')
    ruta = Path(config['paths']['input']) / config['files']['data_docentes']
    
    # ---------------------------------------------------------
    # CARGA DE DATOS (Hojas: DOCENTES ACTIVOS y RUT)
    # ---------------------------------------------------------
    hoja_docentes_activos = config['sheets']['docentes_activos']
    df_docentes_activos = pd.read_excel(ruta, sheet_name=hoja_docentes_activos)

    col_map = mappings['docentes_mappings']['columns']
    df = df_docentes_activos[list(col_map.keys())].rename(columns=col_map).copy() 

    hoja_rut = config['sheets']['rut']
    df_rut = pd.read_excel(ruta, sheet_name=hoja_rut)

    col_map_rut = mappings['rut_mappings']['columns']
    df_rut = df_rut[list(col_map_rut.keys())].rename(columns=col_map_rut).copy() 

    # ---------------------------------------------------------
    # UNIÓN Y DEDUPLICACIÓN
    # ---------------------------------------------------------
    # Combinamos ambas fuentes y nos quedamos con el primer registro por Código Banner
    df = pd.concat([df, df_rut], ignore_index=True) 
    df = df.drop_duplicates(subset=['CODIGO_BANNER'], keep='first')

    # ---------------------------------------------------------
    # LIMPIEZA UTILIZANDO EL MÓDULO 'LIMPIEZA.PY'
    # ---------------------------------------------------------
    df = limpiar_texto_general(df, mappings['docentes_mappings']['text_columns'])

    # Estandarización de fechas
    for col in mappings['docentes_mappings']['date_columns']:
        if col in df.columns: 
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

    # Limpieza específica para nombres (Eliminar comas y exceso de espacios internos)
    if 'NOMBRE_COMPLETO' in df.columns:
        df['NOMBRE_COMPLETO'] = (
            df['NOMBRE_COMPLETO']
            .str.replace(',', '', regex=False) 
            .str.replace(r'\s+', ' ', regex=True) 
            .str.strip()
        )  

    # Formateo de Identidad y Contacto usando limpieza.py
    df['DNI'] = corregir_dni(df['DNI'])
    
    if 'CELULAR' in df.columns:
        df['CELULAR'] = limpiar_celulares(df['CELULAR'])

    # Lógica de Género (M/F/ND)
    mapa_gen = mappings['docentes_mappings']['gender_map']
    df['GENERO'] = df['GENERO'].astype(str).str.upper().str.strip().replace(mapa_gen)
    df['GENERO'] = df['GENERO'].apply(lambda x: x if x in ['M', 'F'] else 'ND')

    # ---------------------------------------------------------
    # EXPORTACIÓN Y FORMATO FINAL
    # ---------------------------------------------------------
    ruta_salida = Path(config['paths']['output']) / config['files']['dim_docentes']
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    
    # Ordenamos las columnas según el estándar del proyecto
    orden = mappings['docentes_mappings']['column_order']
    df = df[orden]

    # Guardamos y aplicamos el diseño estético de Excel
    df.to_excel(ruta_salida, index=False)
    aplicar_formato_excel(ruta_salida)

if __name__ == "__main__":
    dimension_docentes()