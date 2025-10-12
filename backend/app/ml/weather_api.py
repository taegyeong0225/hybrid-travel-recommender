import requests
from datetime import datetime


class WeatherAPI:
    """OpenWeather API 클라이언트"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

        self.sido_to_city = {
            '서울특별시': 'Seoul', '서울': 'Seoul',
            '부산광역시': 'Busan', '부산': 'Busan',
            '인천광역시': 'Incheon', '인천': 'Incheon',
            '경기도': 'Suwon', '경기': 'Suwon',
            '강원도': 'Chuncheon', '강원': 'Chuncheon',
            '제주특별자치도': 'Jeju', '제주': 'Jeju'
        }

        self.cache = {}

    def get_weather(self, sido: str) -> dict:
        """날씨 조회"""

        if sido in self.cache:
            return self.cache[sido]

        city = self.sido_to_city.get(sido, 'Seoul')

        try:
            params = {
                'q': f'{city},KR',
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'kr'   # 한국어 설명을 원한다면 추가
            }

            response = requests.get(self.base_url, params=params, timeout=3)
            data = response.json()

            weather_info = {
                'sido': sido,
                'condition': self._parse_condition(data['weather'][0]['main']),   # Clear → sunny
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description']                  # 상세 설명 추가
            }

            self.cache[sido] = weather_info
            return weather_info

        except Exception as e:
            print(f"날씨 API 오류 ({sido}): {e}")
            return {
                'sido': sido,
                'condition': 'cloudy',
                'temperature': 20.0,
                'description': '날씨 정보를 불러올 수 없음'
            }

    def _parse_condition(self, weather_main: str) -> str:
        mapping = {
            'Clear': 'sunny',
            'Clouds': 'cloudy',
            'Rain': 'rainy',
            'Snow': 'snowy'
        }
        return mapping.get(weather_main, 'cloudy')