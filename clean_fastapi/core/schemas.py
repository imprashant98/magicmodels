from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    page: Optional[int] = None
    size: Optional[int] = None
    items: List[T]
