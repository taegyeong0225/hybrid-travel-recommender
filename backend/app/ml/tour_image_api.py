"""
한국관광공사 TourAPI 이미지 조회 클라이언트
"""
import os
import requests
import logging
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)


class TourImageAPI:
    """한국관광공사 관광사진정보 API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: 한국관광공사 API 키. None이면 환경변수에서 가져옴
        """
        raw_key = api_key or os.getenv("TOURAPI_KEY")
        if not raw_key:
            logger.warning("TOURAPI_KEY not set. Image fetching will be disabled.")
            self.api_key = None
        else:
            # API 키가 URL 인코딩되어 있으면 디코딩
            self.api_key = urllib.parse.unquote(raw_key)

        self.base_url = "http://apis.data.go.kr/B551011/PhotoGalleryService1/gallerySearchList1"

    def get_image_url(self, place_name: str, timeout: int = 3) -> Optional[str]:
        """
        장소명으로 이미지 URL 조회

        Args:
            place_name: 장소명 (예: "경복궁", "남산타워")
            timeout: API 요청 타임아웃 (초)

        Returns:
            이미지 URL (찾지 못하면 None)
        """
        if not self.api_key:
            logger.warning(f"Cannot fetch image for '{place_name}': API key not configured")
            return None

        try:
            # API 요청 (serviceKey는 이미 인코딩되어 있으므로 직접 URL에 포함)
            import urllib.parse
            encoded_keyword = urllib.parse.quote(place_name)

            url = (
                f"{self.base_url}?"
                f"serviceKey={self.api_key}&"
                f"keyword={encoded_keyword}&"
                f"_type=json&"
                f"numOfRows=1&"
                f"pageNo=1"
            )

            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            # 응답 파싱
            data = response.json()
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

            if not items:
                logger.debug(f"No image found for '{place_name}'")
                return None

            # 첫 번째 이미지 URL 반환
            image_url = items[0].get("galWebImageUrl")

            if image_url:
                logger.info(f"Found image for '{place_name}': {image_url}")
                return image_url
            else:
                logger.warning(f"Image URL missing in response for '{place_name}'")
                return None

        except requests.Timeout:
            logger.warning(f"Timeout while fetching image for '{place_name}'")
            return None

        except requests.RequestException as e:
            logger.error(f"Error fetching image for '{place_name}': {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching image for '{place_name}': {e}")
            return None
