import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class PopularityCalculator:
    """인기도 및 트렌드 계산"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # VISIT_START_YMD를 datetime으로 변환
        self.df['VISIT_START_YMD'] = pd.to_datetime(
            self.df['VISIT_START_YMD'], format='%Y%m%d', errors='coerce'
        )
        self.current_date = datetime.now()

    def calculate_popularity(self, days_window: int = 30, decay_rate: float = 0.05) -> pd.DataFrame:
        """시간 가중치 인기도 계산"""

        # 최근 N일 필터링
        cutoff_date = self.current_date - timedelta(days=days_window)
        recent_df = self.df[self.df['VISIT_START_YMD'] >= cutoff_date].copy()

        if len(recent_df) == 0:
            recent_df = self.df.copy()

        # 경과일 계산
        recent_df['days_ago'] = (self.current_date - recent_df['VISIT_START_YMD']).dt.days

        # 시간 가중치
        recent_df['time_weight'] = np.exp(-decay_rate * recent_df['days_ago'])

        # ratings 컬럼 생성 (DGSTFN(만족도), REVISIT_INTENTION(재방문 의향), RCMDTN_INTENTION(추천 의향)의 평균)
        if 'ratings' not in recent_df.columns:
            recent_df['ratings'] = recent_df[['DGSTFN', 'REVISIT_INTENTION', 'RCMDTN_INTENTION']].mean(axis=1)

        # 관광지별 집계
        popularity = recent_df.groupby('VISIT_AREA_NM').agg({
            'ratings': 'mean',
            'time_weight': 'sum',
            'TRAVEL_ID': 'nunique',  # unique travels
            'VISIT_START_YMD': 'count'
        }).rename(columns={
            'ratings': 'avg_rating',
            'time_weight': 'weighted_visits',
            'TRAVEL_ID': 'unique_visitors',
            'VISIT_START_YMD': 'total_visits'
        })

        # 정규화
        popularity['rating_norm'] = popularity['avg_rating'] / 5.0
        popularity['visits_norm'] = self._normalize(popularity['weighted_visits'])
        popularity['visitors_norm'] = self._normalize(popularity['unique_visitors'])

        # 인기도 점수
        popularity['popularity_score'] = (
            0.4 * popularity['rating_norm'] +
            0.35 * popularity['visits_norm'] +
            0.25 * popularity['visitors_norm']
        )

        return popularity.reset_index()

    def calculate_trending(self, recent_days: int = 7, base_days: int = 30) -> pd.DataFrame:
        """트렌딩 점수 계산 (최근 N일 방문수 / 최근 M일 방문수)"""

        recent_cutoff = self.current_date - timedelta(days=recent_days)
        base_cutoff = self.current_date - timedelta(days=base_days)

        recent_df = self.df[self.df['VISIT_START_YMD'] >= recent_cutoff]
        base_df = self.df[self.df['VISIT_START_YMD'] >= base_cutoff]

        # 집계
        recent_counts = recent_df.groupby('VISIT_AREA_NM').size().reset_index(name='recent_visits')
        base_counts = base_df.groupby('VISIT_AREA_NM').size().reset_index(name='base_visits')

        # 병합
        merged = base_counts.merge(recent_counts, on='VISIT_AREA_NM', how='left').fillna(0)

        # 트렌드 점수: 최근 방문 비율
        merged['trending_score'] = merged['recent_visits'] / merged['base_visits']
        merged['trending_score'] = merged['trending_score'].clip(0, 1)  # 0~1 사이로 클리핑

        return merged[['VISIT_AREA_NM', 'trending_score']]

    def _normalize(self, series: pd.Series) -> pd.Series:
        """Min-Max 정규화"""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series(0.5, index=series.index)
        return (series - min_val) / (max_val - min_val)