from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from pre_prosses import OUTPUT_PATH, preprocess_city_bike_trips

# --------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# --------------------------------------------------------------

st.set_page_config(page_title="City Bike Trips Explorer", page_icon="🚲", layout="wide")
alt.data_transformers.disable_max_rows()

DAY_ORDER = [
    "Segunda", "Terça", "Quarta",
    "Quinta", "Sexta", "Sábado", "Domingo"
]


# --------------------------------------------------------------
# CARREGAMENTO DE DADOS
# --------------------------------------------------------------

@st.cache_data(show_spinner="Preparando viagens...")
def load_data() -> pd.DataFrame:
    if OUTPUT_PATH.exists():
        return pd.read_parquet(OUTPUT_PATH)
    return preprocess_city_bike_trips(save_to=OUTPUT_PATH)


# --------------------------------------------------------------
# UTILITÁRIOS
# --------------------------------------------------------------

def sidebar_multiselect(label: str, values: list[str]):
    """Multiselect com ordenação e fallback de vazio."""
    return st.sidebar.multiselect(label, options=values, default=values)


def slider_float(label: str, data: pd.Series):
    """Cria slider com valores mínimo e máximo deduzidos automaticamente."""
    return st.sidebar.slider(
        label,
        min_value=float(data.min()),
        max_value=float(max(data.max(), 0.1)),
        value=(float(data.min()), float(data.max()))
    )


def limit_rows(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
    """Mantém os gráficos responsivos limitando o volume de linhas usadas."""
    if len(df) <= max_rows:
        return df
    return df.sample(max_rows, random_state=42)


def safe_max(series: pd.Series, default: float = 1.0) -> float:
    """Retorna o máximo da série ou um valor padrão quando não houver dados."""
    value = series.max()
    if pd.isna(value):
        return default
    return float(value)


# --------------------------------------------------------------
# FILTROS
# --------------------------------------------------------------

def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
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


# --------------------------------------------------------------
# GRÁFICOS
# --------------------------------------------------------------

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


@st.cache_data(show_spinner=False)
def _aggregate_hourly(df_hash: int, days: tuple, hours: tuple) -> pd.DataFrame:
    """Agrega dados por hora com cache."""
    df_temp = pd.DataFrame({
        'day_of_week': days,
        'hour': hours
    })
    return df_temp.groupby(["day_of_week", "hour"]).size().reset_index(name="viagens")

def hourly_heatmap(df: pd.DataFrame) -> alt.Chart:
    sample = limit_rows(df, max_rows=20000)
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


def top_stations(df: pd.DataFrame, column: str, title: str) -> alt.Chart:
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


def distance_vs_duration(df: pd.DataFrame) -> alt.Chart:
    sample = limit_rows(df, max_rows=5000)

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


# --------------------------------------------------------------
# APP PRINCIPAL
# --------------------------------------------------------------

def main() -> None:
    st.title("City Bike Trips Explorer")
    st.caption("Análise interativa do dataset City Bike Trips (Kaggle)")
    st.caption("Por: Thiago de Oliveira, Alexandre Pinto, Hélio, Natan")

    with st.spinner("Carregando dados..."):
        df = load_data()

    if df.empty:
        st.warning("Nenhum dado disponível após o tratamento.")
        return

    st.sidebar.header("Filtros")
    filtered = apply_filters(df)

    # Exibe métricas
    st.sidebar.markdown(f"**Viagens ativas:** {len(filtered):,}".replace(",", "."))

    st.sidebar.download_button(
        label="Baixar dados filtrados (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="city_bike_trips_filtrado.csv",
        mime="text/csv",
    )

    # Cálculos otimizados em uma única passagem
    num_trips = len(filtered)
    
    if num_trips > 0:
        total_distance = filtered["distance_km"].sum()
        mean_duration = filtered["trip_minutes"].mean()
        mean_speed = filtered["avg_speed_kmh"].mean()
        unique_stations = len(set(filtered["departure_station_name"]) | set(filtered["return_station_name"]))
    else:
        total_distance = mean_duration = mean_speed = 0
        unique_stations = 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Viagens", f"{num_trips:,}".replace(",", "."))
    c2.metric("Distância total (km)", f"{total_distance:,.1f}".replace(",", "."))
    c3.metric("Duração média (min)", f"{mean_duration:,.1f}".replace(",", "."))
    c4.metric("Velocidade média (km/h)", f"{mean_speed:,.1f}".replace(",", "."))

    st.caption(f"Estações distintas na seleção: {unique_stations}")

    # Abas
    tab1, tab2, tab3 = st.tabs([
        "Panorama temporal",
        "Padrões de uso",
        "Estações",
    ])

    with tab1:
        st.altair_chart(trips_over_time(filtered), use_container_width=True)
        st.altair_chart(distance_vs_duration(filtered), use_container_width=True)
        st.altair_chart(trips_vs_duration(filtered), use_container_width=True)

    with tab2:
        st.altair_chart(hourly_heatmap(filtered), use_container_width=True)
        cols = st.columns(2)
        cols[0].altair_chart(distance_distribution(filtered), use_container_width=True)
        cols[1].altair_chart(duration_histogram(filtered), use_container_width=True)

    with tab3:
        cols = st.columns(2)
        cols[0].altair_chart(top_stations(filtered, "departure_station_name", "Saída"), use_container_width=True)
        cols[1].altair_chart(top_stations(filtered, "return_station_name", "Chegada"), use_container_width=True)

        st.markdown("---")

        c1, c2 = st.columns(2)
        c1.altair_chart(top_routes(filtered), use_container_width=True)
        c2.altair_chart(station_flow(filtered), use_container_width=True)

        st.markdown("---")
        st.altair_chart(avg_duration_by_station(filtered), use_container_width=True)

    with st.expander("Prévia dos dados filtrados"):
        st.dataframe(
            filtered[
                [
                    "departure_time", "return_time",
                    "departure_station_name", "return_station_name",
                    "distance_km", "trip_minutes", "avg_speed_kmh", "time_period",
                ]
            ],
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
