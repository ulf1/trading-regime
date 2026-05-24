"""
FastAPI Concurrency Patterns: Sync (Blocking) vs Async.
Detailed instructions for high-performance I/O and CPU bound tasks.
"""

import time
import asyncio
from fastapi import FastAPI, BackgroundTasks
from concurrent.futures import ProcessPoolExecutor

app = FastAPI()

# --- Pattern 1: Async (I/O Bound, Native) ---

@app.get("/async-io")
async def async_io():
    """
    Use 'async def' for code that supports await.
    This does NOT block the event loop.
    """
    await asyncio.sleep(1)  # Simulates async I/O
    return {"message": "Async sleep complete"}


# --- Pattern 2: Sync (I/O Bound, Threaded) ---

@app.get("/sync-io")
def sync_io():
    """
    Use 'def' (NOT 'async def') for blocking synchronous library calls (like older DB drivers).
    FastAPI will automatically execute this in a separate threadpool.
    """
    time.sleep(1)  # Simulates blocking I/O
    return {"message": "Sync sleep complete (run in threadpool)"}


# --- Pattern 3: CPU Bound (ProcessPool) ---

# Global executor for CPU bound tasks
cpu_executor = ProcessPoolExecutor()

def heavy_computation(data: int) -> int:
    """A CPU-intensive function."""
    res = 0
    for i in range(data):
        res += i * i
    return res

@app.get("/cpu-bound/{size}")
async def cpu_bound(size: int):
    """
    CPU bound tasks should NOT be run in 'async def' directly.
    Offload to a ProcessPoolExecutor to avoid blocking the main event loop.
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(cpu_executor, heavy_computation, size)
    return {"result": result}


# --- Pattern 4: Fire-and-Forget (BackgroundTasks) ---

def long_running_task(email: str):
    """A task that takes a long time but doesn't need to return immediately."""
    time.sleep(5)
    print(f"Sent email to {email}")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    """
    Use BackgroundTasks for operations that can happen AFTER returning the response.
    """
    background_tasks.add_task(long_running_task, email)
    return {"message": "Notification scheduled"}
