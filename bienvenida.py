from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from datetime import datetime

# Importaciones de tu orquestador
from src.ops.monitoreo import procesar_resumen_progreso
from src.ops.auditoria import realizar_auditoria_curso
from src.ops.supervision import query_agenda_supervision

console = Console()

def get_status_bar():
    """Crea una barra de estado inferior profesional."""
    date_str = datetime.now().strftime("%d %b %Y | %H:%M")
    status = Text.assemble(
        (" 👤 SOPORTE: ", "bold white"), ("DIEGO ", "bold yellow"),
        (" | ", "dim white"),
        ("📅 ", "white"), (f"{date_str} ", "bold cyan"),
        (" | ", "dim white"),
        ("💫 VERSIÓN: ", "bold white"), ("1.0", "bold green")
    )
    return Panel(status, style="on #1F4E78", expand=True)

def get_metrics_cards():
    """Genera tarjetas horizontales para que no se vea 'aplastado'."""
    # Extraemos data real
    df_prog = procesar_resumen_progreso()
    activos = len(df_prog[df_prog['ESTADO_PROGRAMA'] == 'ACTIVO'])
    hallazgos = realizar_auditoria_curso()
    alertas = len(hallazgos)
    df_hoy, _, _ = query_agenda_supervision()
    hoy_count = len(df_hoy)

    # Tarjeta 1: Sesiones
    c1 = Panel(
        Text(f"{hoy_count}", style="bold green", justify="center"),
        title="[bold white]SESIONES HOY[/]", border_style="green", width=25
    )
    # Tarjeta 2: Cursos
    c2 = Panel(
        Text(f"{activos}", style="bold cyan", justify="center"),
        title="[bold white]PROG. ACTIVOS[/]", border_style="cyan", width=25
    )
    # Tarjeta 3: Alertas
    color_alert = "red" if alertas > 0 else "blue"
    c3 = Panel(
        Text(f"{alertas}", style=f"bold {color_alert}", justify="center"),
        title="[bold white]ALERTAS[/]", border_style=color_alert, width=25
    )

    return Columns([c1, c2, c3], align="center")

def get_module_panel():
    """Crea la tabla de módulos sin guiones, estilo 'Command Launcher'."""
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right")
    table.add_column()

    # Estilo de botones/etiquetas
    modules = [
        ("🚀 [bold #1F4E78][ ETL ][/]", "Actualizar el modelo de datos"),
        ("🦉 [bold #1F4E78][ OPS ][/]", "Supervisión y auditoría de clases"),
        ("📶 [bold #1F4E78][ REPO ][/]", "Generar reportes los domingos con IA"),
        ("🤖 [bold #1F4E78][ BOT ][/]", "scrapping para grabaciones")
    ]

    for cmd, desc in modules:
        table.add_row(cmd, f"[white]{desc}[/]")

    return Panel(
        table, 
        title="[bold cyan] 🛠️  MÓDULOS DE ORQUESTACIÓN [/]", 
        border_style="cyan", 
        padding=(1, 2)
    )

def mostrar_bienvenida():
    console.print()
    # Header Principal
    header = Panel(
        Text("🎓 EDU SUITE: ACADEMIC MANAGEMENT SYSTEM", justify="center", style="bold white"),
        style="on #1F4E78",
        border_style="#1F4E78"
    )
    console.print(header)
    
    # Métricas en el centro
    console.print("\n[bold cyan]📊 ESTADO GLOBAL [/]")
    console.print(get_metrics_cards())
    
    # Módulos abajo
    console.print("\n")
    console.print(get_module_panel())
    
    # Footer
    console.print("\n")
    console.print(get_status_bar())

if __name__ == "__main__":
    mostrar_bienvenida()