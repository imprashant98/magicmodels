from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserFilter(BaseModel):
    id: Optional[int] = None
    id__gt: Optional[int] = None
    id__lt: Optional[int] = None
    username: Optional[str] = None
    username__contains: Optional[str] = None
    username__ilike: Optional[str] = None
    email: Optional[str] = None
    email__contains: Optional[str] = None
    email__ilike: Optional[str] = None
    created_at: Optional[datetime] = None
    created_at__gt: Optional[datetime] = None
    created_at__lt: Optional[datetime] = None
    posts: Optional[str] = None
    posts__contains: Optional[str] = None
    posts__ilike: Optional[str] = None
