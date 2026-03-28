import pandas as pd
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from src.bot.scrapper import gestionar_login_bb
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import (
    log_curso_card, log_accion, log_exito, 
    log_error, log_alerta, log_curso_fin
)
from src.bot.anuncios.core_announcer import (
    asegurar_log_existe, publicar_anuncio, registrar_envio
)
from src.ops.monitoreo import procesar_resumen_progreso, extraer_cronograma_html
from src.bot import preparador # <--- Importante para la auto-carga

def run(preview: bool = True):
    load_dotenv(BASE_DIR / ".env")
    asegurar_log_existe()
    
    # 0. AUTO-CARGA DE COMBUSTIBLE (Asegura que el bot vea los cambios del Excel)
    preparador.run()
    
    PATH_COMBUSTIBLE = BASE_DIR / config['paths']['data'] / config['bot_files']['resumen_bot']
    PATH_TEMPLATE = BASE_DIR / "src/bot/anuncios/templates/bienvenida_template.html"
    PATH_CHROME_PROFILE = BASE_DIR / config['paths']['input'] / "chrome_profile"
    
    # 1. CARGA DE DATOS Y DIAGNÓSTICO
    df_progreso = procesar_resumen_progreso()
    pendientes = df_progreso[df_progreso['ESTADO_BIENVENIDA'] == 'PENDIENTE'].copy()
    
    if pendientes.empty:
        log_alerta("No hay cursos con estado 'PENDIENTE' en el monitoreo.")
        return

    try:
        df_combustible = pd.read_csv(PATH_COMBUSTIBLE, sep=';', encoding='latin1', dtype={'ID': str})
    except:
        log_error("No se pudo leer el archivo de combustible.")
        return

    # Cruce para obtener el ID_Interno (Link de Blackboard)
    df_envio = pendientes.merge(df_combustible[['ID', 'ID_Interno']], on='ID', how='inner')

    if df_envio.empty:
        log_error("Los cursos PENDIENTES no están mapeados en el mapa_ids.csv.")
        log_accion("Ejecuta 'python edu.py bot map' para sincronizar los IDs de Blackboard.", icono="💡")
        return

    log_accion(f"Iniciando proceso para {len(df_envio)} bienvenidas...", icono="🚀")

    # 2. EJECUCIÓN RPA
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PATH_CHROME_PROFILE, headless=False, channel="chrome", args=["--start-maximized"]
            )
            page = context.pages[0]

            if not gestionar_login_bb(page, os.getenv("BB_MAIL"), os.getenv("BB_PASS")):
                log_error("No se pudo validar la sesión de Blackboard.")
                return

            with open(PATH_TEMPLATE, 'r', encoding='utf-8') as f:
                template_html = f.read()

            for i, (_, row) in enumerate(df_envio.iterrows(), 1):
                id_nrc = str(row['ID'])
                log_curso_card(i, len(df_envio), id_nrc, row['CURSO_NOMBRE'])
                
                cronograma = extraer_cronograma_html(id_nrc)
                
                html_final = template_html.format(
                    DOCENTE=row['NOMBRE_COMPLETO'],
                    CURSO_NOMBRE=row['CURSO_NOMBRE'],
                    PERIODO=row['PERIODO'],
                    NRC=row['NRC'],
                    CRONOGRAMA_HTML=cronograma
                )
                
                titulo = f"¡Bienvenidos al curso: {row['CURSO_NOMBRE']}!"
                
                exito = publicar_anuncio(page, row['ID_Interno'], titulo, html_final, solo_vista=preview)
                
                if exito:
                    registrar_envio(id_nrc, tipo="BIENVENIDA")
                    log_exito("Bienvenida registrada correctamente.")
                
                log_curso_fin()
            
            context.close()
        except Exception as e:
            log_error(f"Error crítico: {e}")