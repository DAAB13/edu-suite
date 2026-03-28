import pandas as pd
from pathlib import Path
from datetime import datetime
import os
from src.core.config_loader import config
from src.core.limpieza import estandarizar_id

def obtener_datos_monitoreo():
    output_path = Path(config['paths']['output'])
    df_fact = pd.read_excel(output_path / config['files']['fact_programacion'])
    df_prog = pd.read_excel(output_path / config['files']['dim_programas'])
    df_doc = pd.read_excel(output_path / config['files']['dim_docentes'])

    df_fact['ID'] = df_fact['ID'].apply(estandarizar_id)
    df_prog['ID'] = df_prog['ID'].apply(estandarizar_id)
    df_prog = df_prog[df_prog['ESTADO_PROGRAMA'] != 'CULMINÓ'].copy()

    return df_fact, df_prog, df_doc

def obtener_agenda_diaria():
    # ... (Mantiene tu lógica actual de agenda diaria) ...
    df_fact, df_prog, df_doc = obtener_datos_monitoreo()
    hoy = datetime.now().strftime('%Y-%m-%d')
    df_fact['FECHA'] = pd.to_datetime(df_fact['FECHA']).dt.strftime('%Y-%m-%d')
    agenda = df_fact[df_fact['FECHA'] == hoy].copy()
    agenda = agenda.merge(df_prog[['ID', 'PROGRAMA_NOMBRE', 'CURSO_NOMBRE']], on='ID', how='left')
    agenda = agenda.merge(df_doc[['CODIGO_BANNER', 'NOMBRE_COMPLETO']], on='CODIGO_BANNER', how='left')
    agenda['ESTADO_CLASE'] = agenda['ESTADO_CLASE'].fillna('pendiente')
    return agenda

def procesar_resumen_progreso():
    df_fact, df_prog, df_doc = obtener_datos_monitoreo()

    # Conteos de sesiones
    dictadas = df_fact[df_fact['ESTADO_CLASE'] == 'DICTADA'].groupby('ID').size()
    repro = df_fact[df_fact['ESTADO_CLASE'] == 'REPROGRAMADA'].groupby('ID').size()
    totales = df_fact[df_fact['ESTADO_CLASE'] != 'REPROGRAMADA'].groupby('ID').size()

    resumen = pd.DataFrame({
        'DICTADAS': dictadas,
        'REPROGRAMADAS': repro,
        'TOTAL_SESIONES': totales
    }).fillna(0).reset_index()

    resumen['AVANCE'] = (resumen['DICTADAS'] / resumen['TOTAL_SESIONES']).fillna(0)

    # Gestión de Log de Anuncios
    path_log = Path(config['paths']['data']) / "anuncios_log.csv"
    enviados_set = set()
    if path_log.exists():
        df_log = pd.read_csv(path_log, sep=';', dtype={'ID': str})
        enviados_set = set(df_log[df_log['TIPO_ANUNCIO'] == 'ENCUESTA']['ID'].unique())

    # Mapeo de Docentes (Puente con Fact Table)
    mapa_docente_nrc = df_fact[['ID', 'CODIGO_BANNER']].drop_duplicates(subset=['ID'])

    # Merge Final
    columnas_prog = ['ID', 'PERIODO', 'NRC', 'PROGRAMA_NOMBRE', 'CURSO_NOMBRE', 
                    'ESTADO_PROGRAMA', 'FECHA_INICIO', 'FECHA_FIN', 'MODALIDAD']
    df_final = df_prog[columnas_prog].merge(resumen, on='ID', how='left')
    df_final = df_final.merge(mapa_docente_nrc, on='ID', how='left')
    df_final = df_final.merge(df_doc[['CODIGO_BANNER', 'NOMBRE_COMPLETO']], on='CODIGO_BANNER', how='left')

    # Lógica de Estado de Encuesta con Filtro Robusto (Fix Portugués)
    def definir_estado_encuesta(row):
        # Filtro de seguridad: Excluir Portugués (sin acento)
        prog_nombre = str(row.get('PROGRAMA_NOMBRE', '')).upper()
        if "PORTUGUES" in prog_nombre:
            return "-"
        
        if row['ID'] in enviados_set: return "ENVIADO"
        if row['AVANCE'] >= 0.50: return "PENDIENTE"
        return "-"

    df_final['ESTADO_ENCUESTA'] = df_final.apply(definir_estado_encuesta, axis=1)

    return df_final