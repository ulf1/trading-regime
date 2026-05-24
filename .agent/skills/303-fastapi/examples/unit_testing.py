import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

# --- Example App Structure ---

app = FastAPI()

def get_db():
    "Mock dependency for database access."
    return "production_db_session"

class ItemNotFoundError(Exception):
    "Example custom exception."
    pass

@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.get("/")
def read_root(db: str = Depends(get_db)):
    return {"msg": "Hello", "db": db}

@app.get("/async-data")
async def get_async_data():
    return {"data": "async_result"}

# --- 1. Foundation: TestClient ---

client = TestClient(app)

def test_read_root():
    """Testing a simple sync endpoint using TestClient."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello", "db": "production_db_session"}

# --- 2. Dependency Overrides: The 'Killer Feature' ---

def override_get_db():
    return "test_db_session"

def test_with_db_override():
    """Overriding a dependency to use a test resource."""
    app.dependency_overrides[get_db] = override_get_db
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["db"] == "test_db_session"
    # Overrides persist unless cleared! See fixture below.

# --- 3. Override Cleanup via Fixtures ---

@pytest.fixture(autouse=True)
def clean_overrides():
    """Fixture to ensure dependency_overrides are cleared after each test."""
    yield
    app.dependency_overrides = {}

# --- 5. Mocking External Dependencies ---

def external_api_call():
    # Imagine this calls a real external service
    return {"status": "external_ok"}

@app.get("/external")
def route_with_external():
    return external_api_call()

def test_external_mock():
    """Using patch to mock an external function call."""
    with patch("examples.unit_testing.external_api_call") as mock_call:
        mock_call.return_value = {"status": "mocked_ok"}
        response = client.get("/external")
        assert response.json() == {"status": "mocked_ok"}

# --- 6. Testing Async Endpoints ---

@pytest.mark.asyncio
async def test_async_endpoint():
    """Testing an async route using httpx.AsyncClient."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/async-data")
    assert response.status_code == 200
    assert response.json() == {"data": "async_result"}

# --- 8. Authenticated Test Clients ---

@pytest.fixture
def auth_client():
    """Fixture providing a TestClient with an Authorization header prepopulated."""
    # Mocking user creation and token generation here
    token = "fake-jwt-token-123"
    ac = TestClient(app)
    ac.headers["Authorization"] = f"Bearer {token}"
    return ac

def test_protected_endpoint(auth_client):
    """Example of using the authenticated client fixture."""
    # response = auth_client.get("/protected")
    # assert response.status_code == 200
    pass
