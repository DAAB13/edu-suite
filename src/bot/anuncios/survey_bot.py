import pandas as pd
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.bot.scrapper import gestionar_login_bb
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import (
    console, log_curso_card, log_accion, log_exito, 
    log_error, log_alerta, log_curso_fin
)
from src.bot.anuncios.core_announcer import (
    asegurar_log_existe, preparar_mensaje_html, 
    publicar_anuncio, registrar_envio
)
from src.ops.monitoreo import procesar_resumen_progreso

def run(preview: bool = True):
    """
    🧠 CEREBRO DEL BOT DE ENCUESTAS (V2.1 - Coreccion de Contador y Filtros)
    Filtra cursos aptos y orquestas la ejecución en Blackboard.
    """
    load_dotenv(BASE_DIR / ".env")
    
    # 1. Preparar el entorno (Asegura que el log exista en 00_data)
    asegurar_log_existe()
    
    # 2. Cargar rutas y datos maestros
    PATH_COMBUSTIBLE = BASE_DIR / config['paths']['data'] / config['bot_files']['resumen_bot']
    PATH_LOG_ANUNCIOS = BASE_DIR / config['paths']['data'] / "anuncios_log.csv"
    PATH_CHROME_PROFILE = BASE_DIR / config['paths']['input'] / "chrome_profile"
    
    # Combustible: NRCs con sus IDs internos de Blackboard
    df_combustible = pd.read_csv(PATH_COMBUSTIBLE, sep=';', encoding='latin1', dtype={'ID': str})
    
    # Historial: ¿A quién ya le enviamos encuesta?
    df_log = pd.read_csv(PATH_LOG_ANUNCIOS, sep=';', dtype={'ID': str})
    enviados = set(df_log[df_log['TIPO_ANUNCIO'] == 'ENCUESTA']['ID'].unique())
    
    # Progreso: Obtenemos el avance actual y datos del docente
    df_progreso = procesar_resumen_progreso()

    # 3. LÓGICA DE FILTRADO Y SEGURIDAD
    # Cruzamos combustible con progreso para tener toda la data necesaria para el template
    df_merge = pd.merge(
        df_combustible, 
        df_progreso[['ID', 'AVANCE', 'PERIODO', 'NRC', 'MODALIDAD', 'NOMBRE_COMPLETO', 'PROGRAMA_NOMBRE']], 
        on='ID', 
        how='inner'
    )
    
    # Filtro Senior: Avance >= 50%, no enviado, y EXCLUIR PORTUGUES (Filtro robusto sin acentos)
    pendientes = df_merge[
        (df_merge['AVANCE'] >= 0.50) & 
        (~df_merge['ID'].isin(enviados)) &
        (~df_merge['PROGRAMA_NOMBRE'].str.contains('PORTUGUES', case=False, na=False))
    ].copy()

    if pendientes.empty:
        log_alerta("No hay encuestas pendientes por enviar (Avance < 50%, ya enviadas o son de Portugués).")
        return

    log_accion(f"Detectados {len(pendientes)} cursos aptos para encuesta.", icono="🎯")

    # 4. EJECUCIÓN DEL BOT RPA
    with sync_playwright() as p:
        try:
            # Reutilizamos tu perfil de Chrome para evitar el login manual
            context = p.chromium.launch_persistent_context(
                user_data_dir=PATH_CHROME_PROFILE, 
                headless=False, 
                channel="chrome",
                args=["--start-maximized"]
            )
            page = context.pages[0]

            # Validación de Sesión antes de iniciar la navegación
            if not gestionar_login_bb(page, os.getenv("BB_MAIL"), os.getenv("BB_PASS")):
                log_error("No se pudo validar la sesión de Blackboard. Abortando.")
                return
            
            # USO DE ENUMERATE: Para que el contador sea secuencial (1, 2, 3...)
            for i, (idx, row) in enumerate(pendientes.iterrows(), 1):
                id_nrc = str(row['ID'])
                
                # Log con el contador corregido 'i'
                log_curso_card(i, len(pendientes), id_nrc, row['Nombre_BB'])
                
                # Inyección de datos en Template
                html_final = preparar_mensaje_html(row.to_dict())
                titulo = f"Encuesta de Satisfacción Académica - {row['CURSO_NOMBRE']}"
                
                # Acción en Blackboard (Pasamos el modo preview como 'solo_vista')
                # Esta funcion en core_announcer.py ahora tiene esperas mas largas para el editor
                exito = publicar_anuncio(
                    page, 
                    row['ID_Interno'], 
                    titulo, 
                    html_final, 
                    solo_vista=preview
                )
                
                if exito:
                    registrar_envio(id_nrc)
                    log_exito(f"Encuesta enviada y registrada correctamente.")
                
                log_curso_fin()
                
            context.close()
        except Exception as e:
            log_error(f"Error crítico en survey_bot: {e}")