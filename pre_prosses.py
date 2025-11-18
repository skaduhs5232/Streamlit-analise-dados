from __future__ import annotations

from pathlib import Path
from typing import Optional

import kagglehub
import numpy as np
import pandas as pd

DATASET_ID = "downshift/city-bike-travels-dataset"
RAW_FILENAME = "city_bike_travels.csv"
OUTPUT_PATH = Path("data/processed_city_bike_trips.parquet")

DAY_NAME_MAP = {
    "Monday": "Segunda",
    "Tuesday": "Terça",
    "Wednesday": "Quarta",
    "Thursday": "Quinta",
    "Friday": "Sexta",
    "Saturday": "Sábado",
    "Sunday": "Domingo",
}


def categorize_period(hour: int) -> str:
    if 0 <= hour < 6:
        return "Madrugada"
    if 6 <= hour < 12:
        return "Manhã"
    if 12 <= hour < 18:
        return "Tarde"
    return "Noite"


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def download_raw_file() -> Path:
    dataset_dir = Path(kagglehub.dataset_download(DATASET_ID))
    csv_path = dataset_dir / RAW_FILENAME
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Arquivo {RAW_FILENAME} não encontrado em {dataset_dir}."
        )
    return csv_path


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["departure_time"] = pd.to_datetime(df["departure_time"], errors="coerce", utc=True)
    df["return_time"] = pd.to_datetime(df["return_time"], errors="coerce", utc=True)
    df["duration"] = _coerce_numeric(df["duration"])  # segundos
    df["distance"] = _coerce_numeric(df["distance"])  # metros

    df = df.dropna(
        subset=[
            "departure_time",
            "return_time",
            "duration",
            "distance",
            "departure_station_id",
            "return_station_id",
        ]
    )

    df = df[(df["duration"] > 0) & (df["distance"] > 0)]
    df = df[df["return_time"] >= df["departure_time"]]

    df["departure_time"] = df["departure_time"].dt.tz_localize(None)
    df["return_time"] = df["return_time"].dt.tz_localize(None)

    df["trip_minutes"] = df["duration"] / 60
    df["trip_hours"] = df["duration"] / 3600
    df["distance_km"] = df["distance"] / 1000
    df["avg_speed_kmh"] = np.where(
        df["trip_hours"] > 0,
        df["distance_km"] / df["trip_hours"],
        np.nan,
    )

    df["departure_date"] = df["departure_time"].dt.date
    df["hour"] = df["departure_time"].dt.hour
    df["day_of_week"] = (
        df["departure_time"].dt.day_name().map(DAY_NAME_MAP).fillna("-")
    )
    df["month"] = df["departure_time"].dt.month
    df["month_name"] = df["departure_time"].dt.month_name()
    df["time_period"] = df["hour"].apply(categorize_period)

    df = df.drop_duplicates(
        subset=[
            "departure_time",
            "return_time",
            "departure_station_id",
            "return_station_id",
        ]
    )
    return df


def preprocess_city_bike_trips(save_to: Optional[Path] = OUTPUT_PATH) -> pd.DataFrame:
    csv_path = download_raw_file()
    dtype_map = {
        "departure_station_id": "Int64",
        "return_station_id": "Int64",
        "departure_station_name": "string",
        "return_station_name": "string",
    }
    df = pd.read_csv(csv_path, dtype=dtype_map, sep=";")
    df = _enrich(df)

    if save_to:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(save_to, index=False)

    return df


if __name__ == "__main__":
    data = preprocess_city_bike_trips()
    print(
        f"Dataset tratado com {len(data):,} viagens salvo em {OUTPUT_PATH}".replace(",", ".")
    )
