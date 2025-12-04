#!/usr/bin/env python3

import argparse
import json
import os

import numpy as np
import pandas as pd
import keras
from keras import layers


def load_data(csv_path: str):
    df = pd.read_csv(csv_path)

    # Drop purely technical columns
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # Ensure all remaining columns are numeric
    df = df.astype("float32")

    feature_names = list(df.columns)
    X = df.values.astype("float32")

    # Simple normalization: (x - mean) / std
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1.0  # avoid divide-by-zero

    X_norm = (X - mean) / std

    return X_norm, feature_names, mean, std


def train_model(
    X: np.ndarray,
    batch_size: int = 64,
    epochs: int = 50,
    dropout_rate: float = 0.1,
):
    n_samples, n_features = X.shape

    # Train/val split
    split = int(0.8 * n_samples)
    X_train = X[:split]
    X_val = X[split:]

    model = keras.Sequential([
        layers.Input(shape=(n_features,)),
        layers.Dropout(dropout_rate),              # simuleert missing features
        layers.Dense(64, activation="relu"),
        layers.Dense(64, activation="relu"),
        layers.Dense(n_features, activation="linear"),  # reconstructie
    ])

    model.compile(
        optimizer='adam',
        # learning_rate=1e-3,
        loss="mse",
    )

    history = model.fit(
        X_train,
        X_train,  # autoencoder target = input
        validation_data=(X_val, X_val),
        epochs=epochs,
        batch_size=batch_size,
    )

    return model, history


def save_artifacts(
    model: keras.Model,
    feature_names,
    mean,
    std,
    output: str,
):
    if '/' in output:
        os.makedirs(os.path.dirname(output), exist_ok=True)

    # Save model
    model.save(output + ".keras")

    # Save metadata (feature order + normalization)
    meta = {
        "feature_names": feature_names,
        "mean": mean.tolist(),
        "std": std.tolist(),
    }
    with open(output + ".json", "w") as jsonf:
        json.dump(meta, jsonf, indent=4)
    print(f"Saved model to {output}.keras")
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
        help="Directory to save model and metadata",
    )
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.1)
    args = parser.parse_args()

    print(f"Loading data from {args.csv}...")
    X, feature_names, mean, std = load_data(args.csv)
    print(f"Loaded {X.shape[0]} samples, {X.shape[1]} features")

    print("Training model...")
    model, history = train_model(
        X,
        # batch_size=args.batch_size,
        epochs=args.epochs,
        dropout_rate=args.dropout,
    )

    print("Saving artifacts...")
    save_artifacts(model, feature_names, mean, std, args.output)


if __name__ == "__main__":
    main()
