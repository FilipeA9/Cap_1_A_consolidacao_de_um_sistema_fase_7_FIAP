"""Pagina do servico IoT (Fase 2): irrigacao inteligente ESP32 + clima."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.core.config import (PH_LDR_MAXIMO, PH_LDR_MINIMO,
                                  UMIDADE_MINIMA_ESP32)
from services.fase2_iot import integracao_clima
from services.fase2_iot.irrigacao import decidir_irrigacao, executar_ciclo
from services.fase2_iot.log_parser import importar
from services.fase3_banco.db_manager import DatabaseManager

st.set_page_config(page_title="Irrigação IoT (Fase 2)", page_icon="💧",
                   layout="wide")
st.title("💧 Irrigação Inteligente IoT — Fase 2")
st.caption("Mesma lógica do firmware ESP32 (sketch.ino): NPK por botões, "
           "pH via LDR (0–4095), umidade DHT22 e relé da bomba d'água. "
           "Circuito Wokwi em services/fase2_iot/diagram.json.")

db = DatabaseManager()
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎛️ Simulador interativo", "🌦️ Clima (OpenWeather)",
     "📜 Histórico/Log", "🔌 Hardware (Wokwi)"])

with tab1:
    st.markdown("Reproduza o comportamento do ESP32 ajustando os 'sensores':")
    col1, col2 = st.columns(2)
    with col1:
        umidade = st.slider("Umidade do solo — DHT22 (%)", 0.0, 100.0, 55.0)
        ph_ldr = st.slider("pH simulado — LDR (0–4095)", 0, 4095, 2000)
    with col2:
        n = st.checkbox("Botão N (nitrogênio)", value=True)
        p = st.checkbox("Botão P (fósforo)", value=True)
        k = st.checkbox("Botão K (potássio)", value=True)
        chuva = st.checkbox("Previsão de chuva (código serial '0')", value=False)

    leitura = {'umidade': umidade, 'ph_ldr': ph_ldr, 'nivel_n': n,
               'nivel_p': p, 'nivel_k': k, 'previsao_chuva': chuva}
    decisao = decidir_irrigacao(leitura)

    if decisao['bomba_ligada']:
        st.success(f"🚿 **BOMBA LIGADA** — {decisao['motivo']}")
    else:
        st.error(f"⛔ **Bomba desligada** — {decisao['motivo']}")

    st.caption(f"Regras do firmware: umidade < {UMIDADE_MINIMA_ESP32:.0f}%, "
               f"N, P e K presentes, pH entre {PH_LDR_MINIMO} e {PH_LDR_MAXIMO}, "
               "sem chuva prevista.")

    if st.button("💾 Registrar este ciclo no banco", type="primary"):
        executar_ciclo(db, forcar=leitura, fonte="dashboard")
        st.success("Ciclo gravado em eventos_irrigacao.")

with tab2:
    st.markdown("Consulta a previsão das próximas 24h e decide se a irrigação "
                "deve ser suspensa (probabilidade ≥ 30% ou volume ≥ 2 mm).")
    if st.button("🌦️ Consultar OpenWeather agora"):
        rec = integracao_clima.executar()
        if rec is None:
            st.warning("API indisponível ou OPENWEATHER_API_KEY não configurada "
                       "no arquivo .env.")
        else:
            a = rec['analise']
            st.metric("Probabilidade máx. de chuva",
                      f"{a['probabilidade_maxima']:.0f}%")
            st.metric("Volume previsto (24h)", f"{a['quantidade_total_mm']} mm")
            if rec['suspender_irrigacao']:
                st.error(f"🛑 SUSPENDER IRRIGAÇÃO — {rec['motivo']} "
                         f"(código ESP32: {rec['codigo_esp32']})")
            else:
                st.success(f"✅ IRRIGAÇÃO PERMITIDA — código ESP32: "
                           f"{rec['codigo_esp32']}")
            st.dataframe(a['blocos'], use_container_width=True, hide_index=True)

with tab3:
    eventos = db.obter_eventos_irrigacao(limite=200)
    st.write(f"**{len(eventos)}** eventos registrados")
    st.dataframe(eventos, use_container_width=True, hide_index=True)
    if st.button("📥 Importar log_irrigacao.txt da entrega da Fase 2"):
        try:
            qtd = importar(db=db)
            st.success(f"{qtd} eventos importados do log original.")
            st.rerun()
        except FileNotFoundError as e:
            st.error(str(e))

with tab4:
    st.markdown(
        "O firmware original (`sketch.ino`) e o circuito (`diagram.json`) "
        "estão versionados em `services/fase2_iot/` e podem ser executados "
        "no [Wokwi](https://wokwi.com). O código de clima (0/1) é digitado "
        "no Monitor Serial, como na entrega da Fase 2.")
    img = ROOT / "assets" / "circuito_wokwi.png"
    if img.exists():
        st.image(str(img), caption="Circuito ESP32 da Fase 2 (Wokwi)")
