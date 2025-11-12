# 11주차 메인 추천 [SIDO] not in index 해결

## 문제 상황

### 증상
- 메인 화면에서 추천 여행지가 표시되지 않음
- 프론트엔드에 `"['SIDO'] not in index"` 에러 메시지 표시
- 백엔드 로그에는 특별한 에러가 보이지 않음

### 발생 시점
- 파스텔 블루 디자인 리팩토링 후 메인 페이지 접속 시
- `/recommend` API 호출 시 에러 발생

---

## 원인 분석

### 1. 데이터 로드 불일치
TripMate 추천 시스템은 두 곳에서 데이터를 로드하는데, 서로 다른 파일을 사용하고 있었음:

#### (1) FastAPI 시작 시 - `backend/app/main.py:41`
```python
df = pd.read_csv('app/ml/tn_visit_area_info_with_sido.csv')  # ✅ SIDO 컬럼 포함
recommender = TodayRecommender(df, api_key)
```
- SIDO 컬럼이 포함된 CSV 파일 사용
- 서버 시작 시 모델 초기화용

#### (2) 추천 생성 시 - `backend/app/ml/main.py:16`
```python
PARQUET_PATH = os.path.join(BASE_DIR, "tn_visit_area_info.parquet")  # ❌ SIDO 없음
df = pd.read_parquet(PARQUET_PATH, engine="pyarrow")
```
- SIDO 컬럼이 **없는** Parquet 파일 사용
- subprocess로 실행되는 실제 추천 생성 로직

### 2. Subprocess 실행 구조
`backend/app/main.py:126`의 `/recommend` 엔드포인트는 다음과 같이 작동:

```python
@app.post("/recommend")
def recommend():
    # ...
    result = subprocess.run(["python", "-m", "app.ml.main", "--json"],
                          capture_output=True, text=True)
    # ...
```

- 캐시가 없거나 만료되면 `app.ml.main`을 subprocess로 실행
- 이때 `app.ml.main.py`가 SIDO 없는 파일을 로드
- `recommender.py:35`에서 SIDO 컬럼 접근 시 KeyError 발생

### 3. 에러 발생 위치
**파일**: `backend/app/ml/recommender.py:34-36`

```python
# 3. 관광지 정보 조인
area_info = self.df[['VISIT_AREA_NM', 'VISIT_AREA_TYPE_CD', 'SIDO']].drop_duplicates()
result = result.merge(area_info, on='VISIT_AREA_NM', how='left')
```

- `self.df`에 SIDO 컬럼이 없으면 `KeyError: "['SIDO'] not in index"` 발생
- 에러가 subprocess 내부에서 발생하여 상세 로그가 보이지 않음

---

## 해결 방법

### 1. app.ml.main.py 파일 경로 수정

**파일**: `backend/app/ml/main.py:16`

```python
# Before
PARQUET_PATH = os.path.join(BASE_DIR, "tn_visit_area_info.parquet")

# After
PARQUET_PATH = os.path.join(BASE_DIR, "tn_visit_area_info_with_sido.parquet")
```

**변경 이유**:
- `tn_visit_area_info_with_sido.parquet` 파일은 SIDO 컬럼을 포함
- `main.py`와 `app.ml.main.py`가 동일한 데이터 구조 사용

### 2. SIDO 누락 방지 로직 추가

**파일**: `backend/app/ml/main.py:23-40`

```python
# 2. SIDO 컬럼 확인 (이미 포함되어 있어야 함)
if "SIDO" not in df.columns:
    # SIDO가 없는 경우에만 SGG → SIDO 매핑 시도
    try:
        sgg_df = pd.read_csv(SGG_PATH)

        # 필요한 컬럼만 추출 (SGG_CD, SIDO_NM)
        if "SIDO_NM" in sgg_df.columns:
            sgg_info = sgg_df[["SGG_CD", "SIDO_NM"]].drop_duplicates()
            sgg_info.rename(columns={"SIDO_NM": "SIDO"}, inplace=True)
        else:
            sgg_info = sgg_df[["SGG_CD", "SIDO"]].drop_duplicates()

        # 조인
        df = df.merge(sgg_info, on="SGG_CD", how="left")

    except FileNotFoundError:
        df["SIDO"] = "Unknown"
```

**변경 이유**:
- SIDO 컬럼이 없을 때 자동으로 매핑 시도
- 방어적 프로그래밍으로 에러 방지

### 3. Redis 캐시 초기화

```bash
# 모든 캐시 삭제
docker-compose exec redis redis-cli FLUSHALL

# 또는 추천 캐시만 삭제
docker-compose exec redis redis-cli DEL recommend:default
```

**변경 이유**:
- 기존 에러가 담긴 캐시 데이터 제거
- 새로운 데이터로 추천 재생성 강제

### 4. 백엔드 재시작

```bash
docker-compose restart backend
```

**변경 이유**:
- 변경된 코드 반영
- 모델 재로드

---

## 검증 방법

### 1. 직접 스크립트 실행 테스트
```bash
docker-compose exec backend python -m app.ml.main --json 2>&1
```

**기대 결과**:
```json
{
  "recommendations": [
    {
      "rank": 1,
      "name": "내장산국립공원",
      "type": "자연 관광지",
      "region": "미상",
      "score": 0.455,
      ...
    },
    ...
  ],
  "metadata": {
    "season": "fall",
    "daytype": "weekday",
    ...
  }
}
```

### 2. 백엔드 로그 확인
```bash
docker-compose logs backend --tail=20
```

**기대 출력**:
```
INFO:root:Successfully connected to Redis.
INFO:root:Recommendation model loaded successfully.
INFO:     Application startup complete.
```

### 3. API 엔드포인트 테스트
```bash
curl -X POST http://localhost:8000/recommend
```

**기대 결과**: 200 OK + JSON 추천 데이터

### 4. 프론트엔드 확인
- 브라우저에서 `http://localhost:3000` 접속
- "오늘의 추천 여행지" 섹션에 20개 관광지 표시
- 에러 메시지 없음

---

## 추가 디버깅 팁

### 상세 로그 확인 방법

#### 1. 실시간 로그 모니터링
```bash
docker-compose logs -f backend
```

#### 2. 에러만 필터링
```bash
docker-compose logs backend | grep -i "error\|exception\|traceback" -A 5 -B 2
```

#### 3. subprocess 에러 직접 확인
```bash
docker-compose exec backend python -m app.ml.main --json 2>&1 | head -100
```

#### 4. 데이터 파일 컬럼 확인
```bash
# CSV 헤더 확인
head -1 backend/app/ml/tn_visit_area_info_with_sido.csv

# Parquet 정보 확인 (Docker 내부)
docker-compose exec backend python -c "import pandas as pd; df = pd.read_parquet('app/ml/tn_visit_area_info_with_sido.parquet'); print(df.columns.tolist())"
```

---

## 근본 원인 및 교훈

### 근본 원인
1. **데이터 파일 관리 미흡**
   - 같은 목적의 데이터를 여러 파일 형식으로 중복 관리 (CSV, Parquet)
   - 파일 간 스키마 불일치

2. **subprocess 에러 핸들링 부족**
   - subprocess 내부 에러가 JSON으로만 반환되어 디버깅 어려움
   - 상세 traceback이 로그에 남지 않음

3. **캐싱으로 인한 에러 은폐**
   - Redis 캐시가 있으면 에러가 발생하지 않아 문제 파악 지연

### 개선 방향
1. **단일 데이터 소스 사용**
   - `tn_visit_area_info_with_sido.parquet`를 표준 데이터 파일로 통일
   - 다른 형식 파일은 삭제 또는 deprecated 표시

2. **에러 로깅 강화**
   - subprocess 실행 시 stderr를 로그에 기록
   - 추천 생성 실패 시 상세 traceback 반환

3. **데이터 검증 로직 추가**
   - 모델 초기화 시 필수 컬럼 존재 여부 확인
   - 누락 시 명확한 에러 메시지 출력

4. **통합 테스트 추가**
   - CI/CD에서 추천 API 엔드투엔드 테스트
   - 데이터 스키마 검증 자동화

---

## 참고 파일

- `backend/app/main.py` - FastAPI 메인 파일
- `backend/app/ml/main.py` - 추천 스크립트
- `backend/app/ml/recommender.py` - 추천 엔진
- `backend/app/ml/tn_visit_area_info_with_sido.parquet` - SIDO 포함 데이터 (정답)
- `backend/app/ml/tn_visit_area_info.parquet` - SIDO 없는 데이터 (문제)
- `backend/app/ml/tn_visit_area_info_with_sido.csv` - SIDO 포함 데이터 (CSV 버전)

---

## 해결 완료 체크리스트

- [x] `app.ml.main.py`에서 SIDO 포함 Parquet 파일 로드
- [x] SIDO 누락 방지 로직 추가
- [x] Redis 캐시 초기화
- [x] 백엔드 재시작
- [x] 추천 스크립트 직접 실행 테스트 통과
- [x] 백엔드 로그에서 "Recommendation model loaded successfully" 확인
- [x] 프론트엔드에서 추천 목록 정상 표시
- [x] 에러 메시지 없음

**최종 상태**: ✅ 해결 완료
