#!/usr/bin/env python3

import argparse
import os

import pandas as pd

from models import DataSet, TRAINERS


def ensure_output_dir(output_prefix: str) -> None:
    """
    Zorgt dat de directory van een pad-prefix bestaat.
    Bijv. 'models/ae_model' -> maakt 'models' aan.
    """
    if "/" in output_prefix:
        os.makedirs(os.path.dirname(output_prefix), exist_ok=True)


def load_data(csv_path: str, normalize: bool) -> DataSet:
    """
    Laadt data uit CSV, dropt 'id' kolom, cast naar float32.
    Optioneel normaliseren met (x - mean) / std.
    """
    df = pd.read_csv(csv_path)

    # Drop purely technical columns
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # Ensure all remaining columns are numeric
    df = df.astype("float32")
    feature_names = list(df.columns)
    X = df.values.astype("float32")

    if not normalize:
        return DataSet(X=X, feature_names=feature_names)

    # Simple normalization: (x - mean) / std
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1.0  # avoid divide-by-zero
    X_norm = (X - mean) / std

    return DataSet(X=X_norm, feature_names=feature_names, mean=mean, std=std)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train een reconstructiemodel (autoencoder of random forest) op CSV-data."
    )

    parser.add_argument(
        "--model",
        choices=list(t.MODEL_NAME for t in TRAINERS),
        required=True,
        help="Type model om te trainen",
    )
    parser.add_argument(
        "--csv",
        default="data.csv",
        help="Pad naar CSV bestand met sensor/valve data.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Pad-prefix om model en metadata op te slaan (bijv. models/ae_model).",
    )

    # Laat elke trainer zijn eigen opties toevoegen
    for trainer_cls in TRAINERS:
        trainer_cls.add_cli_args(parser)

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    trainer_clss = [t for t in TRAINERS if t.MODEL_NAME == args.model]
    if len(trainer_clss) == 0:
        raise ValueError(f"Unknown model type: {args.model!r}")

    trainer_cls = trainer_clss[0]
    trainer = trainer_cls.from_args(args)

    print(f"Selected model: {args.model} ({trainer_cls.__name__})")
    print(f"Loading data from {args.csv}...")

    data = load_data(args.csv, normalize=trainer_cls.needs_normalization())
    print(f"Loaded {data.X.shape[0]} samples, {data.X.shape[1]} features"
          f"{' (normalized)' if trainer_cls.needs_normalization() else ''}")

    print("Training model...")
    model = trainer.train(data)

    print("Saving artifacts...")
    ensure_output_dir(args.output)
    trainer.save(model, data, args.output)


if __name__ == "__main__":
    main()
