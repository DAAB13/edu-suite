import os
import re
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pathlib import Path
import tomllib
from rich.console import Console
from rich.panel import Panel

"""Automatiza la extracción de cursos desde Blackboard.

Este módulo realiza el login en Blackboard mediante Playwright, captura
cookies de la sesión y consulta la API `api_memberships` para obtener la
lista de cursos asociados al usuario. El resultado se escribe en
`00_data/mapa_ids.csv` con delimitador `;` y encoding `latin1`.

Requisitos:
- `.env` con `USER_ID_BB`, `BB_MAIL` y `BB_PASS`.
- `config.toml` con endpoints de Blackboard y selectores de login.
"""

console = Console()
# Ajuste de BASE_DIR: Ahora estamos en src/ (un nivel arriba respecto a src/bot/)
BASE_DIR = Path(__file__).resolve().parent.parent

def run():
    # Carga de variables de entorno y configuración
    load_dotenv(BASE_DIR / ".env")
    # atrapamos las variables de entorno necesarias para el login
    USER_ID_BB = os.getenv("USER_ID_BB")
    BB_MAIL = os.getenv("BB_MAIL")
    BB_PASS = os.getenv("BB_PASS")

    # Carga de configuración desde config.toml 
    with open(BASE_DIR / "config.toml", "rb") as f:
        config = tomllib.load(f)

    ARCHIVO_SALIDA = BASE_DIR / config['bot_files']['mapa_ids']
    BB_URLS = config['blackboard']['urls']
    BB_SELECTORS = config['blackboard']['selectors']

    if not USER_ID_BB: # Validación básica de variable
        console.print("[bold magenta]❌ ERROR: USER_ID_BB no encontrado en .env[/bold magenta]")
        return # detenemos la ejecución

    with sync_playwright() as p: # iniciamos Playwright
        console.print("[bold magenta]--- 🎭 INICIANDO AUTENTICACIÓN ---[/bold magenta]")
        browser = p.chromium.launch(headless=False) # headless=False para ver el proceso de login
        context = browser.new_context() # creamos un nuevo contexto para aislar la sesión y capturar cookies
        page = context.new_page() # abrimos una nueva página en el navegador
        page.goto(BB_URLS['login']) # navegamos a la página de login de Blackboard
        
        try: 
            btn_sup = page.locator("text=Supervisores") # boton supervisores
            if btn_sup.is_visible(): # verificamos que el botón de supervisores esté visible
                btn_sup.click() # hacemos click para ir al login de supervisores

            page.wait_for_selector(BB_SELECTORS['user_input'], timeout=10000)
            page.locator(BB_SELECTORS['user_input']).fill(BB_MAIL) # llenamos el campo de email
            page.locator(BB_SELECTORS['pass_input']).fill(BB_PASS) # llenamos el campo de contraseña
            page.locator(BB_SELECTORS['login_btn']).click() 

            try:
                sel_mfa = BB_SELECTORS['mfa_submit'] # selector del botón de MFA
                page.wait_for_selector(sel_mfa, state="visible", timeout=15000) 
                page.locator(sel_mfa).click()
                console.print("[bold cyan]📲 ¡Acepta en tu celular![/bold cyan]")
            except Exception: pass 
            
            page.wait_for_url("**/ultra/stream", timeout=120000) # esperamos a que la URL cambie a la interfaz de cursos (puede tardar un poco por MFA)
            console.print("[bold cyan]✅ Acceso concedido.[/bold cyan]")
            
            cookies = context.cookies() # capturamos las cookies de la sesión para usarlas en la API
            # Convertimos las cookies a un formato de string para el header de la API
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        except Exception as e: # cualquier error durante el login se captura aquí
            console.print(f"[bold magenta]Error en login: {e}[/bold magenta]")
            return
    
    # hacemos la petición a la API de memberships usando las cookies para autenticación
    url_api = BB_URLS['api_memberships'].format(user_id=USER_ID_BB) 
    headers = {"Cookie": cookie_string, "User-Agent": "Mozilla/5.0"} 

    try:
        with console.status("[bold cyan]📡 Descargando mapa de cursos...", spinner="earth"):
            response = requests.get(url_api, headers=headers) # hacemos la petición a la API para obtener los cursos asociados al usuario
        
        if response.status_code == 200: # verificamos que la respuesta sea exitosa
            data = response.json() 
            lista_cursos = []
            results = data.get('results', [])

            for item in results: # iteramos sobre los resultados para extraer la información de cada curso
                curso_obj = item.get('course', {})
                nombre_full = curso_obj.get('name', '')
                
                match = re.search(r'(\d{6}\.\d{4})', nombre_full)
                id_nrc = match.group(1) if match else "N/A"

                if curso_obj.get('id'): 
                    lista_cursos.append({
                        "ID": id_nrc,
                        "Nombre_BB": nombre_full,
                        "ID_Interno": curso_obj.get('id'),
                        "ID_Visible": curso_obj.get('courseId')
                    })

            if lista_cursos:
                ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True) # aseguramos que la carpeta de salida exista
                df = pd.DataFrame(lista_cursos)
                df.to_csv(ARCHIVO_SALIDA, index=False, sep=';', encoding='latin1') # guardamos el resultado en un CSV con el formato requerido
                console.print(Panel(f"[bold white]🔹 Cursos mapeados: {len(df)}\n💾 Guardado en: {ARCHIVO_SALIDA}[/bold white]", 
                                    title="[bold cyan]✅ MAPA ACTUALIZADO[/bold cyan]", border_style="magenta"))
            else:
                console.print("[bold magenta]❌ No se extrajo data de cursos.[/bold magenta]")
        else:
            console.print(f"[bold magenta]❌ Error API ({response.status_code})[/bold magenta]")
    except Exception as e:
        console.print(f"[bold magenta]❌ Error crítico: {e}[/bold magenta]")
