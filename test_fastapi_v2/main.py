from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from database import create_db_and_tables
from user.router import router as user_router
from post.router import router as post_router

app = FastAPI()

@app.get('/')
def read_root():
    return RedirectResponse(url='/docs')

@app.on_event('startup')
def on_startup():
    create_db_and_tables()

app.include_router(user_router)
app.include_router(post_router)
