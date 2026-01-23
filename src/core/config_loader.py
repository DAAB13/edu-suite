import yaml
from pathlib import Path

# Definimos la raíz del proyecto (subimos de 'core' y luego de 'src')
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# rutas config yaml
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"
MAPPINGS_PATH = BASE_DIR / "config" / "mappings.yaml"

def load_config(path):
    """Lee el YAML y lo devuelve como un diccionario de Python."""
    if not path.exists():
        raise FileNotFoundError(f"Error crítico: No encontré el archivo en {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
# Al crear esta variable aquí, otros archivos pueden importarla directamente
config = load_config(CONFIG_PATH)
mappings = load_config(MAPPINGS_PATH)