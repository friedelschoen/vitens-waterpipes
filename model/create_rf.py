#!/usr/bin/env python3

import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


def load_data(csv_path: str):
    df = pd.read_csv(csv_path)

    # Drop purely technical columns
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # Ensure all remaining columns are numeric
    df = df.astype("float32")

    feature_names = list(df.columns)
    X = df.values.astype("float32")

    return X, feature_names


def train_model(
    X: np.ndarray,
    n_estimators: int = 200,
    max_depth: int | None = None,
    n_jobs: int = -1,
):
    """
    Train a multi-output RandomForestRegressor that reconstructs X from X.
    (Net als je autoencoder, maar nu met bomen.)
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        n_jobs=n_jobs,
        random_state=42,
    )
    model.fit(X, X)
    return model


def save_artifacts(
    model: RandomForestRegressor,
    feature_names,
    output: str,
):
    # output is een path-prefix, net als bij je Keras-script
    if "/" in output:
        os.makedirs(os.path.dirname(output), exist_ok=True)

    # Save model
    joblib.dump(model, output + ".joblib")

    # Save metadata (feature order + normalization)
    meta = {
        "feature_names": feature_names,
    }
    with open(output + ".json", "w") as jsonf:
        json.dump(meta, jsonf, indent=4)

    print(f"Saved model to {output}.joblib")
    print(f"Saved metadata to {output}.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data.csv",
        help="Path to CSV file with sensor/valve data",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path prefix to save model and metadata (e.g. models/rf_model)",
    )
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()

    print(f"Loading data from {args.csv}...")
    X, feature_names = load_data(args.csv)
    print(f"Loaded {X.shape[0]} samples, {X.shape[1]} features")

    print("Training RandomForestRegressor (multi-output)...")
    model = train_model(
        X,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        n_jobs=args.n_jobs,
    )

    print("Saving artifacts...")
    save_artifacts(model, feature_names, args.output)


if __name__ == "__main__":
    main()
