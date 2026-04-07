# Instrucciones del proyecto `el-supervisor`

## Propósito
Herramienta CLI para orquestar tareas RPA sobre Blackboard: 
1. mapear IDs de cursos
2. monitorear en vivo el estado de grabaciones. Diseñada para uso operativo local (Windows + Chrome), enfocada en automatización de verificaciones diarias.

## Contexto rápido
- Uso principal: `uv run python bot.py map|live`.
- Tecnologías: Playwright (RPA), pandas (datos), rich (UI consola), tomllib + `.env` (config). 
- Flujo mixto: requiere interacción humana para MFA en escenarios reales.

## Estructura y archivos clave
- `bot.py` — CLI: dispatch a `map` (genera mapa) y `live` (monitoreo).
- `src/map.py` — Autentica con Playwright, captura cookies y llama la API `api_memberships`; escribe `00_data/mapa_ids.csv` (CSV `;`, `latin1`).
- `src/bb.py` — Flujo "live": lee `parquet` de programación, cruza con `mapa_ids.csv`, usa `01_input/chrome_profile` y verifica grabaciones inspeccionando iframes/tablas; muestra dashboard con `rich.Live`.
- `config.toml` / `config.example.toml` — URLs, selectores y rutas (plantillas: `{id_interno}`, `{user_id}`).
- `00_data/mapa_ids.csv` — salida de `map.py`, entrada para `bb.py`.
- `01_input/chrome_profile/` — perfil Chrome persistente (no versionar).
- `.env` (fuera del repo): `USER_ID_BB`, `BB_MAIL`, `BB_PASS`.

## Flujo general (resumen)
1. `uv run python bot.py map` → `src.map.run()`:
	- Login UI (Playwright), captura cookies, llama API, guarda `00_data/mapa_ids.csv`.
2. `uv run python bot.py live` → `src.bb.run()`:
	- Lee `parquet` (ruta en `config.toml`), filtra por día, merge con `mapa_ids.csv`, abre navegador persistente and verifica estado de grabación por curso.

## Zonas sensibles y riesgos (alto impacto)
- `src/bb.py`: depende del esquema del `parquet` (`id`, `fechas`, `hora_inicio`, `curso`, `docente`) y de estructura de la UI (iframes/selectores).
- Login/MFA: flujo semi‑manual; automatización completa no garantizada.
- `map.py`: usa cookies de sesión para la API — frágil ante expiración/cambios de sesión.
- `01_input/chrome_profile` puede contener datos sensibles — no subir al VCS.
- `parquet_file` suele apuntar a ruta externa (OneDrive) — no portátil.
- Headful Chrome (`headless=False`) y `channel="chrome"` requieren entorno gráfico.
- CSV `;` + `latin1`: encoding y delimitador son dependencias explícitas.