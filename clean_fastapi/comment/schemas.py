from pydantic import BaseModel
from typing import Optional


class CommentFilter(BaseModel):
    id: Optional[int] = None
    id__gt: Optional[int] = None
    id__lt: Optional[int] = None
    body: Optional[str] = None
    body__contains: Optional[str] = None
    body__ilike: Optional[str] = None
