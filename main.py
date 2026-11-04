# app/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import List


app = FastAPI()





@app.get("/")
def read_root():
    return {"message": "Hello World from cbc!"}



@app.get("/generate")
async def get_generated_quiz():
    pass
