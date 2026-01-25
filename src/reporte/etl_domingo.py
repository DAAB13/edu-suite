import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.core.config_loader import config, BASE_DIR
from src.core.limpieza import estandarizar_id

def procesar_datos_semana():
    # ... (Mantenemos las rutas y la carga inicial de df_fact y df_dim) ...
    folder_out = BASE_DIR / config['paths']['output']
    path_fact = folder_out / config['files']['fact_programacion']
    path_dim = folder_out / config['files']['dim_programas']
    path_docentes = folder_out / config['files']['dim_docentes'] # <--- NUEVA RUTA
    path_log = BASE_DIR / config['paths']['data'] / config['files']['reprogramacion_log']

    df_fact = pd.read_excel(path_fact)
    df_dim = pd.read_excel(path_dim)
    df_doc = pd.read_excel(path_docentes) # <--- CARGAMOS DOCENTES

    # Aseguramos IDs limpios
    df_fact['ID'] = df_fact['ID'].apply(estandarizar_id)
    df_dim['ID'] = df_dim['ID'].apply(estandarizar_id)

    # 1. FILTRO DE FECHAS (Semana Actual)
    hoy = datetime.now()
    inicio_semana = (hoy - timedelta(days=hoy.weekday())).replace(hour=0, minute=0, second=0)
    fin_semana = (inicio_semana + timedelta(days=6)).replace(hour=23, minute=59, second=59)
    df_fact['FECHA'] = pd.to_datetime(df_fact['FECHA'])
    df_semana = df_fact[(df_fact['FECHA'] >= inicio_semana) & (df_fact['FECHA'] <= fin_semana)].copy()

    # 2. ENRIQUECIMIENTO: Pegamos Nombre del Programa
    df_reporte = df_semana.merge(df_dim[['ID', 'PROGRAMA_NOMBRE']], on='ID', how='left')

    # 3. ENRIQUECIMIENTO: Pegamos Nombre del Docente
    # Usamos CODIGO_BANNER para traer el NOMBRE_COMPLETO
    df_reporte = df_reporte.merge(df_doc[['CODIGO_BANNER', 'NOMBRE_COMPLETO']], on='CODIGO_BANNER', how='left')
    # Renombramos a 'DOCENTE' para cumplir con tu mappings.yaml
    df_reporte = df_reporte.rename(columns={'NOMBRE_COMPLETO': 'DOCENTE'})

    # 4. RECONSTRUCCIÓN DE HORARIO (De '19:00' a '19:00 - 22:00')
    df_reporte['HORARIO'] = df_reporte['HORA_INICIO'].astype(str) + " - " + df_reporte['HORA_FIN'].astype(str)

    # 5. CRUCE CON BITÁCORA (Tus notas manuales)
    if path_log.exists():
        df_log = pd.read_csv(path_log, dtype={'ID': str})
        df_log['ID'] = df_log['ID'].apply(estandarizar_id)
        df_log['FECHA_CLASE'] = pd.to_datetime(df_log['FECHA_CLASE'], dayfirst=True)
        df_reporte = df_reporte.merge(
            df_log[['ID', 'FECHA_CLASE', 'DETALLE']], 
            left_on=['ID', 'FECHA'], right_on=['ID', 'FECHA_CLASE'], how='left'
        )
    else:
        df_reporte['DETALLE'] = ""

    # Rellenamos nulos para evitar errores visuales
    df_reporte['DETALLE'] = df_reporte['DETALLE'].fillna("")
    df_reporte['PROGRAMA_NOMBRE'] = df_reporte['PROGRAMA_NOMBRE'].fillna("SIN PROGRAMA")

    # 6. CÁLCULO DE MÉTRICAS
    metrics = {
        "dictadas": len(df_reporte[df_reporte['ESTADO_CLASE'] == 'DICTADA']),
        "reprogramadas": len(df_reporte[df_reporte['ESTADO_CLASE'] == 'REPROGRAMADA']),
        "total": len(df_reporte)
    }

    return df_reporte, metrics