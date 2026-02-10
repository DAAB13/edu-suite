import pandas as pd
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from rich.live import Live
from rich.table import Table
from dotenv import load_dotenv
from src.core.config_loader import config, BASE_DIR
from src.ops.supervision import query_agenda_supervision 
from src.bot.scrapper import gestionar_login_bb 
from src.bot.ui_bot import console, log_error

def generar_tabla_war_room(progreso):
    """Dibuja el dashboard en tiempo real sin tocar el Excel maestro"""
    table = Table(title="🚀 [bold cyan]supervición diaria[/bold cyan]", border_style="bright_blue", expand=True)
    table.add_column("Hora", justify="center", style="dim")
    table.add_column("ID (NRC)", justify="center", style="cyan")
    table.add_column("Curso", style="white")
    table.add_column("Docente", style="dim")
    table.add_column("Estado de Aula", justify="center")

    for id_nrc, info in progreso.items():
        st = info['estado']
        # Colores dinámicos según el hallazgo del sensor
        color = "green" if "🟢" in st else "bold red" if "🔴" in st else "yellow" if "🔍" in st else "white"
        table.add_row(info['hora'], id_nrc, info['curso'][:40], info['docente'][:30], f"[{color}]{st}[/{color}]")
    return table

def verificar_grabacion_en_vivo(page):
    """Sensor de detección: Navega hasta Class for Teams"""
    try:
        # 1. Expandir carpeta si está cerrada
        boton_teams = page.get_by_text("Sala videoconferencias | Class for Teams").first
        if not boton_teams.is_visible():
            carpeta = page.get_by_text("MIS VIDEOCONFERENCIAS").first
            if carpeta.is_visible():
                carpeta.click()
                time.sleep(2)
                boton_teams = page.get_by_text("Sala videoconferencias | Class for Teams").first

        if boton_teams.is_visible():
            boton_teams.click()
            
            # 2. Localizar frame de grabaciones
            frame_teams = None
            for _ in range(15):
                for f in page.frames:
                    if "Grabaciones" in f.content():
                        frame_teams = f
                        break
                if frame_teams: break
                time.sleep(1)

            if not frame_teams: return "⚠️ Error Frame"

            # 3. Detectar estado 'Grabando' en la tabla
            frame_teams.get_by_text("Grabaciones").click()
            time.sleep(4) 
            
            contenido = frame_teams.locator("table").inner_text()
            
            if "Grabando" in contenido or "Recording" in contenido:
                return "🟢 DICTANDO (Grabando)"
            else:
                return "🔴 ALERTA: No detectado"
        
        return "❌ Sala no encontrada"
    except Exception as e:
        return f"❌ Error: {str(e)[:15]}"

def run():
    """Función principal que Typer llama desde edu.py"""
    load_dotenv(BASE_DIR / ".env")
    
    # 1. Carga de datos operativos
    df_hoy, _, _ = query_agenda_supervision()
    PATH_MAPA = BASE_DIR / config['paths']['data'] / config['bot_files']['mapa_ids']
    df_mapa = pd.read_csv(PATH_MAPA, sep=';', encoding='latin1', dtype={'ID': str})
    
    # Cruzamos agenda con mapa de Blackboard
    df_trabajo = pd.merge(
        df_hoy[['ID', 'HORA_INICIO', 'CURSO_NOMBRE', 'NOMBRE_COMPLETO']], 
        df_mapa[['ID', 'ID_Interno', 'Nombre_BB']], on='ID', how='inner'
    )

    progreso = {row['ID']: {'hora': row['HORA_INICIO'], 'curso': row['CURSO_NOMBRE'], 
                'docente': row['NOMBRE_COMPLETO'], 'estado': "⏳ Pendiente"} 
                for _, row in df_trabajo.iterrows()}

    # 2. Configuración de Playwright
    PATH_CHROME = BASE_DIR / config['paths']['input'] / "chrome_profile"
    URL_BASE = config['blackboard']['urls']['course_outline']

    with Live(generar_tabla_war_room(progreso), console=console, refresh_per_second=2) as live:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PATH_CHROME, headless=False, channel="chrome", args=["--start-maximized"]
            )
            page = context.pages[0]

            # Reutilizamos las credenciales del .env
            import os
            if not gestionar_login_bb(page, os.getenv("BB_MAIL"), os.getenv("BB_PASS")):
                log_error("Login fallido")
                return

            for id_nrc, info in progreso.items():
                progreso[id_nrc]['estado'] = "🔍 Verificando..."
                live.update(generar_tabla_war_room(progreso))

                # Navegación directa al curso
                id_interno = df_trabajo.loc[df_trabajo['ID'] == id_nrc, 'ID_Interno'].values[0]
                page.goto(URL_BASE.format(id_interno=id_interno), wait_until="networkidle")
                
                # Ejecutar sensor y actualizar War Room
                progreso[id_nrc]['estado'] = verificar_grabacion_en_vivo(page)
                live.update(generar_tabla_war_room(progreso))
            
            context.close()