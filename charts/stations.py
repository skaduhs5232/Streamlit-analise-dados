"""Gráficos relacionados a estações."""

import altair as alt
import pandas as pd
import streamlit as st


def top_stations(df: pd.DataFrame, column: str, title: str) -> alt.Chart:
    """Top 10 estações com maior volume de viagens."""
    top = (
        df.groupby(column)
        .size()
        .reset_index(name="viagens")
        .nlargest(10, "viagens")
    )
    return (
        alt.Chart(top)
        .mark_bar()
        .encode(
            x=alt.X("viagens:Q", title="Viagens registradas"),
            y=alt.Y(f"{column}:N", sort="-x", title=title),
            tooltip=[
                alt.Tooltip(f"{column}:N", title=f"Estação de {title.lower()}"),
                alt.Tooltip("viagens:Q", title="Viagens"),
            ],
        )
        .properties(height=300, title=f"Top 10 estações de {title.lower()}")
    )


@st.cache_data(show_spinner=False)
def _get_top_routes(df_hash: int, dep_stations: tuple, ret_stations: tuple) -> pd.DataFrame:
    """Calcula top rotas com cache."""
    df_temp = pd.DataFrame({
        'departure_station_name': dep_stations,
        'return_station_name': ret_stations
    })
    routes = (
        df_temp.groupby(["departure_station_name", "return_station_name"])
        .size()
        .reset_index(name="viagens")
        .nlargest(10, "viagens")
    )
    routes["rota"] = routes["departure_station_name"] + " → " + routes["return_station_name"]
    return routes


def top_routes(df: pd.DataFrame) -> alt.Chart:
    """Top 10 rotas mais utilizadas entre estações."""
    routes = _get_top_routes(
        hash(tuple(df.index)),
        tuple(df["departure_station_name"].values),
        tuple(df["return_station_name"].values)
    )

    return (
        alt.Chart(routes)
        .mark_bar()
        .encode(
            x=alt.X("viagens:Q", title="Viagens registradas"),
            y=alt.Y("rota:N", sort="-x", title="Rota"),
            tooltip=[
                alt.Tooltip("rota:N", title="Rota"),
                alt.Tooltip("viagens:Q", title="Viagens"),
            ],
        )
        .properties(height=320, title="Principais rotas entre estações")
    )


@st.cache_data(show_spinner=False)
def _calculate_station_flow(df_hash: int, dep_stations: tuple, ret_stations: tuple) -> pd.DataFrame:
    """Calcula fluxo de estações com cache."""
    df_dep = pd.Series(dep_stations).value_counts().rename("saidas")
    df_ret = pd.Series(ret_stations).value_counts().rename("chegadas")
    
    flows = pd.concat([df_dep, df_ret], axis=1).fillna(0)
    flows["net_flow"] = flows["chegadas"] - flows["saidas"]
    flows = flows.sort_values("net_flow", ascending=False).head(15).reset_index()
    flows.rename(columns={"index": "station"}, inplace=True)
    return flows


def station_flow(df: pd.DataFrame) -> alt.Chart:
    """Gráfico de saldo de fluxo por estação (chegadas - saídas)."""
    flows = _calculate_station_flow(
        hash(tuple(df.index)),
        tuple(df["departure_station_name"].values),
        tuple(df["return_station_name"].values)
    )

    return (
        alt.Chart(flows)
        .mark_bar()
        .encode(
            x=alt.X("net_flow:Q", title="Saldo (chegadas - saídas)"),
            y=alt.Y("station:N", sort="-x", title="Estação"),
            color=alt.Color("net_flow:Q", title="Saldo", scale=alt.Scale(scheme="magma")),
            tooltip=[
                alt.Tooltip("station:N", title="Estação"),
                alt.Tooltip("net_flow:Q", title="Saldo de viagens"),
                alt.Tooltip("chegadas:Q", title="Chegadas"),
                alt.Tooltip("saidas:Q", title="Saídas"),
            ],
        )
        .properties(height=360, title="Saldo de fluxo por estação")
    )


def avg_duration_by_station(df: pd.DataFrame, column="departure_station_name") -> alt.Chart:
    """Duração média de viagens por estação."""
    station_label = {
        "departure_station_name": "estação de saída",
        "return_station_name": "estação de chegada",
    }.get(column, "estação")

    avg = (
        df.groupby(column)["trip_minutes"]
        .mean()
        .rename("dur_med")
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    return (
        alt.Chart(avg)
        .mark_bar()
        .encode(
            x=alt.X("dur_med:Q", title="Duração média (min)"),
            y=alt.Y(f"{column}:N", sort="-x", title=station_label.capitalize()),
            tooltip=[
                alt.Tooltip(f"{column}:N", title=station_label.capitalize()),
                alt.Tooltip("dur_med:Q", title="Duração média (min)", format=".1f"),
            ],
        )
        .properties(height=300, title=f"Duração média por {station_label}")
    )
