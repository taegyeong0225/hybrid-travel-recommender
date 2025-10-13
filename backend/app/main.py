from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .auth import router as auth_router
from .user_places import router as user_places_router

import logging
logging.basicConfig(level=logging.DEBUG)

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Middleware ---
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router)
app.include_router(user_places_router)

# --- Existing Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

# The recommendation endpoint from previous work
import subprocess
import json

@app.post("/recommend") # Changed to /recommend to match frontend request path
def recommend():
    # In a real app, consider a more robust way to run scripts
    result = subprocess.run(["python", "app/ml/main.py", "--json"], capture_output=True, text=True)
    output = result.stdout.strip()

    if result.returncode != 0 or not output:
        error_msg = result.stderr.strip()
        return {"error": "Failed to get recommendations", "details": error_msg}

    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse recommendation JSON: {str(e)}", "raw_output": output}
