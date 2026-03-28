import pandas as pd
from pathlib import Path
from datetime import timedelta
from src.core.config_loader import config
from src.core.limpieza import estandarizar_id

def query_agenda_supervision():
    output_path = Path(config['paths']['output'])
    
    # Leemos ID como texto para preservar ceros
    df_fact = pd.read_excel(output_path / config['files']['fact_programacion'], dtype={'ID': str})
    df_programas = pd.read_excel(output_path / config['files']['dim_programas'], dtype={'ID': str})
    df_docentes  = pd.read_excel(output_path / config['files']['dim_docentes'])


    df_fact['ID'] = df_fact['ID'].apply(estandarizar_id)
    df_programas['ID'] = df_programas['ID'].apply(estandarizar_id)

    df_merge = df_fact.merge(df_programas[['ID', 'PROGRAMA_NOMBRE']], on='ID', how='left')
    df_merge = df_merge.merge(df_docentes[['CODIGO_BANNER', 'NOMBRE_COMPLETO']], on='CODIGO_BANNER', how='left')

    df_merge['FECHA'] = pd.to_datetime(df_merge['FECHA']).dt.normalize()
    hoy = pd.Timestamp.now().normalize()
    
    agenda_hoy = df_merge[df_merge['FECHA'] == hoy].copy()
    agenda_hoy = agenda_hoy.sort_values(by='HORA_INICIO')

    count_mañana = len(df_merge[df_merge['FECHA'] == hoy + timedelta(days=1)])
    count_pasado = len(df_merge[df_merge['FECHA'] == hoy + timedelta(days=2)])

    return agenda_hoy, count_mañana, count_pasado