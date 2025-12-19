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


def load_data(csv_path: str) -> DataSet:
    """
    Laadt data uit CSV, dropt 'id' kolom, cast naar float32.
    Optioneel normaliseren met (x - mean) / std.
    """
    df = pd.read_csv(csv_path)

    # Ensure all remaining columns are numeric
    df = df.astype("float32")
    feature_names = list(df.columns)
    X = df.values.astype("float32")

    return DataSet(X=X, feature_names=feature_names)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train een reconstructiemodel (autoencoder of random forest) op CSV-data."
    )

    parser.add_argument(
        "--csv",
        default="data.csv",
        help="Pad naar CSV bestand met sensor/valve data.",
    )
    parser.add_argument(
        "--force",
        default=False,
        help="Train models also if they exist.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output-prefix",
    )

    # Laat elke trainer zijn eigen opties toevoegen
    for trainer_cls in TRAINERS:
        trainer_cls.add_cli_args(parser)

    args = parser.parse_args()

    if not args.force and all(trainer.exist(os.path.join(args.output, trainer_cls.MODEL_NAME)) for trainer in TRAINERS):
        print(f"Everything up to date.")
        return

    data = load_data(args.csv)
    print(f"Loaded {data.X.shape[0]} samples, {data.X.shape[1]} features")

    for trainer_cls in TRAINERS:
        output = os.path.join(args.output, trainer_cls.MODEL_NAME)
        if not args.force and trainer_cls.exist(output):
            continue

        trainer = trainer_cls.from_args(args)

        print(f"Selected model: {trainer_cls.__name__}")
        print(f"Loading data from {args.csv}...")

        traindata = data.normalize() if trainer_cls.needs_normalization() else data

        print("Training model...")
        model = trainer.train(traindata)

        print("Saving artifacts...")
        ensure_output_dir(output)
        trainer.save(model, traindata, output)


if __name__ == "__main__":
    main()
