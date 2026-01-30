import win32com.client as win32
from rich.console import Console
from src.core.config_loader import config

console = Console()

def generar_kpis_html(metrics):
    """
    📊 Crea las tarjetas métricas (Dashboard) alineadas a la izquierda.
    """
    color_repro = "#C62828" if metrics['reprogramadas'] > 0 else "#7F8C8D"
    
    html = f"""
    <div style="margin-bottom: 25px;">
        <div style="display: inline-block; width: 180px; padding: 15px; background-color: #f8f9fa; 
                    border-left: 5px solid #1F4E78; border-radius: 4px; margin-right: 15px;">
            <span style="font-family: 'Segoe UI', sans-serif; font-size: 9pt; color: #566573; text-transform: uppercase;">Sesiones Dictadas</span><br>
            <span style="font-family: 'Segoe UI', sans-serif; font-size: 22pt; font-weight: bold; color: #1F4E78;">{metrics['dictadas']}</span>
        </div>

        <div style="display: inline-block; width: 180px; padding: 15px; background-color: #f8f9fa; 
                    border-left: 5px solid {color_repro}; border-radius: 4px;">
            <span style="font-family: 'Segoe UI', sans-serif; font-size: 9pt; color: #566573; text-transform: uppercase;">Reprogramaciones</span><br>
            <span style="font-family: 'Segoe UI', sans-serif; font-size: 22pt; font-weight: bold; color: {color_repro};">{metrics['reprogramadas']}</span>
        </div>
    </div>
    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
    """
    return html

def generar_tabla_html(df):
    """
    🎨 Genera la tabla con estilos corporativos y soporte para 'apachurrado' de texto.
    """
    estilos = """
    <style>
        .report-table { 
            border-collapse: collapse; 
            width: 100%; 
            max-width: 650px; 
            table-layout: auto; /* Permite que las columnas se ajusten */
            font-family: 'Segoe UI', Calibri, sans-serif; 
            font-size: 9pt; 
            margin-top: 15px; 
        }
        .report-table th { background-color: #1F4E78; color: white; padding: 10px; border: 1px solid #ffffff; text-align: center; }
        .report-table td { border: 1px solid #D9D9D9; padding: 8px; text-align: left; word-wrap: break-word; }
        .report-table tr:nth-child(even) { background-color: #F8F9F9; }
        .status-dictada { color: #2E7D32; font-weight: bold; }
        .status-repro { color: #C62828; font-weight: bold; }
    </style>
    """
    # Convertimos a HTML y aplicamos los colores de estado
    html_tabla = df.to_html(index=False, classes='report-table')
    html_tabla = html_tabla.replace('DICTADA', '<span class="status-dictada">DICTADA</span>')
    html_tabla = html_tabla.replace('REPROGRAMADA', '<span class="status-repro">REPROGRAMADA</span>')
    
    return estilos + html_tabla

def crear_borrador_outlook(texto_ia, df_semana, metrics):
    """
    📧 Ensambla el correo final: Dashboard -> IA (Saludo Incluido) -> Tabla.
    """
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = config['reporte_domingo']['coordinador']
        mail.Subject = config['reporte_domingo']['asunto']
        
        # Preparamos los componentes
        kpis_html = generar_kpis_html(metrics)
        tabla_html = generar_tabla_html(df_semana)
        
        mail.Display()
        firma = mail.HTMLBody 
        
        # --- ENSAMBLAJE LIMPIO ---
        # 1. Quitamos el "<p>Estimado William,</p>" manual porque ya viene en {texto_ia}
        # 2. Envolvemos el texto de la IA en un div con estilo para que sea el cuerpo principal
        
        mail.HTMLBody = f"""
        <html>
            <body style="font-family: 'Segoe UI', Calibri, sans-serif; font-size: 11pt; color: #2C3E50;">
                
                {kpis_html}
                
                <div style="background-color: #ffffff; padding: 5px; border-radius: 4px;">
                    {texto_ia.replace('\\n', '<br>')}
                </div>
                
                <br>
                <strong>Resumen detallado de sesiones:</strong><br>
                
                {tabla_html}
                
                <br>
                {firma}
            </body>
        </html>
        """
        mail.Save()
        console.print("[bold green]✉️ ¡Dashboard generado y guardado en Borradores![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error en Outlook: {e}[/bold red]")