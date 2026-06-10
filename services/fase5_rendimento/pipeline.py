"""
FarmTech Solutions - Fase 5 - Pipeline de analise de rendimento de safra.

Porta para modulo Python o que o notebook da Fase 5 fazia sobre o
crop_yield.csv: analise exploratoria, clusterizacao (K-Means), deteccao
de outliers (Isolation Forest) e cinco modelos de regressao (Linear,
Arvore de Decisao, Random Forest, Gradient Boosting e SVR) avaliados com
MAE, RMSE e R2. O notebook original permanece em notebooks/ para consulta.

Execucao: python main.py rendimento
"""

import sys
import os
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import (GradientBoostingRegressor, IsolationForest,
                              RandomForestRegressor)
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import CROP_YIELD_CSV

FEATURES = [
    'Precipitation (mm day-1)',
    'Specific Humidity at 2 Meters (g/kg)',
    'Relative Humidity at 2 Meters (%)',
    'Temperature at 2 Meters (C)',
]
TARGET = 'Yield'


def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(CROP_YIELD_CSV)
    df = df.dropna()
    return df


def analise_exploratoria(df: pd.DataFrame) -> Dict:
    return {
        'n_registros': len(df),
        'culturas': sorted(df['Crop'].unique().tolist()),
        'descritivas': df[FEATURES + [TARGET]].describe(),
        'correlacao': df[FEATURES + [TARGET]].corr(),
        'rendimento_por_cultura': (
            df.groupby('Crop')[TARGET].agg(['mean', 'std', 'min', 'max'])
            .round(1).reset_index()
        ),
    }


def clusterizar(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """K-Means sobre as variaveis climaticas + rendimento (como na Fase 5)."""
    X = StandardScaler().fit_transform(df[FEATURES + [TARGET]])
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df = df.copy()
    df['cluster'] = km.fit_predict(X)
    return df


def detectar_outliers(df: pd.DataFrame, contaminacao: float = 0.05) -> pd.DataFrame:
    iso = IsolationForest(contamination=contaminacao, random_state=42)
    df = df.copy()
    df['outlier'] = iso.fit_predict(df[FEATURES + [TARGET]]) == -1
    return df


def treinar_modelos(df: pd.DataFrame) -> Dict:
    """Treina os 5 modelos preditivos e devolve metricas + modelos."""
    # One-hot da cultura, como boas praticas do notebook original
    X = pd.get_dummies(df[['Crop'] + FEATURES], columns=['Crop'])
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    modelos = {
        'Regressao Linear': LinearRegression(),
        'Arvore de Decisao': DecisionTreeRegressor(random_state=42),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingRegressor(random_state=42),
        'SVR': SVR(kernel='rbf', C=100),
    }

    metricas = []
    treinados = {}
    for nome, modelo in modelos.items():
        modelo.fit(X_train_s, y_train)
        pred = modelo.predict(X_test_s)
        metricas.append({
            'Modelo': nome,
            'MAE': mean_absolute_error(y_test, pred),
            'RMSE': float(np.sqrt(mean_squared_error(y_test, pred))),
            'R2': r2_score(y_test, pred),
        })
        treinados[nome] = modelo

    tabela = (pd.DataFrame(metricas)
              .sort_values('R2', ascending=False)
              .reset_index(drop=True).round(3))
    melhor = tabela.iloc[0]['Modelo']
    return {
        'tabela_metricas': tabela,
        'melhor_modelo': melhor,
        'modelos': treinados,
        'scaler': scaler,
        'colunas_X': list(X.columns),
    }


def prever_rendimento(resultado_treino: Dict, cultura: str,
                      precipitacao: float, umid_especifica: float,
                      umid_relativa: float, temperatura: float) -> float:
    """Previsao interativa usada pela dashboard."""
    entrada = {c: 0.0 for c in resultado_treino['colunas_X']}
    entrada[FEATURES[0]] = precipitacao
    entrada[FEATURES[1]] = umid_especifica
    entrada[FEATURES[2]] = umid_relativa
    entrada[FEATURES[3]] = temperatura
    col_cultura = f"Crop_{cultura}"
    if col_cultura in entrada:
        entrada[col_cultura] = 1.0
    X = pd.DataFrame([entrada])[resultado_treino['colunas_X']]
    X_s = resultado_treino['scaler'].transform(X)
    modelo = resultado_treino['modelos'][resultado_treino['melhor_modelo']]
    return float(modelo.predict(X_s)[0])


def executar_pipeline() -> Dict:
    """Pipeline completo - usado pela CLI e pela dashboard."""
    df = carregar_dados()
    eda = analise_exploratoria(df)
    df_cluster = detectar_outliers(clusterizar(df))
    treino = treinar_modelos(df)
    return {'df': df_cluster, 'eda': eda, 'treino': treino}


def executar_cli():
    print("=" * 60)
    print("ANALISE DE RENDIMENTO DE SAFRA (Fase 5)")
    print("=" * 60)
    r = executar_pipeline()
    print(f"Registros: {r['eda']['n_registros']} | "
          f"Culturas: {', '.join(r['eda']['culturas'])}")
    print(f"Outliers detectados: {int(r['df']['outlier'].sum())}")
    print("\nComparativo dos 5 modelos (conjunto de teste):")
    print(r['treino']['tabela_metricas'].to_string(index=False))
    print(f"\nMelhor modelo: {r['treino']['melhor_modelo']}")


if __name__ == "__main__":
    executar_cli()
