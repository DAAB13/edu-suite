import shutil
from src.core.config_loader import config
from pathlib import Path

def copiar_archivo_onedrive(nombre_archivo_key):
  origen = config['paths']['source_onedrive']
  destino = config['paths']['input']
  nombre_archivo = config['files'][nombre_archivo_key]
  # converimos la ruta en objeto path
  ruta_origen = Path(origen) / nombre_archivo
  ruta_destino = Path(destino) / nombre_archivo

  ruta_destino.parent.mkdir(parents=True, exist_ok=True) # aseguramos que la carpeta destino exista
  try:
    shutil.copy2(ruta_origen, ruta_destino)
  except Exception as e:
    print(f"❌ Falló la copia: {e}")

if __name__ == '__main__':
  copiar_archivo_onedrive('data_docentes') # archivo de prueba