# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
import joblib
import pickle
import sys

def get_recommendations(region_id: str, user_id: str):
    """
    Generate recommendations for a given user in a given region.

    Args:
        region_id (str): The region ID (e.g., 'E', 'F', 'G', 'H').
        user_id (str): The user ID.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SAVEMODEL_DIR = os.path.join(BASE_DIR, "4.SaveModel")
    PREPROC_DIR = os.path.join(BASE_DIR, "2.preprocessed")

    # Load model
    model_path = os.path.join(SAVEMODEL_DIR, "model", f"svd_model_{region_id}.pkl")
    try:
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
    except FileNotFoundError:
        return {"error": f"Model for region {region_id} not found."}

    # Load data
    data_path = os.path.join(PREPROC_DIR, f"df{region_id}.csv")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        return {"error": f"Data for region {region_id} not found."}

    all_items = df['itemID'].unique()
    user_rated_items = df[df['userID'] == user_id]['itemID'].unique()
    items_to_predict = np.setdiff1d(all_items, user_rated_items)

    predictions = []
    for item_id in items_to_predict:
        pred = model.predict(user_id, item_id)
        predictions.append((item_id, pred.est))

    predictions.sort(key=lambda x: x[1], reverse=True)

    top_5_recs = [item[0] for item in predictions[:5]]

    return {"recommendations": top_5_recs}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python recommender.py <region_id> <user_id>")
        sys.exit(1)

    region = sys.argv[1]
    user = sys.argv[2]
    
    recommendations = get_recommendations(region, user)
    print(recommendations)
