from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: str
    author: Optional[int] = Field(default=None, foreign_key='user.id')

