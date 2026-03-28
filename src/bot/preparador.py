import pandas as pd
from pathlib import Path
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import console

def run():
    console.print("[bold cyan]⚙️  Preparando lista de cursos (Bienvenidas + Grabaciones)...[/bold cyan]")

    RUTA_FACT = BASE_DIR / config['paths']['output'] / config['files']['fact_programacion']
    RUTA_DIM_PROG = BASE_DIR / config['paths']['output'] / config['files']['dim_programas']
    RUTA_MAPA = BASE_DIR / config['paths']['data'] / config['bot_files']['mapa_ids']
    RUTA_SALIDA = BASE_DIR / config['paths']['data'] / config['bot_files']['resumen_bot']

    try:
        # Carga con protección de tipos
        df_fact = pd.read_excel(RUTA_FACT, dtype={'ID': str})
        df_dim_prog = pd.read_excel(RUTA_DIM_PROG, dtype={'ID': str})
        df_mapa = pd.read_csv(RUTA_MAPA, sep=config['files'].get('separador_alertas_csv', ';'), encoding='latin1', dtype={'ID': str})

        # Obtenemos todos los IDs únicos que tienen sesiones programadas
        df_sesiones = df_fact[['ID']].drop_duplicates()

        # Filtramos programas que no han terminado
        df_fase = df_dim_prog[df_dim_prog['ESTADO_PROGRAMA'].isin(['ACTIVO', 'POR INICIAR'])].copy()
        
        # Cruce: Programas válidos con sus nombres
        df_merge = pd.merge(df_sesiones, df_fase[['ID', 'CURSO_NOMBRE']], on='ID', how='inner')

        # Cruce final con el mapa de navegación de Blackboard
        df_final = pd.merge(df_merge, df_mapa[['ID', 'ID_Interno', 'Nombre_BB']], on='ID', how='inner')

        df_final['Nombre_BB'] = df_final['Nombre_BB'].fillna(df_final['CURSO_NOMBRE'])
        
        RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_csv(RUTA_SALIDA, index=False, sep=';', encoding='latin1')
        
        console.print(f"[bold green]✅ Lista de navegación actualizada:[/bold green] {len(df_final)} cursos detectados.")
    except Exception as e:
        console.print(f"[bold red]❌ Error en Preparador: {e}[/bold red]")