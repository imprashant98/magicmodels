from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from database import get_session
from core.security import get_current_user
from core.schemas import PaginatedResponse
from .models import User
from .schemas import UserFilter
from .services import UserService

router = APIRouter(prefix="/users", tags=["User"])

def get_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(session)

@router.post("/", response_model=User)
def create_user(item: User, service: UserService = Depends(get_service), current_user: dict = Depends(get_current_user)):
    return service.create(item)

@router.get("/", response_model=PaginatedResponse[User])
def read_users(
    filters: UserFilter = Depends(),
    service: UserService = Depends(get_service),
    page: Optional[int] = Query(None, ge=1),
    size: Optional[int] = Query(None, ge=1, le=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = None,
    order: Optional[str] = "asc"
):
    actual_skip = skip
    actual_limit = limit
    if page is not None and size is not None:
        actual_limit = size
        actual_skip = (page - 1) * size
    elif page is not None:
        actual_skip = (page - 1) * limit
    elif size is not None:
        actual_limit = size

    total, items = service.get_paginated(filters, actual_skip, actual_limit, sort_by, order)
    
    return {
        "total": total,
        "skip": actual_skip,
        "limit": actual_limit,
        "page": page,
        "size": size,
        "items": items
    }

@router.get("/{item_id}", response_model=User)
def read_user(item_id: int, service: UserService = Depends(get_service)):
    item = service.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    return item

@router.patch("/{item_id}", response_model=User)
def update_user(item_id: int, item_data: User, service: UserService = Depends(get_service), current_user: dict = Depends(get_current_user)):
    item = service.update(item_id, item_data)
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    return item

@router.delete("/{item_id}")
def delete_user(item_id: int, service: UserService = Depends(get_service), current_user: dict = Depends(get_current_user)):
    success = service.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
