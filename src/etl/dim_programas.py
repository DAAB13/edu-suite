import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def dimension_programas():
  print("🚀 Iniciando actualización de datos desde OneDrive...")
  copiar_archivo_onedrive('data_programacion')

  ruta = Path(config['paths']['input']) / config['files']['data_programacion']
  hoja_prog = config['sheets']['programacion']

  print(f"🔄 Cargando hoja '{hoja_prog}'...")
  df_programas = pd.read_excel(ruta, sheet_name=hoja_prog)
  df_programas.columns = df_programas.columns.str.replace('\n', ' ', regex=True).str.strip()

  # Aplicamos el filtro usando df_programas
  soportes_permitidos = config['filtros_reporte']['soportes']
  df_programas = df_programas[df_programas['SOPORTE'].isin(soportes_permitidos)].copy()
    
  print(f"🔦 Filtro aplicado. Trabajando con {len(df_programas)} registros de: {soportes_permitidos}")


  #-----------------------------------------------------------------------
  # LÓGICA DE SOPORTE
  # Convertimos FECHAS a datetime para que el orden sea cronológico real
  # Si hay errores en fechas, coerce las vuelve NaT y las pone al final
  #------------------------------------------------------------------
  if 'FECHAS' in df_programas.columns:
    df_programas['FECHAS'] = pd.to_datetime(df_programas['FECHAS'], errors='coerce')
        
    # Ordenamos por Periodo, NRC y Fecha
    # Así, la última clase (sesión 90 o la final) queda al último de cada grupo.
    print("📅 Ordenando registros para capturar el último asistente asignado...")
    df_programas = df_programas.sort_values(by=['PERIODO', 'NRC', 'FECHAS'], ascending=True)
  
  # traemos el mapa y seleccionamos columnas
  col_map = mappings['programas_mappings']['columns']
  df = df_programas[list(col_map.keys())].rename(columns=col_map).copy()

  # creamos el ID PERIODO.NRC
  df['ID'] = df['PERIODO'].astype(str) + '.' + df['NRC'].astype(str)
  
  # formato Nombre Completo del Programa
  df['PROGRAMA_COMPLETO'] = df['PROGRAMA_NOMBRE'].astype(str) + " - " + df['GRUPO'].astype(str)

  # --- NUEVA LÓGICA DE FECHAS REALES (INICIO Y FIN) ---
  print("📅 Calculando fechas reales de inicio y fin por programa...")

  # Creamos un resumen agrupado por ID para obtener el min y max
  # Usamos df_programas porque aún tiene todas las filas (sesiones)
  df_fechas = df_programas.groupby(['PERIODO', 'NRC'])['FECHAS'].agg(['min', 'max']).reset_index()
  df_fechas.columns = ['PERIODO', 'NRC', 'FECHA_INICIO', 'FECHA_FIN']

  # Creamos el ID en este resumen para poder cruzarlo
  df_fechas['ID'] = df_fechas['PERIODO'].astype(str) + '.' + df_fechas['NRC'].astype(str)
    
  # Cruzamos estos nuevos datos con nuestro DataFrame principal 'df'
  # Solo nos interesan las columnas calculadas y el ID para el cruce
  df = df.merge(df_fechas[['ID', 'FECHA_INICIO', 'FECHA_FIN']], on='ID', how='left')

  # CONVERSIÓN A DIMENSIÓN (Eliminar duplicados)
  # Usamos keep='last' para quedarnos con el SOPORTE más reciente asignado al NRC
  df = df.drop_duplicates(subset=['ID'], keep='last')

  # --- LÓGICA DE ESTADO AUTOMÁTICO ---
  print("🤖 Automatizando el estado de los programas según calendario...")
  # definimos hoy (sin hora)
  hoy = pd.Timestamp.now().normalize()
  # aplicamos la lógica de forma directa (Vectorizada)
  df.loc[hoy > df['FECHA_FIN'], 'ESTADO_PROGRAMA'] = 'CULMINÓ'
  df.loc[hoy < df['FECHA_INICIO'], 'ESTADO_PROGRAMA'] = 'POR INICIAR'
  df.loc[(hoy >= df['FECHA_INICIO']) & (hoy <= df['FECHA_FIN']), 'ESTADO_PROGRAMA'] = 'ACTIVO'

  # 4. LIMPIEZA DINÁMICA (Texto)
  for col in mappings['programas_mappings']['text_columns']:
    if col in df.columns:
      df[col] = df[col].astype(str).str.strip().str.upper()

  # 5. LIMPIEZA ESPECÍFICA (Asistente Soporte)
  if 'SOPORTE' in df.columns:
    # Quitamos comas si las hubiera y espacios dobles
    df['SOPORTE'] = (
      df['SOPORTE']
      .str.replace(',', '', regex=False)
      .str.replace(r'\s+', ' ', regex=True)
      .str.strip()
    )

  # EXPORTAR ARCHIVO
  ruta_salida = Path(config['paths']['output']) / config['files']['dim_programas']
  ruta_salida.parent.mkdir(parents=True, exist_ok=True)
  orden = mappings['programas_mappings']['column_order']
  df = df[orden]

  df.to_excel(ruta_salida, index=False)
  aplicar_formato_excel(ruta_salida)
  
  print(f"✅ Dimensión Programas generada exitosamente en: {ruta_salida}")
  print(f"📊 Total de Programas únicos: {len(df)}")

if __name__ == "__main__":
  dimension_programas()