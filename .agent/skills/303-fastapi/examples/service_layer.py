"""
Example of the Service Layer Pattern in FastAPI.
Demonstrates strict separation between Transport (HTTP) and Business Logic.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

# --- Schemas (contract) ---

class ItemBase(BaseModel):
    name: str
    description: str | None = None

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- Exceptions ---

class ItemServiceError(Exception):
    """Base exception for service layer."""
    pass

class ItemNotFoundError(ItemServiceError):
    """Raised when an item is not found."""
    pass


# --- Service Layer (Pure Logic) ---

class ItemService:
    def __init__(self):
        # In a real app, this would be a database session
        self.db = []

    def get_all(self) -> list[ItemResponse]:
        return [ItemResponse(id=i, **item) for i, item in enumerate(self.db)]

    def create(self, item_in: ItemCreate) -> ItemResponse:
        self.db.append(item_in.model_dump())
        item_id = len(self.db) - 1
        return ItemResponse(id=item_id, **item_in.model_dump())

    def get_by_id(self, item_id: int) -> ItemResponse:
        if item_id >= len(self.db) or item_id < 0:
            raise ItemNotFoundError(f"Item {item_id} not found")
        return ItemResponse(id=item_id, **self.db[item_id])


# --- Dependency Injection ---

def get_item_service() -> ItemService:
    # Singleton for demo purposes
    if not hasattr(get_item_service, "_instance"):
        get_item_service._instance = ItemService()
    return get_item_service._instance


# --- Router (Transport Layer) ---

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=list[ItemResponse])
def read_items(service: ItemService = Depends(get_item_service)) -> list[ItemResponse]:
    return service.get_all()

@router.post("/", response_model=ItemResponse)
def create_item(
    item_in: ItemCreate, 
    service: ItemService = Depends(get_item_service)
) -> ItemResponse:
    return service.create(item_in)

@router.get("/{item_id}", response_model=ItemResponse)
def read_item(
    item_id: int, 
    service: ItemService = Depends(get_item_service)
) -> ItemResponse:
    try:
        return service.get_by_id(item_id)
    except ItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
