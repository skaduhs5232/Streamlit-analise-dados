"""Funções auxiliares para manipulação de dados e interface."""

import pandas as pd
import streamlit as st


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
