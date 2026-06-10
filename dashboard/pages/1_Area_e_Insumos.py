"""Pagina do servico da Fase 1: calculo de area de plantio e insumos."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.fase1_calculos import calculos as c
from services.fase1_calculos import clima_r

st.set_page_config(page_title="Área e Insumos (Fase 1)", page_icon="📐",
                   layout="wide")
st.title("📐 Área de Plantio e Manejo de Insumos — Fase 1")
st.caption("Culturas: café (talhão retangular) e cana-de-açúcar (pivô circular). "
           "Dados organizados em vetores, com CRUD completo, como na entrega original.")

if "vetor_culturas" not in st.session_state:
    st.session_state.vetor_culturas = []

# ----- Entrada de dados -----
st.subheader("Entrada de dados")
col1, col2 = st.columns(2)
with col1:
    cultura = st.selectbox("Cultura", ["Café", "Cana-de-açúcar"])
with col2:
    if cultura == "Café":
        comprimento = st.number_input("Comprimento (m)", min_value=1.0, value=100.0)
        largura = st.number_input("Largura (m)", min_value=1.0, value=50.0)
    else:
        raio = st.number_input("Raio do pivô central (m)", min_value=1.0, value=80.0)

if st.button("➕ Calcular e adicionar ao vetor", type="primary"):
    if cultura == "Café":
        registro = c.montar_registro("cafe", "retangulo",
                                     comprimento=comprimento, largura=largura)
    else:
        registro = c.montar_registro("cana", "circulo", raio=raio)
    c.adicionar(st.session_state.vetor_culturas, registro)
    st.success(f"Área calculada: **{registro['area_hectares']:.2f} ha** — "
               "registro adicionado ao vetor.")

# ----- Saida / atualizacao / delecao -----
vetor = st.session_state.vetor_culturas
if vetor:
    st.subheader(f"Vetor de culturas ({len(vetor)} registros)")
    for i, d in enumerate(vetor):
        with st.expander(f"Registro {i+1}: {d['nome_cultura']} — "
                         f"{d['area_hectares']:.2f} ha"):
            st.write(f"Geometria: {d['geometria']}")
            st.table([
                {"Insumo": ins.capitalize(),
                 "Taxa": f"{info['taxa_por_hectare']} {info['unidade']}/ha",
                 "Total": f"{info['quantidade']} {info['unidade']}"}
                for ins, info in d['insumos'].items()
            ])
            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾 Salvar no banco (tabela culturas)", key=f"save{i}"):
                    cultura_id = c.persistir_no_banco(d)
                    st.success(f"Gravado no banco com id={cultura_id}.")
            with b2:
                if st.button("🗑️ Deletar do vetor", key=f"del{i}"):
                    c.deletar(vetor, i)
                    st.rerun()

# ----- Analise em R (entrega "ir alem" da Fase 1) -----
st.subheader("📊 Análise estatística e clima (R — Fase 1)")
st.caption("Executa o script clima.R original via Rscript. Sem R instalado, "
           "usa o fallback em Python (estatísticas + API Open-Meteo).")
if st.button("▶️ Executar análise R / fallback"):
    with st.spinner("Executando análise..."):
        saida = clima_r.executar()
    origem = "Rscript (R instalado)" if clima_r.r_disponivel() else "fallback Python"
    st.info(f"Origem da análise: {origem}")
    st.code(saida)
