import pandas as pd
from pathlib import Path
from src.core.config_loader import config
from src.core.limpieza import estandarizar_id

def realizar_auditoria_curso():
    """
    🔍 MOTOR DE AUDITORÍA
    Revisa la Fact Table buscando errores lógicos o de digitación.
    """
    output_path = Path(config['paths']['output'])
    ruta_fact = output_path / config['files']['fact_programacion']
    
    # 1. Cargamos la data de sesiones (Fact Table)
    df = pd.read_excel(ruta_fact)
    df['ID'] = df['ID'].apply(estandarizar_id)

    # Lista donde guardaremos los hallazgos de errores
    hallazgos = []

    # ---------------------------------------------------------
    # REGLA 01: Un ID solo debe tener un único CURSO_NOMBRE
    # ---------------------------------------------------------
    # Agrupamos por ID y obtenemos los nombres únicos de curso para cada uno
    inconsistencias = df.groupby('ID')['CURSO_NOMBRE'].unique()

    for nrc_id, nombres in inconsistencias.items():
        # Si hay más de un nombre único, tenemos un problema
        if len(nombres) > 1:
            hallazgos.append({
                'ID': nrc_id,
                'Tipo': 'Nombre Contradictorio',
                'Detalle': ' / '.join(map(str, nombres)) # Une los nombres con una barra
            })

    # ---------------------------------------------------------
    # REGLA 02: Sesiones pasadas sin estado (Olvidos)
    # ---------------------------------------------------------
    hoy = pd.Timestamp.now().normalize()
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    
    # Filtramos: Fecha menor a hoy Y Estado es nulo
    olvidos = df[(df['FECHA'] < hoy) & (df['ESTADO_CLASE'].isna())]

    for _, fila in olvidos.iterrows():
        hallazgos.append({
            'ID': fila['ID'],
            'Tipo': 'Estado Faltante',
            'Detalle': f"Clase del {fila['FECHA'].strftime('%d/%m')} no fue marcada como DICTADA/REPRO"
        })

    # Retornamos una lista de diccionarios con los errores encontrados
    return hallazgos