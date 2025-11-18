
import pandas as pd
import streamlit as st

from config import OUTPUT_PATH
from data.preprocessing import preprocess_city_bike_trips


@st.cache_data(show_spinner="Preparando viagens...")
def load_data() -> pd.DataFrame:
    if OUTPUT_PATH.exists():
        return pd.read_parquet(OUTPUT_PATH)
    return preprocess_city_bike_trips(save_to=OUTPUT_PATH)
