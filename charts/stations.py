"""Gráficos relacionados a estações."""

import altair as alt
import pandas as pd
import plotly.graph_objects as go
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


@st.cache_data(show_spinner=False)
def _get_sankey_data(df_hash: int, dep_stations: tuple, ret_stations: tuple, top_n: int = 20) -> dict:
    """Prepara dados para o diagrama de Sankey com cache."""
    df_temp = pd.DataFrame({
        'departure_station_name': dep_stations,
        'return_station_name': ret_stations
    })
    
    # Agrupa e pega as top N rotas
    routes = (
        df_temp.groupby(["departure_station_name", "return_station_name"])
        .size()
        .reset_index(name="value")
        .nlargest(top_n, "value")
    )
    
    # Cria lista de labels únicos (todas as estações envolvidas)
    all_stations = list(pd.concat([routes["departure_station_name"], routes["return_station_name"]]).unique())
    station_map = {station: i for i, station in enumerate(all_stations)}
    
    return {
        "node_labels": all_stations,
        "source": routes["departure_station_name"].map(station_map).tolist(),
        "target": routes["return_station_name"].map(station_map).tolist(),
        "values": routes["value"].tolist()
    }


def route_sankey(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Diagrama de Sankey das principais rotas."""
    data = _get_sankey_data(
        hash(tuple(df.index)),
        tuple(df["departure_station_name"].values),
        tuple(df["return_station_name"].values),
        top_n
    )
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=data["node_labels"],
            color="rgba(31, 119, 180, 0.8)"
        ),
        link=dict(
            arrowlen=15,
            source=data["source"],
            target=data["target"],
            value=data["values"],
            color="rgba(31, 119, 180, 0.4)"
        )
    )])
    
    fig.update_layout(
        title_text=f"Fluxo das Top {top_n} Rotas",
        font_size=12,
        height=600
    )
    return fig


def combined_station_stats(df: pd.DataFrame) -> alt.Chart:
    """Gráfico combinado de saídas e chegadas para as top estações."""
    # Contagem de saídas
    dep_counts = df["departure_station_name"].value_counts().reset_index()
    dep_counts.columns = ["station", "saidas"]
    
    # Contagem de chegadas
    ret_counts = df["return_station_name"].value_counts().reset_index()
    ret_counts.columns = ["station", "chegadas"]
    
    # Merge e cálculo do total
    stats = pd.merge(dep_counts, ret_counts, on="station", how="outer").fillna(0)
    stats["total"] = stats["saidas"] + stats["chegadas"]
    
    # Top 10 pelo total
    top_stats = stats.nlargest(10, "total")
    
    # Melt para formato longo (necessário para Altair grouped bar)
    melted = top_stats.melt(
        id_vars=["station", "total"], 
        value_vars=["saidas", "chegadas"],
        var_name="tipo", 
        value_name="viagens"
    )
    
    # Gráfico
    return (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            y=alt.Y("station:N", sort=alt.EncodingSortField(field="total", order="descending"), title="Estação"),
            x=alt.X("viagens:Q", title="Número de Viagens"),
            color=alt.Color("tipo:N", title="Tipo de Movimento", scale=alt.Scale(scheme="category10")),
            tooltip=[
                alt.Tooltip("station:N", title="Estação"),
                alt.Tooltip("tipo:N", title="Tipo"),
                alt.Tooltip("viagens:Q", title="Viagens"),
                alt.Tooltip("total:Q", title="Total (Saídas + Chegadas)")
            ]
        )
        .properties(
            title="Top 10 Estações: Saídas vs Chegadas (Combined Stats)",
            height=400
        )
    )
