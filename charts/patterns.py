"""Gráficos de padrões de uso das bicicletas."""

import altair as alt
import pandas as pd
import streamlit as st

from config import DAY_ORDER, MAX_ROWS_HEATMAP
from utils.helpers import limit_rows, safe_max


@st.cache_data(show_spinner=False)
def _aggregate_hourly(df_hash: int, days: tuple, hours: tuple) -> pd.DataFrame:
    """Agrega dados por hora com cache."""
    df_temp = pd.DataFrame({
        'day_of_week': days,
        'hour': hours
    })
    return df_temp.groupby(["day_of_week", "hour"]).size().reset_index(name="viagens")


def hourly_heatmap(df: pd.DataFrame) -> alt.Chart:
    """Mapa de calor: intensidade de uso por dia e hora."""
    sample = limit_rows(df, max_rows=MAX_ROWS_HEATMAP)
    hourly = _aggregate_hourly(
        hash(tuple(sample.index)),
        tuple(sample["day_of_week"].values),
        tuple(sample["hour"].values)
    )
    return (
        alt.Chart(hourly)
        .mark_rect()
        .encode(
            x=alt.X("hour:O", title="Hora do dia"),
            y=alt.Y("day_of_week:O", sort=DAY_ORDER, title="Dia da semana"),
            color=alt.Color("viagens:Q", title="Viagens", scale=alt.Scale(scheme="magma")),
            tooltip=[
                alt.Tooltip("day_of_week:N", title="Dia"),
                alt.Tooltip("hour:O", title="Hora"),
                alt.Tooltip("viagens:Q", title="Quantidade de viagens"),
            ],
        )
        .properties(height=300, title="Intensidade por dia e hora")
    )


def duration_histogram(df: pd.DataFrame) -> alt.Chart:
    """Distribuição de densidade das durações de viagem."""
    sampled = limit_rows(df)
    return (
        alt.Chart(sampled)
        .transform_density("trip_minutes", as_=["trip_minutes", "densidade"], extent=[0, safe_max(sampled["trip_minutes"], default=1.0)])
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("trip_minutes:Q", title="Duração da viagem (min)"),
            y=alt.Y("densidade:Q", title="Densidade relativa"),
            tooltip=[
                alt.Tooltip("trip_minutes:Q", title="Duração (min)", format=".1f"),
                alt.Tooltip("densidade:Q", title="Densidade", format=".3f"),
            ],
        )
        .properties(height=260, title="Distribuição das durações")
    )


def distance_distribution(df: pd.DataFrame) -> alt.Chart:
    """Distribuição de densidade das distâncias percorridas."""
    sampled = limit_rows(df)
    return (
        alt.Chart(sampled)
        .transform_density("distance_km", as_=["distance_km", "densidade"], extent=[0, safe_max(sampled["distance_km"], default=1.0)])
        .mark_area(opacity=0.6, color="#3a86ff")
        .encode(
            x=alt.X("distance_km:Q", title="Distância percorrida (km)"),
            y=alt.Y("densidade:Q", title="Densidade relativa"),
            tooltip=[
                alt.Tooltip("distance_km:Q", title="Distância (km)", format=".2f"),
                alt.Tooltip("densidade:Q", title="Densidade", format=".3f"),
            ],
        )
        .properties(height=260, title="Distribuição das distâncias")
    )
