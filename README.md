Aquí tienes el contenido completo del archivo README.md en formato Markdown puro, listo para que lo copies y lo pegues en tu proyecto.

UPN - Sistema de Automatización ETL y Modelo de Datos Académico
Este proyecto es una solución integral de Ingeniería de Datos diseñada para procesar, limpiar y transformar los registros de programación académica de UPN (EPEC/Posgrado). El sistema migra la gestión basada en archivos Excel manuales y desordenados hacia un Modelo de Datos (Star Schema) optimizado para análisis en Power BI y automatización de procesos operativos.

📌 Visión General del Proyecto
El sistema automatiza la extracción de datos desde OneDrive, aplica reglas de negocio para la limpieza de cabeceras, normalización de fechas y deduplicación, generando un modelo de datos "Diego-céntrico". El objetivo primordial es que la gestión de Soporte (Diego) cuente con información verídica y depurada, eliminando el ruido de programas ajenos a su asignación.

🏗️ Arquitectura del Sistema
El proyecto sigue una estructura modular basada en la separación de responsabilidades:

Plaintext
UPN/
├── 01_input/               # Capa Bronze: Archivos originales copiados de OneDrive.
├── 02_output/              # Capa Silver: Dimensiones y Hechos limpios y formateados.
├── config/                 # Configuración centralizada (YAML).
│   ├── mappings.yaml       # Definición de columnas, tipos de datos y orden de salida.
│   └── settings.yaml       # Rutas globales, nombres de archivos y filtros de soporte.
├── src/                    # Código fuente organizado.
│   ├── core/               # Funciones compartidas (config_loader, formateador, funciones).
│   └── etl/                # Scripts de transformación (dim_docentes, dim_programas, fact_programacion).
└── main.py                 # Orquestador que ejecuta el flujo completo del proceso.
🛠️ El Modelo de Datos (Esquema en Estrella)
El procesamiento genera tres entidades principales vinculadas por identificadores únicos:

1. Dimensión Programas (dim_programas.xlsx)
Granularidad: Un registro único por programa académico mediante la llave ID (combinación de PERIODO y NRC).

Lógica Técnica:

Realiza una limpieza de cabeceras eliminando saltos de línea (\n) y espacios en blanco de los títulos.

Filtra los registros según el soporte asignado en el archivo settings.yaml (ej. "DIEGO").

Procesa la columna FECHAS para asegurar un formato cronológico real y útil para el análisis.

2. Dimensión Docentes (dim_docentes.xlsx)
Granularidad: Un registro por cada docente identificado por su CODIGO_BANNER.

Integración: Consolida datos de la hoja de "Docentes Activos" y la tabla "RUT", aplicando reglas de deduplicación y limpieza de nombres (eliminación de comas y espacios múltiples).

Limpieza de Identidad: Formatea el DNI con ceros a la izquierda y normaliza el campo GENERO basándose en un mapa de valores predefinido en los mappings.

3. Fact Table Programación (fact_programacion.xlsx)
Granularidad: Un registro por cada sesión de clase individual.

Relación: Conecta los programas con los docentes asignados, incluyendo horarios, estados de clase y tipos de sesión.

Cálculos de Calidad: Realiza la limpieza de columnas numéricas (horas y tarifas) reemplazando errores por valores neutros para asegurar la integridad de los cálculos.

⚙️ Configuración y Escalabilidad
El diseño permite escalar el sistema sin modificar el código fuente:

Parametrización vía YAML: Los filtros de soporte, las hojas de Excel y las rutas de carpetas se gestionan externamente para mayor flexibilidad.

Filtros Dinámicos: Si se desea incluir a otro soporte (ej. "MARIA"), solo se debe añadir a la lista en settings.yaml y el modelo lo incluirá automáticamente en la siguiente ejecución.

Blindaje de Proceso: El orquestador main.py utiliza bloques try-except para capturar errores críticos e informar al usuario, permitiendo identificar fallas en archivos específicos (como la falta de la columna 'SOPORTE' en el Excel de docentes).

🚀 Reglas de Negocio Implementadas
Normalización de Texto: Conversión automática a mayúsculas y eliminación de espacios en blanco (TRIM) en campos de texto de todas las tablas.

Identificadores Únicos: Generación de llaves primarias (ID) para garantizar la integridad referencial entre la tabla de hechos y la dimensión de programas.

Limpieza de Contacto: Formateo de celulares eliminando espacios y caracteres no numéricos para asegurar la utilidad de la data.

Formateo Ejecutivo: Todos los archivos de salida en 02_output incluyen auto-ajuste de columnas, cabeceras estilizadas y filtros automáticos habilitados mediante la librería openpyxl.

💻 Guía de Ejecución
Asegúrese de que los archivos fuente estén disponibles en la ruta de OneDrive configurada en settings.yaml.

Verifique que el filtro de soporte incluya el nombre deseado.

Ejecute el script principal desde la terminal:

Bash
python main.py
Los resultados finales se generarán automáticamente en la carpeta 02_output/.