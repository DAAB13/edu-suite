import pandas as pd
import time
import os
import tomllib
from pathlib import Path
from playwright.sync_api import sync_playwright
from rich.live import Live
from rich.table import Table
from rich.console import Console
from dotenv import load_dotenv

console = Console()
# Ajuste de BASE_DIR: Ahora estamos en src/ (un nivel arriba respecto a src/bot/)
BASE_DIR = Path(__file__).resolve().parent.parent

def log_error(mensaje): #
    console.print(f"   [bold magenta]│[/bold magenta] [bold magenta]❌ {mensaje}[/bold magenta]")

def log_alerta(mensaje):
    console.print(f"   [bold magenta]│[/bold magenta] [bold cyan]⚠️ {mensaje}[/bold cyan]")

def log_accion(mensaje, icono="⚙️", estilo="bold white"):
    console.print(f"   [bold magenta]│[/bold magenta] {icono} [{estilo}]{mensaje}[/{estilo}]")

def gestionar_login_bb(page, user_mail, user_pass, config_dict):
    log_accion("Verificando sesión...", icono="🔑")
    page.goto(config_dict['blackboard']['urls']['login'], wait_until="domcontentloaded")
    time.sleep(3)
    if "ultra" in page.url or "stream" in page.url: return True
    btn_sup = page.locator("text=Supervisores")
    if btn_sup.is_visible():
        btn_sup.click()
        sel = config_dict['blackboard']['selectors']
        page.locator(sel['user_input']).fill(user_mail)
        page.locator(sel['pass_input']).fill(user_pass)
        page.locator(sel['login_btn']).click()
        try:
            page.wait_for_selector(sel['mfa_submit'], state="visible", timeout=10000)
            page.locator(sel['mfa_submit']).click()
            log_alerta("Acepta en tu celular.")
        except: pass
        page.wait_for_url("**/ultra/stream", timeout=60000)
        return True
    return False

def generar_tabla_war_room(progreso):
    table = Table(title="🕵️ [bold cyan]SUPERVISIÓN DIARIA[/bold cyan]", border_style="magenta", expand=True)
    table.add_column("Hora", justify="center", style="bold white")
    table.add_column("ID (NRC)", justify="center", style="cyan")
    table.add_column("Curso", style="white")
    table.add_column("Docente", style="dim white")
    table.add_column("Estado de Aula", justify="center")

    for id_nrc, info in progreso.items():
        st = info['estado']
        color = "cyan" if "🟢" in st else "bold magenta" if "🔴" in st or "❌" in st else "white"
        table.add_row(str(info['hora']), str(id_nrc), str(info['curso'])[:40], str(info['docente'])[:30], f"[{color}]{st}[/{color}]")
    return table

def verificar_grabacion_en_vivo(page):
    try:
        boton_teams = page.get_by_text("Sala videoconferencias | Class for Teams").first
        if not boton_teams.is_visible():
            carpeta = page.get_by_text("MIS VIDEOCONFERENCIAS").first
            if carpeta.is_visible():
                carpeta.click()
                time.sleep(2)
                boton_teams = page.get_by_text("Sala videoconferencias | Class for Teams").first

        if boton_teams.is_visible():
            boton_teams.click()
            
            frame_teams = None
            for _ in range(15):
                for f in page.frames:
                    if "Grabaciones" in f.content():
                        frame_teams = f
                        break
                if frame_teams: break
                time.sleep(1)

            if not frame_teams: return "⚠️ Error Frame"

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
    load_dotenv(BASE_DIR / ".env")
    with open(BASE_DIR / "config.toml", "rb") as f:
        config_dict = tomllib.load(f)
    
    path_parquet = config_dict['bot_files']['parquet_file']
    df_fact = pd.read_parquet(path_parquet)
    
    hoy = pd.Timestamp.now().normalize()
    df_hoy = df_fact[pd.to_datetime(df_fact['fechas']).dt.normalize() == hoy].copy()
    df_hoy = df_hoy.sort_values(by='hora_inicio')

    PATH_MAPA = BASE_DIR / config_dict['bot_files']['mapa_ids']
    df_mapa = pd.read_csv(PATH_MAPA, sep=';', encoding='latin1', dtype={'ID': str})
    
    df_trabajo = pd.merge(
        df_hoy[['id', 'hora_inicio', 'curso', 'docente']], 
        df_mapa[['ID', 'ID_Interno', 'Nombre_BB']], left_on='id', right_on='ID', how='inner'
    )

    progreso = {row['ID']: {'hora': row['hora_inicio'], 'curso': row['curso'], 
                'docente': row['docente'], 'estado': "⏳ Pendiente"} 
                for _, row in df_trabajo.iterrows()}

    PATH_CHROME = BASE_DIR / config_dict['bot_files']['chrome_profile']
    URL_BASE = config_dict['blackboard']['urls']['course_outline']

    with Live(generar_tabla_war_room(progreso), console=console, refresh_per_second=2) as live:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PATH_CHROME, headless=False, channel="chrome", args=["--start-maximized"]
            )
            page = context.pages[0]

            if not gestionar_login_bb(page, os.getenv("BB_MAIL"), os.getenv("BB_PASS"), config_dict):
                log_error("Login fallido")
                return

            for id_nrc, info in progreso.items():
                progreso[id_nrc]['estado'] = "🔍 Verificando..."
                live.update(generar_tabla_war_room(progreso))

                id_interno = df_trabajo.loc[df_trabajo['ID'] == id_nrc, 'ID_Interno'].values[0]
                page.goto(URL_BASE.format(id_interno=id_interno), wait_until="networkidle")
                
                progreso[id_nrc]['estado'] = verificar_grabacion_en_vivo(page)
                live.update(generar_tabla_war_room(progreso))
            
            context.close()
