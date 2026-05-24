"""
FastAPI Lifespan and Dependency Injection Pattern.
How to manage resource initialization and clean up.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends


# --- Async Database Engine Simulation ---

class AsyncDBEngine:
    async def connect(self):
        print("Connected to DB")

    async def disconnect(self):
        print("Disconnected from DB")

    async def execute(self, query: str):
        return f"Result of {query}"


# --- Lifecycle Context Manager ---

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Handle startup and shutdown events for the entire application.
    Ideal for initializing DB connection pools, ML model loading, etc.
    """
    # [STARTUP]
    db_engine = AsyncDBEngine()
    await db_engine.connect()
    
    # Store in app state for access from dependencies
    app.state.db_engine = db_engine
    
    yield
    
    # [SHUTDOWN]
    await db_engine.disconnect()


# --- Dependencies ---

def get_db(request: Request) -> AsyncDBEngine:
    """
    A dependency to retrieve the database engine initialized during lifespan.
    Can be overridden in tests to mock DB behavior.
    """
    return request.app.state.db_engine


# --- App Configuration ---

app = FastAPI(lifespan=lifespan)

@app.get("/query")
async def db_query(query: str, db: AsyncDBEngine = Depends(get_db)):
    """Async dependency injection for high-concurrency database queries."""
    return {"result": await db.execute(query)}
