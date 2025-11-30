import os
import json
import redis
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .auth import router as auth_router
from .user_places import router as user_places_router
from .ml.recommender import TodayRecommender
from .ml.weather_api import WeatherAPI

import logging
logging.basicConfig(level=logging.INFO)

import requests

# --- 앱 초기화 ---
models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# --- 정적 파일 ---
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logging.info(f"Static files mounted from: {static_dir}")
else:
    logging.warning(f"Static directory not found: {static_dir}")

# --- Redis 연결 ---
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logging.info("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Could not connect to Redis: {e}")
    redis_client = None

# --- ML 모델 로딩 ---
# 매 요청마다 다시 로드하지 않도록 시작 시 데이터와 모델을 로드합니다
recommender = None
try:
    # 데이터 로딩 로직이 간단하다고 가정합니다.
    # ml/main.py가 더 복잡한 설정을 수행한다면, 해당 로직은 적절히 모듈화되어야 합니다.
    df = pd.read_csv('app/ml/tn_visit_area_info_all_with_sido_v3.csv')
    api_key = os.getenv("OPENWEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY")
    if api_key == "YOUR_OPENWEATHER_API_KEY":
        logging.warning("OPENWEATHER_API_KEY environment variable not set. Using a placeholder.")
    recommender = TodayRecommender(df, api_key)
    logging.info("Recommendation model loaded successfully.")
except FileNotFoundError:
    logging.error("Could not load recommendation data file. The recommender will not be available.")
except Exception as e:
    logging.error(f"An error occurred during model loading: {e}")


# --- 미들웨어 ---
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 ---
app.include_router(auth_router, prefix="/api")
app.include_router(user_places_router, prefix="/api")


# --- 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

# 이전 작업의 추천 엔드포인트
import subprocess
import json
import math

def clean_float_values(obj):
    if isinstance(obj, dict):
        return {k: clean_float_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_float_values(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        else:
            return obj
    else:
        return obj

@app.post("/recommend")
def recommend():
    # --- Redis 연결 확인 ---
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service unavailable")

    cache_key = "recommend:default"
    cached_data = redis_client.get(cache_key)
    current_date = datetime.now().date().isoformat()

    # --- 현재 날씨 확인 (서울 기준) ---
    api_key = os.getenv("OPENWEATHER_API_KEY")
    weather_client = WeatherAPI(api_key)
    current_weather = weather_client.get_weather("서울")
    current_condition = current_weather.get("condition", "unknown")

    # --- 캐시 HIT 여부 확인 ---
    if cached_data:
        try:
            cached = json.loads(cached_data)
            metadata = cached.get("metadata", {})
            cached_date = metadata.get("request_date")
            cached_condition = metadata.get("weather_condition")

            if cached_date == current_date and cached_condition == current_condition:
                logging.info("[CACHE HIT] /recommend — same date & weather, reusing results")
                return cached
            else:
                logging.info("[CACHE INVALID] date/weather changed → regenerating")
                redis_client.delete(cache_key)
        except Exception as e:
            logging.warning(f"[CACHE ERROR] decoding failed: {e}")

    # --- 캐시 MISS → 새로 추천 생성 ---
    logging.info("[CACHE MISS] running recommender subprocess")
    result = subprocess.run(["python", "-m", "app.ml.main", "--json"], capture_output=True, text=True)
    output = result.stdout.strip()

    if result.returncode != 0 or not output:
        error_msg = result.stderr.strip()
        return {"error": "Failed to get recommendations", "details": error_msg}

    try:
        data = json.loads(output)
        data.setdefault("metadata", {})
        data["metadata"]["request_date"] = current_date
        data["metadata"]["weather_condition"] = current_condition

        # Redis에 결과를 30분 동안 캐싱
        redis_client.set(cache_key, json.dumps(data, ensure_ascii=False), ex=1800)

        logging.info("[CACHE SAVE] stored new recommendation result in Redis")
        return data

    except json.JSONDecodeError:
        return {"error": "Invalid JSON output", "raw_output": output}

@app.get("/recommend/{user_id}", response_model=schemas.RecommendationResponse)
def get_recommendations_with_caching(user_id: int, db: Session = Depends(get_db)):
    """
    Redis 캐싱을 사용하여 사용자를 위한 여행 추천을 가져옵니다.

    - 결과를 Redis에 30분 TTL로 캐시합니다.
    - 마지막 추천 이후 날짜나 날씨가 변경된 경우 캐시를 무효화합니다.
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")
    if not recommender:
        raise HTTPException(status_code=503, detail="Recommendation service is not available.")

    # 1. 사용자 존재 확인 (선택 사항이지만 권장됨)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cache_key = f"recommend:{user_id}"
    cached_data = redis_client.get(cache_key)
    current_date = datetime.now().date().isoformat()
    
    # API 키 세팅 (기존 변수 사용)
    weather_client = WeatherAPI(api_key=WEATHER_API_KEY)

    # 간단하게 하기 위해 기본 지역의 날씨를 가져옵니다. 이는 사용자의 지역이 될 수 있습니다.
    current_weather = weather_client.get_weather(sido="서울")

    # 2. 캐시 유효성 확인
    if cached_data:
        try:
            cached_result = json.loads(cached_data)
            metadata = cached_result.get("metadata", {})
            stored_date = metadata.get("request_date")
            
            # 추천기의 출력에는 여러 지역에 대한 요약이 포함되어 있습니다.
            # 무효화를 위해 주요 지역('서울')의 날씨를 확인합니다.
            stored_weather_summary = metadata.get("weather_summary", {})
            stored_seoul_weather = stored_weather_summary.get("서울", {}).get("condition")

            # 날짜나 날씨가 변경된 경우 무효화
            if stored_date == current_date and stored_seoul_weather == current_weather:
                logging.info(f"Cache HIT for user {user_id}. Returning cached recommendations.")
                return cached_result
            else:
                logging.info(f"Cache INVALIDATED for user {user_id}. Reason: Date/Weather changed.")
                redis_client.delete(cache_key)
        except (json.JSONDecodeError, KeyError) as e:
            logging.warning(f"Error decoding cache for user {user_id}: {e}. Regenerating.")


    # 3. 캐시 미스 또는 무효인 경우 새로운 추천 생성
    logging.info(f"Cache MISS for user {user_id}. Generating new recommendations.")
    
    # 모델이 아직 개인화되지 않았지만, 여기에서 호출합니다.
    # user_id는 향후 추천기에 전달될 수 있습니다.
    new_recommendations = recommender.recommend(top_n=30)

    # 캐시 무효화 로직을 위한 요청 시간 메타데이터 추가
    new_recommendations["metadata"]["request_date"] = current_date

    # 4. 30분 TTL로 Redis에 저장
    try:
        redis_client.set(cache_key, json.dumps(new_recommendations), ex=1800)
    except TypeError as e:
        # 추천 객체가 JSON 직렬화 불가능한 경우 발생할 수 있습니다
        logging.error(f"Failed to serialize recommendations for caching: {e}")
        # 캐싱이 실패하더라도 사용자에게 데이터를 반환합니다
        return new_recommendations

    return new_recommendations



# 이미지 추가
@app.get("/image")
def get_tour_image(place: str):
    """
    장소명 기반 관광사진 정보 조회 API
    - 한국관광공사 TourAPI (데이터 ID: 15101914)
    - Redis 캐시 적용 (30분 TTL)
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service unavailable")

    # 캐시 키
    cache_key = f"image:{place}"
    cached_url = redis_client.get(cache_key)
    if cached_url:
        logging.info(f"[CACHE HIT] image for '{place}'")
        return {"place": place, "image_url": cached_url}

    # 환경 변수에서 API 키 불러오기
    TOURAPI_KEY = os.getenv("TOURAPI_KEY")
    if not TOURAPI_KEY:
        raise HTTPException(status_code=500, detail="TOURAPI_KEY not set")

    # 관광사진정보 API 요청
    url = (
        f"http://apis.data.go.kr/B551011/PhotoGalleryService1/gallerySearchList1"
        f"?serviceKey={TOURAPI_KEY}&keyword={place}&_type=json"
    )

    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            return {"place": place, "image_url": None, "message": "No image found"}

        # 대표 이미지 선택 (첫 번째 항목)
        image_url = items[0].get("galWebImageUrl")

        # Redis에 캐싱 (TTL 30분)
        if image_url:
            redis_client.set(cache_key, image_url, ex=1800)
            logging.info(f"[CACHE SAVE] stored image for '{place}' in Redis")

        return {"place": place, "image_url": image_url}

    except requests.RequestException as e:
        logging.error(f"Failed to fetch image for {place}: {e}")
        raise HTTPException(status_code=500, detail="Image fetch failed")