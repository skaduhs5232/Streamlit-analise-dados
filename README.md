# City Bike Trips Explorer

Análise interativa de viagens de bicicleta usando Streamlit.

## Estrutura do Projeto

```
BI-Dados/
├── app.py                      # Aplicação principal Streamlit
├── config.py                   # Configurações e constantes globais
├── requirements.txt            # Dependências do projeto
│
├── data/                       # Módulo de dados
│   ├── __init__.py
│   ├── data_loader.py         # Carregamento e cache de dados
│   └── preprocessing.py        # Funções de pré-processamento
│
├── utils/                      # Utilitários
│   ├── __init__.py
│   ├── filters.py             # Lógica de filtros do dashboard
│   └── helpers.py             # Funções auxiliares
│
└── charts/                     # Módulos de visualização
    ├── __init__.py
    ├── temporal.py            # Gráficos temporais
    ├── patterns.py            # Gráficos de padrões de uso
    └── stations.py            # Gráficos de estações
```

## Organização por Responsabilidade

### `config.py`
Centralize todas as configurações e constantes:
- IDs de datasets
- Mapeamentos (dias da semana)
- Limites de visualização

### `data/`
Gerenciamento de dados:
- **data_loader.py**: Cache e carregamento otimizado
- **preprocessing.py**: Transformações e enriquecimento de dados

### `utils/`
Funções utilitárias reutilizáveis:
- **filters.py**: Filtros da sidebar
- **helpers.py**: Funções auxiliares (sliders, limitadores, etc)

### `charts/`
Visualizações organizadas por categoria:
- **temporal.py**: Análises ao longo do tempo
- **patterns.py**: Padrões de uso (heatmaps, distribuições)
- **stations.py**: Análises de estações e rotas

### `app.py`
Apenas orquestração da UI - limpo e focado

## Como Executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Autores

Thiago de Oliveira, Alexandre Pinto, Hélio, Natan
