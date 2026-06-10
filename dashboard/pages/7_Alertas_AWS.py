"""Pagina do servico de mensageria da Fase 7: alertas via AWS SNS."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.alertas import sns_publisher
from services.alertas.alert_engine import executar_todas_verificacoes
from services.core.config import AWS_REGION, SNS_TOPIC_ARN
from services.fase3_banco.db_manager import DatabaseManager

st.set_page_config(page_title="Alertas AWS (Fase 7)", page_icon="🚨",
                   layout="wide")
st.title("🚨 Serviço de Mensageria AWS — Fase 7")
st.caption("Monitora sensores (Fases 1/2) e visão computacional (Fase 6) e "
           "envia e-mail/SMS via AWS SNS com ações corretivas aos funcionários.")

db = DatabaseManager()

# ----- Status da configuracao -----
st.subheader("⚙️ Status da configuração SNS")
col1, col2 = st.columns(2)
col1.metric("Região AWS", AWS_REGION)
col2.metric("Modo", "✅ SNS real" if sns_publisher.sns_configurado()
            else "🟡 Simulado (sem envio)")
if SNS_TOPIC_ARN:
    st.code(SNS_TOPIC_ARN, language=None)
else:
    st.warning("`SNS_TOPIC_ARN` não configurado no `.env`. Os alertas são "
               "registrados no banco, mas não enviados. Siga o passo a passo "
               "em `docs/aws/passo_a_passo_sns.md` para criar o tópico "
               "`farmtech-alertas` e assinar seu e-mail.")

# ----- Regras ativas -----
with st.expander("📜 Regras de alerta e ações corretivas (definidas pelo grupo)"):
    st.markdown(
        "| Origem | Condição | Ação corretiva |\n"
        "|---|---|---|\n"
        "| IoT (Fase 2) | Umidade < 60% | Verificar bomba / irrigação manual |\n"
        "| IoT (Fase 2) | pH (LDR) fora de 1500–2500 | Calcário ou enxofre |\n"
        "| IoT (Fase 2) | N, P ou K ausentes | Fertilizante NPK (Fase 4) |\n"
        "| IoT (Fase 2) | Chuva prevista | Manter bombas desligadas |\n"
        "| Sensores (Fase 4) | Umidade do solo < 30% | Irrigação imediata ~30mm |\n"
        "| Sensores (Fase 4) | pH fora de 5.5–7.0 | Correção do solo |\n"
        "| Visão (Fase 6) | Garrafa detectada | Equipe de limpeza no talhão |")

# ----- Disparos -----
st.subheader("▶️ Disparar verificações")
b1, b2 = st.columns(2)
with b1:
    if st.button("🚨 Rodar todas as verificações agora", type="primary"):
        resultados = executar_todas_verificacoes(db)
        if not resultados:
            st.success("Nenhuma condição de alerta — fazenda dentro dos "
                       "parâmetros.")
        for r in resultados:
            st.warning(f"[{r.get('severidade', '-')}] **{r['tipo']}** — "
                       f"{r['status']}")

with b2:
    if st.button("✉️ Enviar alerta de TESTE via SNS"):
        msg = sns_publisher.formatar_mensagem(
            "dashboard", "teste_conexao", "baixa",
            "Teste de conectividade disparado pela página Alertas AWS.",
            "Nenhuma — apenas validação do tópico SNS.")
        ok, info = sns_publisher.publicar("[FarmTech] Teste de conexão SNS", msg)
        db.inserir_alerta("dashboard", "teste_conexao", "baixa",
                          "Teste de conectividade SNS", "N/A", ok,
                          info if ok else None)
        if ok:
            st.success(f"Mensagem publicada! MessageId: `{info}` — confira "
                       "seu e-mail.")
        else:
            st.error(f"Não enviado: {info}")

# ----- Historico -----
st.subheader("📜 Histórico de alertas")
alertas = db.obter_alertas(limite=200)
if alertas.empty:
    st.info("Nenhum alerta registrado ainda.")
else:
    enviados = int(alertas['enviado_sns'].sum())
    c1, c2 = st.columns(2)
    c1.metric("Alertas registrados", len(alertas))
    c2.metric("Enviados via SNS", enviados)
    st.dataframe(
        alertas[["timestamp", "origem", "tipo", "severidade", "mensagem",
                 "acao_corretiva", "enviado_sns"]],
        use_container_width=True, hide_index=True)
