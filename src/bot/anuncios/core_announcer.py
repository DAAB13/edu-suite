import time
import base64 # Importante para la nueva técnica
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import log_accion, log_exito, log_error, log_alerta

def asegurar_log_existe():
    PATH_DATA = BASE_DIR / config['paths']['data']
    PATH_LOG = PATH_DATA / config['files'].get('anuncios_log', "anuncios_log.csv")
    PATH_DATA.mkdir(parents=True, exist_ok=True)
    if not PATH_LOG.exists():
        df_init = pd.DataFrame(columns=['ID', 'FECHA_ENVIO', 'TIPO_ANUNCIO'])
        df_init.to_csv(PATH_LOG, index=False, sep=';')

def preparar_mensaje_html(datos_curso):
    """Mantiene compatibilidad con survey_bot.py"""
    PATH_TEMPLATE_SURVEY = BASE_DIR / "src/bot/anuncios/encuesta_template.html"
    with open(PATH_TEMPLATE_SURVEY, 'r', encoding='utf-8') as f:
        template = f.read()
    link_encuesta = config.get('announcements', {}).get('survey_link', "N/A")
    return template.format(
        PERIODO=str(datos_curso.get('PERIODO', 'N/A')),
        CURSO_NOMBRE=datos_curso.get('CURSO_NOMBRE', 'N/A'),
        NRC=str(datos_curso.get('NRC', 'N/A')),
        DOCENTE=datos_curso.get('NOMBRE_COMPLETO', 'N/A'),
        MODALIDAD=datos_curso.get('MODALIDAD', 'Virtual sincrónico'),
        LINK_ENCUESTA=link_encuesta
    )

def registrar_envio(id_nrc, tipo="ENCUESTA"):
    PATH_DATA = BASE_DIR / config['paths']['data']
    PATH_LOG = PATH_DATA / config['files'].get('anuncios_log', "anuncios_log.csv")
    nueva_fila = {'ID': str(id_nrc), 'FECHA_ENVIO': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'TIPO_ANUNCIO': tipo}
    df = pd.read_csv(PATH_LOG, sep=';', dtype={'ID': str})
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    df.to_csv(PATH_LOG, index=False, sep=';')

def publicar_anuncio(page, id_interno, titulo, html_content, solo_vista=True):
    """
    INYECCIÓN DEFINITIVA: Usa Base64 para saltar las restricciones de Blackboard Ultra.
    """
    urls = config['blackboard']['urls']
    url_crear = urls['announcement_create'].format(id_interno=id_interno)
    
    try:
        # 1. Navegación
        page.goto(url_crear, wait_until="networkidle", timeout=60000)
        
        # 2. Título
        page.wait_for_selector('input[placeholder*="título"]', state="visible")
        page.fill('input[placeholder*="título"]', titulo)
        
        # 3. Inyectar Cuerpo (Técnica de Decodificación en Navegador)
        log_accion("Inyectando contenido enriquecido (Modo Blindado)...", icono="🛡️")
        editor_sel = "#bb-editor-textbox"
        page.wait_for_selector(editor_sel, state="visible")
        
        # Convertimos el HTML a Base64 para que no se rompa por comillas o saltos de línea
        b64_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        
        page.locator(editor_sel).evaluate("""(el, contentB64) => {
            el.focus();
            // Decodificamos el contenido dentro del navegador
            const decodedHTML = atob(contentB64);
            el.innerHTML = new TextDecoder().decode(Uint8Array.from(atob(contentB64), c => c.charCodeAt(0)));
            
            // Eliminamos la clase que dice que el editor está vacío
            el.classList.remove('ql-blank');
            
            // Disparamos eventos para que Blackboard acepte el cambio
            ['input', 'change', 'blur'].forEach(ev => {
                el.dispatchEvent(new Event(ev, { bubbles: true }));
            });
        }""", b64_content)
        
        # 4. Validamos con una pulsación de tecla para activar el botón 'Publicar'
        page.locator(editor_sel).click()
        page.keyboard.press("End")
        page.keyboard.type(" ")
        page.keyboard.press("Backspace")
        
        log_exito("Contenido inyectado y validado.")

        # 5. Copia por correo
        page.click("label:has-text('Enviar una copia')")
        
        if solo_vista:
            log_alerta("MODO PREVIEW: Revisa el navegador. Si el diseño es correcto, presiona ENTER.")
            input(">>> Presiona ENTER para el siguiente curso...")
            return False
            
        page.click("button:has-text('Publicar')")
        return True
    except Exception as e:
        log_error(f"Fallo en inyección: {str(e)[:50]}")
        return False