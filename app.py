from __future__ import annotations

import altair as alt
import streamlit as st

from charts.patterns import distance_distribution, duration_histogram, hourly_heatmap
from charts.stations import avg_duration_by_station, station_flow, top_routes, top_stations
from charts.temporal import distance_vs_duration, trips_over_time, trips_vs_duration
from data.data_loader import load_data
from utils.filters import apply_filters

# --------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# --------------------------------------------------------------

st.set_page_config(page_title="City Bike Trips Explorer", page_icon="🚲", layout="wide")
alt.data_transformers.disable_max_rows()


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

