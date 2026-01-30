import pandas as pd
from pathlib import Path
from datetime import datetime
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import console

def run():
    console.print("[bold cyan]⚙️  Iniciando Preparador de Combustible (Filtro Anti-Sufijos)...[/bold cyan]")

    RUTA_FACT = BASE_DIR / config['paths']['output'] / config['files']['fact_programacion']
    RUTA_DIM_PROG = BASE_DIR / config['paths']['output'] / config['files']['dim_programas']
    RUTA_MAPA = BASE_DIR / config['paths']['data'] / config['bot_files']['mapa_ids']
    RUTA_SALIDA = BASE_DIR / config['paths']['data'] / config['bot_files']['resumen_bot']

    try:
        # Blindaje de texto para no perder ceros finales
        df_fact = pd.read_excel(RUTA_FACT, dtype={'ID': str})
        df_dim_prog = pd.read_excel(RUTA_DIM_PROG, dtype={'ID': str})
        df_mapa = pd.read_csv(RUTA_MAPA, sep=';', encoding='latin1', dtype={'ID': str})

        df_fact_mini = df_fact[['ID', 'SOPORTE', 'FECHA']].copy()
        df_dim_mini = df_dim_prog[['ID', 'CURSO_NOMBRE', 'ESTADO_PROGRAMA']].copy()

        soporte_obj = config['filtros_reporte']['soportes'][0]
        df_mio = df_fact_mini[df_fact_mini['SOPORTE'] == soporte_obj].copy()
        df_activos = df_dim_mini[df_dim_mini['ESTADO_PROGRAMA'] == 'ACTIVO'].copy()
        
        df_merge = pd.merge(df_mio, df_activos, on='ID', how='inner')
        df_merge['FECHA'] = pd.to_datetime(df_merge['FECHA'])
        df_listos = df_merge[df_merge['FECHA'] <= datetime.now()].copy()

        df_resumen = df_listos.drop_duplicates(subset=['ID']).copy()
        df_final = pd.merge(df_resumen[['ID', 'SOPORTE', 'CURSO_NOMBRE']], 
                            df_mapa[['ID', 'ID_Interno', 'Nombre_BB']], 
                            on='ID', how='inner')

        df_final['Nombre_BB'] = df_final['Nombre_BB'].fillna(df_final['CURSO_NOMBRE'])
        RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_csv(RUTA_SALIDA, index=False, sep=';', encoding='latin1')
        
        console.print(f"[bold green]✅ Combustible ACTUALIZADO:[/bold green] {len(df_final)} cursos listos.")
    except Exception as e:
        console.print(f"[bold red]❌ Error Crítico en Preparador: {e}[/bold red]")