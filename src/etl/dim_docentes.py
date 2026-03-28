import pandas as pd
import numpy as np
import warnings
from pathlib import Path

# --- IMPORTACIONES DE TU PROYECTO ---
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings
# Importamos tus nuevas herramientas de limpieza
from src.core.limpieza import limpiar_texto_general, corregir_dni, limpiar_celulares, limpiar_cabeceras

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
    h_docentes = config.get('excel_config', {}).get('docentes_activos_header', 0)
    h_rut = config.get('excel_config', {}).get('rut_header', 0)

    hoja_docentes_activos = config['sheets']['docentes_activos']
    df_docentes_activos = pd.read_excel(ruta, sheet_name=hoja_docentes_activos, header=h_docentes)
    df_docentes_activos = limpiar_cabeceras(df_docentes_activos)

    col_map = mappings['docentes_mappings']['columns']
    
    # Selección y renombre de columnas de Docentes Activos
    try:
        df = df_docentes_activos[list(col_map.keys())].rename(columns=col_map).copy() 
    except KeyError as e:
        print(f"❌ Error crítico: No se encontraron columnas en {hoja_docentes_activos}. Revisa el header en settings.yaml.")
        return

    hoja_rut = config['sheets']['rut']
    df_rut_raw = pd.read_excel(ruta, sheet_name=hoja_rut, header=h_rut)
    df_rut_raw = limpiar_cabeceras(df_rut_raw)

    col_map_rut = mappings['rut_mappings']['columns']
    df_rut = df_rut_raw[list(col_map_rut.keys())].rename(columns=col_map_rut).copy() 

    # ---------------------------------------------------------
    # UNIÓN, DEDUPLICACIÓN Y LIMPIEZA
    # ---------------------------------------------------------
    df = pd.concat([df, df_rut], ignore_index=True) 
    df = df.drop_duplicates(subset=['CODIGO_BANNER'], keep='first')

    df = limpiar_texto_general(df, mappings['docentes_mappings']['text_columns'])

    for col in mappings['docentes_mappings']['date_columns']:
        if col in df.columns: 
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

    if 'NOMBRE_COMPLETO' in df.columns:
        df['NOMBRE_COMPLETO'] = (
            df['NOMBRE_COMPLETO']
            .str.replace(',', '', regex=False) 
            .str.replace(r'\s+', ' ', regex=True) 
            .str.strip()
        )  

    df['DNI'] = corregir_dni(df['DNI'])
    
    if 'CELULAR' in df.columns:
        df['CELULAR'] = limpiar_celulares(df['CELULAR'])

    mapa_gen = mappings['docentes_mappings']['gender_map']
    df['GENERO'] = df['GENERO'].astype(str).str.upper().str.strip().replace(mapa_gen)
    df['GENERO'] = df['GENERO'].apply(lambda x: x if x in ['M', 'F'] else 'ND')

    # ---------------------------------------------------------
    # EXPORTACIÓN
    # ---------------------------------------------------------
    ruta_salida = Path(config['paths']['output']) / config['files']['dim_docentes']
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    
    orden = mappings['docentes_mappings']['column_order']
    df[orden].to_excel(ruta_salida, index=False)
    aplicar_formato_excel(ruta_salida)

if __name__ == "__main__":
    dimension_docentes()