# backend/app/ml/preprocess_images.py
"""
Parquet 데이터 기반 이미지 매핑 생성
static 폴더의 메타데이터와 Parquet 데이터를 매칭하여 image_map.json 생성
"""
import os
import json
import sys
import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))  # backend
STATIC_PATH = os.path.join(BASE_DIR, 'static')
PARQUET_PATH = os.path.join(os.path.dirname(__file__), 'tn_visit_area_info_with_images.parquet')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'image_map.json')

SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')


def normalize_text(text: str) -> str:
    """텍스트를 정규화 (공백 제거)"""
    if not isinstance(text, str):
        return ""
    return text.strip().replace(' ', '').replace('　', '')


def load_parquet_places() -> set:
    """Parquet에서 고유한 장소명 목록 로드"""
    if not os.path.exists(PARQUET_PATH):
        print(f"⚠️  Parquet 파일을 찾을 수 없습니다: {PARQUET_PATH}")
        return set()

    df = pd.read_parquet(PARQUET_PATH)

    if 'VISIT_AREA_NM' not in df.columns:
        print(f"⚠️  VISIT_AREA_NM 컬럼이 없습니다: {df.columns.tolist()}")
        return set()

    # 고유한 장소명 추출 (null 제외)
    places = set(df['VISIT_AREA_NM'].dropna().unique())

    # '집', '사무실' 등 비관광지 제외
    excluded = {'집', '친구 집', '친구 친지 집', '사무실', '회사', '집 근처', '우리집'}
    places = places - excluded

    return places


def load_metadata_from_json(file_path: str) -> Optional[Tuple[str, str]]:
    """
    메타데이터 JSON 파일에서 장소명과 이미지 파일명 추출

    Returns:
        Tuple[str, str]: (장소명, 이미지파일명) 또는 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        # 구조: {"images": {"VISIT_AREA_NM": "...", "PHOTO_FILE_NM": "..."}}
        if 'images' in data and isinstance(data['images'], dict):
            images = data['images']
            place_name = images.get('VISIT_AREA_NM', '').strip()
            image_file = images.get('PHOTO_FILE_NM', '').strip()

            if place_name and image_file:
                return (place_name, image_file)

        return None
    except Exception as e:
        print(f"⚠️  JSON 파싱 오류 ({file_path}): {e}")
        return None

def scan_metadata_files() -> Dict[str, List[Tuple[str, str]]]:
    """
    static 폴더의 모든 메타데이터를 스캔하여 장소명별 이미지 목록 생성

    Returns:
        Dict[str, List[Tuple[str, str]]]: {장소명: [(지역, 이미지경로), ...]}
    """
    place_images = defaultdict(list)

    if not os.path.isdir(STATIC_PATH):
        print(f"❌ STATIC_PATH를 찾을 수 없습니다: {STATIC_PATH}")
        return dict(place_images)

    # static 폴더 구조: static/지역명/metadata/*.json, static/지역명/images/*.jpg
    for region_dir in os.listdir(STATIC_PATH):
        region_path = os.path.join(STATIC_PATH, region_dir)

        if not os.path.isdir(region_path) or region_dir.startswith('.'):
            continue

        metadata_dir = os.path.join(region_path, 'metadata')
        images_dir = os.path.join(region_path, 'images')

        if not os.path.isdir(metadata_dir) or not os.path.isdir(images_dir):
            continue

        # metadata 폴더의 모든 JSON 파일 처리
        for filename in os.listdir(metadata_dir):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(metadata_dir, filename)
            result = load_metadata_from_json(file_path)

            if result:
                place_name, image_file = result
                image_path = os.path.join(images_dir, image_file)

                # 이미지 파일 존재 확인
                if os.path.exists(image_path):
                    # static 기준 상대 경로로 변환
                    rel_path = os.path.relpath(image_path, STATIC_PATH).replace('\\', '/')
                    url = '/static/' + rel_path
                    place_images[place_name].append((region_dir, url))

    return dict(place_images)


def create_image_map() -> Tuple[Dict[str, str], List[str]]:
    """
    Parquet 데이터와 메타데이터를 매칭하여 이미지 맵 생성

    Returns:
        Tuple[Dict[str, str], List[str]]: (매핑 딕셔너리, 통계 메시지 목록)
    """
    print("=" * 80)
    print("🖼️  이미지 맵 생성 시작")
    print("=" * 80)

    # 1. Parquet에서 장소명 로드
    print("\n📂 Parquet 데이터 로딩 중...")
    parquet_places = load_parquet_places()
    print(f"✅ Parquet 고유 장소: {len(parquet_places):,}개")

    # 2. 메타데이터 스캔
    print("\n📂 메타데이터 스캔 중...")
    place_images = scan_metadata_files()
    print(f"✅ 메타데이터 장소: {len(place_images):,}개")
    total_images = sum(len(imgs) for imgs in place_images.values())
    print(f"✅ 총 이미지 수: {total_images:,}개")

    # 3. Parquet 장소와 매칭
    mapping = {}
    matched_count = 0
    unmatched_count = 0
    unmatched_samples = []

    for place_name in parquet_places:
        if place_name in place_images:
            # 여러 이미지 중 첫 번째 선택 (향후 개선 가능: 평점 기반 선택)
            images = place_images[place_name]
            region, url = images[0]  # 첫 번째 이미지 사용
            mapping[place_name] = url
            matched_count += 1
        else:
            unmatched_count += 1
            if len(unmatched_samples) < 10:
                unmatched_samples.append(place_name)

    # 4. 통계 출력
    messages = []
    match_rate = (matched_count / len(parquet_places) * 100) if parquet_places else 0

    print("\n" + "=" * 80)
    print("📊 매칭 통계")
    print("=" * 80)
    print(f"✅ 매칭 성공: {matched_count:,}개 ({match_rate:.1f}%)")
    print(f"❌ 매칭 실패: {unmatched_count:,}개")

    if unmatched_samples:
        print(f"\n⚠️  매칭 안 된 장소 샘플 (상위 10개):")
        for i, place in enumerate(unmatched_samples, 1):
            print(f"  {i:2d}. {place}")

    messages.append(f"Total: {matched_count}/{len(parquet_places)} matched ({match_rate:.1f}%)")

    return mapping, messages

if __name__ == "__main__":
    mapping, messages = create_image_map()

    try:
        # OUTPUT_PATH 디렉토리 생성
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

        # JSON 파일 저장
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print("✅ 이미지 맵 저장 완료")
        print("=" * 80)
        print(f"📁 저장 경로: {OUTPUT_PATH}")
        print(f"📊 저장된 항목 수: {len(mapping):,}개")

        if messages:
            print("\n📝 추가 정보:")
            for msg in messages:
                print(f"  - {msg}")

    except Exception as ex:
        print(f"\n❌ 저장 실패: {ex}")
        sys.exit(1)