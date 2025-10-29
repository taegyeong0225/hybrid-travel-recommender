import os
import json
import pandas as pd
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../ml/tn_visit_area_info_with_sido.parquet")
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "ml", "tn_visit_area_info_with_images.parquet")

# static 경로 (Docker 안 기준)
STATIC_ROOT = "/app/static"

# 권역 폴더 목록
REGIONS = ["수도권", "동부권", "서부권", "제주권"]

df = pd.read_parquet(DATA_PATH)

def find_image_and_caption(row):
    photo_file_id = str(row.get("PHOTO_FILE_ID", "")).strip()
    photo_file_nm = str(row.get("PHOTO_FILE_NM", "")).strip()
    visit_area_nm = row.get("VISIT_AREA_NM", "").strip()

    if not photo_file_id or not photo_file_nm:
        return None, None

    for region in REGIONS:
        image_path = f"/static/{region}/images/{photo_file_nm}"
        metadata_path = os.path.join(STATIC_ROOT, region, "metadata", f"{photo_file_id}.json")
        caption = None
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                caption = metadata.get("caption", {}).get("IMG_CAPTION")
            except Exception:
                caption = None
        if not caption:
            caption = f"{visit_area_nm}의 대표 관광지입니다." if visit_area_nm else None
        return image_path, caption

    return None, None


# 매핑 실행
print("이미지 및 캡션 매핑 중...")
df[["IMAGE_URL", "CAPTION"]] = df.apply(
    lambda row: pd.Series(find_image_and_caption(row)), axis=1
)

print("매핑 완료. 샘플:")
print(df[["VISIT_AREA_NM", "IMAGE_URL", "CAPTION"]].head(5))

# 저장
try:
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"저장 완료 → {OUTPUT_PATH}")
    logging.info(f"매핑 완료 — 총 {len(df)}개 중 매칭된 항목 저장됨.")
    logging.info(f"결과 저장: {OUTPUT_PATH}")
except Exception as e:
    print(f"Error saving parquet file {OUTPUT_PATH}: {e}")
    logging.error(f"Error saving parquet file {OUTPUT_PATH}: {e}")