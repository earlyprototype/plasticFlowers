# Core Components

This directory contains the core functionality of the Knowledge Graph Kit.

## Files

### `viewer.html`
**Universal knowledge graph viewer** - a single viewer that works with all templates by dynamically reading `config.yaml`.

- Automatically adapts to entity types defined in config
- Generates filters and UI based on configuration
- Reads color schemes from config
- Gets copied to new projects during initialization

**No template-specific viewers needed** - this one file handles everything.

### `graph_manager.py`
Core graph management functionality.

### `config_loader.py`
YAML configuration loader and validator.

### `server.py`
Simple HTTP server for viewing knowledge graphs locally.

