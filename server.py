import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.video import router as video_router
from routes.search import router as search_router
from services.model_registry import ModelRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up models once at startup so the first request isn't slow.
    registry = ModelRegistry.get()
    registry.load_all()
    yield
    registry.release()


app = FastAPI(
    title="VideoRAG API",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(video_router, prefix="/api")
app.include_router(search_router, prefix="/api")

# Serve the frontend from the same process when running locally.
_frontend = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_frontend):
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")
else:
    # Serve from same directory (HuggingFace Spaces)
    _local = os.path.dirname(__file__)
    if os.path.exists(os.path.join(_local, "index.html")):
        app.mount("/", StaticFiles(directory=_local, html=True), name="frontend")
