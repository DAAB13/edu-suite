import pandas as pd
import numpy as np
import warnings
from pathlib import Path

# --- IMPORTACIONES DE TU PROYECTO ---
from src.core.funciones import copiar_archivo_onedrive
from src.core.formateador import aplicar_formato_excel
from src.core.config_loader import config, mappings
# Importamos tus herramientas de limpieza
from src.core.limpieza import limpiar_cabeceras, limpiar_texto_general

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def fact_programacion():
    """
    📅 PROCESO ETL: FACT TABLE DE PROGRAMACIÓN
    Crea el registro detallado de todas las sesiones de clase programadas.
    """
    # 1. Sincronización: Traemos el archivo de programación desde OneDrive
    copiar_archivo_onedrive('data_programacion')
    ruta = Path(config['paths']['input']) / config['files']['data_programacion']
    
    # 2. Carga y Limpieza de Cabeceras
    df = pd.read_excel(ruta, sheet_name=config['sheets']['programacion'])
    df = limpiar_cabeceras(df)

    # 3. Mapeo de Columnas según estándar
    f_map = mappings['programacion_mappings']['columns']
    df = df.rename(columns=f_map)

    # 4. Filtrado por Soporte Académico (Solo lo que te corresponde a ti)
    soportes_val = config['filtros_reporte']['soportes']
    df = df[df['SOPORTE'].isin(soportes_val)].copy()

    # ---------------------------------------------------------
    # 5. CREACIÓN DE ID UNIFICADO (PERIODO.NRC)
    # ---------------------------------------------------------
    # Aseguramos que el NRC tenga 4 cifras (ej. 1010) para mantener la precisión
    def f_limpiar_nrc(v):
        try: return str(int(float(v))).zfill(4)
        except: return "0000"
        
    def f_limpiar_per(v):
        try: return str(int(float(v)))
        except: return "0"

    df['ID'] = df['PERIODO'].apply(f_limpiar_per) + "." + df['NRC'].apply(f_limpiar_nrc)

    # 6. PROCESAMIENTO DE FECHAS
    if 'FECHA' in df.columns:
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    
    # ---------------------------------------------------------
    # 7. PROCESAMIENTO DE HORARIOS (Inicio y Fin)
    # ---------------------------------------------------------
    if 'HORARIO' in df.columns:
        # Dividimos el rango '07:30 PM - 09:00 PM' en dos partes
        horarios = df['HORARIO'].astype(str).str.split('-', n=1, expand=True)
        h_inicio_raw = horarios[0].str.strip()
        
        # Convertimos a formato 24h (19:30) para facilitar el ordenamiento
        df['HORA_INICIO'] = pd.to_datetime(h_inicio_raw, format='%I:%M %p', errors='coerce').dt.strftime('%H:%M').fillna("00:00")
        
        if horarios.shape[1] > 1:
            h_fin_raw = horarios[1].str.strip()
            df['HORA_FIN'] = pd.to_datetime(h_fin_raw, format='%I:%M %p', errors='coerce').dt.strftime('%H:%M').fillna("00:00")
        else:
            df['HORA_FIN'] = "00:00"

    # ---------------------------------------------------------
    # 8. LÓGICA DE ESTADO DE CLASE
    # ---------------------------------------------------------
    hoy = pd.Timestamp.now().normalize()
    
    # Limpieza de la columna estado
    df['ESTADO_CLASE'] = df['ESTADO_CLASE'].astype(str).str.strip().str.upper().replace('NAN', '')
    
    # Si la clase es hoy y no tiene estado, la marcamos como PENDIENTE
    cond_vacio = (df['ESTADO_CLASE'] == '')
    df.loc[cond_vacio & (df['FECHA'].dt.date == hoy.date()), 'ESTADO_CLASE'] = 'PENDIENTE'
    
    # 9. Limpieza final de textos (Enlaces, Sesiones, etc.)
    # No incluimos columnas numéricas aquí para evitar convertirlas a string innecesariamente
    cols_a_limpiar = ['SESION', 'TIPO_SESION', 'ESTADO_CLASE', 'SOPORTE']
    df = limpiar_texto_general(df, cols_a_limpiar)

    # ---------------------------------------------------------
    # 10. EXPORTACIÓN Y FORMATO
    # ---------------------------------------------------------
    ruta_salida = Path(config['paths']['output']) / config['files']['fact_programacion']
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    
    # Seleccionamos y ordenamos columnas finales
    orden = mappings['programacion_mappings']['column_order']
    
    df[orden].to_excel(ruta_salida, index=False)
    aplicar_formato_excel(ruta_salida)
    
    print(f"✅ Fact Table: Generada correctamente.")

if __name__ == "__main__":
    fact_programacion()