import os
import sys
import json
import contextlib
import pandas as pd

# 실행 경로에 따라 import 깨지는 것 방지
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from .weather_api import WeatherAPI
from .recommender import TodayRecommender

# 설정
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") # .env.docker에 저장되어 있음
DATA_PATH = os.path.join(BASE_DIR, "tn_visit_area_info.csv")
SGG_PATH = os.path.join(BASE_DIR, "tc_sgg.csv")

def main():
    # 1. 데이터 로드
    df = pd.read_csv(DATA_PATH)

    # 2. SGG → SIDO 매핑
    try:
        sgg_df = pd.read_csv(SGG_PATH)

        # 필요한 컬럼만 추출 (SGG_CD, SIDO_NM)
        if "SIDO_NM" in sgg_df.columns:
            sgg_info = sgg_df[["SGG_CD", "SIDO_NM"]].drop_duplicates()
            sgg_info.rename(columns={"SIDO_NM": "SIDO"}, inplace=True)
        else:
            sgg_info = sgg_df[["SGG_CD", "SIDO"]].drop_duplicates()

        # 조인
        df = df.merge(sgg_info, on="SGG_CD", how="left")

    except FileNotFoundError:
        df["SIDO"] = "Unknown"

    # 3. Weather API 초기화
    weather_api = WeatherAPI(WEATHER_API_KEY)

    # 4. 추천 엔진 생성
    recommender = TodayRecommender(df, WEATHER_API_KEY)

    # 5. 추천 실행
    results = recommender.recommend(top_n=20)

    return results


if __name__ == "__main__":
    try:
        result = main()

        if "--json" in sys.argv:
            # stdout에 JSON만 출력 (FastAPI에서 읽을 수 있게)
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("데이터 로드 완료")
            print("=== 오늘의 추천 여행지 ===")
            for idx, rec in enumerate(result.get("recommendations", []), start=1):
                print(f"{idx}. {rec['name']} ({rec['region']}) - 점수 {rec['score']:.3f}")
            print("\n=== 메타데이터 ===")
            print(json.dumps(result.get("metadata", {}), ensure_ascii=False, indent=2))
            print("완료!")

    except Exception as e:
        # 오류 발생 시에도 JSON 형식으로 출력
        print(json.dumps({"error": str(e)}, ensure_ascii=False))