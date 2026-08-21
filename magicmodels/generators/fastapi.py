import os
from typing import List
from .base import BaseGenerator
from ..schema import Model, Field

class FastAPIGenerator(BaseGenerator):
    def _map_type(self, field: Field) -> str:
        t = field.type.lower()
        if t == "string":
            py_type = "str"
        elif t == "int":
            py_type = "int"
        elif t == "boolean":
            py_type = "bool"
        elif t == "text":
            py_type = "str"
        elif t == "datetime":
            py_type = "datetime"
        else:
            py_type = "str"

        if field.is_primary_key:
            return f"Optional[{py_type}] = Field(default=None, primary_key=True)"
        elif field.is_foreign_key:
            return f"Optional[int] = Field(default=None, foreign_key='{field.related_model.lower()}.id')"
        
        if field.is_indexed:
            return f"{py_type} = Field(index=True)"
            
        return py_type

    def generate(self, models: List[Model], output_dir: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "core"), exist_ok=True)
        
        # core/security.py
        security_code = """from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Mock authentication for parity with magicapi
    if token != "magicapi-secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": "admin"}
"""
        with open(os.path.join(output_dir, "core", "security.py"), "w") as f:
            f.write(security_code)
            
        with open(os.path.join(output_dir, "core", "__init__.py"), "w") as f:
            f.write("")

        # database.py
        db_code = """from sqlmodel import SQLModel, create_engine, Session
import os

sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
"""
        with open(os.path.join(output_dir, "database.py"), "w") as f:
            f.write(db_code)
            
        # Domain modules
        router_imports = []
        model_imports_for_db = []
        for model in models:
            lower_name = model.name.lower()
            app_dir = os.path.join(output_dir, lower_name)
            os.makedirs(app_dir, exist_ok=True)
            
            with open(os.path.join(app_dir, "__init__.py"), "w") as f:
                f.write("")
                
            router_imports.append(f"from {lower_name}.router import router as {lower_name}_router")
            model_imports_for_db.append(f"from {lower_name}.models import {model.name}")
            
            # 1. models.py
            models_code = "from typing import Optional, List\nfrom datetime import datetime\nfrom sqlmodel import Field, SQLModel\n\n"
            models_code += f"class {model.name}(SQLModel, table=True):\n"
            string_fields = []
            for field in model.fields:
                if field.is_many_to_many:
                    continue
                type_str = self._map_type(field)
                models_code += f"    {field.name}: {type_str}\n"
                if field.type.lower() in ("string", "text"):
                    string_fields.append(field.name)
            models_code += "\n"
            with open(os.path.join(app_dir, "models.py"), "w") as f:
                f.write(models_code)
                
            # 2. schemas.py
            schemas_code = "from sqlmodel import SQLModel\n\n# Put Pydantic validation schemas here if needed\n"
            with open(os.path.join(app_dir, "schemas.py"), "w") as f:
                f.write(schemas_code)

            # 3. utils.py
            utils_code = f"# Utility functions for {model.name}\n"
            with open(os.path.join(app_dir, "utils.py"), "w") as f:
                f.write(utils_code)

            # 4. router.py
            # Build dynamic search filter logic
            search_logic = ""
            if string_fields:
                search_logic += "    if search:\n"
                search_logic += "        query = query.where(\n"
                search_logic += "            or_(\n"
                for sf in string_fields:
                    search_logic += f"                col({model.name}.{sf}).contains(search),\n"
                search_logic += "            )\n"
                search_logic += "        )\n"

            router_code = f"""from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, col, or_, desc, asc
from database import get_session
from core.security import get_current_user
from .models import {model.name}

router = APIRouter(prefix="/{lower_name}s", tags=["{model.name}"])

@router.post("/", response_model={model.name})
def create_{lower_name}(item: {model.name}, session: Session = Depends(get_session), current_user: dict = Depends(get_current_user)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/", response_model=List[{model.name}])
def read_{lower_name}s(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = "asc"
):
    query = select({model.name})
{search_logic}
    if sort_by and hasattr({model.name}, sort_by):
        column = getattr({model.name}, sort_by)
        if order == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))
            
    query = query.offset(skip).limit(limit)
    return session.exec(query).all()

@router.get("/{{item_id}}", response_model={model.name})
def read_{lower_name}(item_id: int, session: Session = Depends(get_session)):
    item = session.get({model.name}, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="{model.name} not found")
    return item

@router.patch("/{{item_id}}", response_model={model.name})
def update_{lower_name}(item_id: int, item_data: {model.name}, session: Session = Depends(get_session), current_user: dict = Depends(get_current_user)):
    item = session.get({model.name}, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="{model.name} not found")
    update_data = item_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/{{item_id}}")
def delete_{lower_name}(item_id: int, session: Session = Depends(get_session), current_user: dict = Depends(get_current_user)):
    item = session.get({model.name}, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="{model.name} not found")
    session.delete(item)
    session.commit()
    return {{"ok": True}}
"""
            with open(os.path.join(app_dir, "router.py"), "w") as f:
                f.write(router_code)

        # Append models to database.py so SQLModel detects them
        with open(os.path.join(output_dir, "database.py"), "a") as f:
            f.write("\n")
            f.write("\n".join(model_imports_for_db))
            f.write("\n")

        # main.py
        main_code = "from fastapi import FastAPI\nfrom database import create_db_and_tables\n"
        main_code += "\n".join(router_imports) + "\n\n"
        main_code += "app = FastAPI()\n\n"
        main_code += "@app.on_event('startup')\ndef on_startup():\n    create_db_and_tables()\n\n"
        for model in models:
            lower_name = model.name.lower()
            main_code += f"app.include_router({lower_name}_router)\n"
            
        with open(os.path.join(output_dir, "main.py"), "w") as f:
            f.write(main_code)

        # requirements.txt
        req_code = "fastapi==0.110.0\nsqlmodel==0.0.16\nuvicorn==0.27.1\n"
        with open(os.path.join(output_dir, "requirements.txt"), "w") as f:
            f.write(req_code)

        # Dockerfile
        dockerfile_code = """FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile_code)

        # docker-compose.yml
        compose_code = """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
"""
        with open(os.path.join(output_dir, "docker-compose.yml"), "w") as f:
            f.write(compose_code)
