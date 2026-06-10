"""
FarmTech Solutions - Fase 7 - Publicador de alertas no AWS SNS.

Publica mensagens no topico SNS `farmtech-alertas` (regiao sa-east-1,
escolhida na Fase 5 por soberania de dados e latencia). Os funcionarios
da fazenda assinam o topico por e-mail (e opcionalmente SMS) e recebem
as acoes corretivas.

Configuracao (arquivo .env):
    AWS_REGION=sa-east-1
    SNS_TOPIC_ARN=arn:aws:sns:sa-east-1:<conta>:farmtech-alertas
    AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (usuario IAM farmtech-app,
    permissao minima sns:Publish)

Se o SNS nao estiver configurado, opera em MODO SIMULADO: o alerta e
gravado no banco e impresso no console, sem envio - a dashboard indica
claramente o modo ativo. O passo a passo de criacao do topico esta em
docs/aws/passo_a_passo_sns.md.
"""

import sys
import os
from typing import Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.core.config import AWS_REGION, SNS_TOPIC_ARN


def sns_configurado() -> bool:
    """True se ha topico configurado e boto3 disponivel."""
    if not SNS_TOPIC_ARN:
        return False
    try:
        import boto3  # noqa: F401
        return True
    except ImportError:
        return False


def publicar(assunto: str, mensagem: str) -> Tuple[bool, Optional[str]]:
    """Publica no topico SNS.

    Returns:
        (enviado, message_id_ou_erro)
    """
    if not sns_configurado():
        return False, "SNS nao configurado (modo simulado)"

    try:
        import boto3
        cliente = boto3.client("sns", region_name=AWS_REGION)
        resposta = cliente.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=assunto[:100],  # limite do SNS
            Message=mensagem,
        )
        return True, resposta.get("MessageId")
    except Exception as e:
        return False, f"Erro ao publicar no SNS: {e}"


def formatar_mensagem(origem: str, tipo: str, severidade: str,
                      detalhe: str, acao_corretiva: str) -> str:
    """Padrao de mensagem recebida por e-mail/SMS pelos funcionarios."""
    from datetime import datetime
    return (
        "ALERTA FARMTECH SOLUTIONS\n"
        f"{'=' * 40}\n"
        f"Data/Hora : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"Origem    : {origem}\n"
        f"Tipo      : {tipo}\n"
        f"Severidade: {severidade.upper()}\n"
        f"{'=' * 40}\n"
        f"Situacao:\n{detalhe}\n\n"
        f"ACAO CORRETIVA RECOMENDADA:\n{acao_corretiva}\n"
        f"{'=' * 40}\n"
        "Dashboard: execute `streamlit run dashboard/app.py` para detalhes."
    )


if __name__ == "__main__":
    # Teste manual de envio (python -m services.alertas.sns_publisher)
    msg = formatar_mensagem(
        origem="teste", tipo="teste_conexao", severidade="baixa",
        detalhe="Mensagem de teste do publicador SNS.",
        acao_corretiva="Nenhuma - apenas validacao da configuracao.")
    ok, info = publicar("[FarmTech] Teste de conexao SNS", msg)
    print(f"Enviado: {ok} | {info}")
