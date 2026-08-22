from sqlmodel import Session, select, col, desc, asc
from typing import List, Optional, Tuple
from .models import Post
from .schemas import PostFilter

class PostService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, item_data: Post) -> Post:
        self.session.add(item_data)
        self.session.commit()
        self.session.refresh(item_data)
        return item_data

    def get_paginated(
        self,
        filters: PostFilter,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[int, List[Post]]:
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
                
        total = len(self.session.exec(query).all())
        query = query.offset(skip).limit(limit)
        items = self.session.exec(query).all()
        return total, items

    def get_by_id(self, item_id: int) -> Optional[Post]:
        return self.session.get(Post, item_id)

    def update(self, item_id: int, item_data: Post) -> Optional[Post]:
        item = self.get_by_id(item_id)
        if not item:
            return None
        update_data = item_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get_by_id(item_id)
        if not item:
            return False
        self.session.delete(item)
        self.session.commit()
        return True
