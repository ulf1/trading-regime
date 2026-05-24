# Python Coding Standards

## 1. Naming

- **Variables/Functions:** `snake_case`
- **Classes/Types:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **File Names:** `snake_case` (preferred) or `kebab-case`
- **Private Members:** Leading underscore `_`

## 2. Style & Typing

- **Type Hints:** Required for all function parameters and return values.
- **Modern Syntax:** Use Python 3.10+ unions (`str | None`, not `Optional[str]`).
- **Line Length:** 88 characters (Black standard).
- **Strings:** Use f-strings for formatting.
- **Imports:** Sort imports (isort standard).
- **Dependencies:** Managed exclusively via `pyproject.toml` with `uv`.

```python
# ✅ Good: Type hints, clear naming, modern syntax
def calculate_total_price(items: list[dict], tax_rate: float) -> float:
    subtotal = sum(item["price"] for item in items)
    return subtotal * (1 + tax_rate)
```

## 3. Code Quality

- **Function Size:** Max 50 lines per function.
- **Complexity:** Avoid deep nesting (max 3 levels).
- **DRY:** Extract duplicated logic into shared functions.
- **Composition:** Favor composition over inheritance.
- **Async:** Prefer `asyncio` for I/O-bound tasks. Never block inside async functions.
- **Resources:** Use context managers (`with` statements) for resource management.

## 4. Security

- **Input Validation:** Validate and sanitize all external input.
- **Secrets:** Never hardcode secrets. Use environment variables.
- **SQL/NoSQL:** Use parameterized queries exclusively.
- **Exceptions:** Catch specific exceptions only (no bare `except:`). Fail fast for invalid inputs.

## 5. Testing

- **Framework:** `pytest` with Arrange–Act–Assert pattern.
- **Coverage:** Target ≥80%. Every new feature must include tests.
- **Mocking:** Mock external dependencies.

## 6. Logging & Error Handling

- **Logging:** Use `logging` module (structured JSON in production environments).
- **Correlation IDs:** Include request/correlation IDs where applicable.
- **Error Flow:** Fail fast for invalid inputs. Never use bare `except:`.
