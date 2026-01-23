import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def fact_programacion():
    print("🚀 Iniciando construcción de la Fact Table de Programación...")
    # 1. Copiamos el archivo (esta vez le pasamos la llave correcta)
    copiar_archivo_onedrive('data_programacion')

    ruta = Path(config['paths']['input']) / config['files']['data_programacion']
    hoja = config['sheets']['programacion']

    print(f"🔄 Cargando datos desde '{hoja}'...")
    df_programacion = pd.read_excel(ruta, sheet_name=hoja)

    # LIMPIEZA DE CABECERAS (Blindaje contra saltos de línea \n)
    df_programacion.columns = df_programacion.columns.str.replace('\n', ' ', regex=True).str.strip()

    soportes_permitidos = config['filtros_reporte']['soportes']
    df = df_programacion[df_programacion['SOPORTE'].isin(soportes_permitidos)].copy()
    print(f"🔦 Filtro aplicado. Trabajando con {len(df)} registros de: {soportes_permitidos}")
    
    # FILTRADO Y RENOMBRADO SEGÚN MAPPING
    f_map = mappings['programacion_mappings']['columns']
    # Seleccionamos solo las que definimos en el YAML
    df = df[list(f_map.keys())].rename(columns=f_map).copy()

    # cramos la columna ID
    df['ID'] = df['PERIODO'].astype(str) + '.' + df['NRC'].astype(str)

    # FORMATEO DE DATOS
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    
    # Limpieza de Texto (Mayúsculas y espacios)
    text_cols = ['SOPORTE', 'ESTADO_CLASE', 'TIPO_SESION']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Limpieza Numérica (Horas y Tarifas)
    for col in mappings['programacion_mappings']['numeric_columns']:
        if col in df.columns:
            # Reemplazamos errores por 0 para no romper cálculos
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # EXPORTACIÓN
    ruta_salida = Path(config['paths']['output']) / config['files']['fact_programacion']

    orden = mappings['programacion_mappings']['column_order']
    df = df[orden]
    
    df.to_excel(ruta_salida, index=False)
    aplicar_formato_excel(ruta_salida)
    
    print(f"✅ Fact Table generada: {ruta_salida}")
    print(f"📊 Total de registros procesados: {len(df)}")

if __name__ == "__main__":
    fact_programacion()