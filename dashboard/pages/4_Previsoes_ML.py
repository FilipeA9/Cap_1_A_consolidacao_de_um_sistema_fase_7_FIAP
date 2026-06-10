"""Pagina do servico da Fase 4: previsoes de ML + recomendacoes de manejo."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.fase3_banco.db_manager import DatabaseManager
from services.fase4_ml.ml_models import GerenciadorModelos
from services.fase4_ml.recommendation_system import SistemaRecomendacao

st.set_page_config(page_title="Previsões ML (Fase 4)", page_icon="🤖",
                   layout="wide")
st.title("🤖 Previsões e Recomendações — Fase 4")
st.caption("Modelos Random Forest / Gradient Boosting para umidade, pH e "
           "rendimento + sistema especialista de manejo.")

db = DatabaseManager()


@st.cache_resource
def carregar_gerenciador():
    g = GerenciadorModelos(db)
    if not g.carregar_todos_modelos():
        return None
    return g


gerenciador = carregar_gerenciador()

if gerenciador is None:
    st.warning("Modelos não encontrados. Treine-os agora ou rode "
               "`python main.py treinar-ml`.")
    if st.button("🏋️ Treinar modelos agora", type="primary"):
        with st.spinner("Treinando modelos (Random Forest / Gradient Boosting)..."):
            g = GerenciadorModelos(db)
            g.treinar_todos_modelos()
            g.salvar_todos_modelos()
        st.cache_resource.clear()
        st.rerun()
    st.stop()

# ----- Metricas dos modelos -----
st.subheader("📈 Desempenho dos modelos (conjunto de teste)")
cols = st.columns(3)
modelos = [("Umidade do solo", gerenciador.modelo_umidade),
           ("pH do solo", gerenciador.modelo_ph),
           ("Rendimento", gerenciador.modelo_rendimento)]
for col, (nome, modelo) in zip(cols, modelos):
    with col:
        st.metric(f"{nome} — R²", f"{modelo.metricas.get('r2_test', 0):.3f}")
        st.caption(f"RMSE: {modelo.metricas.get('rmse_test', 0):.3f} | "
                   f"MAE: {modelo.metricas.get('mae_test', 0):.3f}")

# ----- Previsao interativa -----
st.subheader("🔮 Previsão a partir das condições atuais")
leituras = db.obter_leituras_recentes(limite=1)
padrao = leituras.iloc[0] if not leituras.empty else None

col1, col2, col3 = st.columns(3)
with col1:
    umidade_solo = st.number_input("Umidade do solo (%)", 0.0, 100.0,
                                   float(padrao['umidade_solo']) if padrao is not None else 35.0)
    temperatura_solo = st.number_input("Temperatura do solo (°C)", 0.0, 50.0,
                                       float(padrao['temperatura_solo']) if padrao is not None else 25.0)
with col2:
    ph_solo = st.number_input("pH do solo", 0.0, 14.0,
                              float(padrao['ph_solo']) if padrao is not None else 6.5)
    temperatura_ar = st.number_input("Temperatura do ar (°C)", 0.0, 50.0,
                                     float(padrao['temperatura_ar']) if padrao is not None else 28.0)
with col3:
    umidade_ar = st.number_input("Umidade do ar (%)", 0.0, 100.0,
                                 float(padrao['umidade_ar']) if padrao is not None else 65.0)
    luminosidade = st.number_input("Luminosidade (lux)", 0.0, 1000.0,
                                   float(padrao['luminosidade']) if padrao is not None else 400.0)

if st.button("🔮 Gerar previsões e recomendações", type="primary"):
    dados_atuais = {
        'umidade_solo': umidade_solo, 'temperatura_solo': temperatura_solo,
        'ph_solo': ph_solo, 'temperatura_ar': temperatura_ar,
        'umidade_ar': umidade_ar, 'luminosidade': luminosidade,
    }
    previsoes = gerenciador.fazer_previsao_completa(dados_atuais)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Umidade prevista", f"{previsoes.get('umidade_prevista', 0):.1f}%")
    c2.metric("pH previsto", f"{previsoes.get('ph_previsto', 0):.2f}")
    c3.metric("Rendimento previsto",
              f"{previsoes.get('rendimento_previsto', 0):.2f} ton/ha")
    c4.metric("Confiança média", f"{previsoes.get('confianca', 0) * 100:.0f}%")

    st.subheader("🌾 Plano de manejo recomendado")
    sistema = SistemaRecomendacao(db)
    recomendacoes = sistema.gerar_plano_manejo_completo(dados_atuais, previsoes)
    if not recomendacoes:
        st.success("Todas as variáveis em níveis adequados — manter manejo atual.")
    for rec in recomendacoes:
        icone = {"alta": "🔴", "média": "🟡", "baixa": "🟢"}[rec['prioridade']]
        st.warning(f"{icone} **{rec['tipo_acao'].upper()}** "
                   f"(prioridade {rec['prioridade']}): {rec['justificativa']}")

    # Persiste previsao no banco (rastreabilidade)
    sensor_id = int(padrao['sensor_id']) if padrao is not None else 1
    db.inserir_previsao(sensor_id,
                        previsoes.get('umidade_prevista', 0),
                        previsoes.get('ph_previsto', 0),
                        previsoes.get('rendimento_previsto', 0),
                        previsoes.get('confianca', 0))
    st.caption("Previsão registrada na tabela `previsoes`.")
