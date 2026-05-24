---
name: 301-uv
description: High-performance Python project, environment, and dependency management utility. Leverages uv for ultra-fast package resolution, PEP-723 script metadata, and robust pyproject.toml / uv.lock workflows to optimize workspace organization and similarity search performance.
capabilities:
  file_extensions:
    - .py
    - .toml
    - .lock
  actions:
    - initialize_python_env: Scaffolds a new uv-based project structure.
    - sync_dependencies: Synchronizes local environment (.venv) with lockfile.
    - run_pep723_script: Executes standalone Python scripts with inline dependency metadata.
    - optimize_toolchain: Manages global Python tools and versions.
triggers:
  verbs:
    - initialize
    - sync
    - install
    - add
    - run
  nouns:
    - pyproject.toml
    - uv.lock
    - .venv
    - script metadata
    - toolchain
tags:
  - python
  - tooling
manifest:
  knowledge_base: []
  logic_examples:
    - examples/uv_script_metadata.py
---

# UV: Fast Python Package & Project Manager

High-performance automation for Python environments, replacing `pip`, `pipx`, `poetry`, and `pyenv`.

## 1. Quick-Start Snippets

### 1.1 Project Initialization
```bash
uv init # Create a new project with pyproject.toml
uv add <package> # Add dependency and update uv.lock
uv sync # Restore .venv from uv.lock
```

### 1.2 PEP 723 Script Metadata
Declare dependencies directly within scripts for automated environment creation.
```bash
uv run <file.py> # Automatically resolves inline dependencies
```
*Example metadata (see `/examples`):*
```python
# /// script
# dependencies = ["httpx", "rich"]
# ///
```

## 2. Core Constraints
- **Isolation**: Always use `.venv` Managed by `uv`. Never use global `pip`.
- **Locking**: Commit `uv.lock` to ensure deterministic environments for all agents.
- **Scripting**: For agent-triggered scripts, prefer PEP 723 inline metadata over separate requirement files.

## 3. Tool Management
- **Ad-hoc Execution**: `uvx <tool>` (run without permanent install).
- **Persistent Tools**: `uv tool install <tool>` (modern `pipx` alternative).
