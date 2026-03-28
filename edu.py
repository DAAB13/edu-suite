import typer
import time
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from pathlib import Path
from datetime import datetime

# --- CONFIGURACIÓN E IMPORTS ---
from src.core.config_loader import mappings, config, BASE_DIR
from src.etl.dim_docentes import dimension_docentes
from src.etl.dim_programas import dimension_programas
from src.etl.fact_programacion import fact_programacion

# COMUNICACIONES (Reportes y Bienvenidas)
from src.mail.reporte_semanal.etl_domingo import procesar_datos_semana
from src.mail.reporte_semanal.agente_ia import redactar_resumen_semanal
from src.mail.outlook import crear_borrador_outlook

# BOT RPA (Blackboard)
from src.bot.live import monitor 
from src.bot import mapa, preparador, scrapper, ui_bot

# 1. Instancias de la App
app = typer.Typer(help="🐍 Sistema de Orquestación Operativa y RPA 😎", add_completion=False)
mail_app = typer.Typer(name="mail", help="📫 Gestión de Correos y Reportes")
bot_app = typer.Typer(name="bot", help="🤖 Automatización de Grabaciones y RPA")

console = Console()

# ==========================================
# --- COMANDO: RUN (ETL) ---
# ==========================================
@app.command("run")
def ejecutar_todo():
    """🕹️ Actualización del modelo de datos completo"""
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


# ==========================================
# --- MÓDULO: MAIL ---
# ==========================================
@mail_app.command("sun")
def ejecutar_reporte_domingo():
    """🌅 [DOMINGOS] Generar reporte ejecutivo en Outlook"""
    console.print(Panel.fit("📬 INICIANDO REPORTE SEMANAL", border_style="cyan"))
    df_completo, kpis = procesar_datos_semana()
    df_para_outlook = df_completo[df_completo['ESTADO_CLASE'].isin(['DICTADA', 'REPROGRAMADA'])].copy()
    orden = mappings['domingo_mappings']['column_order']
    df_final = df_para_outlook[orden].copy()
    df_final['FECHA'] = df_final['FECHA'].dt.strftime('%d/%m/%Y') 
    texto_ia = redactar_resumen_semanal(df_completo, kpis)
    crear_borrador_outlook(texto_ia, df_final, kpis)
    console.print("\n[bold white on green] ✨ ¡BORRADOR LISTO EN OUTLOOK! [/bold white on green]\n")

# ==========================================
# --- MÓDULO: BOT (RPA Blackboard) ---
# ==========================================
@bot_app.command("map")
def bot_actualizar_mapa():
    """🗺️ Sincronizar IDs de Blackboard"""
    console.print(Panel.fit("📡 ACTUALIZANDO MAPA", border_style="magenta"))
    mapa.run()

@bot_app.command("sync")
def bot_recoleccion():
    """🚀 Recolección de grabaciones"""
    preparador.run()
    start_time = time.time()
    nuevos = scrapper.run() 
    duracion = time.strftime("%M min %S seg", time.gmtime(time.time() - start_time))
    console.print(Panel(f"📹 Grabaciones: {nuevos}\n⏱️ Tiempo: {duracion}", title="DASHBOARD", border_style="green"))

@bot_app.command("live")
def bot_supervision_live():
    """👁️ Monitor de asistencia live"""
    monitor.run()


# --- REGISTRO DE SUB-APPS ---
app.add_typer(mail_app)
app.add_typer(bot_app)

if __name__ == "__main__":
    app()