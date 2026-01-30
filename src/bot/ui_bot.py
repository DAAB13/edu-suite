from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def mostrar_tabla_prevuelo(df_input):
    """Muestra los NRCs completos (.1010)."""
    console.print("\n[bold magenta]╭── 🤖 BOT RPA: PREPARACIÓN DE VUELO ──╮[/bold magenta]")
    table = Table(title=f"📦 CARGA: {len(df_input)} CURSOS DETECTADOS", border_style="magenta", expand=True)
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("ID (Periodo.NRC)", style="bold cyan", no_wrap=True) 
    table.add_column("Curso", style="white")
    table.add_column("Estado Llave", justify="center")

    for idx, row in df_input.iterrows():
        val_id = str(row.get('ID', 'N/A'))
        if val_id.endswith('.0'): val_id = val_id[:-2]
        estado = "[green]LISTO[/green]" if str(row.get('ID_Interno', '')) != 'nan' else "[bold red]FALTA[/bold red]"
        table.add_row(str(idx + 1), val_id, str(row.get('CURSO_NOMBRE', 'N/A'))[:45], estado)
    console.print(table)

def log_curso_card(actual, total, id_nrc, nombre):
    header = Text.assemble((f" 📘 CURSO {actual}/{total} ", "bold white on blue"), (f"  NRC: {id_nrc}", "bold cyan"))
    console.print(Panel(Text(f"\n{nombre}", style="italic yellow"), title=header, border_style="bright_blue", expand=True))

def log_accion(mensaje, icono="⚙️", estilo="dim cyan"):
    console.print(f"   [bold magenta]│[/bold magenta] {icono} [{estilo}]{mensaje}[/{estilo}]")

def log_exito(mensaje):
    console.print(f"   [bold magenta]│[/bold magenta] [bold green]✅ {mensaje}[/bold green]")

def log_alerta(mensaje):
    console.print(f"   [bold magenta]│[/bold magenta] [bold yellow]⚠️ {mensaje}[/bold yellow]")

def log_error(mensaje):
    console.print(f"   [bold magenta]│[/bold magenta] [bold red]❌ {mensaje}[/bold red]")

def log_curso_fin():
    console.print("[dim white]   ╰───────────────────────────────────────────[/dim white]")