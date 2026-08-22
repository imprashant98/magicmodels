from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from core.exceptions import sqlalchemy_exception_handler
from sqlalchemy.exc import SQLAlchemyError
from auth.router import router as auth_router
from user.router import router as user_router
from post.router import router as post_router

app = FastAPI()

app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

app.include_router(auth_router)
@app.get('/')
def read_root():
    return RedirectResponse(url='/docs')

app.include_router(user_router)
app.include_router(post_router)
