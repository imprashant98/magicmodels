from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, col, desc, asc
from database import get_session
from core.security import get_current_user
from core.schemas import PaginatedResponse
from .models import Post
from .schemas import PostFilter

router = APIRouter(prefix="/posts", tags=["Post"])

@router.post("/", response_model=Post)
def create_post(item: Post, session: Session = Depends(get_session), current_user: dict = Depends(get_current_user)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/", response_model=PaginatedResponse[Post])
def read_posts(
    filters: PostFilter = Depends(),
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = None,
    order: Optional[str] = "asc"
):
    query = select(Post)
    
    filter_dict = filters.dict(exclude_none=True)
    for key, value in filter_dict.items():
        if "__" in key:
            field, op = key.split("__")
            column = getattr(Post, field)
            if op == "contains":
                query = query.where(col(column).contains(value))
            elif op == "ilike":
                query = query.where(col(column).ilike(f"%{value}%"))
            elif op == "gt":
                query = query.where(column > value)
            elif op == "lt":
                query = query.where(column < value)
        else:
            query = query.where(getattr(Post, key) == value)
            
    if sort_by and hasattr(Post, sort_by):
        column = getattr(Post, sort_by)
        if order == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
            
    total = len(session.exec(query).all())
    query = query.offset(skip).limit(limit)
    items = session.exec(query).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items
    }

@router.get("/{item_id}", response_model=Post)
def read_post(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Post, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    return item

@router.patch("/{item_id}", response_model=Post)
def update_post(item_id: int, item_data: Post, session: Session = Depends(get_session), current_user: dict = Depends(get_current_user)):
    item = session.get(Post, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    update_data = item_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_post(item_id: int, session: Session = Depends(get_session), current_user: dict = Depends(get_current_user)):
    item = session.get(Post, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Post not found")
    session.delete(item)
    session.commit()
    return {"ok": True}
