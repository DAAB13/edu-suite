import pandas as pd
from pathlib import Path
from src.core.config_loader import config
from src.core.limpieza import estandarizar_id

def obtener_datos_monitoreo():
    """
    🛠️ PREPARADOR DE DATOS PARA MONITOREO
    Carga y filtra la información necesaria para los reportes de progreso.
    """
    output_path = Path(config['paths']['output'])
    
    # 1. Cargamos las fuentes de datos principales
    df_fact = pd.read_excel(output_path / config['files']['fact_programacion'])
    df_prog = pd.read_excel(output_path / config['files']['dim_programas'])

    # 2. Blindaje de IDs (Clean Code: usando tu función centralizada)
    df_fact['ID'] = df_fact['ID'].apply(estandarizar_id)
    df_prog['ID'] = df_prog['ID'].apply(estandarizar_id)

    # 3. FILTRO INICIAL: Solo nos interesan cursos que NO han terminado
    # Esto elimina los 'CULMINÓ' de nuestra vista principal
    df_prog = df_prog[df_prog['ESTADO_PROGRAMA'] != 'CULMINÓ'].copy()

    return df_fact, df_prog


def procesar_resumen_progreso():
    """
    📊 CALCULADORA DE MÉTRICAS
    Transforma miles de sesiones individuales en un resumen por curso.
    """
    # 1. Obtenemos los datos limpios del paso anterior
    df_fact, df_prog = obtener_datos_monitoreo()

    # 2. CALCULAMOS LOS CONTEOS POR ID
    # Contamos clases dictadas
    dictadas = df_fact[df_fact['ESTADO_CLASE'] == 'DICTADA'].groupby('ID').size()
    
    # Contamos clases reprogramadas (para tu nueva columna)
    repro = df_fact[df_fact['ESTADO_CLASE'] == 'REPROGRAMADA'].groupby('ID').size()
    
    # Contamos el total de sesiones reales (excluyendo las reprogramadas)
    totales = df_fact[df_fact['ESTADO_CLASE'] != 'REPROGRAMADA'].groupby('ID').size()

    # 3. UNIMOS TODO EN UN SOLO RESUMEN
    resumen = pd.DataFrame({
        'DICTADAS': dictadas,
        'REPROGRAMADAS': repro,
        'TOTAL_SESIONES': totales
    }).fillna(0).reset_index() # Rellenamos con 0 si un curso no tiene dictadas o repros

    # 4. CALCULAMOS EL % DE AVANCE
    # Evitamos dividir por cero con una validación simple
    resumen['AVANCE'] = (resumen['DICTADAS'] / resumen['TOTAL_SESIONES']).fillna(0)

    # 5. MERGE FINAL: Pegamos estos cálculos a la lista de programas (ACTIVOS/POR INICIAR)
    # Aquí traemos el Nombre, Estado y Fechas de dim_programas
    columnas_prog = ['ID', 'PROGRAMA_NOMBRE', 'CURSO_NOMBRE', 'ESTADO_PROGRAMA', 'FECHA_INICIO', 'FECHA_FIN']
    df_final = df_prog[columnas_prog].merge(resumen, on='ID', how='left')

    return df_final
