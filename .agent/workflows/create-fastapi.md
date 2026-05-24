---
description: Scaffold a new FastAPI project with Service Layer pattern, Pydantic settings, and test structure.
---

# Create FastAPI Project

Scaffold a new FastAPI application using the Service Layer pattern.

## Steps

1. Ask the user for:
   - Project name
   - Whether to include database support (SQLAlchemy)
   - Whether to include authentication

2. Create the directory structure:
```text
src/
└── api/
    ├── main.py              # App initialization, lifespan
    ├── config.py            # Pydantic Settings (pydantic-settings)
    ├── dependencies.py      # Shared DI providers
    ├── routers/
    │   └── __init__.py
    ├── services/
    │   └── __init__.py
    └── schemas/
        ├── __init__.py
        ├── requests.py
        └── responses.py
tests/
└── api/
    ├── __init__.py
    └── test_api.py
pyproject.toml
.env
README.md
```

3. Generate `pyproject.toml` with:
   - Dependencies: `fastapi`, `uvicorn[standard]`, `pydantic-settings`
   - Dev dependencies: `pytest`, `httpx`, `ruff`

4. Generate `src/api/main.py` with:
   - `lifespan` context manager
   - Global exception handlers for custom service exceptions
   - CORS middleware if needed

5. Generate `src/api/config.py` with `pydantic-settings` for `.env` management.

6. Generate a sample router + service + schema to demonstrate the pattern:
   - Router: handles HTTP, calls service, returns response schema
   - Service: pure Python logic, raises custom exceptions (no HTTP imports)
   - Schemas: separate Create, Update, and Response models

7. Generate `tests/api/test_api.py` with `httpx.AsyncClient` test skeleton.

8. Run `uv sync` to install dependencies.
