from pydantic import BaseModel
from typing import Optional


class PostFilter(BaseModel):
    id: Optional[int] = None
    id__gt: Optional[int] = None
    id__lt: Optional[int] = None
    title: Optional[str] = None
    title__contains: Optional[str] = None
    title__ilike: Optional[str] = None
    body: Optional[str] = None
    body__contains: Optional[str] = None
    body__ilike: Optional[str] = None
