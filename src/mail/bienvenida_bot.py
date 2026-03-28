import pandas as pd
from pathlib import Path
from rich.console import Console
from src.core.config_loader import config, BASE_DIR
from src.comns.outlook import enviar_correo_base

console = Console()

def ejecutar_envio_bienvenidas(preview=True):
    # 1. CARGA DE DATOS
    df_fact = pd.read_excel(BASE_DIR / config['paths']['output'] / config['files']['fact_programacion'])
    df_dim = pd.read_excel(BASE_DIR / config['paths']['output'] / config['files']['dim_programas'])
    df_doc = pd.read_excel(BASE_DIR / config['paths']['output'] / config['files']['dim_docentes'])

    # 2. IDENTIFICAR CURSOS "POR INICIAR" EN RANGO (3 DÍAS)
    hoy = pd.Timestamp.now().normalize()
    margen = hoy + pd.Timedelta(days=config['bienvenida_comms']['dias_anticipacion'])
    
    proximos_inicios = df_dim[df_dim['ESTADO_PROGRAMA'] == 'POR INICIAR'].copy()
    proximos_inicios['FECHA_INICIO'] = pd.to_datetime(proximos_inicios['FECHA_INICIO']).dt.normalize()
    
    targets = proximos_inicios[(proximos_inicios['FECHA_INICIO'] >= hoy) & 
                            (proximos_inicios['FECHA_INICIO'] <= margen)]

    if targets.empty:
        console.print("[yellow]No se encontraron inicios pendientes para procesar.[/yellow]")
        return

    # 3. CSS PARA TABLA MODERNA (Sin doble raya, estilo profesional)
    estilo_tabla = """
    <style>
        .modern-table { border-collapse: collapse; width: 100%; font-family: Calibri, Arial, sans-serif; font-size: 9pt; }
        .modern-table th { background-color: #FFC000; color: black; padding: 8px; border: 1px solid #000; text-align: center; font-weight: bold; }
        .modern-table td { padding: 6px; border: 1px solid #000; text-align: left; }
    </style>
    """

    conteo_exito = 0
    for _, prog in targets.iterrows():
        periodo = str(prog['PERIODO'])
        nrc = str(prog['NRC'])
        nombre_curso = str(prog['CURSO_NOMBRE'])

        # Filtro estricto por Periodo + NRC
        sesiones = df_fact[(df_fact['NRC'].astype(str) == nrc) & 
                        (df_fact['PERIODO'].astype(str) == periodo)].sort_values('FECHA')
        
        if sesiones.empty:
            continue

        cod_banner = sesiones['CODIGO_BANNER'].iloc[0]
        filtro_docente = df_doc[df_doc['CODIGO_BANNER'] == cod_banner]
        
        if filtro_docente.empty:
            console.print(f"[bold red]⚠ NRC {nrc} OMITIDO:[/bold red] Docente {cod_banner} no encontrado.")
            continue
            
        docente = filtro_docente.iloc[0]
        f_inicio_str = sesiones['FECHA'].min().strftime('%d/%m/%Y')

        # Generar Tabla
        df_tabla = sesiones.copy()
        df_tabla['HORARIO'] = df_tabla['HORA_INICIO'].astype(str) + " - " + df_tabla['HORA_FIN'].astype(str)
        df_tabla['FECHAS'] = df_tabla['FECHA'].dt.strftime('%d/%m/%Y')
        df_tabla['DOCENTE'] = docente['NOMBRE_COMPLETO']
        df_tabla['CURSO'] = nombre_curso
        
        cols = ['CURSO', 'SESION', 'FECHAS', 'HORARIO', 'SOPORTE', 'DOCENTE']
        tabla_html = df_tabla[cols].to_html(index=False, classes='modern-table', border=0)

        # URL Tutoriales Proporcionada
        url_tutoriales = "https://educorpperu-my.sharepoint.com/:f:/g/personal/postgrado_upn_edu_pe/Ej-NexzBAQROqS54Bz4ACm4Bw8FYOO4hNV6tTl2VnVAnUQ?e=6M3ZAs&CT=1770847051904&OR=OWA-NT-Mail&CID=44ccf870-1f27-8569-2c11-188386a1b743"

        # SPEECH ÍNTEGRO
        html_body = f"""
        <html>
        <head>{estilo_tabla}</head>
        <body style="font-family: Calibri, sans-serif; font-size: 11pt; color: black;">
            <p>Estimado(a) docente, reciba un cordial saludo;</p>
            <p>De acuerdo con lo informado por nuestro coordinador académico, me permito solicitar su especial apoyo para el desarrollo del curso que tiene a cargo y que <b>inicia la presente semana.</b></p>
            
            <div style="margin: 15px 0;">{tabla_html}</div>

            <p><b>IMPORTANTE: Solicitamos su especial apoyo con las siguientes acciones para el cumplimiento de la correcta publicación de los contenidos:</b></p>
            
            <p>1. Subir el <b>material, el sílabo (formato PDF - obligatorio) y la bienvenida</b> a sus estudiantes del curso al aula virtual (Blackboard), Se adjunta Plantilla del PPT UPN Y la estructura de carga de material en Blackboard que debe considerar para el desarrollo de sus clases:</p>
            <ul style="list-style-type: circle;">
                <li><b>Sección anuncios:</b> Colocar el mensaje de bienvenida y otros anuncios de interés para el estudiante.</li>
                <li><b>Sección Información general del curso:</b> Colocar el silabo del curso (formato pdf), presentación del docente (ppt) y <b>CRONOGRAMA DE CLASES</b> (explicado en punto 2)</li>
                <li><b>Sección Recursos y materiales:</b> colocar toda la información del curso:
                    <ul style="list-style-type: disc;">
                        <li>PPT del curso (1 archivo mínimo por semana, separar por carpetas o especificar en el nombre del archivo a que semana corresponde.)</li>
                        <li>Recursos adicionales elaborados para el estudiante (lecturas, artículos, videos, etc.)</li>
                    </ul>
                </li>
                <li><b>Sección evaluación del curso o actividades calificadas:</b> el docente subirá la rúbrica del curso y creará actividades calificadas propias de su curso (trabajos, tareas, etc).</li>
            </ul>

            <p>2. Debe cargar un contenido con el título <b>CRONOGRAMA DE CLASES</b>. En el cual deberá colocar el cuadro de programación de las clases de su curso (fechas y horarios) tal como está detallado en el presente correo. En la parte final del cronograma se sugiere colocar mensaje indicando: "En caso de variación de fechas u horarios por motivos de fuerza mayor, se les comunicará la reprogramación correspondiente".</p>

            <p>Debe tener en cuenta que la asistencia de estudiantes podrá tomarla a través del sistema Portal Docente.</p>
            <p>Para conocer el <b>LISTADO DE ESTUDIANTES</b> de su clase, podrá visualizarlo de las siguientes formas:</p>
            <ul>
                <li><b>Intranet UPN</b> <a href="https://intranet.upn.edu.pe/WebLogin/">https://intranet.upn.edu.pe/WebLogin/</a>, entrar a ACADÉMICO y buscar Pestaña REPORTES > reportes académicos</li>
                <li><b>Aula Virtual Blackboard:</b> En la página principal de “contenido” hacia lado derecho ubicará la sección LISTA (ver a los participantes de su curso)</li>
            </ul>
            <p>Le sugerimos que pueda armar un registro auxiliar en excel para llevar nota de la participación de los estudiantes de su curso, lo que le servirá al momento de colocar las calificaciones.</p>
            
            <p>Le compartimos un enlace drive con los tutoriales de la plataforma blackboard ultra para que conozca más acerca de la plataforma: <a href="{url_tutoriales}">Tutoriales BB Ultra Docentes</a></p>
            
            <p><b>Importante:</b> Una vez culminado el curso, cuenta con un máximo de 7 días para registrar las notas en Portal Docente (Intranet UPN <a href="https://intranet.upn.edu.pe/WebLogin/">https://intranet.upn.edu.pe/WebLogin/</a>, entrar a ACADÉMICO y buscar Pestaña REGISTRO DE NOTAS). Debe tener en cuenta que, transcurrido el plazo de 7 días, el curso se elimina automáticamente de la plataforma. El proceso de carga de notas se encuentra en el Manual adjunto.</p>
            
            <p>Para temas de <b>INCIDENCIAS TÉCNICAS</b> con el sistema deberá reportarlo hacia SOPORTE TIC, para lo cual tiene los siguientes mecanismos disponibles:</p>
            <ul>
                <li>Intranet UPN <a href="https://intranet.upn.edu.pe/WebLogin/">https://intranet.upn.edu.pe/WebLogin/</a>, entrar a ACADÉMICO y buscar Pestaña HERRAMIENTAS > soporte virtual UPN</li>
                <li>Correo: <a href="mailto:mesaayudaupn@upn.edu.pe">mesaayudaupn@upn.edu.pe</a></li>
                <li>Whatsapp ArturoUPN: <a href="https://wa.me/+51951750111">https://wa.me/+51951750111</a> (sistema automático que buscará darle solución, y en caso no se logre lo contactará con un miembro del equipo de soporte)</li>
                <li>Para problemas con clave: <a href="mailto:ayudaclave@upn.edu.pe">ayudaclave@upn.edu.pe</a></li>
            </ul>

            <p style="background-color: yellow; display: inline-block; padding: 2px;">Para cualquier apoyo adicional relacionado al aspecto académico, puede comunicarse conmigo a través del presente correo</p>
            
            <p>Atentamente</p>
        </body>
        </html>
        """

        asunto = f"inicio de curso: {f_inicio_str} | {nombre_curso} - {periodo}.{nrc}"
        adjuntos = [str(BASE_DIR / config['bienvenida_comms']['folder_adjuntos'] / f) for f in config['bienvenida_comms']['archivos']]
        
        # El motor 'enviar_correo_base' debe estar configurado con mail.Save() para modo preview
        enviar_correo_base(docente['CORREO_INSTITUCIONAL'], asunto, html_body, adjuntos, preview)
        conteo_exito += 1

    console.print(f"\n[bold green]✔ ¡Éxito! {conteo_exito} borradores guardados silenciosamente en Outlook.[/bold green]")