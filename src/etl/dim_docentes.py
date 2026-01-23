import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def dimension_docentes():  
  print("🚀 Iniciando actualización de datos desde OneDrive...")
  copiar_archivo_onedrive('data_docentes')

  ruta = Path(config['paths']['input']) / config['files']['data_docentes']
  
  #--------------------------
  # HOJA DOCENTES ACTIVOS
  #--------------------------
  hoja_docentes_activos = config['sheets']['docentes_activos']
  print(f"🔄 Cargando hoja '{hoja_docentes_activos}'...")
  df_docentes_activos = pd.read_excel(ruta, sheet_name=hoja_docentes_activos)

  col_map = mappings['docentes_mappings']['columns'] # traemos el mapa de yaml
  df = df_docentes_activos[list(col_map.keys())].rename(columns=col_map).copy() # renombramos las columnas con mappings


  #--------------------------
  # HOJA RUT
  #--------------------------
  hoja_rut = config['sheets']['rut']
  print(f"🔄 Cargando hoja '{hoja_rut}'...")
  df_rut = pd.read_excel(ruta, sheet_name=hoja_rut)

  col_map_rut = mappings['rut_mappings']['columns'] # traemos el mapa de yaml
  df_rut = df_rut[list(col_map_rut.keys())].rename(columns=col_map_rut).copy() # renombramos las columnas con mappings


  #--------------------------
  # UNIÓN Y DEDUPLICACIÓN
  #--------------------------
  df = pd.concat([df, df_rut], ignore_index=True) ## Unimos ambas tablas. Ponemos 'df' primero para darle prioridad

  # Eliminamos duplicados por CODIGO_BANNER. 
  # keep='first' mantiene al docente que estaba en ACTIVOS y descarta el de RUT si se repite.
  df = df.drop_duplicates(subset=['CODIGO_BANNER'], keep='first')

  #--------------------------
  # LIMPIEZA DINÁMICA
  #--------------------------
  for col in mappings['docentes_mappings']['text_columns']:
    if col in df.columns: # evita que el script falle si falta la columna
      df[col] = df[col].astype(str).str.strip().str.upper()
  for col in mappings['docentes_mappings']['date_columns']:
    if col in df.columns: # evita que el script falle si falta la columna
      df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

  if 'NOMBRE_COMPLETO' in df.columns:
    print("🧹 Limpiando comas en nombres...")
    df['NOMBRE_COMPLETO'] = (
      df['NOMBRE_COMPLETO']
      .str.replace(',', '', regex=False) # Quita la coma
      .str.replace(r'\s+', ' ', regex=True) # Reduce múltiples espacios a uno solo
      .str.strip()
    )  

  # LIMPIEZA DNI
  df['DNI'] = df['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(8)

  # LIMPIEZA GÉNERO
  # Traemos el mapa del YAML
  mapa_gen = mappings['docentes_mappings']['gender_map']
  # Nota: Primero pasamos a mayúsculas para que coincida con las llaves del YAML
  df['GENERO'] = df['GENERO'].astype(str).str.upper().str.strip().replace(mapa_gen)
  # Limpieza de seguridad: Si hay algo que no sea M o F, ponemos 'ND' (No Determinado)
  df['GENERO'] = df['GENERO'].apply(lambda x: x if x in ['M', 'F'] else 'ND')

  # LIMPIEZA CELULAR
  if 'CELULAR' in df.columns:
    # .replace(r'\s+', '', regex=True) busca cualquier tipo de espacio y lo elimina
    df['CELULAR'] = df['CELULAR'].astype(str).str.replace(r'\s+', '', regex=True).str.strip()
  
  #--------------------------
  # EXPORTAR ARCHIVO
  #--------------------------
  ruta_salida = Path(config['paths']['output']) / config['files']['dim_docentes']
  ruta_salida.parent.mkdir(parents=True, exist_ok=True)
  
  orden = mappings['docentes_mappings']['column_order']
  df = df[orden]

  df.to_excel(ruta_salida, index=False)
  aplicar_formato_excel(ruta_salida)

  print(f"✅ Proceso terminado. Archivo guardado en: {ruta_salida}")

if __name__ == "__main__":
    dimension_docentes()
  
  