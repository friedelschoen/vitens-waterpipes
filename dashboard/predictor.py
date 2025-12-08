from abc import ABC, abstractmethod
import json
from typing import cast

import joblib
import numpy as np
import keras
from sklearn.ensemble import RandomForestRegressor


class Predictor(ABC):
    @abstractmethod
    def predict(self, input: dict[str, float]) -> dict[str, float]:
        ...


class PassthroughPredictor(Predictor):
    def predict(self, input: dict[str, float]) -> dict[str, float]:
        return input


class ModelPredictor(Predictor, ABC):
    """
    Basisclass voor alle "vector in → vector uit"-modellen.

    - Kan optioneel normalisatie (mean/std) gebruiken als `normalized=True`.
    - Subclasses hoeven alleen `_predict_row` te implementeren.
    """

    def __init__(self, path: str, skip_names: list[str], normalized: bool = False):
        self.path = path
        self.skip_names = skip_names
        self.normalized = normalized

        with open(path + ".json") as metaf:
            meta = json.load(metaf)

        self.feature_names = list(meta["feature_names"])

        if self.normalized:
            self.mean = np.array(meta["mean"], dtype="float32")
            self.std = np.array(meta["std"], dtype="float32")
            self.std[self.std == 0] = 1.0
        else:
            # Dummy velden zodat code niet crasht als je er per ongeluk aan zit
            self.mean = []
            self.std = []

    @abstractmethod
    def _predict_row(self, x_batch: np.ndarray) -> np.ndarray:
        """
        x_batch: shape (batch, n_features)
        return:  shape (batch, n_features)
        """
        ...

    def predict(self, input: dict[str, float]) -> dict[str, float]:
        x = np.array(
            list(input[name] for name in self.feature_names),
            'float32'
        )

        # Normaliseren indien nodig
        if self.normalized:
            x_in = (x - self.mean) / self.std
        else:
            x_in = x

        x_in = x_in[None, :]  # batch-dim toevoegen

        # Modelvoorspelling
        y_pred = self._predict_row(x_in)[0]

        # De-normaliseren indien nodig
        if self.normalized:
            y_pred = y_pred * self.std + self.mean

        # Dict terugbouwen
        result = input.copy()
        for i, name in enumerate(self.feature_names):
            if name in self.skip_names:
                continue
            # clamp op >= 0 om negatieve flows/drukken te voorkomen
            result[name] = max(float(y_pred[i]), 0.0)

        return result


class KerasPredictor(ModelPredictor):
    def __init__(self, path: str, skip_names: list[str]):
        super().__init__(path, skip_names, True)
        self.model = cast(
            keras.Model, keras.models.load_model(path + ".keras")
        )

    def _predict_row(self, input: np.ndarray) -> np.ndarray:
        return self.model.predict(input, verbose=cast(str, 0))


class RandomForestPredictor(ModelPredictor):
    def __init__(self, path: str, skip_names: list[str]):
        super().__init__(path, skip_names, False)
        self.model = cast(
            RandomForestRegressor,
            joblib.load(path + ".joblib"),
        )

    def _predict_row(self, input: np.ndarray) -> np.ndarray:
        return self.model.predict(input)
