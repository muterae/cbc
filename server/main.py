# server/main.py
from fastapi import FastAPI

from routers.bands import router as bands_router
from routers.quiz import router as quiz_router

app = FastAPI(
    title="CBC Learning Companion API",
    version="0.1.0",
    description="Adaptive Grade 3 Mathematics quiz generation for Kenya's CBC.",
)

app.include_router(bands_router)
app.include_router(quiz_router)


@app.get("/")
def read_root():
    return {"message": "Hello World from cbc!"}
