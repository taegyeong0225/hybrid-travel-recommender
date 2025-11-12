"""
추천 결과와 이미지 매핑 테스트 스크립트
"""
import json
import os
import pandas as pd

# 경로 설정
BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMAGE_MAP_PATH = os.path.join(os.path.dirname(__file__), 'image_map.json')
PARQUET_PATH = os.path.join(os.path.dirname(__file__), 'tn_visit_area_info_with_images.parquet')

def load_image_map():
    """이미지 매핑 로드"""
    if not os.path.exists(IMAGE_MAP_PATH):
        print(f"❌ 이미지 맵 파일이 없습니다: {IMAGE_MAP_PATH}")
        return {}

    with open(IMAGE_MAP_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_parquet_data():
    """Parquet 데이터 로드"""
    if not os.path.exists(PARQUET_PATH):
        print(f"❌ Parquet 파일이 없습니다: {PARQUET_PATH}")
        return None

    return pd.read_parquet(PARQUET_PATH)

def test_image_mapping():
    """이미지 매핑 테스트"""
    print("=" * 80)
    print("🖼️  추천 결과 이미지 매핑 테스트")
    print("=" * 80)

    # 1. 데이터 로드
    image_map = load_image_map()
    df = load_parquet_data()

    if not image_map:
        print("⚠️  이미지 맵이 비어있습니다.")
        return

    if df is None:
        print("⚠️  데이터를 로드할 수 없습니다.")
        return

    print(f"\n📊 이미지 맵 총 항목 수: {len(image_map)}")
    print(f"📊 Parquet 데이터 행 수: {len(df)}")

    # 2. VISIT_AREA_NM 컬럼 확인
    if 'VISIT_AREA_NM' not in df.columns:
        print("\n❌ VISIT_AREA_NM 컬럼이 없습니다!")
        print(f"사용 가능한 컬럼: {df.columns.tolist()}")
        return

    # 3. 고유한 장소명 추출
    unique_places = df['VISIT_AREA_NM'].dropna().unique()
    print(f"📊 고유한 장소명 수: {len(unique_places)}")

    # 4. 매칭 통계
    matched = []
    unmatched = []

    for place in unique_places:
        if place in image_map:
            matched.append(place)
        else:
            unmatched.append(place)

    match_rate = (len(matched) / len(unique_places) * 100) if unique_places.size > 0 else 0

    print(f"\n✅ 매칭된 장소: {len(matched)}개 ({match_rate:.1f}%)")
    print(f"❌ 매칭 안 된 장소: {len(unmatched)}개 ({100-match_rate:.1f}%)")

    # 5. 샘플 매칭 결과 출력
    print("\n" + "=" * 80)
    print("🎯 매칭된 장소 샘플 (상위 10개)")
    print("=" * 80)
    for i, place in enumerate(matched[:10], 1):
        image_url = image_map[place]
        print(f"{i:2d}. {place:30s} → {image_url}")

    print("\n" + "=" * 80)
    print("⚠️  매칭 안 된 장소 샘플 (상위 20개)")
    print("=" * 80)
    for i, place in enumerate(unmatched[:20], 1):
        print(f"{i:2d}. {place}")

    # 6. 인기 장소 TOP 20 매칭 확인
    print("\n" + "=" * 80)
    print("🔥 인기 장소 TOP 20 이미지 매칭 상태")
    print("=" * 80)

    # 방문 횟수로 인기 장소 추출
    top_places = df['VISIT_AREA_NM'].value_counts().head(20)

    for rank, (place, count) in enumerate(top_places.items(), 1):
        has_image = "✅" if place in image_map else "❌"
        image_url = image_map.get(place, "이미지 없음")
        print(f"{rank:2d}. {has_image} {place:30s} (방문 {count:5d}회)")
        if place in image_map:
            print(f"    └─ {image_url}")

    # 7. 통계 요약
    top20_matched = sum(1 for place, _ in top_places.items() if place in image_map)
    top20_match_rate = (top20_matched / 20 * 100) if len(top_places) >= 20 else 0

    print("\n" + "=" * 80)
    print("📈 최종 통계")
    print("=" * 80)
    print(f"전체 매칭률: {match_rate:.1f}% ({len(matched)}/{len(unique_places)})")
    print(f"TOP 20 매칭률: {top20_match_rate:.1f}% ({top20_matched}/20)")

    if top20_match_rate < 80:
        print("\n⚠️  주의: TOP 20 장소의 이미지 매칭률이 낮습니다!")
        print("   → 인기 장소의 이미지를 우선적으로 추가하는 것을 권장합니다.")

    return {
        'total_places': len(unique_places),
        'matched': len(matched),
        'unmatched': len(unmatched),
        'match_rate': match_rate,
        'top20_match_rate': top20_match_rate
    }

if __name__ == "__main__":
    test_image_mapping()
