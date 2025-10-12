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
def recommend():
    result = subprocess.run(["python", "app/ml/main.py", "--json"], capture_output=True)
    output = result.stdout.decode("utf-8").strip()

    if not output:
        return {"error": "모델 실행 결과가 비어 있습니다."}

    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        return {"error": f"JSON 파싱 실패: {str(e)}", "raw_output": output}