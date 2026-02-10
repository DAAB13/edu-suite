# 🎓 Edu suite: orquestado operativo

**EDU SUITE** es una herramienta de línea de comandos (CLI) diseñada para eliminar la carga administrativa manual en la gestión de programas academicos. Centraliza el procesamiento de datos, la auditoría de clases, la generación de reportes con IA y la automatización RPA
---

## 🏗️ Arquitectura y Estructura del Proyecto

El sistema está diseñado bajo el principio de **Separación de Responsabilidades (SoC)**, asegurando que cada módulo tenga una función única y clara.

```plaintext
EDU-SUITE/
├── .venv/                    # Entorno virtual de Python
├── 00_data/                  # Almacenamiento local de bitácoras y persistencia
│   ├── anuncios_log.csv      # Registro de encuestas enviadas (NUEVO)
│   ├── combustible_bot.csv   # Registro de carga para el bot RPA
│   ├── grabaciones_log.xlsx  # Histórico de grabaciones recolectadas
│   ├── mapa_ids.csv          # Mapeo de IDs internos de Blackboard
│   └── repro_log.csv         # Bitácora de clases reprogramadas
├── 01_input/                 # Insumos maestros (OneDrive)
│   ├── chrome_profile/       # Perfil de usuario para persistencia del bot
│   ├── PANEL - DOCENTES EPEC V1.xlsx
│   └── PANEL DE PROGRAMACIÓN V7.xlsx
├── 02_output/                # Repositorio de resultados del ETL
│   ├── dim_docentes.xlsx  
│   ├── dim_programas.xlsx    
│   └── fact_programacion.xlsx  
├── config/                   # Configuración dinámica mediante YAML
│   ├── mappings.yaml         # Diccionarios de columnas y mapeo
│   └── settings.yaml         # Rutas globales y selectores del bot
├── src/                    
│   ├── bot/                  # Automatización RPA
│   │   ├── anuncios/         # Módulo de Comunicación Masiva (NUEVO)
│   │   │   ├── core_announcer.py     # Motor de inyección HTML y persistencia
│   │   │   ├── encuesta_template.html # Plantilla visual de la encuesta
│   │   │   └── survey_bot.py         # Orquestador de filtros y envíos
│   │   ├── live/             # Monitoreo en Tiempo Real (NUEVO)
│   │   │   └── monitor.py            # Dashboard de supervisión "War Room"
│   │   ├── __init__.py
│   │   ├── mapa.py
│   │   ├── preparador.py
│   │   ├── scrapper.py
│   │   └── ui_bot.py
│   ├── core/                 # Motores de carga y limpieza
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   ├── formateador.py
│   │   ├── funciones.py
│   │   └── limpieza.py
│   ├── etl/                  # Procesos de transformación (Dimensionamiento)
│   │   ├── __init__.py
│   │   ├── dim_docentes.py
│   │   ├── dim_programas.py
│   │   └── fact_programacion.py
│   ├── ops/                  # Comandos de negocio y monitoreo
│   │   ├── __init__.py
│   │   ├── auditoria.py
│   │   ├── monitoreo.py
│   │   └── supervision.py
│   └── reporte/              # Generación de reportes e IA
│       ├── __init__.py
│       ├── agente_ia.py
│       ├── etl_domingo.py
│       ├── outlook.py
│       └── repro.py
├── .env                      # Credenciales y llaves API (Protegido)
├── .gitignore                # Archivos excluidos de Git
├── bienvenida.py             # Script de inicialización visual
├── edu.py                    # Orquestador principal de la CLI
├── README.md                 # Documentación técnica
└── requirements.txt          # Dependencias (Pandas, Rich, Typer, etc.)
```


## Guía comandos CLI
Comando principal: python edu.py
1. MODELO DE DATOS 
-     python edu.py run: Actualiza el modelo de datos completo.
2. CONSULTA DIARIA
-     python edu.py ops day: Visualiza la agenda de clases de hoy
-     python edu.py ops check: Para detectar inconsistencias
-     python edu.py ops status: Monitor de programas activos con barras de progreso y cuenta regresiva de inicios.
3. REPORTE SEMANAL
-     python edu.py repo preview: Genera una vista previa del reporte semanal
-     python edu.py repo mail: Automatiza la creación del reporte en Outlook
-     python edu.py repo log: Registro rápido de reprogramaciones en la bitácora local
4. RPA - GRABACIONES BLACKBOARD
-     python edu.py bot map: Sincroniza los IDs internos de Blackboard.
-     python edu.py bot sync: Inicia el flujo completo de recolección de grabaciones
-     python edu.py bot survey: Envío masivo de encuestas a cursos
-     python edu.py bot live: supervición de clases grabadas en vivo

## Configuración y requisitos

**Interfaz:** Typer y Rich para una consola visual y profesional.

**Datos:** Pandas, Numpy y Openpyxl para el manejo de archivos Excel.

**IA:** Groq para la generación de lenguaje natural en reportes.

**Automatización:** Playwright

**Organización** Python-dotenv y PyYAML para la gestión de entornos.


## ⚙️ Modulos
1. **MODELO DE DATOS (`run`)**: Procesa los Excel maestros y genera el modelo relacional.
2. **OPERACIONES (`ops`)**: Agenda diaria, auditoría de errores y monitoreo de progreso.
3. **REPORTES (`repo`)**: Generación de sustentos técnicos y redacción ejecutiva con IA.
4. **BOT RPA (`bot`)**: Sincronización y extracción masiva de grabaciones.




## 🛠️ Solución de Problemas Frecuentes

| Error Común | Causa | Solución |
| :--- | :--- | :--- |
| `PermissionError: [Errno 13]` | El Excel de input está abierto. | Cierra el archivo en Excel antes de ejecutar el comando. |
| `KeyError: 'Columna X'` | TI cambió el nombre de una columna. | Actualiza el nombre en `config/mappings.yaml` sin tocar el código. |
| `Groq API Error` | La API Key expiró o no hay internet. | Verifica el archivo `.env` y tu conexión a la red. |
| `Rutas de OneDrive` | El path es demasiado largo. | Asegúrate de que la carpeta raíz esté mapeada lo más cerca posible al `C:/`. |