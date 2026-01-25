# 🎓 EDU-CLI: Academic Management Suite

**EDU-CLI** es una plataforma de orquestación de datos y supervisión académica de alto rendimiento, desarrollada para la gestión operativa de programas de Postgrado en la **UPN**. Esta herramienta transforma la complejidad de los archivos de programación masivos en Excel hacia un modelo de datos relacional y un tablero de control (TUI) intuitivo y profesional.

---

## 🏗️ Arquitectura y Estructura del Proyecto

El sistema está diseñado bajo el principio de **Separación de Responsabilidades (SoC)**, asegurando que cada módulo tenga una función única y clara.

```plaintext
edu-suite/
├── 01_data/                # Almacenamiento local de bitácoras y archivos persistentes.
├── 02_output/              # Repositorio de Dimensiones y Fact Table generadas.
├── config/                 # Configuración dinámica mediante archivos YAML.
├── src/                    # Código fuente del sistema.
│   ├── core/               # Lógica de limpieza, mappings y cargador de configuración.
│   ├── etl/                # Motores de transformación (Docentes, Programas, Fact Table).
│   └── ops/                # Comandos de negocio, monitoreo y auditoría.
├── edu.py                  # Punto de entrada y orquestador principal de la CLI.
└── requirements.txt        # Dependencias (Typer, Pandas, Rich, PyYAML).

🚀 Funcionalidades Detalladas
1. Motor ETL de Alta Precisión (python edu.py run)
El proceso de transformación de datos no solo copia información, sino que la enriquece:

Dimensión Docentes: Normaliza identidades y consolida la base de datos de profesores.

Dimensión Programas: Realiza un Cálculo de Fechas Extremas mediante agrupaciones (groupby), detectando el inicio y fin real de cada curso a partir de sus múltiples sesiones.

Fact Table: Construye la tabla de hechos con una Llave Única Estandarizada (ID = Periodo.NRC), permitiendo cruces de datos infalibles con otros sistemas.

2. Dashboard de Monitoreo Proactivo (python edu.py ops status)
Este comando ofrece una visualización avanzada de la carga de trabajo actual:

Resumen Ejecutivo: Tarjetas dinámicas organizadas por columnas que muestran el conteo total de programas activos desglosados por categoría.

Visualización de Progreso: Implementación de una barra de avance moderna con estilo de puntos (●●●○○) y colorización inteligente (Rojo/Amarillo/Verde) según el cumplimiento.

Prevención de Próximos Inicios: Tabla dedicada a cursos por iniciar, ordenada cronológicamente con una Cuenta Regresiva automática de días faltantes.

3. Supervisión Diaria y Agenda (python edu.py ops day)
Optimizado para la gestión minuto a minuto:

Dashboard Temporal: Resumen de sesiones para Hoy, Mañana y Pasado Mañana mediante un diseño de tarjetas en paneles.

Detección de Inconsistencias: El sistema realiza una auditoría silenciosa y alerta si detecta errores en la data (como estados NaN o sesiones sin docente) antes de mostrar la agenda.

🧠 Estándares de Ingeniería y Diseño
Estandarización de IDs y Limpieza
Para evitar la duplicidad y asegurar la integridad referencial, el sistema aplica la función estandarizar_id en todas las capas, garantizando el formato XXXXXX.XXXX.

Gestión de Tipos de Datos (Anti-Error)
Se implementó una corrección crítica para resolver el conflicto entre pd.Timestamp y datetime.date. El sistema normaliza todas las fechas en la capa ETL mediante .dt.normalize(), asegurando que las comparaciones lógicas en los dashboards funcionen sin errores de ejecución.

Interfaz de Usuario (TUI) de Alto Contraste
El diseño visual en la terminal ha sido pulido para ser "pixel-perfect":

Accesibilidad: Uso de códigos hexadecimales (#000000 sobre Yellow) para garantizar que las cabeceras sean legibles en cualquier tema de terminal.

Layout Adaptativo: Las métricas de resumen utilizan Columns para auto-ajustarse al ancho de la ventana del usuario.

🔧 Guía de Uso Rápido
Bash
# Sincronizar y generar el modelo de datos completo
python edu.py run

# Consultar el tablero de control de programas activos
python edu.py ops status

# Ver la agenda de supervisión para los próximos 3 días
python edu.py ops day

# Ejecutar auditoría profunda de errores en la data
python edu.py ops check