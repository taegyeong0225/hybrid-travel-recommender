import pandas as pd
import json
import os
from datetime import datetime

from .weather_api import WeatherAPI
from .popularity_calculator import PopularityCalculator
from .context_booster import ContextBooster
from .tour_image_api import TourImageAPI
from .image_utils import get_place_image

class TodayRecommender:
    """오늘의 추천 엔진"""

    def __init__(self, df: pd.DataFrame, weather_api_key: str):
        self.df = df
        self.weather_api = WeatherAPI(weather_api_key)
        self.context_booster = ContextBooster()
        self.image_map = self._load_image_map()
        self.tour_image_api = TourImageAPI()  # 한국관광공사 API 클라이언트

    def _load_image_map(self) -> dict:
        """image_map.json 파일 로딩"""
        try:
            image_map_path = os.path.join(os.path.dirname(__file__), 'image_map.json')
            with open(image_map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load image_map.json: {e}")
            return {}

    def recommend(self, top_n: int = 20) -> dict:
        """메인 추천 로직"""

        # 1. 인기도 계산
        pop_calc = PopularityCalculator(self.df)
        popularity_df = pop_calc.calculate_popularity()
        trending_df = pop_calc.calculate_trending()

        # 2. 데이터 병합
        result = popularity_df.merge(
            trending_df,
            on='VISIT_AREA_NM',
            how='left'
        ).fillna({'trending_score': 0})

        # 집 같은 불필요한 장소 제거
        result = result[result['VISIT_AREA_NM'] != '집']

        # 3. 관광지 정보 조인
        area_info = self.df[['VISIT_AREA_NM', 'VISIT_AREA_TYPE_CD', 'SIDO']].drop_duplicates()
        result = result.merge(area_info, on='VISIT_AREA_NM', how='left')

        # 4. 날씨 정보 가져오기
        unique_sidos = result['SIDO'].dropna().unique().tolist()
        weather_dict = {sido: self.weather_api.get_weather(sido) for sido in unique_sidos}

        # 5. 컨텍스트 점수 계산
        result['context_score'] = result.apply(
            lambda row: self.context_booster.calculate_context_score(row, weather_dict),
            axis=1
        )

        # 6. 최종 점수
        result['final_score'] = (
            0.5 * result['popularity_score'] +
            0.1 * result['trending_score'] +
            0.4 * result['context_score']
        )

        # 7. 중복 제거 (같은 장소명은 점수가 가장 높은 것만 유지)
        result = result.sort_values(by='final_score', ascending=False)
        result = result.drop_duplicates(subset=['VISIT_AREA_NM'], keep='first')

        # 8. Top N 자르기
        final_recommendations = result.head(top_n)

        # 9. 결과 포맷팅
        return self._format_output(final_recommendations, weather_dict)

    def _format_output(self, df: pd.DataFrame, weather_dict: dict) -> dict:
        """출력 포맷 - 안전성 보강"""
        df = df.reset_index(drop=True).copy()

        recommendations = []
        for i, row in df.iterrows():
            # 안전한 값 추출 / 기본값 적용
            name = row.get('VISIT_AREA_NM', '') or ''
            region = row.get('SIDO', '') or ''
            poi_id = row.get('POI_ID', '') or ''
            try:
                type_cd = int(row.get('VISIT_AREA_TYPE_CD')) if pd.notnull(row.get('VISIT_AREA_TYPE_CD')) else 8
            except Exception:
                type_cd = 8

            popularity = float(row.get('popularity_score') or 0.0)
            context_score = float(row.get('context_score') or 0.0)
            avg_rating = float(row.get('avg_rating') or 0.0)
            trending_score = float(row.get('trending_score') or 0.0)
            final_score = float(row.get('final_score') or 0.0)

            # 이미지 경로 가져오기 (우선순위 순서)
            # 1. image_map.json에서 찾기 (기존 매핑된 이미지)
            # 2. Google Places API로 실시간 가져오기
            # 3. 한국관광공사 API로 조회
            # 4. 기본 이미지
            
            image_url = get_place_image(name)
            
            # Google Places API에서도 못 찾으면 한국관광공사 API 시도
            if not image_url:
                api_image_url = self.tour_image_api.get_image_url(name)
                if api_image_url:
                    image_url = api_image_url
                else:
                    # 그래도 없으면 기본 이미지
                    image_url = '/static/default.jpg'

            recommendations.append({
                'rank': i + 1,
                'name': name,
                'poi_id': str(poi_id) if poi_id else name,  # POI_ID가 없으면 name을 사용
                'type': self._get_type_name(type_cd),
                'region': region,
                'score': round(final_score, 3),
                'popularity': round(popularity, 3),
                'context_score': round(context_score, 3),
                'avg_rating': round(avg_rating, 2),
                'is_trending': trending_score > 0.5,
                'image_url': image_url
            })

        return {
            'recommendations': recommendations,
            'metadata': {
                'season': self.context_booster.get_season(),
                'daytype': self.context_booster.get_daytype(),
                'weather_summary': self._summarize_weather(weather_dict),
                'generated_at': datetime.now().isoformat(),
                'total_candidates': len(df)
            }
        }

    def _get_type_name(self, type_cd: int) -> str:
        """유형명 변환"""
        mapping = {
            1: '자연 관광지', 2: '문화 관광지', 3: '레저/스포츠',
            4: '쇼핑', 5: '음식점', 6: '숙박', 7: '축제/행사', 8: '기타'
        }
        return mapping.get(type_cd, '기타')

    def _summarize_weather(self, weather_dict: dict) -> dict:
        """날씨 요약"""
        summary = {}
        for sido, weather in weather_dict.items():
            summary[sido] = {
                'condition': weather['condition'],
                'temperature': round(weather['temperature'], 1),
                'description': weather['description']
            }
        return summary