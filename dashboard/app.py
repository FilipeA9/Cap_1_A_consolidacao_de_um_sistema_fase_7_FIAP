"""
FarmTech Solutions - Fase 7 - Dashboard integradora (evolucao da Fase 4).
Pagina inicial: visao geral da fazenda + disparo rapido dos servicos.

Execucao: streamlit run dashboard/app.py   (ou: python main.py dashboard)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.fase3_banco.db_manager import DatabaseManager

st.set_page_config(page_title="FarmTech Solutions - Fase 7",
                   page_icon="🌱", layout="wide")


@st.cache_resource
def get_db():
    return DatabaseManager()


db = get_db()

st.sidebar.title("🌱 FarmTech Solutions")
st.sidebar.markdown("**Sistema Integrado - Fase 7**")
st.sidebar.markdown("---")
st.sidebar.info(
    "Cada pagina ao lado integra o servico de uma Fase do PBL:\n\n"
    "1. Area e Insumos (Fase 1)\n"
    "2. Banco de Dados (Fases 2/3)\n"
    "3. Irrigacao IoT (Fases 2/3)\n"
    "4. Previsoes ML (Fase 4)\n"
    "5. Rendimento Safra (Fase 5)\n"
    "6. Visao Computacional (Fase 6)\n"
    "7. Alertas AWS (Fase 7)"
)

st.title("🌱 FarmTech Solutions — Sistema Integrado de Gestão Agrícola")
st.caption("Fase 7: consolidação dos serviços das Fases 1 a 6 + mensageria AWS")

# ----- Indicadores gerais -----
stats = db.obter_estatisticas()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sensores ativos", stats['total_sensores'])
c2.metric("Leituras coletadas", stats['total_leituras'])
c3.metric("Eventos de irrigação", stats['eventos_irrigacao'])
c4.metric("Alertas gerados", stats['alertas_gerados'])

if stats['total_leituras'] == 0:
    st.warning("Banco vazio. Execute `python main.py setup` (ou clique abaixo) "
               "para popular o sistema com dados simulados e treinar os modelos.")
    if st.button("▶️ Executar setup agora", type="primary"):
        with st.spinner("Executando setup (simulação + treino dos modelos)..."):
            import setup_projeto
            setup_projeto.main()
        st.cache_resource.clear()
        st.rerun()

# ----- Ultimas leituras -----
leituras = db.obter_leituras_recentes(limite=200)
if not leituras.empty:
    st.subheader("📡 Últimas leituras dos sensores")
    import plotly.express as px
    df_plot = leituras.sort_values("timestamp")
    fig = px.line(df_plot, x="timestamp",
                  y=["umidade_solo", "ph_solo", "temperatura_solo"],
                  labels={"value": "valor", "variable": "variável"},
                  title="Umidade, pH e temperatura do solo (últimas leituras)")
    st.plotly_chart(fig, use_container_width=True)

# ----- Disparo rapido de servicos (botoes da Fase 7) -----
st.subheader("⚡ Disparo rápido de serviços")
b1, b2, b3 = st.columns(3)

with b1:
    if st.button("💧 Executar ciclo de irrigação (Fase 2)"):
        from services.fase2_iot.irrigacao import executar_ciclo
        ev = executar_ciclo(db)
        estado = "LIGADA ✅" if ev['bomba_ligada'] else "desligada ⛔"
        st.success(f"Bomba {estado} — {ev['motivo']}")

with b2:
    if st.button("🚨 Rodar motor de alertas (Fase 7)"):
        from services.alertas.alert_engine import executar_todas_verificacoes
        resultados = executar_todas_verificacoes(db)
        if resultados:
            for r in resultados:
                st.warning(f"[{r.get('severidade','-')}] {r['tipo']} — {r['status']}")
        else:
            st.success("Nenhuma condição de alerta encontrada.")

with b3:
    if st.button("📤 Exportar CSVs para Oracle (Fase 3)"):
        from services.fase3_banco.export_oracle import exportar
        gerados = exportar()
        st.success(f"{len(gerados)} tabelas exportadas para a pasta exports/.")

# ----- Acoes de manejo pendentes -----
acoes = db.obter_acoes_pendentes()
if not acoes.empty:
    st.subheader("📋 Ações de manejo pendentes")
    st.dataframe(
        acoes[["cultura_nome", "tipo_acao", "descricao", "quantidade",
               "unidade", "data_acao"]],
        use_container_width=True, hide_index=True)
