# server/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from retriever import load_query_vectors
from routers.bands import router as bands_router
from routers.intro_quiz import router as intro_quiz_router
from routers.profiles import router as profiles_router
from routers.quiz import router as quiz_router

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the precomputed query vectors before serving traffic.

    This is a ~150 KB JSON read, not a model load, so it is cheap. Doing it here
    means the first learner request does not pay for it, and a missing or corrupt
    cache is logged at boot instead of surfacing as a silent fallback later.
    """
    try:
        load_query_vectors()
    except Exception as exc:  # noqa: BLE001 - never block startup on the cache
        log.warning("Query vector cache unavailable at startup: %s", exc)
    yield


app = FastAPI(
    title="CBC Learning Companion API",
    version="0.1.0",
    description="Adaptive Grade 3 Mathematics quiz generation for Kenya's CBC.",
    lifespan=lifespan,
)

app.include_router(bands_router)
app.include_router(intro_quiz_router)
app.include_router(profiles_router)
app.include_router(quiz_router)


@app.get("/")
def read_root():
    return {"message": "Hello World from cbc!"}
