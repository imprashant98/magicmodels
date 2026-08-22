from sqlmodel import Session, select, col, desc, asc
from typing import List, Optional, Tuple
from .models import Comment
from .schemas import CommentFilter


class CommentService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, item_data: Comment) -> Comment:
        self.session.add(item_data)
        self.session.commit()
        self.session.refresh(item_data)
        return item_data

    def get_paginated(
        self,
        filters: CommentFilter,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[int, List[Comment]]:
        query = select(Comment)

        filter_dict = filters.dict(exclude_none=True)
        for key, value in filter_dict.items():
            if "__" in key:
                field, op = key.split("__")
                column = getattr(Comment, field)
                if op == "contains":
                    query = query.where(col(column).contains(value))
                elif op == "ilike":
                    query = query.where(col(column).ilike(f"%{value}%"))
                elif op == "gt":
                    query = query.where(column > value)
                elif op == "lt":
                    query = query.where(column < value)
            else:
                query = query.where(getattr(Comment, key) == value)
                
        if sort_by and hasattr(Comment, sort_by):
            column = getattr(Comment, sort_by)
            if order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

        total = len(self.session.exec(query).all())
        query = query.offset(skip).limit(limit)
        items = self.session.exec(query).all()
        return total, items

    def get_by_id(self, item_id: int) -> Optional[Comment]:
        return self.session.get(Comment, item_id)

    def update(self, item_id: int, item_data: Comment) -> Optional[Comment]:
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
