# Antigravity Agents - How-to Guide

This directory contains the custom instructions, workflows, and skills that define the intelligence and behavior of the Antigravity agent in this workspace.

## 1. Customization Tiers

Antigravity uses a three-tier system for agent instructions:

| Tier | Folder | Activation | Purpose |
|---|---|---|---|
| **Rules** | `.agent/rules/` | **Always Active** | Core constraints, coding style, and safety rules. |
| **Workflows** | `.agent/workflows/` | **Manual (`/`)** | User-triggered procedures and saved prompts. |
| **Skills** | `.agent/skills/` | **Contextual** | Specialized knowledge loaded only when relevant. |

---

## 2. Rules (Always Active)

Rules are system-level instructions injected into every conversation. They do not have special headers; any `.md` file in `.agent/rules/` is automatically read by the agent.

**Available Rules:**
- `interaction.md`: Behavior, conciseness, and output formatting.
- `project-structure.md`: Mandatory file layouts and naming conventions.
- `python-style.md`: PEP 8, types, and testing standards.

---

## 3. Workflows (Manual Trigger)

Workflows are "saved prompts" triggered manually by typing `/` followed by the workflow name.

**How to call:**
Type `/` in the chat to see a list of available workflows.

**Current Workflows:**
- `/code-review`: Review code for security, correctness, performance, and standards compliance.
- `/create-cli`: Scaffold a new CLI project with Click, pyproject.toml, and test structure.
- `/create-fastapi`: Scaffold a new FastAPI project with Service Layer pattern, Pydantic settings, and test structure.

---

## 4. Skills (Progressive Disclosure)

Skills are "latent knowledge" packages. They are **not** loaded into the context window unless the agent detects they are needed based on your request.

**How they are "called":**
When you ask for something (e.g., "Implement a custom Hamilton Filter in PyTorch"), the agent scans the `description` field in the frontmatter of all `SKILL.md` files. If there is a match, the full instructions are loaded.

**Available Skills:**

### Meta & Design (0xx Series)
- `001-skill-creator`: Create, scaffold, validate, audit, and improve Agent Skills (SKILL.md packages) for Antigravity or any compatible agent runtime.

### Python Environment & API Scaffolding (3xx Series)
- `301-uv`: High-performance Python project, environment, and dependency management utility leveraging `uv` for ultra-fast package resolution and robust workflow optimization.
- `302-cli`: High-performance Python CLI engineering framework with expert instruction for Click, Typer, and Argparse orchestration, unit testing, and TUI aesthetics.
- `303-fastapi`: High-performance FastAPI orchestration framework supporting the Service Layer pattern, Pydantic v2 validation, and async/sync lifecycle management.

### Scientific Computing & Infrastructure (3xx Series)
- `326-numpy`: Best practices for writing correct, fast, and idiomatic NumPy code, focusing on vectorized operations and performance optimizations.
- `326-numpy-unittest`: Best practices for writing unit tests for NumPy code, validating shapes, types, and mathematical invariants.
- `327-pandas`: Best practices for writing high-quality, performant, and maintainable pandas code for tabular data transformation and analysis.
- `327-pandas-unittest`: Best practices for writing unit tests for pandas data transformations, DataFrame/Series values, and mocking.
- `340-terraform`: Expert framework for writing, reviewing, refactoring, or troubleshooting Terraform and HCL infrastructure-as-code.

### Deep Learning & Quantitative Models (3xx & 8xx Series)
- `323-pytorch`: Comprehensive best practices for writing production-quality PyTorch code, covering model definitions, training loops, AMP, and optimization.
- `323-pytorch-unittest`: Best practices for writing robust unit tests for PyTorch tensors, model architectures, gradients, and AMP.
- `324-pytorch-to-vhdl`: High-performance orchestration for converting PyTorch models to synthesizable VHDL for FPGA-optimized inference.
- `899_pytorch_hamiliton`: High-performance vectorized Markov Regime-Switching (MRS) model engineering and batched Hamilton Filters in PyTorch.
- `899_pytorch_hamiliton_unittest`: High-performance unit testing suite for the vectorized PyTorch Markov Regime-Switching (MRS) model and Hamilton Filter.

---

## 5. Adding New Content

- **New Rule**: Create a `.md` file in `.agent/rules/`.
- **New Workflow**: Create a `.md` file in `.agent/workflows/` with a YAML description at the top:
  ```markdown
  ---
  description: [Trigger description]
  ---
  ```
- **New Skill**: Create a directory in `.agent/skills/` containing a `SKILL.md` with:
  ```markdown
  ---
  name: [name]
  description: [When to use this skill]
  ---
  ```
