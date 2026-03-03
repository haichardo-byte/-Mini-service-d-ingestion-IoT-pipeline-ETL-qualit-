# src/etl_pipeline.py
import pandas as pd
import logging
import os
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ETL")


def run_etl(input_file: str, output_dir: str):
    # Création du dossier de sortie si nécessaire
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Dossier de sortie : %s", output_dir)

    # Chargement des données
    df = pd.read_json(input_file)
    logger.info("Chargement terminé (%d lignes)", len(df))

    # Nettoyage
    df["irrigation"] = (
        df["irrigation"]
        .str.upper()
        .replace({"OUI": "ON", "NON": "OFF"})
    )
    df["temperature"] = df["temperature"].clip(-50, 60)
    df["humidity"] = df["humidity"].clip(0, 100)

    # Outliers simples avec z-score
    for col in ["temperature", "humidity"]:
        mean, std = df[col].mean(), df[col].std()
        df = df[(df[col] - mean).abs() / std <= 3]

    # Features dérivées
    df["temp_humidity_index"] = df["temperature"] + 0.1 * df["humidity"]
    df["air_quality_index"] = df[["pm25", "pm10", "ozone", "no2"]].sum(
        axis=1, skipna=True
    )

    # Export des fichiers
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    features_path = os.path.join(output_dir, "cleaned_with_features.csv")

    df.to_csv(cleaned_path, index=False)
    df.to_csv(features_path, index=False)
    logger.info("ETL terminé, fichiers exportés :\n - %s\n - %s", cleaned_path, features_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mini pipeline ETL SmartFarm")
    parser.add_argument("--input", default="data/rawdata.json")
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()

    run_etl(args.input, args.output)