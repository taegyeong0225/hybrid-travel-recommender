import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class PopularityCalculator:
    """인기도 및 트렌드 계산"""

    def __init__(self, df: pd.DataFrame):
        # 입력 데이터 프레임을 복사해서 내부에서 다룸
        self.df = df.copy()

        # VISIT_START_YMD 컬럼을 가능한 한 유연하게 datetime으로 변환
        # (이미 datetime이거나 'YYYYMMDD', 또는 일반 문자열/타임스탬프 모두 처리)
        if 'VISIT_START_YMD' in self.df.columns:
            self.df['VISIT_START_YMD'] = pd.to_datetime(
                self.df['VISIT_START_YMD'], errors='coerce', infer_datetime_format=True
            )
        else:
            # 해당 컬럼이 없으면 새 컬럼 생성(모두 NaT)
            self.df['VISIT_START_YMD'] = pd.NaT

        # VISIT_AREA_NM이 결측이면 'Unknown'으로 대체 (그룹바이 키로 사용)
        if 'VISIT_AREA_NM' in self.df.columns:
            self.df['VISIT_AREA_NM'] = self.df['VISIT_AREA_NM'].fillna('Unknown')
        else:
            self.df['VISIT_AREA_NM'] = 'Unknown'

        # 평점 관련 컬럼이 없을 수 있으므로 존재 여부 체크
        self.rating_cols = [c for c in ['DGSTFN', 'REVISIT_INTENTION', 'RCMDTN_INTENTION'] if c in self.df.columns]

        # TRAVEL_ID 컬럼이 없으면 대체 컬럼으로 처리하거나 새로 생성 (모두 NaN이면 unique count는 0)
        if 'TRAVEL_ID' not in self.df.columns:
            self.df['TRAVEL_ID'] = np.nan

        # 현재 기준일
        self.current_date = datetime.now()

    def calculate_popularity(self, days_window: int = 30, decay_rate: float = 0.05) -> pd.DataFrame:
        """시간 가중치 인기도 계산"""

        # 최근 N일 필터링 (VISIT_START_YMD가 NaT인 행은 제외)
        cutoff_date = self.current_date - timedelta(days=days_window)
        recent_df = self.df[self.df['VISIT_START_YMD'].notna() & (self.df['VISIT_START_YMD'] >= cutoff_date)].copy()

        # recent_df가 비어있으면 날짜 정보가 없는 행들을 제외한 전체 데이터로 대체
        if len(recent_df) == 0:
            recent_df = self.df[self.df['VISIT_START_YMD'].notna()].copy()

        # 만약 그래도 비어있다면(아예 날짜가 없으면) 전체 데이터 사용하되
        # VISIT_START_YMD가 NaT인 행은 현재 날짜로 치환해서 처리
        if len(recent_df) == 0:
            tmp = self.df.copy()
            tmp['VISIT_START_YMD'] = tmp['VISIT_START_YMD'].fillna(pd.Timestamp(self.current_date))
            recent_df = tmp

        # 경과일 계산 (NaT는 위에서 제거/대체되어 없어야 함)
        recent_df['days_ago'] = (pd.Timestamp(self.current_date) - recent_df['VISIT_START_YMD']).dt.days.clip(lower=0)

        # 시간 가중치 (decay)
        recent_df['time_weight'] = np.exp(-decay_rate * recent_df['days_ago'])

        # ratings 컬럼 생성: 존재하는 평점 컬럼의 평균, 없으면 0으로 채움
        if len(self.rating_cols) > 0:
            recent_df['ratings'] = recent_df[self.rating_cols].mean(axis=1, skipna=True).fillna(0.0)
        else:
            recent_df['ratings'] = 0.0

        # 관광지별 집계
        # TRAVEL_ID가 없거나 NaN이면 nunique 결과가 0이 될 수 있음(의도적 처리)
        popularity = recent_df.groupby('VISIT_AREA_NM').agg({
            'ratings': 'mean',
            'time_weight': 'sum',
            'TRAVEL_ID': pd.Series.nunique,
            'VISIT_START_YMD': 'count'
        }).rename(columns={
            'ratings': 'avg_rating',
            'time_weight': 'weighted_visits',
            'TRAVEL_ID': 'unique_visitors',
            'VISIT_START_YMD': 'total_visits'
        })

        # NaN/무한 처리 (안전성)
        popularity['avg_rating'] = popularity['avg_rating'].fillna(0.0)
        popularity['weighted_visits'] = popularity['weighted_visits'].fillna(0.0)
        popularity['unique_visitors'] = popularity['unique_visitors'].fillna(0.0)
        popularity['total_visits'] = popularity['total_visits'].fillna(0)

        # 정규화 (rating은 5점 기준으로 가정)
        popularity['rating_norm'] = popularity['avg_rating'] / 5.0
        popularity['visits_norm'] = self._normalize(popularity['weighted_visits'])
        popularity['visitors_norm'] = self._normalize(popularity['unique_visitors'])

        # 인기도 점수
        popularity['popularity_score'] = (
            0.4 * popularity['rating_norm'] +
            0.35 * popularity['visits_norm'] +
            0.25 * popularity['visitors_norm']
        )

        # 안전한 반환: 인덱스를 컬럼으로 변환
        return popularity.reset_index()

    def calculate_trending(self, recent_days: int = 7, base_days: int = 30) -> pd.DataFrame:
        """트렌딩 점수 계산 (최근 N일 방문수 / 최근 M일 방문수)
        base_visits가 0인 경우 처리:
          - base==0 and recent>0 -> trending_score = 1.0
          - base==0 and recent==0 -> trending_score = 0.0
        결과는 0~1로 클립됨.
        """

        recent_cutoff = self.current_date - timedelta(days=recent_days)
        base_cutoff = self.current_date - timedelta(days=base_days)

        recent_df = self.df[self.df['VISIT_START_YMD'].notna() & (self.df['VISIT_START_YMD'] >= recent_cutoff)]
        base_df = self.df[self.df['VISIT_START_YMD'].notna() & (self.df['VISIT_START_YMD'] >= base_cutoff)]

        # 집계
        recent_counts = recent_df.groupby('VISIT_AREA_NM').size().reset_index(name='recent_visits')
        base_counts = base_df.groupby('VISIT_AREA_NM').size().reset_index(name='base_visits')

        # 병합 (모든 후보 포함)
        merged = base_counts.merge(recent_counts, on='VISIT_AREA_NM', how='outer').fillna(0)

        # 안전한 트렌드 계산: base==0 처리
        bv = merged['base_visits'].values
        rv = merged['recent_visits'].values

        trending = np.zeros(len(merged), dtype=float)
        # base > 0 인 경우 정상 비율
        mask_base_pos = bv > 0
        trending[mask_base_pos] = rv[mask_base_pos] / bv[mask_base_pos]
        # base == 0 인 경우 recent>0이면 1, 아니면 0
        mask_base_zero = bv == 0
        trending[mask_base_zero] = np.where(rv[mask_base_zero] > 0, 1.0, 0.0)

        merged['trending_score'] = np.clip(trending, 0.0, 1.0)

        return merged[['VISIT_AREA_NM', 'trending_score']]

    def _normalize(self, series: pd.Series) -> pd.Series:
        """Min-Max 정규화. 상수 시리즈일 경우 0.5로 채움."""
        if series is None or len(series) == 0:
            return pd.Series([], dtype=float)
        min_val = series.min()
        max_val = series.max()
        if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
            return pd.Series(0.5, index=series.index, dtype=float)
        return (series - min_val) / (max_val - min_val)