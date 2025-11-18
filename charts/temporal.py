"""Gráficos relacionados a análises temporais."""

import altair as alt
import pandas as pd
import streamlit as st

from config import MAX_ROWS_SCATTER
from utils.helpers import limit_rows, safe_max


@st.cache_data(show_spinner=False)
def _aggregate_daily_trips(df_hash: int, departure_dates: tuple, distances: tuple) -> pd.DataFrame:
    """Agrega dados diários com cache."""
    df_temp = pd.DataFrame({
        'departure_date': departure_dates,
        'distance_km': distances
    })
    return (
        df_temp.groupby("departure_date")
        .agg(viagens=("departure_date", "count"),
             distancia=("distance_km", "sum"))
        .reset_index()
    )


def trips_over_time(df: pd.DataFrame) -> alt.Chart:
    """Gráfico de evolução diária de viagens."""
    daily = _aggregate_daily_trips(
        hash(tuple(df.index)),
        tuple(df["departure_date"].values),
        tuple(df["distance_km"].values)
    )
    return (
        alt.Chart(daily)
        .mark_line(point=True)
        .encode(
            x=alt.X("departure_date:T", title="Data de partida"),
            y=alt.Y("viagens:Q", title="Viagens realizadas"),
            tooltip=[
                alt.Tooltip("departure_date:T", title="Data"),
                alt.Tooltip("viagens:Q", title="Quantidade de viagens"),
                alt.Tooltip("distancia:Q", title="Distância total (km)", format=".1f"),
            ],
        )
        .properties(height=320, title="Evolução diária de viagens")
    )


def distance_vs_duration(df: pd.DataFrame) -> alt.Chart:
    """Gráfico de dispersão: distância versus duração."""
    sample = limit_rows(df, max_rows=MAX_ROWS_SCATTER)

    scatter = (
        alt.Chart(sample)
        .mark_circle(opacity=0.35, size=35, stroke="white", strokeWidth=0.3)
        .encode(
            x=alt.X(
                "trip_minutes:Q",
                title="Duração da viagem (min)",
                scale=alt.Scale(domain=[0, 2000])
            ),
            y=alt.Y(
                "distance_km:Q",
                title="Distância percorrida (km)",
            ),
            color=alt.Color("time_period:N", title="Período do dia"),
            size=alt.Size("avg_speed_kmh:Q", title="Velocidade média (km/h)", legend=alt.Legend(orient="bottom")),
            tooltip=[
                alt.Tooltip("departure_station_name:N", title="Estação de saída"),
                alt.Tooltip("return_station_name:N", title="Estação de chegada"),
                alt.Tooltip("distance_km:Q", title="Distância (km)", format=".2f"),
                alt.Tooltip("trip_minutes:Q", title="Duração (min)", format=".1f"),
                alt.Tooltip("avg_speed_kmh:Q", title="Velocidade média (km/h)", format=".1f"),
            ],
        )
    )

    tendencia = (
        alt.Chart(sample)
        .transform_loess("trip_minutes", "distance_km", bandwidth=0.3)
        .mark_line(color="#f4a261", strokeDash=[6, 3], strokeWidth=2)
        .encode(
            x="trip_minutes:Q",
            y="distance_km:Q",
        )
    )

    return (scatter + tendencia).properties(height=360, title="Distância versus duração")


def trips_vs_duration(df: pd.DataFrame) -> alt.Chart:
    """Gráfico de volume de viagens por faixa de duração."""
    bins = list(range(0, 181, 5))
    binned = (
        df.assign(duration_bin=pd.cut(df["trip_minutes"], bins=bins))
        .groupby("duration_bin")
        .agg(viagens=("trip_minutes", "count"), distancia_med=("distance_km", "mean"))
        .reset_index()
    )
    binned["duration_mid"] = binned["duration_bin"].apply(lambda x: x.mid)

    bars = (
        alt.Chart(binned)
        .mark_bar(opacity=0.85)
        .encode(
            x=alt.X("duration_mid:Q", title="Duração das viagens (min)"),
            y=alt.Y("viagens:Q", title="Viagens registradas"),
            tooltip=[
                alt.Tooltip("duration_mid:Q", title="Duração (min)", format=".0f"),
                alt.Tooltip("viagens:Q", title="Viagens"),
                alt.Tooltip("distancia_med:Q", title="Distância média (km)", format=".1f"),
            ],
        )
    )

    line = (
        alt.Chart(binned)
        .mark_line(strokeWidth=2)
        .encode(
            x="duration_mid:Q",
            y=alt.Y("distancia_med:Q", title="Distância média (km)"),
            tooltip=[
                alt.Tooltip("duration_mid:Q", title="Duração (min)", format=".0f"),
                alt.Tooltip("distancia_med:Q", title="Distância média (km)", format=".1f"),
            ],
        )
    )

    return (
        (bars + line)
        .resolve_scale(y="independent")
        .properties(height=260, title="Volume de viagens por duração")
    )
