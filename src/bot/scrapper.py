from pathlib import Path
import time
import pandas as pd
import re
import xlsxwriter
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import (
    mostrar_tabla_prevuelo, log_curso_card, log_accion, 
    log_exito, log_error, log_curso_fin, log_alerta
)

def parsear_fecha_bb(texto_raw):
    meses_en = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
    try:
        match = re.search(r'([A-Za-z]+)\s+(\d+).+,\s+(\d{4})', texto_raw.replace("\n", " "))
        if match:
            mes, dia, anio = match.groups()
            return f"{int(dia):02d}/{meses_en.get(mes, '01')}/{anio}"
    except: return texto_raw

def gestionar_login_upn(page, user_mail, user_pass):
    log_accion("Verificando sesión...", icono="🔐")
    page.goto(config['blackboard']['urls']['login'], wait_until="domcontentloaded")
    time.sleep(3)
    if "ultra" in page.url or "stream" in page.url: return True
    btn_sup = page.locator("text=Supervisores")
    if btn_sup.is_visible():
        btn_sup.click()
        sel = config['blackboard']['selectors']
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

def extraer_grabaciones_curso(page):
    """Navega y extrae links con escaneo de frames dinámico."""
    capturas = []
    try:
        boton_teams = page.get_by_text("Sala videoconferencias | Class for Teams").first
        
        # 1. Expandir carpeta si es necesario
        if not boton_teams.is_visible():
            carpeta = page.get_by_text("MIS VIDEOCONFERENCIAS").first
            if carpeta.is_visible():
                log_accion("Expandiendo carpeta MIS VIDEOCONFERENCIAS...", icono="📂")
                carpeta.click()
                time.sleep(2)
                boton_teams = page.get_by_text("Sala videoconferencias | Class for Teams").first

        if boton_teams.is_visible():
            boton_teams.click()
            log_accion("Esperando carga de Class for Teams...", icono="⏳")
            
            # 2. ESCÁNER DE FRAMES INTELIGENTE
            frame_teams = None
            # Reintentamos durante 20 segundos para superar la pantalla de "Cargando contenido..."
            for _ in range(20):
                for f in page.frames:
                    try:
                        btn_grab = f.get_by_text("Grabaciones")
                        if btn_grab.is_visible():
                            frame_teams = f
                            break
                    except: continue
                if frame_teams: break
                time.sleep(1)
            
            if frame_teams:
                log_accion("Accediendo a la pestaña Grabaciones...", icono="📑")
                frame_teams.get_by_text("Grabaciones").click()
                time.sleep(5)
                
                filas = frame_teams.locator("tr")
                for i in range(1, filas.count()):
                    cols = filas.nth(i).locator("td")
                    if cols.count() < 3: continue
                    f_raw = cols.nth(0).inner_text().split('\n')[0].strip()
                    btn_menu = cols.last.locator("button").first
                    link = "No disponible"
                    if btn_menu.is_visible():
                        btn_menu.click()
                        time.sleep(1)
                        page.evaluate("navigator.clipboard.writeText('')")
                        frame_teams.get_by_text("Copiar enlace", exact=True).first.click()
                        time.sleep(1)
                        link = page.evaluate("navigator.clipboard.readText()")
                    capturas.append({"ID": "", "fecha": parsear_fecha_bb(f_raw), "duracion": cols.nth(2).inner_text().strip(), "link_grabacion": link})
            else:
                log_error("No se detectó el entorno de grabaciones (Iframe no cargó).")
        return capturas
    except Exception as e:
        log_error(f"Error en extracción: {e}")
        return capturas

def run():
    load_dotenv(BASE_DIR / ".env")
    PATH_COMBUSTIBLE = BASE_DIR / config['paths']['data'] / config['bot_files']['resumen_bot']
    PATH_LOG_EXCEL = BASE_DIR / config['paths']['data'] / config['bot_files']['grabaciones_log']
    PATH_CHROME_PROFILE = BASE_DIR / config['paths']['input'] / "chrome_profile"
    URL_BASE = config['blackboard']['urls']['course_outline']

    df_historico = pd.read_excel(PATH_LOG_EXCEL, dtype={'ID': str}) if PATH_LOG_EXCEL.exists() else pd.DataFrame()
    grabaciones_conocidas = set(zip(df_historico['ID'], df_historico['fecha'])) if not df_historico.empty else set()
    df_tareas = pd.read_csv(PATH_COMBUSTIBLE, sep=';', encoding='latin1', dtype={'ID': str})
    
    mostrar_tabla_prevuelo(df_tareas)
    nuevas_capturas = []

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PATH_CHROME_PROFILE, headless=False, channel="chrome",
                args=["--start-maximized", "--disable-web-security"],
                permissions=["clipboard-read", "clipboard-write"]
            )
            page = context.pages[0]
            if gestionar_login_upn(page, os.getenv("UPN_MAIL"), os.getenv("UPN_PASS")):
                for idx, row in df_tareas.iterrows():
                    id_nrc = str(row['ID'])
                    log_curso_card(idx + 1, len(df_tareas), id_nrc, row['Nombre_BB'])
                    page.goto(URL_BASE.format(id_interno=row['ID_Interno']), wait_until="networkidle")
                    
                    sesiones = extraer_grabaciones_curso(page)
                    for s in sesiones:
                        if (id_nrc, s['fecha']) not in grabaciones_conocidas:
                            s['ID'] = id_nrc
                            nuevas_capturas.append(s)
                            log_exito(f"Nueva grabación capturada: {s['fecha']}")
                    log_curso_fin()
            context.close()
        except Exception as e:
            log_error(f"Error de navegador: {e}")

    if nuevas_capturas:
        df_final = pd.concat([df_historico, pd.DataFrame(nuevas_capturas)], ignore_index=True)
        # Guardado blindado
        writer = pd.ExcelWriter(PATH_LOG_EXCEL, engine='xlsxwriter')
        df_final.to_excel(writer, index=False, sheet_name='Sheet1')
        formato_texto = writer.book.add_format({'num_format': '@'})
        writer.sheets['Sheet1'].set_column('A:A', 20, formato_texto)
        writer.close()
        log_exito(f"🚀 Reporte actualizado con IDs protegidos.")