from icecream import ic
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.models.base import Base
from src.data.database import engine

from src.web.api import (
    auth as api_auth,
    users as api_users,
    messages as api_messages,
)
from src.web.views import (
    auth as views_auth,
    messages as views_chats,
    messages_ws as views_chats_ws,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ic("Starting up the application...")
    Base.metadata.create_all(bind=engine)

    yield

    ic("Shutting down the application...")
    # Base.metadata.drop_all(bind=engine)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_auth.router)
app.include_router(api_users.router)
app.include_router(api_messages.router)

app.include_router(views_auth.router)
app.include_router(views_chats.router)
app.include_router(views_chats_ws.router)

app.mount(
    "/static",
    StaticFiles(directory="src/frontend/static"),
    name="static",
)


@app.get("/", status_code=status.HTTP_302_FOUND, include_in_schema=False)
async def root():
    return RedirectResponse(
        url="/messages",
        status_code=status.HTTP_302_FOUND,
    )
