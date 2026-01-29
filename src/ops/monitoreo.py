import pandas as pd
from pathlib import Path
from datetime import datetime
from src.core.config_loader import config
from src.core.limpieza import estandarizar_id

def obtener_datos_monitoreo():
    """
    🛠️ PREPARADOR DE DATOS PARA MONITOREO
    Carga y filtra la información necesaria para los reportes de progreso.
    """
    output_path = Path(config['paths']['output'])
    
    # 1. Cargamos las fuentes de datos principales (incluimos docentes para la agenda)
    df_fact = pd.read_excel(output_path / config['files']['fact_programacion'])
    df_prog = pd.read_excel(output_path / config['files']['dim_programas'])
    df_doc = pd.read_excel(output_path / config['files']['dim_docentes']) # <--- Nuevo: para nombres de profes

    # 2. Blindaje de IDs (Clean Code: usando tu función centralizada)
    df_fact['ID'] = df_fact['ID'].apply(estandarizar_id)
    df_prog['ID'] = df_prog['ID'].apply(estandarizar_id)

    # 3. FILTRO INICIAL: Solo nos interesan cursos que NO han terminado
    # Esto elimina los 'CULMINÓ' de nuestra vista principal
    df_prog = df_prog[df_prog['ESTADO_PROGRAMA'] != 'CULMINÓ'].copy()

    return df_fact, df_prog, df_doc


def obtener_agenda_diaria():
    """
    📅 GENERADOR DE AGENDA CON SEMÁFORO VISUAL
    Prepara la tabla 'ops day' con colores y estados personalizados.
    """
    df_fact, df_prog, df_doc = obtener_datos_monitoreo()
    
    # 1. Filtramos por la fecha de hoy
    hoy = datetime.now().strftime('%Y-%m-%d')
    df_fact['FECHA'] = pd.to_datetime(df_fact['FECHA']).dt.strftime('%Y-%m-%d')
    agenda = df_fact[df_fact['FECHA'] == hoy].copy()
    
    # 2. Enriquecemos con nombres de programa y docentes
    agenda = agenda.merge(df_prog[['ID', 'PROGRAMA_NOMBRE', 'CURSO_NOMBRE']], on='ID', how='left')
    agenda = agenda.merge(df_doc[['CODIGO_BANNER', 'NOMBRE_COMPLETO']], on='CODIGO_BANNER', how='left')

    # 3. LÓGICA DEL SEMÁFORO Y ESTADOS
    # Reemplazamos NaN por 'pendiente' en minúsculas
    agenda['ESTADO_CLASE'] = agenda['ESTADO_CLASE'].fillna('pendiente')

    def formatear_estado(valor):
        if valor == 'DICTADA':
            return "[bold green]DICTADA[/bold green]"
        elif valor == 'REPROGRAMADA':
            return "[bold orange3]REPROGRAMADA[/bold orange3]"
        elif valor == 'pendiente':
            # Amarillo mostaza usando código HEX (#DAA520)
            return "[#DAA520]pendiente[/#DAA520]"
        return valor

    agenda['ESTADO_FORMAT'] = agenda['ESTADO_CLASE'].apply(formatear_estado)

    # 4. Seleccionamos y renombramos columnas para la vista final
    columnas_vista = {
        'HORA_INICIO': 'Hora',
        'ID': 'ID',
        'PROGRAMA_NOMBRE': 'Programa',
        'CURSO_NOMBRE': 'Curso',
        'NOMBRE_COMPLETO': 'Docente',
        'ESTADO_FORMAT': 'Estado'
    }
    
    return agenda[list(columnas_vista.keys())].rename(columns=columnas_vista)


def procesar_resumen_progreso():
    """
    📊 CALCULADORA DE MÉTRICAS
    Transforma miles de sesiones individuales en un resumen por curso.
    """
    # 1. Obtenemos los datos limpios (ignoramos docentes aquí)
    df_fact, df_prog, _ = obtener_datos_monitoreo()

    # 2. CALCULAMOS LOS CONTEOS POR ID
    # Contamos clases dictadas
    dictadas = df_fact[df_fact['ESTADO_CLASE'] == 'DICTADA'].groupby('ID').size()
    
    # Contamos clases reprogramadas
    repro = df_fact[df_fact['ESTADO_CLASE'] == 'REPROGRAMADA'].groupby('ID').size()
    
    # Contamos el total de sesiones reales (excluyendo las reprogramadas)
    totales = df_fact[df_fact['ESTADO_CLASE'] != 'REPROGRAMADA'].groupby('ID').size()

    # 3. UNIMOS TODO EN UN SOLO RESUMEN
    resumen = pd.DataFrame({
        'DICTADAS': dictadas,
        'REPROGRAMADAS': repro,
        'TOTAL_SESIONES': totales
    }).fillna(0).reset_index()

    # 4. CALCULAMOS EL % DE AVANCE
    resumen['AVANCE'] = (resumen['DICTADAS'] / resumen['TOTAL_SESIONES']).fillna(0)

    # 5. MERGE FINAL
    columnas_prog = ['ID', 'PROGRAMA_NOMBRE', 'CURSO_NOMBRE', 'ESTADO_PROGRAMA', 'FECHA_INICIO', 'FECHA_FIN']
    df_final = df_prog[columnas_prog].merge(resumen, on='ID', how='left')

    return df_final