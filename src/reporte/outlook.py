import win32com.client as win32
from rich.console import Console
from src.core.config_loader import config

console = Console()

def generar_kpis_html(metrics):
    """
    📊 Tarjetas KPI usando tablas para máxima compatibilidad con Outlook.
    """
    color_repro = "#C62828" if metrics['reprogramadas'] > 0 else "#7F8C8D"
    
    # Estructura de tabla fluida (2 columnas que se ajustan)
    html = f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
            <td style="padding-bottom: 20px;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="left" style="margin-right: 15px; margin-bottom: 10px;">
                    <tr>
                        <td style="background-color: #f8f9fa; border-left: 5px solid #1F4E78; padding: 15px; width: 150px; border-radius: 4px;">
                            <span style="font-family: 'Segoe UI', sans-serif; font-size: 8pt; color: #566573; text-transform: uppercase;">Sesiones Dictadas</span><br>
                            <span style="font-family: 'Segoe UI', sans-serif; font-size: 20pt; font-weight: bold; color: #1F4E78;">{metrics['dictadas']}</span>
                        </td>
                    </tr>
                </table>
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="left" style="margin-bottom: 10px;">
                    <tr>
                        <td style="background-color: #f8f9fa; border-left: 5px solid {color_repro}; padding: 15px; width: 150px; border-radius: 4px;">
                            <span style="font-family: 'Segoe UI', sans-serif; font-size: 8pt; color: #566573; text-transform: uppercase;">Reprogramaciones</span><br>
                            <span style="font-family: 'Segoe UI', sans-serif; font-size: 20pt; font-weight: bold; color: {color_repro};">{metrics['reprogramadas']}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <hr style="border: 0; border-top: 1px solid #eee; margin: 10px 0;">
    """
    return html

def generar_tabla_html(df):
    """
    🎨 Tabla con distribución proporcional para priorizar las primeras columnas.
    """
    estilos = """
    <style>
        .res-table { 
            width: 100% !important; 
            border-collapse: collapse; 
            table-layout: fixed; /* Forzamos a respetar los porcentajes definidos */
            font-family: 'Segoe UI', Calibri, sans-serif;
            font-size: 8.5pt;
        }
        .res-table th {
            background-color: #1F4E78;
            color: #ffffff;
            padding: 10px 5px;
            border: 1px solid #ffffff;
            text-align: center;
        }
        .res-table td {
            padding: 8px 5px;
            border: 1px solid #D9D9D9;
            word-wrap: break-word; /* Permite que el texto largo salte de línea */
        }
    </style>
    """
    
    html_tabla = df.to_html(index=False, classes='res-table', border=0)
    
    # --- DISTRIBUCIÓN DE ANCHOS (%) ---
    # Asignamos el 50% del total de la tabla a las dos primeras columnas
    mappings = {
        '<th>PROGRAMA_NOMBRE</th>': '<th style="width: 30%;">PROGRAMA</th>',
        '<th>CURSO_NOMBRE</th>': '<th style="width: 20%;">CURSO</th>',
        '<th>SESION</th>': '<th style="width: 6%;">SES</th>',
        '<th>PERIODO</th>': '<th style="width: 8%;">PERIODO</th>',
        '<th>NRC</th>': '<th style="width: 7%;">NRC</th>',
        '<th>FECHA</th>': '<th style="width: 9%;">FECHA</th>',
        '<th>HORARIO</th>': '<th style="width: 10%;">HORARIO</th>',
        '<th>DOCENTE</th>': '<th style="width: 15%;">DOCENTE</th>',
        '<th>ESTADO_CLASE</th>': '<th style="width: 10%;">ESTADO</th>'
    }
    
    for original, nuevo in mappings.items():
        html_tabla = html_tabla.replace(original, nuevo)

    # Colores de estado
    html_tabla = html_tabla.replace('DICTADA', '<b style="color: #2E7D32;">DICTADA</b>')
    html_tabla = html_tabla.replace('REPROGRAMADA', '<b style="color: #C62828;">REPROGRAMADA</b>')
    
    return estilos + html_tabla


def crear_borrador_outlook(texto_ia, df_semana, metrics):
    """
    📧 Ensambla el correo con un contenedor expandido para evitar compresión.
    """
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = config['reporte_domingo']['coordinador']
        mail.Subject = config['reporte_domingo']['asunto']
        
        kpis_html = generar_kpis_html(metrics)
        tabla_html = generar_tabla_html(df_semana)
        
        mail.Display()
        firma = mail.HTMLBody 
        
        # Aumentamos el max-width a 1000px para que la tabla tenga espacio de sobra
        mail.HTMLBody = f"""
        <html>
            <body style="margin:0; padding:15px; background-color: #ffffff;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td align="left">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 1100px;">
                                <tr>
                                    <td style="font-family: 'Segoe UI', sans-serif;">
                                        {kpis_html}
                                        
                                        <div style="font-size: 11pt; color: #2C3E50; line-height: 1.5; margin: 20px 0;">
                                            {texto_ia.replace('\\n', '<br>')}
                                        </div>
                                        
                                        <p style="margin-bottom: 10px; font-size: 10pt;"><strong>Detalle de sesiones de la semana:</strong></p>
                                        
                                        <div style="width: 100%;">
                                            {tabla_html}
                                        </div>
                                        
                                        <br>
                                        {firma}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mail.Save()
        console.print("[bold green]✉️ ¡Borrador expandido generado correctamente![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error en Outlook: {e}[/bold red]")