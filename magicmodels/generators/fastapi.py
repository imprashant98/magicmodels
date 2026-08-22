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
        
        # .env.example
        env_code = """DATABASE_URL=sqlite:///database.db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
        with open(os.path.join(output_dir, ".env.example"), "w") as f:
            f.write(env_code)

        # core/config.py
        config_code = """from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///database.db"
    SECRET_KEY: str = "your-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
"""
        with open(os.path.join(output_dir, "core", "config.py"), "w") as f:
            f.write(config_code)

        # core/security.py
        security_code = """from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username}
"""
        with open(os.path.join(output_dir, "core", "security.py"), "w") as f:
            f.write(security_code)
            
        # core/exceptions.py
        exceptions_code = """from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"message": "A database error occurred. Check inputs."},
    )
"""
        with open(os.path.join(output_dir, "core", "exceptions.py"), "w") as f:
            f.write(exceptions_code)
            
        # auth/router.py
        os.makedirs(os.path.join(output_dir, "auth"), exist_ok=True)
        with open(os.path.join(output_dir, "auth", "__init__.py"), "w") as f:
            f.write("")
        auth_router_code = """from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from core.security import create_access_token
from core.config import settings
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Example placeholder: replace with actual DB user lookup
    if form_data.username != "admin" or form_data.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
"""
        with open(os.path.join(output_dir, "auth", "router.py"), "w") as f:
            f.write(auth_router_code)
            
        with open(os.path.join(output_dir, "core", "__init__.py"), "w") as f:
            f.write("")
            
        # core/schemas.py
        core_schemas_code = """from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    page: Optional[int] = None
    size: Optional[int] = None
    items: List[T]
"""
        with open(os.path.join(output_dir, "core", "schemas.py"), "w") as f:
            f.write(core_schemas_code)

        # database.py
        db_code = """from sqlmodel import create_engine, Session
from core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
"""
        with open(os.path.join(output_dir, "database.py"), "w") as f:
            f.write(db_code)
            
        # alembic.ini
        alembic_ini_code = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = sqlite:///database.db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        with open(os.path.join(output_dir, "alembic.ini"), "w") as f:
            f.write(alembic_ini_code)

        # alembic/env.py
        os.makedirs(os.path.join(output_dir, "alembic", "versions"), exist_ok=True)
        alembic_env_code = """import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from sqlmodel import SQLModel
from core.config import settings

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import all models here so SQLModel.metadata has them!
"""
        for model in models:
            alembic_env_code += f"from {model.name.lower()}.models import {model.name}\n"
        
        alembic_env_code += """
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
        with open(os.path.join(output_dir, "alembic", "env.py"), "w") as f:
            f.write(alembic_env_code)
            
        # Domain modules
        router_imports = []
        model_imports_for_db = []
        for model in models:
            lower_name = model.name.lower()
            app_dir = os.path.join(output_dir, lower_name)
            
            router_imports.append(f"from {lower_name}.router import router as {lower_name}_router")
            model_imports_for_db.append(f"from {lower_name}.models import {model.name}")
            
            if os.path.exists(app_dir):
                print(f"FastAPI app for '{model.name}' already exists. Skipping generation to preserve your code.")
                continue
                
            os.makedirs(app_dir, exist_ok=True)
            
            with open(os.path.join(app_dir, "__init__.py"), "w") as f:
                f.write("")
            
            # 1. models.py
            models_code = "from typing import Optional\nfrom sqlmodel import Field, SQLModel\n"
            string_fields = []
            has_datetime = False
            for field in model.fields:
                if field.type.lower() == "datetime":
                    has_datetime = True
                if field.type.lower() in ("string", "text"):
                    string_fields.append(field.name)
                    
            if has_datetime:
                models_code += "from datetime import datetime\n"
                
            models_code += "\n\n"
            models_code += f"class {model.name}(SQLModel, table=True):\n"
            
            for field in model.fields:
                if field.is_many_to_many:
                    continue
                type_str = self._map_type(field)
                models_code += f"    {field.name}: {type_str}\n"
                if field.type.lower() in ("string", "text"):
                    string_fields.append(field.name)
            with open(os.path.join(app_dir, "models.py"), "w") as f:
                f.write(models_code)
                
            # 2. schemas.py
            filter_fields = ""
            for field in model.fields:
                if field.is_many_to_many or field.is_foreign_key:
                     continue
                py_type = self._map_type(field).split("=")[0].strip()
                if py_type.startswith("Optional["):
                    base_py_type = py_type[9:-1]
                else:
                    base_py_type = py_type
                    
                filter_fields += f"    {field.name}: Optional[{base_py_type}] = None\n"
                if base_py_type == "str":
                    filter_fields += f"    {field.name}__contains: Optional[{base_py_type}] = None\n"
                    filter_fields += f"    {field.name}__ilike: Optional[{base_py_type}] = None\n"
                if base_py_type in ("int", "datetime"):
                    filter_fields += f"    {field.name}__gt: Optional[{base_py_type}] = None\n"
                    filter_fields += f"    {field.name}__lt: Optional[{base_py_type}] = None\n"

            schemas_code = "from pydantic import BaseModel\nfrom typing import Optional\n"
            if "datetime" in filter_fields:
                schemas_code += "from datetime import datetime\n"
            schemas_code += "\n\n"
            schemas_code += f"class {model.name}Filter(BaseModel):\n"
            schemas_code += filter_fields if filter_fields else "    pass\n"
            with open(os.path.join(app_dir, "schemas.py"), "w") as f:
                f.write(schemas_code)

            # 3. utils.py
            utils_code = f"# Utility functions for {model.name}\n"
            with open(os.path.join(app_dir, "utils.py"), "w") as f:
                f.write(utils_code)

            # 5. services.py
            services_code = f"""from sqlmodel import Session, select, col, desc, asc
from typing import List, Optional, Tuple
from .models import {model.name}
from .schemas import {model.name}Filter


class {model.name}Service:
    def __init__(self, session: Session):
        self.session = session

    def create(self, item_data: {model.name}) -> {model.name}:
        self.session.add(item_data)
        self.session.commit()
        self.session.refresh(item_data)
        return item_data

    def get_paginated(
        self,
        filters: {model.name}Filter,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[int, List[{model.name}]]:
        query = select({model.name})

        filter_dict = filters.dict(exclude_none=True)
        for key, value in filter_dict.items():
            if "__" in key:
                field, op = key.split("__")
                column = getattr({model.name}, field)
                if op == "contains":
                    query = query.where(col(column).contains(value))
                elif op == "ilike":
                    query = query.where(col(column).ilike(f"%{{value}}%"))
                elif op == "gt":
                    query = query.where(column > value)
                elif op == "lt":
                    query = query.where(column < value)
            else:
                query = query.where(getattr({model.name}, key) == value)
                
        if sort_by and hasattr({model.name}, sort_by):
            column = getattr({model.name}, sort_by)
            if order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

        total = len(self.session.exec(query).all())
        query = query.offset(skip).limit(limit)
        items = self.session.exec(query).all()
        return total, items

    def get_by_id(self, item_id: int) -> Optional[{model.name}]:
        return self.session.get({model.name}, item_id)

    def update(self, item_id: int, item_data: {model.name}) -> Optional[{model.name}]:
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
"""
            with open(os.path.join(app_dir, "services.py"), "w") as f:
                f.write(services_code)

            # 4. router.py
            router_code = f"""from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from database import get_session
from core.security import get_current_user
from core.schemas import PaginatedResponse
from .models import {model.name}
from .schemas import {model.name}Filter
from .services import {model.name}Service

router = APIRouter(prefix="/{lower_name}s", tags=["{model.name}"])


def get_service(
    session: Session = Depends(get_session)
) -> {model.name}Service:
    return {model.name}Service(session)


@router.post("/", response_model={model.name})
def create_{lower_name}(
    item: {model.name},
    service: {model.name}Service = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[{model.name}])
def read_{lower_name}s(
    filters: {model.name}Filter = Depends(),
    service: {model.name}Service = Depends(get_service),
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

    total, items = service.get_paginated(
        filters, actual_skip, actual_limit, sort_by, order
    )

    return {{
        "total": total,
        "skip": actual_skip,
        "limit": actual_limit,
        "page": page,
        "size": size,
        "items": items
    }}


@router.get("/{{item_id}}", response_model={model.name})
def read_{lower_name}(
    item_id: int,
    service: {model.name}Service = Depends(get_service)
):
    item = service.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="{model.name} not found")
    return item


@router.patch("/{{item_id}}", response_model={model.name})
def update_{lower_name}(
    item_id: int,
    item_data: {model.name},
    service: {model.name}Service = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    item = service.update(item_id, item_data)
    if not item:
        raise HTTPException(status_code=404, detail="{model.name} not found")
    return item


@router.delete("/{{item_id}}")
def delete_{lower_name}(
    item_id: int,
    service: {model.name}Service = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    success = service.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="{model.name} not found")
    return {{"ok": True}}
"""
            with open(os.path.join(app_dir, "router.py"), "w") as f:
                f.write(router_code)

        # Do not append models to database.py so we avoid unused imports
        # They are now dynamically added to alembic/env.py

        # main.py
        main_code = "from fastapi import FastAPI\nfrom fastapi.responses import RedirectResponse\n"
        main_code += "from core.exceptions import sqlalchemy_exception_handler\nfrom sqlalchemy.exc import SQLAlchemyError\n"
        main_code += "from auth.router import router as auth_router\n"
        main_code += "\n".join(router_imports) + "\n\n\n"
        main_code += "app = FastAPI()\n\n"
        main_code += "app.add_exception_handler(\n"
        main_code += "    SQLAlchemyError, sqlalchemy_exception_handler\n)\n\n"
        main_code += "app.include_router(auth_router)\n"
        for model in models:
            lower_name = model.name.lower()
            main_code += f"app.include_router({lower_name}_router)\n\n\n"
        main_code += "@app.get('/')\ndef read_root():\n    return RedirectResponse(url='/docs')\n"
        
        with open(os.path.join(output_dir, "main.py"), "w") as f:
            f.write(main_code)
            
        # Tests setup
        os.makedirs(os.path.join(output_dir, "tests"), exist_ok=True)
        pytest_ini_code = """[pytest]
asyncio_mode = auto
"""
        with open(os.path.join(output_dir, "pytest.ini"), "w") as f:
            f.write(pytest_ini_code)
            
        conftest_code = """import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel, Session, create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from main import app  # noqa: E402
from database import get_session  # noqa: E402

# Use an in-memory SQLite for testing
sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
"""
        with open(os.path.join(output_dir, "tests", "conftest.py"), "w") as f:
            f.write(conftest_code)
            
        # Generate basic CRUD tests for each model
        for model in models:
            lower_name = model.name.lower()
            test_file = os.path.join(output_dir, "tests", f"test_{lower_name}.py")
            if os.path.exists(test_file):
                continue
            test_code = f"""from fastapi.testclient import TestClient

# Note: Tests will return 401 if not authenticated.
# To fully test CRUD, override the auth dependency in conftest.py
# or generate a mock token.


def test_read_{lower_name}s(client: TestClient):
    response = client.get("/{lower_name}s/")
    # Ensure it returns 401 Unauthorized initially since we added JWT auth
    assert response.status_code == 401
"""
            with open(os.path.join(output_dir, "tests", f"test_{lower_name}.py"), "w") as f:
                f.write(test_code)

        # requirements.txt
        req_code = "fastapi==0.110.0\nsqlmodel==0.0.16\nuvicorn==0.27.1\ngunicorn==21.2.0\npydantic-settings==2.2.1\npython-jose[cryptography]==3.3.0\npasslib[bcrypt]==1.7.4\nalembic==1.13.1\npytest==8.0.2\npytest-asyncio==0.23.5\nhttpx==0.27.0\n"
        with open(os.path.join(output_dir, "requirements.txt"), "w") as f:
            f.write(req_code)

        # Dockerfile
        dockerfile_code = """FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
"""
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile_code)

        # docker-compose.yml
        available_port = self.find_available_port()
        compose_code = f"""version: '3.8'
services:
  api:
    build: .
    ports:
      - "{available_port}:8000"
    volumes:
      - .:/app
    command: >
      bash -c "alembic upgrade head && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --reload"
"""
        with open(os.path.join(output_dir, "docker-compose.yml"), "w") as f:
            f.write(compose_code)
