import typer
import os
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns  # <--- Agregado para el nuevo layout
from rich.text import Text
from pathlib import Path
from datetime import datetime # Para fechas automáticas
# Importaciones de tu proyecto
from src.core.config_loader import mappings
from src.etl.dim_docentes import dimension_docentes
from src.etl.dim_programas import dimension_programas
from src.etl.fact_programacion import fact_programacion
from src.core.config_loader import config
from src.ops.supervision import query_agenda_supervision 
from src.ops.auditoria import realizar_auditoria_curso
from src.ops.monitoreo import procesar_resumen_progreso
from src.reporte.repro import registrar_reprogramacion
from src.reporte.etl_domingo import procesar_datos_semana
from src.reporte.agente_ia import redactar_resumen_semanal
from src.reporte.outlook import crear_borrador_outlook
from src.bot import mapa, preparador, scrapper, ui_bot


# 1. Configuración de la App Principal
app = typer.Typer(
    help="🐍 Sistema de Orquestación Operativa y RPA 😎",
    add_completion=False #Esto quita las opciones de completion
)

console = Console()

# módulos
ops_app = typer.Typer(name="ops", help="🦉 Consultas operativas")
repo_app = typer.Typer(name="repo", help="📶 Reporte domingo")
bot_app = typer.Typer(name="bot", help="🤖 Automatización de Grabaciones (RPA)")
app.add_typer(ops_app)
app.add_typer(repo_app)
app.add_typer(bot_app)


# --- COMANDO: RUN (ETL) ---
@app.command("run")
def ejecutar_todo():
    """🕹️  Modelo de datos"""
    console.print(Panel.fit("🚀 [bold blue]ACTUALIZACIÓN DEL MODELO DE DATOS[/bold blue]", border_style="blue"))
    try:
        with console.status("[bold yellow]Procesando Dimensiones...") as status:
            dimension_docentes()
            console.log("🟢 Dimensión Docentes: Actualizada")
            dimension_programas()
            console.log("🟢 Dimensión Programas: Actualizada")

        with console.status("[bold magenta]Construyendo Fact Table...") as status:
            fact_programacion()
            console.log("⭐ Fact Programación: Actualizada")

        console.print("\n[bold white on green]--- 🦄 ETL FINALIZADO ---[/bold white on green]\n")
    except Exception as e:
        console.print(f"\n[bold red]--- ❌ ERROR: {e} ---[/bold red]")


# --- COMANDO: OPS DAY (AGENDA) ---
@ops_app.command("day")
def agenda_diaria():
    """🔍 Agenda diaria"""
    fecha_hoy = pd.Timestamp.now().strftime('%d/%m')
    df_hoy, count_manana, count_pasado = query_agenda_supervision()

    # --- CHEQUEO SILENCIOSO DE CALIDAD (Movido arriba para las tarjetas) ---
    hallazgos = realizar_auditoria_curso() 
    num_alertas = len(hallazgos)

    # --- BLOQUE DE TARJETAS (ESTILO DASHBOARD) ---
    # Definimos las tarjetas con colores temáticos para hoy, mañana y pasado
    metrica_hoy = f" [bold cyan][/bold cyan][bold black on cyan]{len(df_hoy)}[/bold black on cyan][bold cyan][/bold cyan] SESIONES HOY ({fecha_hoy})"
    metrica_manana = f" [bold blue][/bold blue][bold black on blue]{count_manana}[/bold black on blue][bold blue][/bold blue] mañana"
    metrica_pasado = f" [bold blue][/bold blue][bold black on blue]{count_pasado}[/bold black on blue][bold blue][/bold blue] pasado mañana"
    
    # Tarjeta Dinámica de Alertas: Verde si es 0, Roja si hay olvidos
    color_alerta = "red" if num_alertas > 0 else "green"
    metrica_alertas = f" [bold {color_alerta}][/bold {color_alerta}][bold white on {color_alerta}]{num_alertas}[/bold white on {color_alerta}][bold {color_alerta}][/bold {color_alerta}] ALERTAS"

    # Organizamos las 4 tarjetas en la fila horizontal
    resumen_grid = Columns([metrica_hoy, metrica_manana, metrica_pasado, metrica_alertas], padding=(0, 2))

    console.print() # <--- ESTE ES EL SALTO DE LÍNEA

    # Envolvemos todo en un Panel elegante
    console.print(Panel(
        resumen_grid,
        title="🗓️  [bold white]RESUMEN DE CARGA[/bold white]",
        title_align="left",
        border_style="cyan",
        padding=(1, 2)
    ))

    # --- AVISO DE CALIDAD ---
    if hallazgos:
        console.print("[dim yellow]Ejecuta 'python edu.py ops check' para ver los detalles.[/dim yellow]")

    table = Table(
        title=f"\n👍 [bold]AGENDA DEL DÍA ({fecha_hoy})[/bold]",
        title_justify="left",
        header_style="bold green",
        border_style="green"
    )

    table.add_column("Hora", style="cyan", justify="center")
    table.add_column("ID", style="magenta")
    table.add_column("Programa", style="yellow")
    table.add_column("Curso", style="white")
    table.add_column("Docente", style="white")
    table.add_column("Estado", justify="center")

    for _, fila in df_hoy.iterrows():
        # --- LÓGICA DE ESTADO: MÁS LIMPIA Y SIN COLOR PARA PENDIENTE ---
        estado_raw = str(fila['ESTADO_CLASE'])
        
        if pd.isna(fila['ESTADO_CLASE']) or estado_raw.upper() == "NAN":
            # Blanco por defecto y en minúsculas
            estado_display = "pendiente" 
        elif estado_raw == "DICTADA":
            estado_display = "[bold green]DICTADA[/bold green]"
        elif estado_raw == "REPROGRAMADA":
            estado_display = "[bold orange3]REPROGRAMADA[/bold orange3]"
        else:
            estado_display = estado_raw
        
        table.add_row(
            str(fila['HORA_INICIO']),
            str(fila['ID']),
            str(fila['PROGRAMA_NOMBRE'])[:60],
            str(fila['CURSO_NOMBRE'])[:45],
            str(fila['NOMBRE_COMPLETO'])[:35],
            estado_display 
        )
        
    console.print(table)


# --- COMANDO: CHECK (AUDITORÍA) ---
@ops_app.command("check")
def revisar_inconsistencias():
    """🚨 Alertas """
    # Llamamos al "cerebro" que busca los errores
    hallazgos = realizar_auditoria_curso()

    # Si la lista está vacía, mostramos un mensaje de éxito
    if not hallazgos:
        console.print(Panel.fit(
            "✅ [bold green]¡TODO EN ORDEN![/bold green]\nNo se detectaron inconsistencias en la data.", 
            border_style="green"
        ))
        return

    # Si hay errores, creamos la tabla roja como en tu imagen
    table = Table(
        title="\n🚨 [bold red]ALERTAS DETECTADAS[/bold red]",
        header_style="bold red", 
        border_style="red"
    )

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Tipo", style="bold white")
    table.add_column("Detalle", style="white")

    # Llenamos la tabla con los diccionarios que devuelve auditoria.py
    for h in hallazgos:
        table.add_row(
            str(h['ID']), 
            str(h['Tipo']), 
            str(h['Detalle'])
        )

    console.print(table)
    console.print(f"\n[dim red]* Se encontraron {len(hallazgos)} error(es) que requieren atención.[/dim red]")


# --- COMANDO: STATUS (MONITOREO) ---
@ops_app.command("status")
def monitoreo_progreso():
    """📈 Programas activos"""
    # 1. Obtenemos el resumen procesado desde monitoreo.py
    df = procesar_resumen_progreso()
    
    # 2. SECCIÓN: CURSOS ACTIVOS
    df_activos = df[df['ESTADO_PROGRAMA'] == 'ACTIVO'].copy()
    
    if not df_activos.empty:
        # --- BLOQUE DE ESTADÍSTICAS (MODO DASHBOARD) ---
        total_activos = len(df_activos)
        conteo_cursos = df_activos['CURSO_NOMBRE'].value_counts() #
        
        # Creamos "tarjetas" individuales para cada curso
        etiquetas = [
            f" [bold cyan]●[/bold cyan] [bold white]{cant}[/bold white] {curso.title()[:25]}" 
            for curso, cant in conteo_cursos.items()
        ]
        
        # Organizamos las tarjetas en columnas para aprovechar el ancho
        resumen_organizado = Columns(etiquetas, padding=(0, 2), equal=False)

        # Imprimimos el panel resumen antes de la tabla
        console.print(Panel(
            resumen_organizado,
            title=f"📌 [bold cyan]{total_activos} CURSOS ACTIVOS[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(1, 2)
        ))

        # --- CONSTRUCCIÓN DE LA TABLA ---
        table = Table(
            title="🚀 [bold cyan]DETALLE CURSOS ACTIVOS[/bold cyan]",
            title_justify="left",
            header_style="bold white on blue",
            border_style="blue"
        )

        table.add_column("ID", style="magenta", no_wrap=True)
        table.add_column("Curso", style="white", width=30)
        table.add_column("Repro", justify="center", style="bold red")
        table.add_column("Progreso", justify="center")
        table.add_column("Avance %", width=20)
        table.add_column("Fin", style="dim")

        for _, fila in df_activos.iterrows():
            pct = fila['AVANCE']
            bloques = int(pct * 10)
            color_bar = "red" if pct < 0.3 else "yellow" if pct < 0.7 else "green"
            
            # Estilo de puntos moderno
            barra = f"[{color_bar}]" + "●" * bloques + "[/ " + color_bar + "]" + "○" * (10 - bloques)
            
            # Fecha limpia sin horas
            fecha_fin_txt = fila['FECHA_FIN'].strftime('%Y-%m-%d') if pd.notnull(fila['FECHA_FIN']) else "N/A"
            
            table.add_row(
                str(fila['ID']),
                str(fila['CURSO_NOMBRE'])[:30],
                str(int(fila['REPROGRAMADAS'])),
                f"{int(fila['DICTADAS'])}/{int(fila['TOTAL_SESIONES'])}",
                f"{barra} [bold]{pct:.0%}[/bold]",
                fecha_fin_txt 
            )

        console.print(table)
    else:
        console.print(Panel.fit("[yellow]No hay cursos actualmente en estado ACTIVO.[/yellow]", border_style="yellow"))

    # 3. SECCIÓN: PRÓXIMOS INICIOS
    df_proximos = df[df['ESTADO_PROGRAMA'] == 'POR INICIAR'].copy()
    
    if not df_proximos.empty:
        # Ordenamos por fecha para ver lo más urgente arriba
        df_proximos = df_proximos.sort_values(by='FECHA_INICIO')

        table_ini = Table(
            title="\n📅 [bold yellow]PREPARACIÓN: PRÓXIMOS INICIOS[/bold yellow]",
            title_justify="left",
            header_style="bold #000000 on yellow",
            border_style="yellow"
        )

        table_ini.add_column("ID", style="cyan", no_wrap=True)
        table_ini.add_column("Curso", style="white", width=40)
        table_ini.add_column("Fecha Inicio", justify="center")
        table_ini.add_column("Cuenta Regresiva", justify="right")

        # Fecha de hoy para calcular la resta
        hoy_dt = pd.Timestamp.now().normalize()

        for _, fila in df_proximos.iterrows():
            # Aseguramos que la fecha sea comparable
            fecha_ini = pd.to_datetime(fila['FECHA_INICIO']).normalize()
            dias_faltan = (fecha_ini - hoy_dt).days
            
            # Semáforo de urgencia
            if dias_faltan <= 3:
                txt_countdown = f"[bold red]¡Inicia en {dias_faltan} días![/bold red]"
            else:
                txt_countdown = f"[green]Faltan {dias_faltan} días[/green]"

            table_ini.add_row(
                str(fila['ID']),
                str(fila['CURSO_NOMBRE']).title()[:40],
                fecha_ini.strftime('%Y-%m-%d'),
                txt_countdown
            )

        console.print(table_ini)


# --- COMANDO: log (reprogramaciones csv) ---
@repo_app.command("log")
def log_repro(
    id: str = typer.Option(..., help="ID de la clase (Periodo.NRC)"),
    fecha: str = typer.Option(..., help="Fecha de la clase (DD/MM/YYYY)"),
    detalle: str = typer.Option(..., help="Motivo de la reprogramación")
):
    """📝 Registro log reprogramaciones"""
    registrar_reprogramacion(id, fecha, detalle)



@repo_app.command("preview")
def preview_reporte():
    """👀 Vista previa reporte"""
    df, kpis = procesar_datos_semana() #
    
    # 1. KPIs Rápidos en Terminal
    console.print(f"\n[bold blue]📊 ESTADO DE OPERACIONES (SEMANA ACTUAL)[/bold blue]")
    console.print(f"✅ Dictadas: {kpis['dictadas']} | ⚠️ Reprogramadas: {kpis['reprogramadas']}\n")

    # 2. GENERACIÓN DE REDACCIÓN (Ahora va primero)
    with console.status("[bold magenta]🧠 Groq redactando resumen ejecutivo...[/bold magenta]"):
        texto_ia = redactar_resumen_semanal(df, kpis)

    console.print(Panel(
        texto_ia, 
        title="[bold white]📝 BORRADOR PARA WILLIAM[/bold white]", 
        border_style="magenta",
        padding=(1, 2)
    ))

    # 3. TABLA DE SUSTENTO (Abajo como anexo)
    orden_columnas = mappings['domingo_mappings']['column_order'] #
    df_visual = df[orden_columnas].copy()
    df_visual['FECHA'] = df_visual['FECHA'].dt.strftime('%d/%m/%Y')

    table = Table(title="Sustento Técnico de Sesiones", header_style="bold white on blue", show_lines=True)
    for col in orden_columnas:
        table.add_column(col)

    for _, row in df_visual.iterrows():
        color_estado = "green" if row['ESTADO_CLASE'] == 'DICTADA' else "red"
        row_data = [str(row[c]) for c in orden_columnas]
        row_data[-1] = f"[{color_estado}]{row['ESTADO_CLASE']}[/{color_estado}]"
        table.add_row(*row_data)

    console.print(table)


@repo_app.command("mail")
def ejecutar_reporte_domingo():
    """🌅 Generar reporte outlook"""
    console.print(Panel.fit("📬 [bold cyan]INICIANDO REPORTE SEMANAL EJECUTIVO[/bold cyan]", border_style="cyan"))

    # 1. Fase de Datos (ETL)
    with console.status("[bold blue]📊 Recopilando sesiones de la semana...[/bold blue]"):
        df_completo, kpis = procesar_datos_semana() #
        
        # Filtro Senior: Solo clases Dictadas o Reprogramadas para William
        df_para_outlook = df_completo[df_completo['ESTADO_CLASE'].isin(['DICTADA', 'REPROGRAMADA'])].copy()
        
        # Aplicamos el orden de columnas del mappings.yaml
        orden = mappings['domingo_mappings']['column_order']
        df_final = df_para_outlook[orden].copy()
        
        # IMPORTANTE: Formateamos la fecha a texto solo después de haber ordenado
        df_final['FECHA'] = df_final['FECHA'].dt.strftime('%d/%m/%Y') 

    # 2. Fase de Inteligencia (IA)
    with console.status("[bold magenta]🧠 Redactando mensaje ejecutivo con Groq...[/bold magenta]"):
        texto_ia = redactar_resumen_semanal(df_completo, kpis) #

    # 3. Fase de Comunicación (Outlook)
    with console.status("[bold green]📧 Abriendo Outlook e inyectando reporte...[/bold green]"):
        crear_borrador_outlook(texto_ia, df_final, kpis)

    console.print("\n[bold white on green] ✨ ¡TODO LISTO! Revisa tu bandeja de Borradores en Outlook. [/bold white on green]\n")


@bot_app.command("map")
def bot_actualizar_mapa():
    """🗺️  Actualiza la base de IDs internos de Blackboard"""
    console.print(Panel.fit("📡 [bold magenta]ACTUALIZANDO MAPA DE CURSOS[/bold magenta]", border_style="magenta"))
    mapa.run()


@bot_app.command("sync")
def bot_flujo_completo():
    """🚀 RECOLECCIÓN INTEGRAL: Preparar -> Scrapear -> Generar Excel"""
    ui_bot.console.print(Panel("[bold cyan]🔥 INICIANDO RECOLECCIÓN DE GRABACIONES[/bold cyan]", border_style="cyan"))
    
    # 1. Preparación de datos
    with ui_bot.console.status("[bold yellow]Filtrando tus cursos del Panel V7...[/bold yellow]"):
        preparador.run()
    
    # 2. Ejecución del Scrapper
    scrapper.run()
    
    # 3. Dashboard Final (Toque Wao)
    resumen = Text.assemble(
        ("\n📊 OPERACIÓN COMPLETADA EXITOSAMENTE\n", "bold green"),
        ("Tus links han sido recolectados y ordenados por NRC.\n", "white"),
        ("\nArchivo de pegado: ", "dim"), (f"00_data/{config['bot_files']['grabaciones_log']}", "bold magenta"),
        ("\n\n[💡] Sugerencia: Filtra por NRC en el Excel para copiar bloques enteros.", "italic cyan")
    )
    
    ui_bot.console.print(Panel(resumen, title="[✨ DASHBOARD FINAL]", border_style="green", expand=True))
    ui_bot.console.print("\n[bold white on green] ✨ ¡CICLO EDU-SUITE FINALIZADO! [/bold white on green]\n")


if __name__ == "__main__":
    app()