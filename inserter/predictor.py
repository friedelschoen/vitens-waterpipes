from abc import ABC, abstractmethod
import json
import os.path
from typing import cast

import joblib
import keras
import numpy as np
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
            list(input[sensor_name] for sensor_name in self.feature_names),
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
        for i, sensor_name in enumerate(self.feature_names):
            if sensor_name in self.skip_names:
                continue
            # clamp op >= 0 om negatieve flows/drukken te voorkomen
            result[sensor_name] = max(float(y_pred[i]), 0.0)

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


class PerFeatureModelPredictor(Predictor):
    """
    Laadt één joblib-bestand met:
        {
            "models": {feature_name: estimator},
            "feature_names": [...],
            "mean": [...]/None,
            "std": [...]/None,
        }

    En kan voor elk feature een voorspelling maken op basis van
    alle andere features.
    """

    def __init__(self, path: str, skip_names: list[str]):
        payload = joblib.load(path + ".joblib")

        self.models: dict[str, keras.Model] = payload["models"]
        self.feature_names: list[str] = payload["feature_names"]
        self.skip_names = set(skip_names)

        mean = payload.get("mean")
        std = payload.get("std")
        if mean is not None and std is not None:
            self.mean = np.array(mean, dtype="float32")
            self.std = np.array(std, dtype="float32")
            self.std[self.std == 0] = 1.0
            self.normalized = True
        else:
            self.mean = []
            self.std = []
            self.normalized = False

    def predict(self, src: dict[str, float]) -> dict[str, float]:
        n_features = len(self.feature_names)
        x = np.zeros(n_features, dtype="float32")

        # Bouw volledige vector in feature-volgorde
        for i, sensor_name in enumerate(self.feature_names):
            v = src.get(sensor_name, None)
            if v is None:
                if self.normalized:
                    # neutrale waarde: mean
                    x[i] = self.mean[i]
                else:
                    x[i] = 0.0
            else:
                x[i] = float(v)

        # normaliseer indien mogelijk
        if self.normalized:
            x_full = (x - self.mean) / self.std
        else:
            x_full = x

        result = src.copy()

        for j, sensor_name in enumerate(self.feature_names):
            if sensor_name in self.skip_names:
                continue

            model = self.models.get(sensor_name)
            if model is None:
                # veiligheid: als er geen model is, sla over
                continue

            # input = alle features behalve j
            x_in = np.delete(x_full, j)
            y_pred = model.predict(x_in[None, :])[0]

            # terugschalen naar originele schaal
            if self.normalized:
                y_pred = y_pred * self.std[j] + self.mean[j]

            # clamp >= 0
            result[sensor_name] = max(float(y_pred), 0.0)

        return result


PREDICTORS: dict[str, Predictor] = {
    "none": PassthroughPredictor(),
    "ae": KerasPredictor("/data/model/ae", ["timestamp"]),
    # "rf": RandomForestPredictor("/model/rf", ["timestamp"]),
    "lin": PerFeatureModelPredictor("/data/model/lin", ["timestamp"]),
    "ridge": PerFeatureModelPredictor("/data/model/ridge", ["timestamp"]),
    "lasso": PerFeatureModelPredictor("/data/model/lasso", ["timestamp"]),
}
