from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Field:
    name: str
    type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_many_to_many: bool = False
    related_model: Optional[str] = None
    is_indexed: bool = False

@dataclass
class Model:
    name: str
    fields: List[Field] = field(default_factory=list)
