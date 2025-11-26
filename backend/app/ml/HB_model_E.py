# 데이터 로드 → 전처리 → GridSearchCV → SVD 학습 → 평가(Recall@5) → 추천 결과 생성

# 필수 라이브러리 불러오기
import pandas as pd

visit_E = pd.read_csv('./1.inputdata/tn_visit_area_info_E.csv')

id_list=['E']

visit_data_list=[visit_E]

# 권역별 반복 처리 구조
for id, visit_area_info in zip(id_list, visit_data_list):

    # VISIT_AREA_TYPE_CD가 관광지(1~8)인 데이터만 필터링
    visit_info = visit_area_info[
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 1) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 2) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 3) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 4) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 5) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 6) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 7) |
        (visit_area_info['VISIT_AREA_TYPE_CD'] == 8)
    ]

    # 동일 관광지명이 2회 이상 등장하는 데이터만 유지 (데이터 신뢰도 향상 목적)
    visit_info = visit_info.groupby('VISIT_AREA_NM').filter(lambda x: len(x) > 1)

    # index 정리
    visit_info = visit_info.reset_index(drop=True)

# 전처리 완료된 데이터프레임 저장 (E 권역)
visit_final_E = visit_info

# 세 가지 만족도 점수를 평균내어 rating 생성
# DGSTFN: 만족도 / REVISIT_INTENTION: 재방문 의사 / RCMDTN_INTENTION: 추천 의사
# 사용자 만족도 기반의 실제 평점을 생성
# 추천 모델 입력으로 사용할 핵심 feature
visit_final_E['ratings'] = visit_final_E[['DGSTFN', 'REVISIT_INTENTION', 'RCMDTN_INTENTION']].mean(axis=1)

visit_final_E['TRAVELER_ID'] = visit_final_E['TRAVEL_ID'].str.split('_').str[1]

# 세부 전처리
# A권역
# LOTNO_ADDR에서 시·도를 추출해 새로운 컬럼(SIDO) 생성
visit_final_E['SIDO'] = visit_final_E['LOTNO_ADDR'].str.split().str[0]

dfe = visit_final_E

# LOTNO_ADDR(주소) 기준으로 가장 많이 등장한 VISIT_AREA_NM을 계산
# 동일 주소에 여러 방문지역명이 섞여 있을 때, 최빈값으로 대표 지역명을 정함
most_frequent_visits = (
    dfe.groupby('LOTNO_ADDR')['VISIT_AREA_NM']
       .agg(lambda x: x.mode().iloc[0])
       .reset_index()
)

# 계산한 최빈 방문지역명을 원본 데이터프레임에 병합
dfe = dfe.merge(
    most_frequent_visits,
    on='LOTNO_ADDR',
    how='left',
    suffixes=('', '_most_frequent')
)

# 기존 VISIT_AREA_NM을 최빈값으로 갱신
dfe['VISIT_AREA_NM'] = dfe['VISIT_AREA_NM_most_frequent'].fillna(dfe['VISIT_AREA_NM'])

# 임시로 생성됐던 컬럼 제거
dfe.drop(columns=['VISIT_AREA_NM_most_frequent'], inplace=True)

# 결과 확인용 컬럼 출력
dfe[['TRAVELER_ID', 'VISIT_AREA_NM', 'ratings', 'SIDO']]

# 후처리

df1 = dfe.rename(columns={'TRAVELER_ID': 'userID','VISIT_AREA_NM': 'itemID','ratings': 'rating'})

df1=df1[['userID','itemID','rating','SIDO']]

df1.to_csv("./2.preprocessed/dfE.csv")

# 모델 수정

import pandas as pd
import numpy as np
import joblib

from surprise import SVD
from surprise.model_selection import cross_validate, GridSearchCV
from surprise import Dataset
from surprise import Reader

# 예상 점수 범위 설정
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(df1[['userID', 'itemID', 'rating']], reader)

algo = SVD()
param_grid = {
    'n_factors': [20, 50, 100, 150, 200],      # 더 작은 값 추가
    'n_epochs': [20, 50, 100],                  # 중간값 추가
    'lr_all': [0.002, 0.005, 0.01, 0.02],      # 더 세밀하게
    'reg_all': [0.02, 0.05, 0.1, 0.2],
    'reg_bu': [0.01, 0.05, 0.1],
    'reg_bi': [0.01, 0.05, 0.1]
}
grid = GridSearchCV(SVD, param_grid, measures=['RMSE', 'MAE'], cv=5, n_jobs=-1, joblib_verbose= 10)
grid.fit(data=data)
best_params = grid.best_params['rmse']

print(grid.best_score['rmse'])
print(best_params)

from surprise.model_selection import train_test_split

# 데이터 불러오기
data = Dataset.load_from_df(df1[['userID', 'itemID', 'rating']], reader)

# 훈련데이터, 테스트 데이터로 나누기
trainset, testset = train_test_split(data, test_size= 0.2, random_state = 42)

testset_df = pd.DataFrame(testset, columns=['userID', 'itemID', 'rating'])

import pickle

# GridSearch 결과 자동 적용
algo = SVD(**best_params)
algo.fit(trainset)
cross_validate(algo=algo, data=data, measures=['RMSE', 'MAE'], cv=10, verbose=True, n_jobs=-1)

# 모델(.pkl) 파일을 저장할 경로 지정
file_path = './4.SaveModel/model/svd_model_E.pkl'

# 지정한 경로에 모델을 pickle 형태로 저장
with open(file_path, 'wb') as file:
    pickle.dump(algo, file)

loaded_model1 = joblib.load('./4.SaveModel/model/svd_model_E.pkl')

predictions=loaded_model1.test(testset)

prediction_data = []

for uid, iid, true_r, est, _ in predictions:
    prediction_data.append({'userID': uid,
                            'itemID': iid,
                            'true_rating': true_r,
                            'predicted_rating': est})

print(prediction_data)

# 딕셔너리 리스트를 DataFrame 형태로 변환
predictions_df_E = pd.DataFrame(prediction_data)

# itemID와 SIDO를 매핑하기 위한 딕셔너리 생성
itemID_to_SIDO = df1.set_index('itemID')['SIDO'].to_dict()

# 예측 결과 DataFrame에 SIDO 컬럼 추가
predictions_df_E['SIDO'] = predictions_df_E['itemID'].map(itemID_to_SIDO)

# 실제 관심 여부(true_rec), 예측 관심 여부(est_rec) 초기화
predictions_df_E['true_rec'] = np.nan
predictions_df_E['est_rec'] = np.nan

# 실제 평점과 예측 평점의 평균 계산
mean_true_rating = predictions_df_E['true_rating'].mean()
mean_predicted_rating = predictions_df_E['predicted_rating'].mean()

# 실제 평점이 평균보다 높으면 true_rec = 1, 아니면 0
predictions_df_E['true_rec'] = np.where(predictions_df_E['true_rating'] > mean_true_rating, 1, 0)

# 예측 평점이 평균보다 높으면 est_rec = 1, 아니면 0
predictions_df_E['est_rec'] = np.where(predictions_df_E['predicted_rating'] > mean_predicted_rating, 1, 0)

grouped = predictions_df_E.groupby(['userID', 'true_rec'])

# 그룹별(사용자 × true_rec)로 반복 처리
for (user_id, true_rec), group in grouped:
    # true_rec 값이 1인 경우만 처리
    if true_rec == 1:
        # 해당 그룹에서 SIDO 값별 등장 횟수 계산
        sido_counts = group['SIDO'].value_counts()

        # 가장 많이 등장한 SIDO(최빈 지역)를 선택
        majority_sido = sido_counts.index[0] if len(sido_counts) > 0 else None

        # 최빈 SIDO와 일치하면 true_rec = 1, 나머지는 0으로 설정
        predictions_df_E.loc[group.index, 'true_rec'] = (group['SIDO'] == majority_sido).astype(int)

# userID와 predicted_rating 기준으로 다시 그룹화
grouped = predictions_df_E.groupby(['userID', 'predicted_rating'])

# 그룹별(사용자 × pred_rec)로 반복 처리
for (user_id, pred_rec), group in grouped:
    # pred_rec 값이 1인 경우만 처리
    if pred_rec == 1:
        # 해당 그룹에서 SIDO 값별 등장 횟수 계산
        sido_counts = group['SIDO'].value_counts()

        # 가장 많이 등장한 SIDO(최빈 지역)를 선택
        majority_sido = sido_counts.index[0] if len(sido_counts) > 0 else None

        # 최빈 SIDO와 일치하면 pred_rec = 1, 나머지는 0으로 설정
        predictions_df_E.loc[group.index, 'pred_rec'] = (group['SIDO'] == majority_sido).astype(int)

# 결과 출력
print(predictions_df_E)

def recall5_calculator(df):
    # userID 기준 오름차순, true_rec 기준 내림차순, predicted_rating 기준 내림차순으로 정렬
    # 이것은 표준 Recall@K가 아닌 커스텀 평가 지표입니다:
    # 실제 관심 아이템(true_rec=1)을 우선 배치하고, 그 중에서 예측 점수가 높은 순으로 평가
    df_sorted = df.sort_values(by=['userID', 'true_rec', 'predicted_rating'],
                               ascending=[True, False, False])

    # 특정 사용자에 대해 Recall@K를 계산하는 내부 함수
    def calculate_recall_at_k(user_data, k=5):
        # 전체 실제 관심 아이템(true_rec=1)의 개수
        total_relevant_items = user_data['true_rec'].sum()
        
        # 상위 K개 데이터 선택
        top_k_data = user_data.head(k)
        
        # 상위 K개 중 실제 관심 아이템(true_rec=1)의 개수
        relevant_in_top_k = top_k_data['true_rec'].sum()

        # Recall@K 계산: (상위 K개 중 관심 아이템 수) / (전체 관심 아이템 수)
        recall_at_k = relevant_in_top_k / total_relevant_items if total_relevant_items > 0 else 0

        return recall_at_k

    # userID 기준으로 그룹화하여 사용자별 Recall@5 계산
    recall_at_5_values = df_sorted.groupby('userID').apply(
        lambda x: calculate_recall_at_k(x, k=5),
        include_groups=False
    )

    # 전체 사용자에 대한 평균 Recall@5 계산
    average_recall_at_5 = recall_at_5_values.mean()

    return average_recall_at_5

# 평균 Recall@5 출력
cf_recall_at_5 = recall5_calculator(predictions_df_E)
print('수도권 권역의 CF Recall@5:' + str(cf_recall_at_5))

# 예측 기준으로 관심(est_rec=1)인 데이터만 필터링
filtered_predictions_df_E = predictions_df_E[predictions_df_E['est_rec'] == 1]

# userID 기준으로 그룹화 후 predicted_rating 상위 5개 아이템 선택
top_5_items_per_user = (
    filtered_predictions_df_E
    .sort_values('predicted_rating', ascending=False)
    .groupby('userID', as_index=False)
    .head(5)
)

# userID별로 itemID를 리스트 형태로 묶어 추천 리스트 생성
recommendation_lists = (
    top_5_items_per_user
    .groupby('userID')['itemID']
    .apply(list)
    .reset_index()
)

# 컬럼명을 userID / recommendation 으로 변경
recommendation_lists.columns = ['userID', 'recommendation']

# 각 사용자별 추천 리스트가 최대 5개까지만 포함되도록 제한
recommendation_lists['recommendation'] = recommendation_lists['recommendation'].apply(lambda x: x[:5])

# 최종 추천 결과 DataFrame 생성 후 CSV로 저장
df_E_final = recommendation_lists.copy()
df_E_final.to_csv('../4.SaveModel/result/testset_output/E_test_ouput.csv')

# ============================================================================
# Content-Based Filtering 모듈 추가 (하이브리드 추천을 위한 준비)
# ============================================================================

print("\n=== Content-Based 모듈 로딩 중 (TF-IDF) ===")

import os
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import load_npz

# CB 설정 (TF-IDF)
TFIDF_MODEL_DIR = "./4.SaveModel/model/tfidf_model"
MATRIX_PATH = os.path.join(TFIDF_MODEL_DIR, "tfidf_matrix.npz")
VECTORIZER_PATH = os.path.join(TFIDF_MODEL_DIR, "tfidf_vectorizer.pkl")
INDICES_PATH = os.path.join(TFIDF_MODEL_DIR, "poi_indices.pkl")
NAMES_PATH = os.path.join(TFIDF_MODEL_DIR, "poi_names.pkl")

# TF-IDF 모델 로드
try:
    # TF-IDF 행렬 로드
    tfidf_matrix = load_npz(MATRIX_PATH)
    print(f"TF-IDF 행렬 로드: {tfidf_matrix.shape}")

    # POI 인덱스 로드
    with open(INDICES_PATH, 'rb') as f:
        poi_indices = pickle.load(f)
    print(f"POI 인덱스 로드: {len(poi_indices)} 개")

    # POI 이름 로드
    with open(NAMES_PATH, 'rb') as f:
        poi_names = pickle.load(f)
    print(f"POI 이름 로드: {len(poi_names)} 개")

except Exception as e:
    print(f"❌ TF-IDF 모델 로드 실패: {e}")
    print("먼저 CB_model_E_tfidf.py를 실행하세요!")
    raise

# Fuzzy Matching: 사용자 아이템 → POI 아이템 매핑
print("\n아이템 이름 매칭 중...")
item_mapping = {}
all_user_items = df1['itemID'].unique()

# POI 정규화 맵 생성
poi_normalized_map = {}
for poi_name in poi_indices.keys():
    normalized = str(poi_name).lower().replace(" ", "")
    if normalized not in poi_normalized_map:
        poi_normalized_map[normalized] = poi_name

# 1단계: 정확 매칭
for user_item in all_user_items:
    if user_item in poi_indices:
        item_mapping[user_item] = user_item

# 2단계: 정규화 매칭
unmatched_items = [item for item in all_user_items if item not in item_mapping]

for user_item in unmatched_items:
    user_normalized = str(user_item).lower().replace(" ", "")
    if user_normalized in poi_normalized_map:
        item_mapping[user_item] = poi_normalized_map[user_normalized]

matched_count = len(item_mapping)
matched_ratio = matched_count / len(all_user_items) * 100
print(f"아이템 매칭 완료: {matched_count}/{len(all_user_items)} ({matched_ratio:.2f}%)")

still_unmatched = [item for item in all_user_items if item not in item_mapping]
if len(still_unmatched) > 0:
    print(f"매칭 실패: {len(still_unmatched)} 개")

# 아이템 간 유사도 계산 함수 (TF-IDF 기반)
def get_item_similarity(item1, item2):
    """두 아이템 간의 TF-IDF 코사인 유사도 계산"""
    # 매핑 적용
    poi_item1 = item_mapping.get(item1, item1)
    poi_item2 = item_mapping.get(item2, item2)

    # POI 인덱스 확인
    if poi_item1 not in poi_indices or poi_item2 not in poi_indices:
        return 0.0

    try:
        # POI 인덱스 가져오기
        idx1 = poi_indices[poi_item1]
        idx2 = poi_indices[poi_item2]

        # TF-IDF 벡터 추출
        vec1 = tfidf_matrix[idx1:idx1+1]
        vec2 = tfidf_matrix[idx2:idx2+1]

        # 코사인 유사도 계산
        similarity = cosine_similarity(vec1, vec2)[0][0]
        return float(similarity)

    except Exception as e:
        return 0.0

# 사용자가 선호한 아이템 가져오기
def get_user_liked_items(user_id, threshold=4.0):
    """사용자가 높은 평점을 준 아이템 리스트 반환"""
    user_ratings = df1[df1['userID'] == user_id]
    liked_items = user_ratings[user_ratings['rating'] >= threshold]['itemID'].tolist()
    return liked_items

# CB 점수 계산 함수
def calculate_cb_score(user_id, candidate_item):
    """
    사용자가 선호한 아이템들과 후보 아이템의 평균 유사도 계산
    
    Args:
        user_id: 사용자 ID
        candidate_item: 후보 아이템명
    
    Returns:
        평균 유사도 (0~1)
    """
    # 사용자가 높은 평점을 준 아이템들 가져오기
    user_liked_items = get_user_liked_items(user_id, threshold=4.0)
    
    if not user_liked_items:
        return 0.0
    
    # 각 선호 아이템과 후보 아이템 간 유사도 계산
    similarities = []
    for liked_item in user_liked_items:
        sim = get_item_similarity(liked_item, candidate_item)
        if sim > 0:
            similarities.append(sim)
    
    # 평균 유사도 반환
    if similarities:
        return np.mean(similarities)
    else:
        return 0.0

print("Content-Based 모듈 로딩 완료\n")


sido_df=df1[['itemID', 'SIDO']].drop_duplicates()

# 모든 사용자-아이템 조합에 대한 예측 수행
user_item_matrix = df1.pivot_table(index = 'userID', columns = 'itemID', values = 'rating').fillna(0)

print("\n=== 모든 사용자-아이템 조합에 대해 SVD 예측 수행 중 ===")
all_users = user_item_matrix.index.tolist()
all_items = user_item_matrix.columns.tolist()

print(f"사용자 수: {len(all_users)}, 아이템 수: {len(all_items)}")
print(f"예측 조합 수: {len(all_users) * len(all_items):,}")

# 모든 조합 생성
all_predictions = []
for user_id in all_users:
    for item_id in all_items:
        # SVD 예측 (실제 평점은 0으로)
        pred = loaded_model1.predict(user_id, item_id)
        all_predictions.append({
            'user_id': user_id,
            'item_id': item_id,
            'predicted_rating': pred.est
        })

result_dfc = pd.DataFrame(all_predictions)
dfc_pivot = result_dfc.pivot_table('predicted_rating', index='user_id', columns='item_id')

print(f"예측 완료: {len(result_dfc):,} 개")
print(f"dfc_pivot 형태: {dfc_pivot.shape}")

# ============================================================================
# 하이브리드 추천 생성 (CF + CB)
# ============================================================================

print("\n=== 하이브리드 추천 생성 중 ===")

# 하이브리드 파라미터
ALPHA = 0.7  # CF 가중치
BETA = 0.3   # CB 가중치 (1 - ALPHA)
TOP_K_CANDIDATES = 20  # CF에서 먼저 선택할 후보 개수
FINAL_K = 5  # 최종 추천 개수

# 이미 방문한 곳 제외하고 하이브리드 추천
hybrid_recommendations = []

for idx, user in enumerate(user_item_matrix.index):
    # 해당 사용자가 방문한 곳
    applied_accs = set(user_item_matrix.loc[user][user_item_matrix.loc[user] != 0].index)

    # 1단계: CF 기반 상위 후보 선택
    sorted_acc_indices = dfc_pivot.iloc[idx].argsort()[::-1]
    cf_candidates = [acc for acc in user_item_matrix.columns[sorted_acc_indices]
                     if acc not in applied_accs][:TOP_K_CANDIDATES]

    # 2단계: 각 후보에 대해 하이브리드 점수 계산
    hybrid_scores = []

    for item in cf_candidates:
        # CF 점수 (정규화: 0~1 범위로)
        cf_score_raw = dfc_pivot.iloc[idx][item]
        cf_score_normalized = (cf_score_raw - 1) / 4  # 1~5 범위를 0~1로 변환

        # CB 점수 계산
        cb_score = calculate_cb_score(user, item)

        # 하이브리드 점수 = α * CF + β * CB
        hybrid_score = ALPHA * cf_score_normalized + BETA * cb_score

        hybrid_scores.append((item, hybrid_score, cf_score_normalized, cb_score))
    
    # 3단계: 하이브리드 점수 기준으로 정렬 후 상위 K개 선택
    hybrid_scores.sort(key=lambda x: x[1], reverse=True)
    top_items = hybrid_scores[:FINAL_K]
    
    # 결과 저장
    for item, h_score, cf_score, cb_score in top_items:
        hybrid_recommendations.append({
            'userID': user,
            'itemID': item,
            'hybrid_score': h_score,
            'cf_score': cf_score,
            'cb_score': cb_score
        })

# DataFrame으로 변환
hybrid_df = pd.DataFrame(hybrid_recommendations)

print(f"하이브리드 추천 생성 완료: {len(hybrid_df)} 개 추천")
print(f"평균 CF 점수: {hybrid_df['cf_score'].mean():.3f}")
print(f"평균 CB 점수: {hybrid_df['cb_score'].mean():.3f}")
print(f"평균 하이브리드 점수: {hybrid_df['hybrid_score'].mean():.3f}\n")

# 기존 형식으로 변환 (SIDO 필터링을 위해)
top_recommendations = hybrid_df[['userID', 'itemID']].copy()
top_recommendations_with_sido = pd.merge(top_recommendations, sido_df, on='itemID', how='left')

def filter_majority_sido(group):
    sido_counts = group['SIDO'].value_counts()
    if len(sido_counts) > 0:
        majority_sido = sido_counts.idxmax()
        group = group[group['SIDO'] == majority_sido]
    return group

# userID 기준으로 그룹화한 뒤, 각 사용자 그룹에 대해 filter_majority_sido 함수 적용
# (include_groups=True 옵션: groupby 결과에서 그룹 키를 함께 전달)
filtered_top_recommendations = (
    top_recommendations_with_sido[['userID', 'itemID', 'SIDO']]
    .groupby('userID', group_keys=False)
    .apply(filter_majority_sido, include_groups=False)
    .reset_index(drop=True)
)

# 함수 적용 후 생성된 멀티인덱스를 정리해 단일 인덱스로 재설정
filtered_top_recommendations.reset_index(drop=True, inplace=True)

# ============================================================================
# 최종 결과 저장
# ============================================================================

# 1. 기존 형식 (CF 전용) - 호환성 유지
filtered_top_recommendations.to_csv('./4.SaveModel/result/final_output/E_top_recommendations.csv')
print("CF 전용 추천 결과 저장: E_top_recommendations.csv")

# 2. 하이브리드 상세 결과 (점수 정보 포함)
# SIDO 정보 추가
hybrid_df_with_sido = pd.merge(hybrid_df, sido_df, on='itemID', how='left')

# SIDO 필터링 적용
hybrid_filtered = (
    hybrid_df_with_sido
    .groupby('userID', group_keys=False)
    .apply(filter_majority_sido, include_groups=False)
    .reset_index(drop=True)
)

hybrid_filtered.to_csv('./4.SaveModel/result/final_output/E_hybrid_recommendations_detailed.csv', index=False)
print("하이브리드 상세 추천 결과 저장: E_hybrid_recommendations_detailed.csv")

# ============================================================================
# CB 점수 분포 확인
# ============================================================================

print("\n=== CB 점수 분포 분석 ===")

# CB 점수가 0인 비율 계산
cb_zero_count = (hybrid_df['cb_score'] == 0).sum()
cb_zero_ratio = cb_zero_count / len(hybrid_df) * 100

print(f"CB 점수가 0인 항목 개수: {cb_zero_count}/{len(hybrid_df)}")
print(f"CB 점수가 0인 비율: {cb_zero_ratio:.2f}%")
print("\nCB 점수 통계:")
print(hybrid_df['cb_score'].describe())

# ============================================================================
# 하이브리드 평가 함수
# ============================================================================

def evaluate_hybrid_recall(hybrid_df, test_df, k=5):
    """
    하이브리드 추천 결과에 대한 Recall@K 계산 (CF와 동일한 기준 적용)

    Args:
        hybrid_df: 하이브리드 추천 결과 (userID, itemID, hybrid_score 포함)
        test_df: 테스트셋 데이터 (userID, itemID, rating 포함)
        k: 상위 K개 추천 평가

    Returns:
        평균 Recall@K
    """
    # SIDO 정보 추가
    test_df_with_sido = test_df.merge(sido_df, left_on='itemID', right_on='itemID', how='left')

    # true_rec 계산 (CF와 동일한 방식)
    mean_rating = test_df['rating'].mean()
    test_df_with_sido['true_rec'] = (test_df_with_sido['rating'] > mean_rating).astype(int)

    # 사용자별 최빈 SIDO 기준으로 true_rec 재조정
    for user_id in test_df_with_sido['userID'].unique():
        user_data = test_df_with_sido[
            (test_df_with_sido['userID'] == user_id) &
            (test_df_with_sido['true_rec'] == 1)
        ]

        if len(user_data) > 0:
            sido_counts = user_data['SIDO'].value_counts()
            majority_sido = sido_counts.index[0] if len(sido_counts) > 0 else None

            # 최빈 SIDO와 일치하는 항목만 true_rec=1 유지
            mask = (test_df_with_sido['userID'] == user_id) & (test_df_with_sido['true_rec'] == 1)
            test_df_with_sido.loc[mask, 'true_rec'] = (
                test_df_with_sido.loc[mask, 'SIDO'] == majority_sido
            ).astype(int)

    # 실제 관심 아이템 추출
    relevant_items = test_df_with_sido[test_df_with_sido['true_rec'] == 1].groupby('userID')['itemID'].apply(set).to_dict()

    recall_scores = []

    # 사용자별로 Recall@K 계산
    for user_id in hybrid_df['userID'].unique():
        # 해당 사용자의 실제 관심 아이템
        if user_id not in relevant_items:
            continue

        user_relevant = relevant_items[user_id]

        if len(user_relevant) == 0:
            continue

        # 해당 사용자의 하이브리드 추천 상위 K개
        user_recommendations = (
            hybrid_df[hybrid_df['userID'] == user_id]
            .nlargest(k, 'hybrid_score')['itemID']
            .tolist()
        )

        # 추천된 아이템 중 실제 관심 아이템의 개수
        relevant_recommended = len(set(user_recommendations) & user_relevant)

        # Recall@K = (추천된 관심 아이템 수) / (전체 관심 아이템 수)
        recall_at_k = relevant_recommended / len(user_relevant)
        recall_scores.append(recall_at_k)

    # 평균 Recall@K 반환
    return np.mean(recall_scores) if recall_scores else 0.0

# ============================================================================
# 성능 비교 평가
# ============================================================================

print("\n=== 성능 비교 평가 ===")

# 하이브리드 Recall@5 계산
hybrid_recall_at_5 = evaluate_hybrid_recall(hybrid_df, testset_df, k=5)

print(f"\n[Recall@5 비교]")
print(f"CF 전용 Recall@5:      {cf_recall_at_5:.4f}")
print(f"하이브리드 Recall@5:    {hybrid_recall_at_5:.4f}")

# 성능 개선율 계산
if cf_recall_at_5 > 0:
    improvement = ((hybrid_recall_at_5 - cf_recall_at_5) / cf_recall_at_5) * 100
    print(f"성능 개선율:            {improvement:+.2f}%")
else:
    print("성능 개선율:            계산 불가 (CF Recall이 0)")

print("\n=== 하이브리드 추천 시스템 완료 ===")
print(f"총 사용자 수: {len(user_item_matrix)}")
print(f"사용자당 추천 개수: {FINAL_K}")
print(f"CF 가중치: {ALPHA}, CB 가중치: {BETA}")
print(f"최종 추천 개수: {len(hybrid_filtered)}")