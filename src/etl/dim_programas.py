import pandas as pd
import numpy as np
import warnings
from pathlib import Path

# --- IMPORTACIONES DE TU PROYECTO ---
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings
# Importamos tus herramientas
from src.core.limpieza import limpiar_texto_general, limpiar_cabeceras

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def dimension_programas():
    """
    📊 PROCESO ETL: DIMENSIÓN PROGRAMAS
    Transforma la programación de clases en una lista única de programas.
    """
    copiar_archivo_onedrive('data_programacion')
    ruta = Path(config['paths']['input']) / config['files']['data_programacion']
    
    h_prog = config.get('excel_config', {}).get('programas_header', 0)
    df_raw = pd.read_excel(ruta, sheet_name=config['sheets']['programacion'], header=h_prog)
    df_raw = limpiar_cabeceras(df_raw)

    soportes_val = config['filtros_reporte']['soportes']
    df_raw = df_raw[df_raw['SOPORTE'].isin(soportes_val)].copy()

    if 'FECHAS' in df_raw.columns:
        df_raw['FECHAS'] = pd.to_datetime(df_raw['FECHAS'], errors='coerce')
    
    def crear_id(row):
        try:
            p = str(int(float(row['PERIODO'])))
            n = str(int(float(row['NRC']))).zfill(4)
            return f"{p}.{n}"
        except: return "0.0000"

    df_raw['ID'] = df_raw.apply(crear_id, axis=1)

    # Cálculo de fechas extremas
    df_fechas = df_raw.groupby('ID')['FECHAS'].agg(['min', 'max']).reset_index()
    df_fechas.columns = ['ID', 'FECHA_INICIO', 'FECHA_FIN']
    df_fechas['FECHA_INICIO'] = pd.to_datetime(df_fechas['FECHA_INICIO']).dt.normalize()
    df_fechas['FECHA_FIN'] = pd.to_datetime(df_fechas['FECHA_FIN']).dt.normalize()

    col_map = mappings['programas_mappings']['columns']
    df = df_raw.drop_duplicates(subset=['ID'], keep='last').copy()
    df = df.rename(columns=col_map)
    
    df['PROGRAMA_COMPLETO'] = df['PROGRAMA_NOMBRE'].astype(str) + " - " + df['GRUPO'].astype(str)
    df = df.merge(df_fechas, on='ID', how='left')

    # Lógica de estados
    hoy = pd.Timestamp.now().normalize()
    df['ESTADO_PROGRAMA'] = 'ACTIVO'
    df.loc[hoy > df['FECHA_FIN'], 'ESTADO_PROGRAMA'] = 'CULMINÓ'
    df.loc[hoy < df['FECHA_INICIO'], 'ESTADO_PROGRAMA'] = 'POR INICIAR'

    df = limpiar_texto_general(df, mappings['programas_mappings']['text_columns'])

    # Exportación
    ruta_salida = Path(config['paths']['output']) / config['files']['dim_programas']
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    
    orden = mappings['programas_mappings']['column_order']
    df[orden].to_excel(ruta_salida, index=False)
    aplicar_formato_excel(ruta_salida)
    
    print(f"📊 Total de Programas únicos procesados: {len(df)}")

if __name__ == "__main__":
    dimension_programas()