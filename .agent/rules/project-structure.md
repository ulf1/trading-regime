# Project Structure

## 1. Directory Layout

- `/src` — Application source code (internals depend on app type; see skill-specific layouts)
- `/tests` — Unit and integration tests (mirror `src/` structure)
- `/config` — Static configuration files (YAML, TOML); Python settings go in `src/config.py`
- `/docs` — Documentation
- `/scripts` — Automation scripts

## 2. Naming Conventions for `src/` Internals

| Folder / File | Purpose | Applies to |
|---|---|---|
| `schemas/` | Pydantic validation models (request/response/config) | CLI, FastAPI |
| `services/` | Business logic, pure Python (no HTTP coupling) | FastAPI |
| `routers/` | HTTP transport layer | FastAPI |
| `agents/` | Agent definitions (schema + prompt + class) | LangGraph MAS |
| `graphs/` | LangGraph runtime (state + nodes + workflow) | LangGraph MAS |
| `chains/` | LCEL chain definitions | LangChain |
| `utils/llm.py` | LLM initialisation & caching | LangChain/LangGraph |
| `prompts/` | Prompt templates (when not embedded in agent file) | LangChain |

> ⚠️ **Avoid `models/`** as a folder name — it is ambiguous (Pydantic models vs. LLM model objects vs. ML model artefacts). Use `schemas/` for Pydantic models and `utils/llm.py` for LLM initialisation.

## 3. Documentation

- **Public APIs:** Document intent and usage.
- **Complex Logic:** Document "why", not just "how".
- **README:** Keep `README.md` up to date with: project description, setup instructions, usage examples, dependencies, and license.

## 4. Version Control (Git)

### Commit Messages
- **Format:** `<type>: <subject>` (e.g., `feat: Add user authentication`)
- **Tense:** Present tense ("Add feature", not "Added feature")
- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branch Strategy
- `main`/`master`: Production-ready code
- `develop`: Integration branch
- `feature/*`, `bugfix/*`, `hotfix/*`: Development branches
