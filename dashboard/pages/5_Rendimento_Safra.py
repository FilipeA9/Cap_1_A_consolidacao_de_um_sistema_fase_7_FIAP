"""Pagina do servico da Fase 5: analise de rendimento de safra (crop_yield)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import plotly.express as px
import streamlit as st

from services.fase5_rendimento import pipeline

st.set_page_config(page_title="Rendimento de Safra (Fase 5)", page_icon="📈",
                   layout="wide")
st.title("📈 Análise de Rendimento de Safra — Fase 5")
st.caption("Base histórica crop_yield.csv: EDA, clusterização (K-Means), "
           "outliers (Isolation Forest) e 5 modelos de regressão. "
           "Notebook original em notebooks/.")


@st.cache_resource(show_spinner="Executando pipeline da Fase 5...")
def rodar_pipeline():
    return pipeline.executar_pipeline()


r = rodar_pipeline()
df, eda, treino = r['df'], r['eda'], r['treino']

c1, c2, c3 = st.columns(3)
c1.metric("Registros", eda['n_registros'])
c2.metric("Culturas", len(eda['culturas']))
c3.metric("Outliers detectados", int(df['outlier'].sum()))

tab1, tab2, tab3, tab4 = st.tabs(
    ["🔍 Exploração", "🧩 Clusters e outliers", "🏆 5 modelos", "🔮 Previsão"])

with tab1:
    st.subheader("Rendimento por cultura (ton/ha)")
    st.dataframe(eda['rendimento_por_cultura'], use_container_width=True,
                 hide_index=True)
    st.subheader("Correlação entre variáveis")
    st.plotly_chart(px.imshow(eda['correlacao'], text_auto=".2f",
                              color_continuous_scale="RdBu_r"),
                    use_container_width=True)

with tab2:
    fig = px.scatter(
        df, x="Temperature at 2 Meters (C)", y="Yield",
        color=df['cluster'].astype(str), symbol="outlier",
        hover_data=["Crop"],
        labels={"color": "cluster"},
        title="Clusters K-Means e outliers (Isolation Forest)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Outliers aparecem com símbolo diferente — cenários discrepantes "
               "que merecem investigação (mesma análise do notebook da Fase 5).")

with tab3:
    st.subheader("Comparativo dos 5 algoritmos de regressão")
    st.dataframe(treino['tabela_metricas'], use_container_width=True,
                 hide_index=True)
    st.success(f"🏆 Melhor modelo: **{treino['melhor_modelo']}** "
               f"(maior R² no conjunto de teste)")

with tab4:
    st.subheader("Previsão interativa de rendimento")
    col1, col2 = st.columns(2)
    with col1:
        cultura = st.selectbox("Cultura", eda['culturas'])
        precipitacao = st.number_input("Precipitação (mm/dia)", 0.0, 5000.0, 2000.0)
        umid_esp = st.number_input("Umidade específica 2m (g/kg)", 0.0, 30.0, 15.0)
    with col2:
        umid_rel = st.number_input("Umidade relativa 2m (%)", 0.0, 100.0, 75.0)
        temperatura = st.number_input("Temperatura 2m (°C)", -10.0, 50.0, 26.0)

    if st.button("🔮 Prever rendimento", type="primary"):
        rendimento = pipeline.prever_rendimento(
            treino, cultura, precipitacao, umid_esp, umid_rel, temperatura)
        st.metric(f"Rendimento previsto — {cultura}",
                  f"{rendimento:,.0f} (unidade da base)")
        st.caption(f"Modelo utilizado: {treino['melhor_modelo']}")
