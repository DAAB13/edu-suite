import pandas as pd
from datetime import datetime
from pathlib import Path
from rich.console import Console
# Importamos la configuración y tu herramienta de limpieza
from src.core.config_loader import config, BASE_DIR
from src.core.limpieza import estandarizar_id

console = Console()

# 1. Definimos la ruta usando lo que configuraste en settings.yaml
# Accedemos a '00_data' y al nombre 'repro_log.csv'
LOG_PATH = BASE_DIR / config['paths']['data'] / config['files']['reprogramacion_log']

def registrar_reprogramacion(id_clase: str, fecha_clase: str, detalle: str):
    """
    Guarda una nueva fila en el log de reprogramaciones.
    id_clase: El NRC o ID (ej: 202401.1020)
    fecha_clase: Cuándo era la clase (DD/MM/YYYY)
    detalle: Qué pasó (ej: 'Docente con problemas de conexión')
    """
    try:
        # 2. Asegurar que la carpeta exista antes de intentar guardar
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 3. Limpiamos el ID con tu función centralizada
        id_limpio = estandarizar_id(id_clase)
        
        # 4. Creamos el diccionario con la estructura que definimos
        nueva_fila = {
            "FECHA_REGISTRO": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ID": id_limpio,
            "FECHA_CLASE": fecha_clase,
            "DETALLE": detalle
        }
        
        # Convertimos a DataFrame para usar la potencia de pandas
        df = pd.DataFrame([nueva_fila])
        
        # 5. Guardado Inteligente (Append)
        # Si el archivo no existe, escribe cabeceras. Si existe, solo añade la fila.
        header_necesario = not LOG_PATH.exists()
        df.to_csv(LOG_PATH, mode='a', index=False, header=header_necesario, encoding='utf-8')
        
        console.print(f"[bold green]✔[/bold green] Reprogramación registrada para ID: [yellow]{id_limpio}[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red]✘ Error al guardar en el log:[/bold red] {e}")