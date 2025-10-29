import pandas as pd
import os

# -----------------------------
# 경로 설정
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "../ml/tn_visit_area_info.csv")
CSV_OUTPUT_PATH = os.path.join(BASE_DIR, "../ml/tn_visit_area_info_with_sido.csv")
PARQUET_OUTPUT_PATH = os.path.join(BASE_DIR, "../ml/tn_visit_area_info_with_sido.parquet")

# -----------------------------
# 데이터 로드
# -----------------------------
print(f"CSV 불러오는 중: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)

# -----------------------------
# 도로명 주소 기반 시도 매핑 사전
# -----------------------------
sido_map = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전라북도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}

# -----------------------------
# 시도(SIDO) 컬럼 생성
# -----------------------------
df["SIDO"] = "미상"

# -----------------------------
# 도로명 기반 매핑
# -----------------------------
print("\nSIDO 매핑 중...")
for key, val in sido_map.items():
    mask = df["ROAD_NM_ADDR"].str.contains(key, na=False)
    df.loc[mask, "SIDO"] = val

# -----------------------------
# SGG_CD 상태 분석
# -----------------------------
null_sgg_count = df["SGG_CD"].isna().sum()
total_rows = len(df)
ratio = null_sgg_count / total_rows * 100

print(f"\n총 {total_rows:,}행 중 SGG_CD 결측치: {null_sgg_count:,}개 ({ratio:.2f}%)")

# 결측치 중 도로명 기반으로만 매핑된 행 요약
only_road_mask = df["SGG_CD"].isna() & (df["SIDO"] != "미상")
road_only_count = only_road_mask.sum()

print(f"도로명 기반으로만 매핑된 행 수: {road_only_count:,}개")

# 샘플 5개 미리보기
print("\n도로명 기반 매핑 예시:")
print(df.loc[only_road_mask, ["ROAD_NM_ADDR", "SIDO"]].head(5))

# -----------------------------
# 결과 요약 출력
# -----------------------------
print("\n=== 시도 분포 ===")
print(df["SIDO"].value_counts())

# -----------------------------
# CSV 저장
# -----------------------------
df.to_csv(CSV_OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"\nCSV 저장 완료 → {CSV_OUTPUT_PATH}")

# -----------------------------
# Parquet 저장
# -----------------------------
try:
    df.to_parquet(PARQUET_OUTPUT_PATH, index=False)
    print(f"Parquet 저장 완료 → {PARQUET_OUTPUT_PATH}")
except Exception as e:
    print(f"Parquet 저장 실패: {e}")

print("\n모든 작업 완료.")