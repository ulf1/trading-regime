---
name: 303-fastapi
description: High-performance FastAPI orchestration framework. Expert instruction for Service Layer pattern, Pydantic v2 validation, dependency injection, unit testing best practices (TestClient, pytest-asyncio, dependency_overrides), and async/sync lifecycle management. Optimized for semantic discovery of RESTful API design, middleware configuration, and high-concurrency Python backends. Includes `/assets` for knowledge base and `/examples` for production-grade testing, concurrency, and architecture skeletons.
tags:
  - python
  - fastapi
  - pydantic
  - rest-api
  - pytest
  - backend
capabilities:
  actions:
    - scaffold_fastapi_app
    - optimize_async_concurrency
    - validate_pydantic_schemas
    - test_api_endpoints
    - design_service_layer
  file_extensions:
    - .py
    - .env
    - pyproject.toml
    - conftest.py
triggers:
  verbs:
    - scaffold
    - validate
    - configure
    - test
    - mock
    - override
  nouns:
    - FastAPI
    - Pydantic
    - TestClient
    - Router
    - Service
    - Depends
    - Pytest
manifest:
  knowledge_base:
    - assets/manifest.json
  logic_examples:
    - examples/service_layer.py
    - examples/concurrency.py
    - examples/exceptions.py
    - examples/lifecycle.py
    - examples/unit_testing.py
---

# FastAPI Specialist Expert System

This skill enforces mandatory architecture for robust, enterprise-grade FastAPI applications using the **Service Layer Pattern** and **Async/Sync Concurrency** optimizations.

## 1. High-Performance Service Layer
Strict isolation between the **Transport (FastAPI)** and **Business Logic (Services)** is non-negotiable.

### Mandatory Directory Layout
```text
.
├── src/api/                 # Main app logic
│   ├── main.py
│   ├── dependencies.py
│   ├── routers/
│   ├── services/
│   ├── schemas/
│   └── config.py
└── tests/api/               # Mirrored test structure
```

## 2. Async/Sync Concurrency Matrix
| Operation Type | Implementation Rule | Engine Detail |
| :--- | :--- | :--- |
| **Async I/O** | `async def` | runs in event loop (non-blocking) |
| **Sync I/O** | `def` | runs in FastAPI external threadpool |
| **CPU Bound** | `def` + `ProcessPoolExecutor` | offloads heavy math to separate process |

## 3. Global Error Handling Strategy
Instead of returning `HTTPException` from service logic, raise custom Python exceptions and map them at the app perimeter. Refer to `examples/exceptions.py`.

```python
# Quick snippet: Map exceptions in main.py
@app.exception_handler(ItemNotFoundError)
async def handle_not_found(request: Request, exc: ItemNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})
```

## 4. 🧪 Unit Testing FastAPI Applications

FastAPI testing relies primarily on `TestClient` and `dependency_overrides`.

### Core Best Practices:
1. **Use `TestClient`:** For robust HTTPX-based testing.
2. **Leverage `dependency_overrides`:** Swap database sessions (`get_db`) or authentication layers without touching production code.
3. **Clean Up Overrides:** Always clear overrides using an `autouse=True` fixture in your setup.
4. **Centralize:** Use `conftest.py` for all global fixtures (clients, db, auth).
5. **Mock External Calls:** Use `unittest.mock.patch`.
6. **Async Testing:** Use `pytest.mark.asyncio` and `httpx.AsyncClient` for asynchronous endpoints.
7. **Isolate DB:** Use nested transactions (SAVEPOINTs) to provide clean rollup states per test.

```python
# Quick Snippet: Clean testing with TestClient & Overrides
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_overrides():
    yield
    app.dependency_overrides = {}

def test_override_example():
    app.dependency_overrides[get_db] = mock_get_db
    response = client.get("/")
    assert response.status_code == 200
```

> [!NOTE]
> Detailed structural examples for auth fixtures, mock patching, and async/await tests exceed 20 lines and are documented in `examples/unit_testing.py`.

## 5. Manifest & Knowledge Base
Refer to `assets/manifest.json` for detailed production examples and exhaustive documentation on:
- Lifecycle context management (`lifespan`)
- Resource dependency injection (`Depends`)
- Advanced Pydantic v2 validation patterns
- Detailed concurrency optimization techniques
