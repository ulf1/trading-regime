---
description: Scaffold a new CLI project with Click, pyproject.toml, and test structure.
---

# Create CLI Project

Scaffold a new Click-based CLI application with the following structure:

## Steps

1. Ask the user for:
   - Project name
   - CLI framework preference (click, typer, argparse) — default: click
   - Single-command or multi-command CLI
   - Whether to include rich output, config file support, or logging

2. Create the directory structure:
```text
src/cli/
└── {project_name}/
    ├── __init__.py
    ├── __main__.py          # Entry point
    ├── cli.py               # Main CLI group
    ├── commands/            # Individual command modules
    │   └── __init__.py
    ├── utils/               # Shared logic & decorators
    │   └── __init__.py
    └── schemas/             # Pydantic contract definition
        └── __init__.py
tests/cli/{project_name}/
├── __init__.py
└── test_cli.py
pyproject.toml
README.md
```

3. Generate `pyproject.toml` with:
   - `[project.scripts]` entry point
   - Dependencies: `click>=8.0`, `rich>=10.0`
   - Dev dependencies: `pytest`, `pytest-cov`, `ruff`

4. Generate `src/cli/{project_name}/cli.py` with:
   - `@click.group()` and `@click.version_option()`
   - Type hints on all parameters
   - `rich.console.Console` for output
   - Proper error handling with `sys.exit(1)`

5. Generate `tests/cli/{project_name}/test_cli.py` with `CliRunner` test skeleton.

6. Run `uv sync` to install dependencies.