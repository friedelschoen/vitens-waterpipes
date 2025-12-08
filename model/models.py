

# =========================
# Abstracte model-laag
# =========================

from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass
import json
from typing import cast

import joblib
import keras
from keras import layers
import numpy as np
from sklearn.ensemble import RandomForestRegressor


@dataclass
class DataSet:
    X: np.ndarray
    feature_names: list[str]
    mean: np.ndarray | None = None
    std: np.ndarray | None = None

    def normalize(self) -> "DataSet":
        # Simple normalization: (x - mean) / std
        mean = self.X.mean(axis=0)
        std = self.X.std(axis=0)
        std[std == 0] = 1.0  # avoid divide-by-zero
        X_norm = (self.X - mean) / std

        return DataSet(X=X_norm, feature_names=self.feature_names, mean=mean, std=std)


class ModelTrainer(ABC):
    MODEL_NAME: str = "base"

    @classmethod
    @abstractmethod
    def add_cli_args(cls, parser: argparse.ArgumentParser) -> None:
        """
        Voeg model-specifieke CLI-argumenten toe.
        Bijvoorbeeld --ae-epochs, --rf-n-estimators, ...
        """
        ...

    @classmethod
    @abstractmethod
    def from_args(cls, args: argparse.Namespace) -> "ModelTrainer":
        """
        Construeer een trainer uit argparse-args.
        """
        ...

    @classmethod
    @abstractmethod
    def needs_normalization(cls) -> bool:
        """
        Geeft aan of de data genormaliseerd moet worden voor dit modeltype.
        """
        ...

    @abstractmethod
    def train(self, data: DataSet):
        """
        Train het model op de gegeven data en retourneer het getrainde model.
        """
        ...

    @abstractmethod
    def save(self, model, data: DataSet, output_prefix: str) -> None:
        """
        Sla model + metadata op onder de gegeven output-prefix.
        """
        ...


class AutoencoderTrainer(ModelTrainer):
    MODEL_NAME = "ae"

    @classmethod
    def add_cli_args(cls, parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group("Autoencoder (ae) opties")
        group.add_argument("--ae-epochs", type=int, default=50,
                           help="Aantal epochs voor de autoencoder.")
        group.add_argument("--ae-batch-size", type=int, default=64,
                           help="Batch size voor de autoencoder.")
        group.add_argument("--ae-dropout", type=float, default=0.1,
                           help="Dropout-rate (simuleert missing features).")

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "AutoencoderTrainer":
        return cls(epochs=args.ae_epochs,  batch_size=args.ae_batch_size, dropout_rate=args.ae_dropout)

    @classmethod
    def needs_normalization(cls) -> bool:
        return True

    def __init__(self,  epochs: int,                 batch_size: int,                dropout_rate: float):
        self.epochs = epochs
        self.batch_size = batch_size
        self.dropout_rate = dropout_rate

    def train(self, data: DataSet) -> keras.Model:
        X = data.X
        n_samples, n_features = X.shape

        # Train/val split
        split = int(0.8 * n_samples)
        X_train = X[:split]
        X_val = X[split:]

        model = keras.Sequential(
            [
                layers.Input(shape=(n_features,)),
                # simuleert missing features
                layers.Dropout(self.dropout_rate),
                layers.Dense(64, activation="relu"),
                layers.Dense(64, activation="relu"),
                layers.Dense(n_features, activation="linear"),  # reconstructie
            ]
        )

        model.compile(
            optimizer="adam",
            loss="mse",
        )

        model.fit(
            X_train,
            X_train,  # autoencoder target = input
            validation_data=(X_val, X_val),
            epochs=self.epochs,
            batch_size=self.batch_size,
        )

        return model

    def save(self, model: keras.Model, data: DataSet, output_prefix: str) -> None:
        # Save model
        model.save(output_prefix + ".keras")

        # Save metadata
        meta = {
            "feature_names": data.feature_names,
            "mean": data.mean.tolist() if data.mean is not None else None,
            "std": data.std.tolist() if data.std is not None else None,
        }
        with open(output_prefix + ".json", "w") as jsonf:
            json.dump(meta, jsonf, indent=4)

        print(f"[AE] Saved model to {output_prefix}.keras")
        print(f"[AE] Saved metadata to {output_prefix}.json")


class RandomForestTrainer(ModelTrainer):
    MODEL_NAME = "rf"

    @classmethod
    def add_cli_args(cls, parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group("RandomForest (rf) opties")
        group.add_argument("--rf-n-estimators", type=int, default=200,
                           help="Aantal bomen in het RandomForest.")
        group.add_argument("--rf-max-depth", type=int, default=None,
                           help="Maximale diepte van de bomen (of None).")
        group.add_argument("--rf-n-jobs", type=int, default=-1,
                           help="Aantal parallelle jobs voor training.")

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "RandomForestTrainer":
        return cls(
            n_estimators=args.rf_n_estimators,
            max_depth=args.rf_max_depth,
            n_jobs=args.rf_n_jobs,
        )

    @classmethod
    def needs_normalization(cls) -> bool:
        return False

    def __init__(self,  n_estimators: int,
                 max_depth: int,
                 n_jobs: int):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.n_jobs = n_jobs

    # --- instance-level ---

    def train(self, data: DataSet) -> RandomForestRegressor:
        """
        Train een multi-output RandomForestRegressor die X reconstrueert uit X.
        (Net als je autoencoder, maar dan met bomen.)
        """
        X = data.X
        model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            n_jobs=self.n_jobs,
            random_state=42,
        )
        model.fit(X, X)
        return model

    def save(self, model: RandomForestRegressor, data: DataSet, output_prefix: str) -> None:
        joblib.dump(model, output_prefix + ".joblib",
                    compress=cast(int, ('xz', 9)))

        meta = {
            "feature_names": data.feature_names,
        }
        with open(output_prefix + ".json", "w") as jsonf:
            json.dump(meta, jsonf, indent=4)

        print(f"[RF] Saved model to {output_prefix}.joblib")
        print(f"[RF] Saved metadata to {output_prefix}.json")


TRAINERS: list[type[ModelTrainer]] = [
    AutoencoderTrainer,
    RandomForestTrainer,
]
