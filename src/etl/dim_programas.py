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
    Transforma la programación de clases en una lista única de programas con fechas globales.
    """
    # 1. Sincronización: Traemos la última versión del Panel de Programación
    copiar_archivo_onedrive('data_programacion')
    ruta = Path(config['paths']['input']) / config['files']['data_programacion']
    
    # 2. Carga y Limpieza inicial de cabeceras usando limpieza.py
    df_raw = pd.read_excel(ruta, sheet_name=config['sheets']['programacion'])
    df_raw = limpiar_cabeceras(df_raw)

    # 3. Filtrado por Soporte Académico
    soportes_val = config['filtros_reporte']['soportes']
    df_raw = df_raw[df_raw['SOPORTE'].isin(soportes_val)].copy()

    # 4. Estandarización de Fechas y Creación de ID Único
    if 'FECHAS' in df_raw.columns:
        df_raw['FECHAS'] = pd.to_datetime(df_raw['FECHAS'], errors='coerce')
    
    def crear_id(row):
        try:
            p = str(int(float(row['PERIODO'])))
            n = str(int(float(row['NRC']))).zfill(4)
            return f"{p}.{n}"
        except:
            return "0.0000"

    df_raw['ID'] = df_raw.apply(crear_id, axis=1)

    # ---------------------------------------------------------
    # 5. CÁLCULO DE FECHAS EXTREMAS (La razón del Merge)
    # ---------------------------------------------------------
    # Agrupamos todas las sesiones para hallar el inicio y fin real del curso
    df_fechas = df_raw.groupby('ID')['FECHAS'].agg(['min', 'max']).reset_index()
    df_fechas.columns = ['ID', 'FECHA_INICIO', 'FECHA_FIN']

    df_fechas['FECHA_INICIO'] = pd.to_datetime(df_fechas['FECHA_INICIO']).dt.normalize()
    df_fechas['FECHA_FIN'] = pd.to_datetime(df_fechas['FECHA_FIN']).dt.normalize()

    # 6. Preparación de la Dimensión (Deduplicación)
    col_map = mappings['programas_mappings']['columns']
    df = df_raw.drop_duplicates(subset=['ID'], keep='last').copy()
    df = df.rename(columns=col_map)
    
    # Columna calculada para nombres de programa completos
    df['PROGRAMA_COMPLETO'] = df['PROGRAMA_NOMBRE'].astype(str) + " - " + df['GRUPO'].astype(str)

    # 7. CRUCE: Pegamos las fechas calculadas a nuestra lista única de programas
    df = df.merge(df_fechas, on='ID', how='left')

    # ---------------------------------------------------------
    # 8. LÓGICA DE NEGOCIO Y LIMPIEZA FINAL
    # ---------------------------------------------------------
    # Determinamos el estado actual del programa basado en el día de hoy
    hoy = pd.Timestamp.now().normalize()
    df['ESTADO_PROGRAMA'] = 'ACTIVO'
    df.loc[hoy > df['FECHA_FIN'], 'ESTADO_PROGRAMA'] = 'CULMINÓ'
    df.loc[hoy < df['FECHA_INICIO'], 'ESTADO_PROGRAMA'] = 'POR INICIAR'

    # Limpieza de texto usando tu módulo centralizado
    text_cols = mappings['programas_mappings']['text_columns']
    df = limpiar_texto_general(df, text_cols)

    # ---------------------------------------------------------
    # 9. EXPORTACIÓN Y FORMATO
    # ---------------------------------------------------------
    ruta_salida = Path(config['paths']['output']) / config['files']['dim_programas']
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    
    # Orden final según el diccionario de mapeos
    orden = mappings['programas_mappings']['column_order']
    df = df[orden] 
    
    df.to_excel(ruta_salida, index=False)
    aplicar_formato_excel(ruta_salida)
    
    print(f"📊 Total de Programas únicos procesados: {len(df)}")

if __name__ == "__main__":
    dimension_programas()