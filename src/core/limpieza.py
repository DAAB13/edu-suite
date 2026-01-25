import pandas as pd
import numpy as np

def limpiar_texto_general(df, columnas_texto):
    """
    🧹 LIMPIEZA INTEGRAL DE TEXTO
    ----------------------------
    Esta función recorre una lista de columnas y aplica un estandar:
    1. Convierte todo a string (evita errores de tipo).
    2. Elimina espacios sobrantes al inicio y final (strip).
    3. Transforma todo a MAYÚSCULAS para uniformidad.
    4. Reemplaza los textos 'NAN' (que a veces deja Excel) por valores nulos reales.
    """
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().replace('NAN', np.nan)
    return df

def corregir_dni(serie_dni):
    """
    🆔 FORMATEADOR DE DNI
    --------------------
    Especial para los reportes de UPN donde el DNI a veces viene con decimales (.0).
    - Elimina el '.0' si existe.
    - Asegura que siempre tenga 8 dígitos (rellena con ceros a la izquierda).
    """
    return serie_dni.astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(8)

def limpiar_celulares(serie_celular):
    """
    📱 LIMPIEZA DE TELÉFONOS
    -----------------------
    Elimina cualquier espacio en blanco que el docente haya puesto entre los números.
    Ejemplo: '999 888 777' -> '999888777'
    """
    return serie_celular.astype(str).str.replace(r'\s+', '', regex=True).str.strip()

def limpiar_cabeceras(df):
    """
    📑 LIMPIEZA DE CABECERAS
    Quita saltos de línea, espacios y pone todo en MAYÚSCULAS.
    Esto evita que el código falle si el Excel tiene "NRC " con un espacio al final.
    """
    df.columns = df.columns.str.replace('\n', ' ', regex=True).str.strip().str.upper()
    return df

def estandarizar_id(val):
    """
    🛠️ BLINDAJE DE ID (PERIODO.NRC)
    Asegura que el ID mantenga el formato 'PERIODO.XXXX'.
    Si Excel recortó los ceros (ej: .100 -> .1000), esto los restaura.
    """
    v = str(val)
    if '.' in v:
        p, n = v.split('.')
        # ljust asegura que el NRC tenga 4 dígitos hacia la derecha
        return f"{p}.{n.ljust(4, '0')}"
    return v