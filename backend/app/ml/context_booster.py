from datetime import datetime


class ContextBooster:
    """계절/날씨/요일에 따른 컨텍스트 부스팅"""

    def __init__(self):
        # 계절별 유형 적합도
        self.season_affinity = {
            'spring': {1: 1.3, 2: 1.1, 3: 1.0, 4: 1.2, 5: 1.0, 6: 1.0, 7: 1.2, 8: 1.0},
            'summer': {1: 1.5, 2: 0.9, 3: 1.4, 4: 1.1, 5: 1.0, 6: 1.0, 7: 1.3, 8: 1.0},
            'fall': {1: 1.4, 2: 1.2, 3: 1.1, 4: 1.1, 5: 1.2, 6: 1.0, 7: 1.2, 8: 1.0},
            'winter': {1: 1.2, 2: 1.3, 3: 1.3, 4: 1.2, 5: 1.0, 6: 1.0, 7: 1.1, 8: 1.0}
        }

        # 날씨별 실내/외 적합도
        self.weather_rules = {
            'sunny': {'outdoor': 1.2, 'indoor': 0.95},
            'cloudy': {'outdoor': 1.0, 'indoor': 1.0},
            'rainy': {'outdoor': 0.7, 'indoor': 1.3},
            'snowy': {'outdoor': 0.8, 'indoor': 1.2}
        }

        # 온도별 적합도
        self.temp_rules = {
            'outdoor': [
                (-100, 0, 0.7), (0, 10, 0.85), (10, 15, 1.0),
                (15, 25, 1.2), (25, 30, 1.0), (30, 35, 0.8), (35, 100, 0.6)
            ],
            'indoor': [
                (-100, 0, 1.2), (0, 10, 1.1), (10, 30, 1.0),
                (30, 35, 1.1), (35, 100, 1.3)
            ]
        }

        # 실내/실외 분류
        self.indoor_types = [2, 4, 5, 6]
        self.outdoor_types = [1, 3, 7]

    def get_season(self) -> str:
        """현재 계절"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'fall'
        else:
            return 'winter'

    def get_daytype(self) -> str:
        """요일 구분"""
        weekday = datetime.now().weekday()
        return 'weekend' if weekday >= 5 else 'weekday'

    def calculate_context_score(self, row, weather_dict: dict) -> float:
        """컨텍스트 점수 계산"""

        area_type = row.get('VISIT_AREA_TYPE_CD', 8)
        sido = row.get('SIDO', '서울')
        area_name = row.get('VISIT_AREA_NM', '')

        # 1. 계절 승수
        season = self.get_season()
        season_mult = self.season_affinity[season].get(area_type, 1.0)

        # 2. 날씨 정보
        weather = weather_dict.get(sido, {})
        condition = weather.get('condition', 'cloudy')
        temperature = weather.get('temperature', 20.0)

        # 실내/실외 판단
        is_indoor = area_type in self.indoor_types
        location_type = 'indoor' if is_indoor else 'outdoor'

        # 날씨 승수
        weather_mult = self.weather_rules[condition][location_type]

        # 온도 승수
        temp_mult = self._get_temp_multiplier(temperature, location_type)

        # 특수 케이스
        if condition == 'snowy' and ('스키' in area_name or '리조트' in area_name):
            weather_mult = 1.5
            temp_mult = 1.2

        # 컨텍스트 점수 (가중 평균)
        context_score = (
                                0.4 * season_mult +
                                0.4 * weather_mult +
                                0.2 * temp_mult
                        ) / (0.4 + 0.4 + 0.2)

        # 0-1 정규화
        context_score = (context_score - 0.7) / (1.5 - 0.7)
        context_score = max(0, min(1, context_score))

        return context_score

    def _get_temp_multiplier(self, temp: float, location_type: str) -> float:
        """온도에 따른 승수"""
        rules = self.temp_rules[location_type]
        for min_temp, max_temp, multiplier in rules:
            if min_temp <= temp < max_temp:
                return multiplier
        return 1.0