# GEMINI Project Analysis: EDU SUITE

This document provides a comprehensive analysis of the EDU SUITE project, designed to serve as a persistent context for AI-assisted development.

## 1. Project Overview

**EDU SUITE** is a sophisticated Python-based command-line interface (CLI) tool designed to automate and streamline academic program management. It functions as an operational orchestrator, handling data processing, class auditing, AI-powered report generation, and Robotic Process Automation (RPA) for administrative tasks.

The project is architected with a clear **Separation of Concerns (SoC)**, dividing functionalities into distinct, self-contained modules.

### Core Technologies:

*   **CLI Framework:** `Typer` and `Rich` for a visually appealing and user-friendly console experience.
*   **Data Manipulation:** `Pandas` and `Numpy` for efficient data processing and transformation, primarily from Excel sources.
*   **Automation (RPA):** `Playwright` is used for browser automation, specifically for interacting with the Blackboard learning platform to scrape recording data.
*   **AI & Reporting:** `Groq` is leveraged for natural language generation to create executive summaries in weekly reports, which are then drafted into Outlook.
*   **Configuration:** `PyYAML` and `python-dotenv` manage dynamic settings and sensitive credentials, separating configuration from code.

### Architectural Breakdown:

The project follows a modular structure:

*   **`edu.py`:** The main entry point and orchestrator of the CLI, defining all available commands.
*   **`src/core/`:** Contains the core logic for loading configurations (`config_loader.py`), formatting data, and other foundational functions.
*   **`src/etl/`:** Houses the Extract, Transform, Load (ETL) pipeline scripts. These scripts process source Excel files (`PANEL - DOCENTES EPEC V1.xlsx`, `PANEL DE PROGRAMACIÓN V8.xlsx`) and generate dimensional models (`dim_docentes.xlsx`, `dim_programas.xlsx`) and a fact table (`fact_programacion.xlsx`).
*   **`src/bot/`:** Manages all RPA tasks. This includes a `scrapper.py` for collecting data from Blackboard, a `preparador.py` to set up the data for the bot, and modules for sending mass announcements (`anuncios/`).
*   **`src/mail/`:** Handles all email-related automation. It contains modules for generating a weekly report (`reporte_semanal/`) and interfacing with Outlook (`outlook.py`).
*   **`config/`:** All project configuration is centralized in `settings.yaml` (for paths, selectors, URLs) and `mappings.yaml` (for column name mappings), allowing for easy updates without code changes.
*   **`00_data/`:** Serves as local storage for logs and stateful data, like recording history and entity mappings.
*   **`01_input/` & `02_output/`:** Designated directories for raw input data and the processed output of the ETL jobs, respectively.

## 2. Building and Running

The project is a CLI application and does not require a "build" step. It is run directly using a Python interpreter.

### Setup:

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```
2.  **Activate the environment:**
    *   **Windows:** `.venv\Scripts\activate`
    *   **macOS/Linux:** `source .venv/bin/activate`
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Key Commands:

The main entry point is `edu.py`. All commands are initiated via `python edu.py [subcommand]`.

*   **Update the entire data model:**
    ```bash
    python edu.py run
    ```
*   **Generate and draft the weekly executive report in Outlook:**
    ```bash
    python edu.py mail sun
    ```
*   **Run the RPA bot to collect Blackboard recordings:**
    ```bash
    # Step 1: Sync Blackboard internal IDs
    python edu.py bot map

    # Step 2: Run the full collection flow
    python edu.py bot sync
    ```
*   **Monitor live class assistance:**
    ```bash
    python edu.py bot live
    ```

## 3. Development Conventions

*   **Configuration over Code:** Business logic and environmental details (like column names, paths, selectors) are stored in YAML files (`config/`). Changes to these should be the first step when adapting to external data source changes.
*   **Modularity:** New features should be added in their respective modules (`bot`, `etl`, `mail`, etc.) to maintain separation of concerns.
*   **Entry Points:** The `edu.py` script is the primary orchestrator. New high-level commands should be registered here. Sub-commands should be added to the respective Typer sub-apps (`mail_app`, `bot_app`).
*   **Data Flow:** The standard data flow is `01_input` -> `src/etl` -> `02_output`. ETL scripts are responsible for this transformation.
*   **Environment Variables:** Sensitive information like API keys (`.env` file) is loaded via `python-dotenv`. This file should not be committed to source control.
*   **Rich CLI Output:** The `rich` library is used extensively for formatted and user-friendly output (Panels, Tables, logging). New CLI features should adopt this for consistency.
