from typing import Optional
from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    body: str
    post: Optional[int] = Field(default=None, foreign_key='post.id')
    user: Optional[int] = Field(default=None, foreign_key='user.id')
