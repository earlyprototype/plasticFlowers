# Project Overview

This project is a Knowledge Graph Kit, a Python-based tool for building, visualizing, and exploring knowledge graphs. It provides an interactive web interface for visualizing the graph, and an optional Gemini integration for AI-powered chat and insights.

The core of the project is the `GraphManager` class, which handles all CRUD operations on the knowledge graph. The graph data is stored in a JSON file (`_data/entities.json`), and the graph's schema is defined in a YAML file (`config.yaml`).

The web interface is a single-page application (`viewer.html`) that uses the `vis.js` library to render the graph. A simple Python HTTP server (`server.py`) is used to serve the web interface and the graph data.

The project also includes an optional Gemini integration for AI-powered chat and insights. This is provided by a separate Flask-based API server (`gemini_api_server.py`) that handles chat sessions, context management, and communication with the Gemini API.

The project includes a setup wizard (`setup_wizard.py`) that guides the user through the process of creating a new knowledge graph project from a template.

## Project Templates

The project provides a set of pre-built templates for different use cases:

*   **Academic Research:** For academic research, literature reviews, and systematic analysis.
*   **Systems:** For software architecture, microservices mapping, and dependency tracking.
*   **Ecosystem:** For stakeholder analysis, organizational networks, and value flow mapping.
*   **Generic:** A blank canvas for custom domains.

Each template defines a specific schema for the knowledge graph, including entity types, relationship types, and visualization settings. The templates can be customized to fit the user's needs.

## Project Dependencies

The project has the following Python dependencies:

*   `pyyaml`: For parsing the `config.yaml` file.
*   `google-generativeai`: For the optional Gemini AI chat integration.

These dependencies can be installed using pip:
```bash
pip install -r requirements.txt
```

## Building and Running

### Interactive Setup (Recommended)

For Windows users, two scripts are provided to automate the setup process:
*   `SETUP.bat`: A batch script that can be double-clicked to run the setup wizard.
*   `setup.ps1`: A PowerShell script that can be run from the command line.
```powershell
.\setup.ps1
```
These scripts will check for Python, install the required dependencies, and then run the setup wizard.

For other operating systems, you can run the setup wizard directly:
```bash
python setup_wizard.py
```
The wizard will guide you through choosing a template, configuring AI integration (optional), and setting up the project.

Once the project is created, navigate to the project directory:
```bash
cd <project-directory>
```
Start the server:
```bash
python server.py
```
Or, if you enabled Gemini integration:
```bash
python start_server.py
```
Open your browser to `http://localhost:8000/viewer.html` to see the knowledge graph.

### Manual Setup

1.  Choose and copy a template from the `templates` directory.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Initialize the project:
    ```bash
    cd <project-directory>
    python init.py
    ```
4.  Start the server:
    ```bash
    python server.py
    ```
5.  Open your browser to `http://localhost:8000/viewer.html`.

## Development Conventions

*   The project follows a standard Python project structure.
*   The core logic is separated into the `core` directory.
*   The frontend is a single HTML file (`viewer.html`) with embedded JavaScript and CSS.
*   The project uses a `config.yaml` file for configuration, which allows for easy customization of the knowledge graph schema.
*   The `GraphManager` class provides a clear API for interacting with the knowledge graph.
*   The Gemini integration is provided by a separate Flask-based API server, which allows for a clean separation of concerns.
*   The project is well-documented, with a comprehensive `README.md` file and a `TEMPLATES.md` file that explains the different templates.
*   The `.gitignore` file is well-configured to exclude unnecessary files from the repository, such as Python cache files, virtual environments, IDE-specific files, and project-specific files like `gemini_config.json`.

## Contributing

The project has clear contribution guidelines outlined in the `CONTRIBUTING.md` file. Key points include:

*   **Reporting Issues:** Use clear, descriptive titles and provide steps to reproduce.
*   **Code Contributions:** Fork the repository, create a feature branch, and submit a pull request.
*   **Code Style:** Follow PEP 8 for Python code and use descriptive variable names.
*   **Testing:** Test changes with all templates and verify that the wizard and viewer still work correctly.