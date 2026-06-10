"""Pagina do servico de Banco de Dados (Fases 2/3): CRUD, MER/DER e Oracle."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.fase3_banco.db_manager import DatabaseManager
from services.fase3_banco.export_oracle import exportar

st.set_page_config(page_title="Banco de Dados (Fases 2/3)", page_icon="🗄️",
                   layout="wide")
st.title("🗄️ Banco de Dados Estruturado — Fases 2/3")
st.caption("SQLite operacional + DDL/exportação compatíveis com Oracle "
           "(recuperação da entrega da Fase 3). MER/DER em docs/mer_der/.")

db = DatabaseManager()
tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Tabelas (CRUD)", "🔎 Consulta SQL", "📤 Exportar p/ Oracle", "🧩 MER/DER"])

with tab1:
    tabela = st.selectbox("Tabela", db.listar_tabelas())
    df = db.obter_tabela(tabela)
    st.write(f"**{len(df)}** registros")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty and "id" in df.columns:
        col1, col2 = st.columns([1, 3])
        with col1:
            registro_id = st.number_input("ID para deletar", min_value=1, step=1)
        with col2:
            st.write("")
            if st.button("🗑️ Deletar registro"):
                db.deletar_registro(tabela, int(registro_id))
                st.success(f"Registro {registro_id} removido de {tabela}.")
                st.rerun()

with tab2:
    st.caption("Apenas SELECT (consultas de leitura), como nos prints da Fase 3.")
    query = st.text_area("Consulta SQL",
                         "SELECT sensor_id, AVG(umidade_solo) AS umidade_media, "
                         "AVG(ph_solo) AS ph_medio\n"
                         "FROM leituras_sensores GROUP BY sensor_id;")
    if st.button("▶️ Executar consulta"):
        try:
            st.dataframe(db.executar_sql(query), use_container_width=True,
                         hide_index=True)
        except Exception as e:
            st.error(str(e))

with tab3:
    st.markdown(
        "Gera um CSV por tabela na pasta `exports/`, prontos para importar "
        "no **Oracle SQL Developer** (conexão `oracle.fiap.com.br:1521/ORCL`, "
        "usuário RM), seguindo o passo a passo do enunciado da Fase 3. "
        "O DDL Oracle equivalente está em `services/fase3_banco/ddl_oracle.sql`.")
    if st.button("📤 Exportar todas as tabelas", type="primary"):
        gerados = exportar()
        for tabela_, linhas, caminho in gerados:
            st.write(f"`{tabela_}` — {linhas} linhas → `{caminho}`")
        st.success("Exportação concluída.")

with tab4:
    st.markdown("### Modelo Entidade-Relacionamento (resumo)")
    st.markdown(
        "- **sensores** 1—N **leituras_sensores** (telemetria IoT)\n"
        "- **sensores** 1—N **culturas** (talhão monitorado)\n"
        "- **culturas** 1—N **acoes_manejo** e 1—N **producao**\n"
        "- **sensores** 1—N **previsoes** (saídas dos modelos de IA)\n"
        "- **eventos_irrigacao**, **deteccoes_visao** e **alertas**: "
        "tabelas de eventos das Fases 2, 6 e 7\n\n"
        "Documentação completa (DER + dicionário de dados): "
        "`docs/mer_der/modelo_dados.md`")
