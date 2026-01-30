import os
import re
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pathlib import Path

# Importaciones de EDU-SUITE
from src.core.config_loader import config, BASE_DIR
from rich.console import Console
from rich.panel import Panel

console = Console()

def run():
    # 1. CARGA DE CONFIGURACIÓN Y CREDENCIALES
    load_dotenv(BASE_DIR / ".env")
    USER_ID_BB = os.getenv("USER_ID_BB")
    UPN_MAIL = os.getenv("UPN_MAIL")
    UPN_PASS = os.getenv("UPN_PASS")

    # Rutas dinámicas desde settings.yaml
    ARCHIVO_SALIDA = BASE_DIR / config['paths']['data'] / config['bot_files']['mapa_ids']
    BB_URLS = config['blackboard']['urls']
    BB_SELECTORS = config['blackboard']['selectors']

    if not USER_ID_BB:
        console.print("[bold red]❌ ERROR: USER_ID_BB no encontrado en .env[/bold red]")
        return

    # 2. LOGIN Y CAPTURA DE COOKIES
    # Usamos Playwright solo para obtener la sesión inicial
    with sync_playwright() as p:
        console.print("[bold magenta]--- 🎭 INICIANDO AUTENTICACIÓN ---[/bold magenta]")
        browser = p.chromium.launch(headless=False) # Headless=False para que veas el proceso
        context = browser.new_context()
        page = context.new_page()
        page.goto(BB_URLS['login'])
        
        try:
            # Flujo de Login UPN
            btn_sup = page.locator("text=Supervisores")
            if btn_sup.is_visible():
                btn_sup.click()

            page.wait_for_selector(BB_SELECTORS['user_input'], timeout=10000)
            page.locator(BB_SELECTORS['user_input']).fill(UPN_MAIL)
            page.locator(BB_SELECTORS['pass_input']).fill(UPN_PASS)
            page.locator(BB_SELECTORS['login_btn']).click()

            # Manejo de MFA (Z Flip6)
            try:
                sel_mfa = BB_SELECTORS['mfa_submit']
                page.wait_for_selector(sel_mfa, state="visible", timeout=15000)
                page.locator(sel_mfa).click()
                console.print("[bold cyan]📲 ¡Acepta en tu celular![/bold cyan]")
            except Exception: pass
            
            page.wait_for_url("**/ultra/stream", timeout=120000)
            console.print("[bold green]✅ Acceso concedido.[/bold green]")
            
            # Extraemos las cookies para usarlas con la librería 'requests' (más rápido que navegar)
            cookies = context.cookies()
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            browser.close()
        except Exception as e:
            console.print(f"[red]Error en login: {e}[/red]")
            return

    # 3. CONSUMO DE API DE BLACKBOARD
    # Construimos la URL inyectando tu USER_ID_BB
    url_api = BB_URLS['api_memberships'].format(user_id=USER_ID_BB)
    headers = {"Cookie": cookie_string, "User-Agent": "Mozilla/5.0"}

    try:
        with console.status("[bold cyan]📡 Descargando mapa de cursos...", spinner="earth"):
            response = requests.get(url_api, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            lista_cursos = []
            results = data.get('results', [])

            for item in results:
                curso_obj = item.get('course', {})
                nombre_full = curso_obj.get('name', '')
                
                # Regex para extraer el NRC (ej: 202401.1005)
                match = re.search(r'(\d{6}\.\d{4})', nombre_full)
                id_nrc = match.group(1) if match else "N/A"

                if curso_obj.get('id'): 
                    lista_cursos.append({
                        "ID": id_nrc, # Este es tu ID de EDU-SUITE
                        "Nombre_BB": nombre_full,
                        "ID_Interno": curso_obj.get('id'), # Este lo necesita el BOT
                        "ID_Visible": curso_obj.get('courseId')
                    })

            if lista_cursos:
                # Aseguramos que la carpeta exista
                ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)
                
                df = pd.DataFrame(lista_cursos)
                # Guardamos usando el separador configurado
                df.to_csv(ARCHIVO_SALIDA, index=False, sep=config['files'].get('separador_alertas_csv', ';'), encoding='latin1')
                
                console.print(Panel(f"🔹 Cursos mapeados: {len(df)}\n💾 Guardado en: {ARCHIVO_SALIDA}", 
                                    title="✅ MAPA ACTUALIZADO", border_style="green"))
            else:
                console.print("[bold red]❌ No se extrajo data de cursos.[/bold red]")
        else:
            console.print(f"[bold red]❌ Error API ({response.status_code})[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Error crítico: {e}[/bold red]")