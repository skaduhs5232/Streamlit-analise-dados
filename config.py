from pathlib import Path

# Configurações do dataset
DATASET_ID = "downshift/city-bike-travels-dataset"
RAW_FILENAME = "city_bike_travels.csv"
OUTPUT_PATH = Path("data/processed_city_bike_trips.parquet")

# Mapeamento de dias da semana
DAY_NAME_MAP = {
    "Monday": "Segunda",
    "Tuesday": "Terça",
    "Wednesday": "Quarta",
    "Thursday": "Quinta",
    "Friday": "Sexta",
    "Saturday": "Sábado",
    "Sunday": "Domingo",
}

# Ordem dos dias para visualizações
DAY_ORDER = [
    "Segunda", "Terça", "Quarta",
    "Quinta", "Sexta", "Sábado", "Domingo"
]

# Configurações de visualização
MAX_ROWS_SCATTER = 5000
MAX_ROWS_HEATMAP = 20000
MAX_ROWS_DEFAULT = 10000
