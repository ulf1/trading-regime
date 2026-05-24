---
name: 302-cli
description: High-performance Python CLI engineering framework. Expert instruction for Click, Typer, and Argparse orchestration. Specialized in Unit Testing (CliRunner), TDD, Rich TUI aesthetics, POSIX compliance, shell completion, and modular subcommand architectures.
capabilities:
  actions:
    - scaffold_cli_project
    - optimize_terminal_ux
    - validate_cli_compliance
    - implement_subcommand_architecture
    - test_cli_interface
    - generate_shell_completion
  file_extensions: [".py", ".sh", ".toml", ".yaml"]
triggers:
  verbs: [scaffold, architect, command, terminal, test, mock, validate, complete]
  nouns: [CLI, Click, Typer, Argparse, CliRunner, Rich, ANSI, ExitCode, Subcommand]
tags:
  - python
  - cli
manifest:
  knowledge_base:
    - assets/cli_frameworks.json
    - assets/common_pitfalls.json
    - assets/testing_patterns.json
  logic_examples:
    - examples/click_patterns.py
    - examples/typer_patterns.py
    - examples/error_handling.py
    - examples/rich_ui_formatting.py
    - examples/cli_skeleton_template.py
    - examples/pyproject_template.toml
    - examples/testing_click.py
    - examples/testing_typer.py
    - examples/testing_rich.py
    - examples/testing_mocks.py
---

# CLI Architect Skill (Skill 302_cli)

This skill provides expert guidance for building modular, type-safe, and production-grade Command Line Interfaces (CLIs) in Python, prioritizing developer experience (DX), POSIX compliance, and high-quality TUI aesthetics.

---

## 1. Overview & Core Logic
Building scalable command-line tools requires selecting the correct abstraction layer and structuring commands modularly. This skill focuses on:
* Selecting between **Click**, **Typer**, and standard library **Argparse**.
* Best practices for designing deep subcommand structures.
* Standardized testing methods to assert outputs, prompts, and rich ANSI UI formatting.

---

## 2. Rules & Best Practices
> [!IMPORTANT]
> **POSIX Compliance**: Always return precise POSIX-standard exit codes:
> * `0` for success.
> * `1` for execution failures or general crashes.
> * `2` for user input, parameter parsing, or argument usage validation failures.

> [!TIP]
> **TUI Interactivity**: For long-running execution sequences, always utilize `rich.progress` to communicate frame updates to the user. A frozen UI is highly frustrating and can trigger early terminations.

* **Documentation Discipline**: Every `@option`, `@argument`, and `@command` decorator MUST explicitly define a descriptive `help="..."` attribute to ensure auto-generated shell commands are clear.
* **Storage Path Architecture**: Never hardcode configuration file locations. Utilize `click.get_app_dir()` to retrieve OS-compliant configuration directories (e.g. standard AppData or XDG specs).

---

## 3. Implementation Snippets

### A. Multi-Command Click Group Pattern
Recommended project architecture for scalable, multi-command CLIs utilizing Click:
```python
import click

@click.group()
@click.pass_context
def cli(ctx):
    """Main application command group."""
    ctx.ensure_object(dict)

@cli.command()
@click.pass_context
def run(ctx):
    """Execute main execution workflow."""
    click.echo("Running workflow...")
```

### B. Stripping Rich ANSI Formatting for Assertions
When testing Rich-rendered TUI interfaces, use `Console(record=True)` to extract and assert on clean plain-text representations:
```python
from io import StringIO
from rich.console import Console

def test_rich_ui():
    console = Console(file=StringIO(), record=True)
    console.print("[bold green]Success[/bold green]")
    # Strips all ESC patterns for clean assert checks
    assert "Success" in console.export_text()
```

---

## 4. Error Handling & Edge Cases
* **Testing IO Loops**: Standard console runners (`click.testing.CliRunner`) execute in-process. If your code captures global stdout/stderr or spawns subprocesses, use `monkeypatch` to redirect standard input/output streams and mock inputs cleanly (`input="Y\n"`).
* **Isolating Filesystems**: When commands write to the local directory, always wrap test invocations using `with runner.isolated_filesystem():` to prevent stale test artifacts from dirtying the workspace.

---

## 5. Manifest & Resources

### Framework Comparison Matrix
| Framework | Best For | Testing Tool |
| :--- | :--- | :--- |
| **Click** | Deeply-nested subcommand trees, complex parameter pipelines. | `click.testing.CliRunner` |
| **Typer** | Fast FastAPI-style APIs, type-hinted parameters, quick bootstrapping. | `typer.testing.CliRunner` |
| **Argparse** | Zero-dependency simple scripts utilizing standard libraries. | `pytest` + standard mocks |

### Related Assets & Reference Implementation
| Asset Type | Path |
| :--- | :--- |
| **CLI Frameworks** | [cli_frameworks.json](assets/cli_frameworks.json) |
| **Common Pitfalls** | [common_pitfalls.json](assets/common_pitfalls.json) |
| **Testing Patterns** | [testing_patterns.json](assets/testing_patterns.json) |
| **Logic: Click** | [click_patterns.py](examples/click_patterns.py) |
| **Logic: Typer** | [typer_patterns.py](examples/typer_patterns.py) |
| **Logic: Errors** | [error_handling.py](examples/error_handling.py) |
| **Logic: Rich UI** | [rich_ui_formatting.py](examples/rich_ui_formatting.py) |
| **Logic: Skeleton** | [cli_skeleton_template.py](examples/cli_skeleton_template.py) |
| **Logic: Pyproject** | [pyproject_template.toml](examples/pyproject_template.toml) |
| **Test: Click** | [testing_click.py](examples/testing_click.py) |
| **Test: Typer** | [testing_typer.py](examples/testing_typer.py) |
| **Test: Rich** | [testing_rich.py](examples/testing_rich.py) |
| **Test: Mocks** | [testing_mocks.py](examples/testing_mocks.py) |
