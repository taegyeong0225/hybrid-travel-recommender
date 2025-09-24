# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
import os
import joblib
import surprise
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split, GridSearchCV
import pickle

def train_model(region_id: str):
    """
    Train a model for a given region.

    Args:
        region_id (str): The region ID (e.g., 'E', 'F', 'G', 'H').
    """
    print(f"Starting training for region {region_id}...")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "1.inputdata")
    PREPROC_DIR = os.path.join(BASE_DIR, "2.preprocessed")
    SAVEMODEL_DIR = os.path.join(BASE_DIR, "4.SaveModel")

    # Load data
    visit_df = pd.read_csv(os.path.join(DATA_DIR, f"tn_visit_area_info_{region_id}.csv"))

    # Preprocessing
    visit_info = visit_df[(visit_df['VISIT_AREA_TYPE_CD'] >= 1) & (visit_df['VISIT_AREA_TYPE_CD'] <= 8)]
    visit_info = visit_info.groupby('VISIT_AREA_NM').filter(lambda x: len(x) > 1)
    visit_info = visit_info.reset_index(drop=True)

    visit_info['ratings'] = visit_info[['DGSTFN', 'REVISIT_INTENTION', 'RCMDTN_INTENTION']].mean(axis=1)
    visit_info['TRAVELER_ID'] = visit_info['TRAVEL_ID'].str.split('_').str[1]
    visit_info['SIDO'] = visit_info['LOTNO_ADDR'].str.split().str[0]

    most_frequent_visits = visit_info.groupby('LOTNO_ADDR')['VISIT_AREA_NM'].agg(lambda x: x.mode().iloc[0]).reset_index()
    visit_info = visit_info.merge(most_frequent_visits, on='LOTNO_ADDR', how='left', suffixes=('', '_most_frequent'))
    visit_info['VISIT_AREA_NM'] = visit_info['VISIT_AREA_NM_most_frequent'].fillna(visit_info['VISIT_AREA_NM'])
    visit_info.drop(columns=['VISIT_AREA_NM_most_frequent'], inplace=True)

    df1 = visit_info.rename(columns={'TRAVELER_ID': 'userID', 'VISIT_AREA_NM': 'itemID', 'ratings': 'rating'})
    df1 = df1[['userID', 'itemID', 'rating', 'SIDO']]
    
    # Ensure preprocessed directory exists
    os.makedirs(PREPROC_DIR, exist_ok=True)
    df1.to_csv(os.path.join(PREPROC_DIR, f"df{region_id}.csv"))

    # Train model
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df1[['userID', 'itemID', 'rating']], reader)

    # Split data
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

    # Grid search
    param_grid = {'n_factors': [50, 100], 'n_epochs': [10, 20], 'lr_all': [0.005, 0.01], 'reg_all': [0.02, 0.1]}
    grid = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=3, n_jobs=-1)
    grid.fit(data)

    print(f"Best RMSE for region {region_id}: {grid.best_score['rmse']}")
    print(f"Best params for region {region_id}: {grid.best_params['rmse']}")

    # Train final model with best params
    algo = SVD(**grid.best_params['rmse'])
    algo.fit(trainset)

    # Save model
    model_path = os.path.join(SAVEMODEL_DIR, "model")
    os.makedirs(model_path, exist_ok=True)
    file_path = os.path.join(model_path, f"svd_model_{region_id}.pkl")
    with open(file_path, 'wb') as file:
        pickle.dump(algo, file)

    print(f"Model for region {region_id} saved to {file_path}")


if __name__ == "__main__":
    regions = ['E', 'F', 'G', 'H']
    for region in regions:
        train_model(region)
