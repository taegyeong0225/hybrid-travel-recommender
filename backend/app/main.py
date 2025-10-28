import os
import json
import redis
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .auth import router as auth_router
from .user_places import router as user_places_router
from .ml.recommender import TodayRecommender
from .ml.weather_api import get_current_weather

import logging
logging.basicConfig(level=logging.INFO)

# --- App Initialization ---
models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# --- Redis Connection ---
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logging.info("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Could not connect to Redis: {e}")
    redis_client = None

# --- ML Model Loading ---
# Load data and model on startup to avoid reloading on every request
recommender = None
try:
    # This assumes your data loading logic is simple.
    # If ml/main.py does more complex setup, that logic should be properly modularized.
    df = pd.read_csv('app/ml/1.inputdata/tn_visit_area_info_E.csv')
    api_key = os.getenv("OPENWEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY")
    if api_key == "YOUR_OPENWEATHER_API_KEY":
        logging.warning("OPENWEATHER_API_KEY environment variable not set. Using a placeholder.")
    recommender = TodayRecommender(df, api_key)
    logging.info("Recommendation model loaded successfully.")
except FileNotFoundError:
    logging.error("Could not load recommendation data file. The recommender will not be available.")
except Exception as e:
    logging.error(f"An error occurred during model loading: {e}")


# --- Middleware ---
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
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


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.get("/recommend/{user_id}", response_model=schemas.RecommendationResponse)
def get_recommendations_with_caching(user_id: int, db: Session = Depends(get_db)):
    """
    Get travel recommendations for a user with Redis caching.

    - Caches results in Redis with a 30-minute TTL.
    - Invalidates cache if the date or weather has changed since the last recommendation.
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")
    if not recommender:
        raise HTTPException(status_code=503, detail="Recommendation service is not available.")

    # 1. Check user existence (optional but good practice)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cache_key = f"recommend:{user_id}"
    cached_data = redis_client.get(cache_key)
    current_date = datetime.now().date().isoformat()
    
    # For simplicity, we get weather for a default region. This could be user's region.
    current_weather = get_current_weather(sido="서울")

    # 2. Check cache validity
    if cached_data:
        try:
            cached_result = json.loads(cached_data)
            metadata = cached_result.get("metadata", {})
            stored_date = metadata.get("request_date")
            
            # The recommender's output contains a summary for multiple regions.
            # We'll check the weather for the primary region ('서울') for invalidation.
            stored_weather_summary = metadata.get("weather_summary", {})
            stored_seoul_weather = stored_weather_summary.get("서울", {}).get("condition")

            # Invalidate if date or weather has changed
            if stored_date == current_date and stored_seoul_weather == current_weather:
                logging.info(f"Cache HIT for user {user_id}. Returning cached recommendations.")
                return cached_result
            else:
                logging.info(f"Cache INVALIDATED for user {user_id}. Reason: Date/Weather changed.")
                redis_client.delete(cache_key)
        except (json.JSONDecodeError, KeyError) as e:
            logging.warning(f"Error decoding cache for user {user_id}: {e}. Regenerating.")


    # 3. Generate new recommendations if cache miss or invalid
    logging.info(f"Cache MISS for user {user_id}. Generating new recommendations.")
    
    # Although the model is not yet personalized, we call it here.
    # The user_id could be passed to the recommender in the future.
    new_recommendations = recommender.recommend(top_n=20)

    # Add request-time metadata for cache invalidation logic
    new_recommendations["metadata"]["request_date"] = current_date

    # 4. Store in Redis with a 30-minute TTL
    try:
        redis_client.set(cache_key, json.dumps(new_recommendations), ex=1800)
    except TypeError as e:
        # This can happen if the recommendation object is not JSON serializable
        logging.error(f"Failed to serialize recommendations for caching: {e}")
        # Still return the data to the user even if caching fails
        return new_recommendations

    return new_recommendations