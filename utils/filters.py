"""Lógica de filtros para o dashboard."""

import pandas as pd
import streamlit as st

from utils.helpers import sidebar_multiselect, slider_float


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todos os filtros configurados na sidebar ao DataFrame."""
    min_date, max_date = df["departure_time"].min().date(), df["departure_time"].max().date()

    # Período
    date_range = st.sidebar.date_input(
        "Período de partida",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    # Filtros categóricos
    selected_departure = st.sidebar.multiselect(
        "Estações de saída",
        sorted(df["departure_station_name"].dropna().unique().tolist()),
        default=[]
    )

    selected_return = st.sidebar.multiselect(
        "Estações de chegada",
        sorted(df["return_station_name"].dropna().unique().tolist()),
        default=[]
    )

    period_options = sidebar_multiselect(
        "Período do dia",
        sorted(df["time_period"].unique().tolist())
    )

    # Filtros numéricos
    distance_filter = slider_float("Faixa de distância (km)", df["distance_km"])
    duration_filter = slider_float("Faixa de duração (min)", df["trip_minutes"])

    # Máscara final
    mask = (
        (df["departure_time"].dt.date.between(start_date, end_date))
        & (df["time_period"].isin(period_options))
        & (df["distance_km"].between(*distance_filter))
        & (df["trip_minutes"].between(*duration_filter))
    )

    if selected_departure:
        mask &= df["departure_station_name"].isin(selected_departure)

    if selected_return:
        mask &= df["return_station_name"].isin(selected_return)

    return df.loc[mask].copy()
