import pandas as pd
from datetime import datetime

from weather_api import WeatherAPI
from popularity_calculator import PopularityCalculator
from context_booster import ContextBooster

class TodayRecommender:
    """오늘의 추천 엔진"""

    def __init__(self, df: pd.DataFrame, weather_api_key: str):
        self.df = df
        self.weather_api = WeatherAPI(weather_api_key)
        self.context_booster = ContextBooster()

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

        # 7. Top N 자르기
        final_recommendations = result.sort_values(by="final_score", ascending=False).head(top_n)

        # 8. 결과 포맷팅
        return self._format_output(final_recommendations, weather_dict)

    def _format_output(self, df: pd.DataFrame, weather_dict: dict) -> dict:
        """출력 포맷"""

        recommendations = []
        for idx, row in df.iterrows():
            recommendations.append({
                'rank': idx + 1,
                'name': row['VISIT_AREA_NM'],
                'type': self._get_type_name(row.get('VISIT_AREA_TYPE_CD', 8)),
                'region': row.get('SIDO', ''),
                'score': round(row['final_score'], 3),
                'popularity': round(row['popularity_score'], 3),
                'context_score': round(row['context_score'], 3),
                'avg_rating': round(row['avg_rating'], 2),
                'is_trending': row['trending_score'] > 0.5
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