from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

import json

class RequestData(BaseModel):
    region: str
    user_id: Optional[str] = None

@app.post("/recommend")
def recommend(data: RequestData):
    region_map = {
        "E_capital": "E",
        "F_east": "F",
        "G_west": "G",
        "H_jeju": "H",
    }
    region_id = region_map.get(data.region)
    if not region_id:
        return {"error": "Invalid region"}

    user_id = data.user_id or "e000004"

    script = os.path.join(BASE_DIR, "ml", "recommender.py")

    try:
        result = subprocess.check_output(["python", script, region_id, user_id], stderr=subprocess.STDOUT)
        return json.loads(result.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        return {"error": e.output.decode("utf-8")}