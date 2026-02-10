import pandas as pd
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from src.core.config_loader import config, BASE_DIR
from src.bot.ui_bot import log_accion, log_exito, log_error, log_alerta

# Configuración de rutas
PATH_DATA = BASE_DIR / config['paths']['data']
PATH_LOG = PATH_DATA / "anuncios_log.csv"
PATH_TEMPLATE = BASE_DIR / "src/bot/anuncios/encuesta_template.html"

def asegurar_log_existe():
    """Crea la carpeta data y el archivo log si no existen"""
    PATH_DATA.mkdir(parents=True, exist_ok=True)
    if not PATH_LOG.exists():
        df_init = pd.DataFrame(columns=['ID', 'FECHA_ENVIO', 'TIPO_ANUNCIO'])
        df_init.to_csv(PATH_LOG, index=False, sep=';')
        log_accion("Archivo anuncios_log.csv creado automáticamente.", icono="📄")

def preparar_mensaje_html(datos_curso):
    """Lee el template e inyecta las variables con validación de nulos y limpieza de decimales"""
    with open(PATH_TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # --- FUNCIÓN DE LIMPIEZA SENIOR PARA ELIMINAR EL .0 ---
    def limpiar_id_visual(val):
        if pd.isna(val): return "N/A"
        try:
            # Si el valor tiene decimal .0 (ej: 1004.0), lo convertimos a int y luego str
            num = float(val)
            if num == int(num):
                return str(int(num))
            return str(num)
        except:
            return str(val)

    # Lógica de fallback: Si el Excel no tiene modalidad, usamos tu estándar
    modalidad_val = datos_curso.get('MODALIDAD')
    if pd.isna(modalidad_val) or str(modalidad_val).strip() == "":
        modalidad_val = "Virtual sincrónico"

    # Inyectamos los datos dinámicos usando el diccionario del curso
    return template.format(
        PERIODO=limpiar_id_visual(datos_curso.get('PERIODO')),
        CURSO_NOMBRE=datos_curso.get('CURSO_NOMBRE', 'N/A'),
        NRC=limpiar_id_visual(datos_curso.get('NRC')),
        DOCENTE=datos_curso.get('NOMBRE_COMPLETO', 'N/A'),
        MODALIDAD=modalidad_val
    )

def registrar_envio(id_nrc, tipo="ENCUESTA"):
    """Guarda la acción exitosa en el CSV asegurando que el ID se trate como texto"""
    nueva_fila = {
        'ID': str(id_nrc),
        'FECHA_ENVIO': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'TIPO_ANUNCIO': tipo
    }
    # Forzamos dtype='str' para que los NRCs no se conviertan a números decimales en el archivo
    df = pd.read_csv(PATH_LOG, sep=';', dtype={'ID': str})
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    df.to_csv(PATH_LOG, index=False, sep=';')

def publicar_anuncio(page, id_interno, titulo, html_content, solo_vista=True):
    """
    Navegación y publicación adaptada al editor Quill (#bb-editor-textbox)
    con disparo de evento para asegurar que Blackboard reconozca el mensaje.
    """
    url_crear = f"https://upn.blackboard.com/ultra/courses/{id_interno}/announcements/announcement-detail?courseId={id_interno}&mode=create"
    
    try:
        # 1. Navegación con espera de red estable
        page.goto(url_crear, wait_until="networkidle", timeout=60000)
        
        # 2. Llenar el título
        selector_titulo = 'input[placeholder*="Escriba un título"]'
        page.wait_for_selector(selector_titulo, state="visible", timeout=15000)
        page.locator(selector_titulo).fill(titulo)
        
        # 3. INYECCIÓN EN EL EDITOR REAL (ID detectado por inspección)
        log_accion("Detectado editor Quill. Inyectando y activando persistencia...", icono="🖋️")
        
        selector_editor = "#bb-editor-textbox"
        page.wait_for_selector(selector_editor, state="visible", timeout=15000)
        
        # Inyectamos el HTML y disparamos el evento 'input' para que la app reconozca el cambio
        page.locator(selector_editor).evaluate("""(el, html) => {
            el.innerHTML = html;
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }""", html_content)
        
        # 4. Check 'Enviar copia por correo'
        page.locator("label:has-text('Enviar una copia por correo')").click()
        
        # SALIDA DE SEGURIDAD (No publica si es preview)
        if solo_vista:
            log_alerta("MODO PREVIEW: Validar contenido y variables en pantalla.")
            input(">>> Revisa Blackboard. Presiona ENTER en la consola para continuar...")
            return False
            
        # 5. Publicación efectiva (Solo si preview=False en edu.py)
        page.locator("button:has-text('Publicar')").click()
        return True
        
    except Exception as e:
        log_error(f"Falla en inyección o publicación: {str(e)[:100]}")
        return False